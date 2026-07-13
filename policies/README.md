# Versionado verificable de documentos legales

Sistema de evidencia para demostrar, ante la Agencia de Protección de Datos o un tribunal,
**qué texto exacto** aceptó un apoderado/estudiante y que **no fue modificado después**
(Ley 21.719: la carga de la prueba del consentimiento recae en el responsable).

## Cómo funciona

1. **Versiones congeladas.** Cada documento legal publicado se congela como copia inmutable
   en `versions/<doc>/<vX.Y.Z>/`. Un cambio de texto **nunca** edita una versión existente:
   se congela una versión nueva y se re-solicita consentimiento si el cambio es material.
2. **Manifiesto con hashes.** `manifest.json` registra cada versión con su SHA-256, tamaño
   y fecha de congelamiento. El registro de consentimientos (backend HumanOS) referencia
   `doc + version + sha256`, no un link mutable.
3. **Sellado de tiempo externo.** El hash de cada versión se sella ante terceros para que
   nadie —incluidos nosotros— pueda retrodatar el texto:
   - **RFC 3161** (`scripts/timestamp_rfc3161.sh`): sello firmado por una TSA. Para valor
     probatorio pleno en Chile, usar un prestador acreditado bajo la Ley 19.799
     (pendiente: definir certificadora). Mientras tanto el script usa freetsa.org como TSA
     de prueba.
   - **OpenTimestamps** (`scripts/anchor_opentimestamps.sh`, opcional): anclaje gratuito
     en la blockchain de Bitcoin.
   - **Historial público de git**: este repo es público; commits y tags firmados
     (`policy/<doc>-<version>`) son evidencia adicional alojada por un tercero (GitHub).
4. **CI de inmutabilidad** (`.github/workflows/policy-integrity.yml`): en cada PR verifica
   que los hashes coincidan con el manifiesto y que bajo `versions/` solo haya **adiciones**
   — cualquier modificación o borrado de una versión congelada hace fallar el build.

## Publicar una versión nueva (runbook)

```bash
# 1. Editar el documento fuente (ej: privacy.html) y congelar la versión
python3 scripts/policy_freeze.py privacy.html --doc privacy --version v1.1.0 \
    --title "Política de Privacidad"

# 2. Sellar ante la TSA (definir TSA_URL de la certificadora acreditada)
TSA_URL=https://tsa.certificadora.cl scripts/timestamp_rfc3161.sh privacy v1.1.0

# 3. (Opcional) anclar en OpenTimestamps
scripts/anchor_opentimestamps.sh privacy v1.1.0

# 4. Commit + tag firmado + push
git add policies/ && git commit -m "policy: privacy v1.1.0"
git tag -s policy/privacy-v1.1.0 -m "Política de Privacidad v1.1.0"
git push origin main --tags
```

Luego, en el backend de HumanOS: registrar la versión nueva y disparar re-consentimiento
de los titulares afectados si el cambio es material (ver `docs/consent-evidence-design.md`).

## Verificar integridad

```bash
python3 scripts/policy_verify.py                            # hashes vs manifiesto
python3 scripts/policy_verify.py --against-ref origin/main  # inmutabilidad
openssl ts -verify -data <doc-congelado> \
    -in <dir>/timestamp.tsr -CAfile <ca-de-la-tsa.pem>      # sello RFC 3161
```

## Qué entregar ante una auditoría o disputa

Para un consentimiento dado, el paquete de evidencia es:

1. El registro de consentimiento del backend (quién, cuándo, alcance, `doc+version+sha256`).
2. El archivo congelado de esa versión (`versions/<doc>/<version>/`) — su SHA-256 debe
   coincidir con el del registro.
3. El sello RFC 3161 (`timestamp.tsr`) y/o la prueba OpenTimestamps (`.ots`) que demuestran
   que ese hash existía antes del consentimiento.
4. El correo de confirmación que recibió el apoderado con el documento adjunto.

## Estructura

- `manifest.json` — registro append-only de versiones congeladas
- `versions/<doc>/<vX.Y.Z>/` — documento congelado + sellos (`timestamp.tsq/.tsr/.tsa.json`, `.ots`)
- `drafts/` — borradores en preparación (NO congelados, sin valor de evidencia)
