#!/usr/bin/env bash
# Ancla una versión congelada en la blockchain de Bitcoin vía OpenTimestamps (gratuito).
# Complemento del sellado RFC 3161: nadie (ni nosotros) puede retrodatar el anclaje.
#
# Uso:
#   scripts/anchor_opentimestamps.sh <doc> <version>
#
# Requiere el cliente ots:  pip install opentimestamps-client
# El anclaje demora horas en confirmarse; completarlo después con:  ots upgrade <archivo>.ots
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOC="${1:?Uso: anchor_opentimestamps.sh <doc> <version>}"
VERSION="${2:?Falta la versión (ej: v1.0.0)}"

command -v ots >/dev/null || {
  echo "ERROR: cliente 'ots' no instalado. Instalar con: pip install opentimestamps-client" >&2
  exit 1
}

DIR="$ROOT/policies/versions/$DOC/$VERSION"
[ -d "$DIR" ] || { echo "ERROR: no existe $DIR" >&2; exit 1; }

FILE="$(find "$DIR" -maxdepth 1 -type f ! -name 'timestamp.*' ! -name '*.ots' | head -n 1)"
[ -n "$FILE" ] || { echo "ERROR: no se encontró el documento congelado en $DIR" >&2; exit 1; }
[ ! -f "$FILE.ots" ] || { echo "ERROR: $FILE.ots ya existe." >&2; exit 1; }

ots stamp "$FILE"
echo "Anclaje creado: ${FILE#"$ROOT"/}.ots"
echo "En ~24h, actualizar la prueba con:  ots upgrade '$FILE.ots'  y commitear el .ots final."
