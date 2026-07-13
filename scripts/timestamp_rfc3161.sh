#!/usr/bin/env bash
# Sella una versión congelada con una Autoridad de Sellado de Tiempo (RFC 3161).
#
# Uso:
#   scripts/timestamp_rfc3161.sh <doc> <version> [tsa_url]
#   TSA_URL=https://tsa.certificadora.cl scripts/timestamp_rfc3161.sh privacy v1.0.0
#
# Sin argumento ni TSA_URL usa freetsa.org (solo para pruebas — para valor probatorio
# pleno en Chile usar un prestador acreditado bajo la Ley 19.799).
#
# Genera junto al documento congelado:
#   timestamp.tsq      solicitud (hash SHA-256 del documento)
#   timestamp.tsr      respuesta firmada por la TSA (la evidencia)
#   timestamp.tsa.json metadatos (TSA usada, fecha, archivo, hash)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOC="${1:?Uso: timestamp_rfc3161.sh <doc> <version> [tsa_url]}"
VERSION="${2:?Falta la versión (ej: v1.0.0)}"
TSA="${3:-${TSA_URL:-https://freetsa.org/tsr}}"

DIR="$ROOT/policies/versions/$DOC/$VERSION"
[ -d "$DIR" ] || { echo "ERROR: no existe $DIR (¿congelaste la versión con policy_freeze.py?)" >&2; exit 1; }

TSQ="$DIR/timestamp.tsq"
TSR="$DIR/timestamp.tsr"
META="$DIR/timestamp.tsa.json"
[ ! -f "$TSR" ] || { echo "ERROR: $TSR ya existe. Los sellos son inmutables; no se re-sella una versión." >&2; exit 1; }

# El documento congelado es el único archivo del directorio que no es anexo de sellado.
FILE="$(find "$DIR" -maxdepth 1 -type f ! -name 'timestamp.*' ! -name '*.ots' | head -n 1)"
[ -n "$FILE" ] || { echo "ERROR: no se encontró el documento congelado en $DIR" >&2; exit 1; }

echo "Documento : ${FILE#"$ROOT"/}"
echo "TSA       : $TSA"

openssl ts -query -data "$FILE" -sha256 -cert -out "$TSQ"
curl -sS --fail -H 'Content-Type: application/timestamp-query' \
     --data-binary "@$TSQ" -o "$TSR" "$TSA"

# Validar que la respuesta sea un TimeStampResp válido y mostrar su contenido.
openssl ts -reply -in "$TSR" -text | sed -n '1,14p'

SHA256="$(sha256sum "$FILE" | cut -d' ' -f1)"
cat > "$META" <<EOF
{
  "tsa_url": "$TSA",
  "requested_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "file": "${FILE#"$ROOT"/}",
  "sha256": "$SHA256",
  "note": "Verificar con: openssl ts -verify -data <archivo> -in timestamp.tsr -CAfile <ca-de-la-tsa.pem>"
}
EOF

echo
echo "Sello guardado en ${TSR#"$ROOT"/}"
echo "Commitear los archivos timestamp.* junto a la versión congelada."
