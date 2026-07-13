# Diseño: registro verificable de consentimientos NNA (HumanOS estudiante)

Especificación para el backend de HumanOS (`humanos.eco`). Complementa el sistema de
versionado de políticas de este repo (`policies/README.md`). Objetivo: poder acreditar
—años después— qué texto exacto autorizó cada apoderado/estudiante, cuándo, con qué
alcance, y que ni el texto ni el registro fueron alterados ex post (Ley 21.719).

## 1. Reglas de edad (Ley 21.719, vigencia 2026-12-01)

| Edad del estudiante | Consentimiento requerido |
|---|---|
| < 14 años | Apoderado/representante legal (el del niño no tiene valor) |
| 14–15 años | Apoderado para **datos sensibles** + asentimiento del estudiante |
| 16–17 años | Estudiante puede consentir; se mantiene autorización del apoderado como política de producto |

Decisión de producto: **se exige autorización del apoderado para todo menor de 18** y
asentimiento del propio estudiante desde los 14, porque la app puede recibir datos
sensibles por texto libre (chat IA) y un flujo único es defendible y simple.

## 2. Estados de la cuenta del estudiante

```
creada_por_colegio → pendiente_consentimiento → activa
                                              ↘ rechazada (apoderado no autoriza)
activa → suspendida_por_revocacion → datos eliminados/anonimizados (plazo definido)
```

- La cuenta se crea con los datos mínimos que provee el colegio (nombre, email, curso,
  fecha de nacimiento para determinar el flujo de edad).
- **Ningún uso de la app** hasta `activa`. El estudiante de 14+ además pasa por pantalla
  de asentimiento en su primer login.
- La revocación no borra el registro de consentimiento: agrega un registro nuevo de tipo
  `revocacion` (el historial es append-only).

## 3. Esquema del registro de consentimientos (PostgreSQL)

```sql
CREATE TABLE consent_records (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    kind            TEXT NOT NULL CHECK (kind IN ('consentimiento','asentimiento','revocacion')),
    -- quién
    student_id      UUID NOT NULL,
    guardian_id     UUID,                    -- NULL en asentimiento del estudiante
    school_id       UUID NOT NULL,
    -- qué texto exacto se aceptó (referencia al manifiesto de policies/)
    policy_doc      TEXT NOT NULL,           -- ej: 'consentimiento-nna'
    policy_version  TEXT NOT NULL,           -- ej: 'v1.0.0'
    policy_sha256   CHAR(64) NOT NULL,       -- hash del documento congelado
    -- alcance granular autorizado
    scopes          JSONB NOT NULL,          -- ej: {"uso_basico":true,"modulos_bienestar":false,...}
    -- contexto de la acción
    ip_address      INET,
    user_agent      TEXT,
    auth_token_id   UUID,                    -- token de un solo uso del mail al apoderado
    email_message_id TEXT,                   -- message-id del correo de confirmación enviado
    -- encadenamiento anti-manipulación
    prev_hash       CHAR(64) NOT NULL,       -- record_hash de la fila anterior ('0'*64 en la primera)
    record_hash     CHAR(64) NOT NULL        -- sha256 del contenido canónico de esta fila + prev_hash
);

-- Append-only: el registro no se corrige, se complementa con registros nuevos.
CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'consent_records es append-only';
END $$ LANGUAGE plpgsql;

CREATE TRIGGER consent_records_immutable
    BEFORE UPDATE OR DELETE ON consent_records
    FOR EACH ROW EXECUTE FUNCTION forbid_mutation();
```

`record_hash = sha256(canonical_json(fila sin record_hash) || prev_hash)`, con
`canonical_json` de claves ordenadas y sin espacios. Cualquier alteración de una fila
intermedia rompe la cadena y es detectable con un recorrido completo.

## 4. Anclaje periódico del registro

Job diario (cron):

1. Calcular el `record_hash` de la última fila del día (cierra la cadena del día).
2. Sellarlo vía RFC 3161 contra la TSA acreditada (mismo mecanismo que
   `scripts/timestamp_rfc3161.sh`) y/o OpenTimestamps.
3. Guardar el `.tsr`/`.ots` en almacenamiento WORM (ej: S3 Object Lock, modo compliance).

Con esto, ni siquiera un administrador de la BD puede reescribir la historia: la cadena
más el sello externo fijan el contenido y la fecha.

## 5. Flujo del mail de autorización (Opción 2)

1. Colegio carga la nómina (convenio de encargo de tratamiento firmado previamente).
2. Backend crea cuentas en `pendiente_consentimiento` y genera por apoderado un
   **token de un solo uso** (UUID, expiración 30 días, asociado a estudiante+apoderado).
3. Mail al apoderado con link `https://humanos.eco/consentimiento/<token>`.
4. La página de autorización muestra **la versión congelada vigente** del documento
   (`policy_doc/policy_version`), identifica estudiante y apoderado, y ofrece scopes
   granulares (uso básico / módulos de bienestar / comunicaciones).
5. Al autorizar: se inserta el `consent_record`, la cuenta pasa a `activa` (o queda a la
   espera del asentimiento si el estudiante tiene 14+).
6. **Correo de confirmación al apoderado con el PDF del documento adjunto**, indicando
   fecha, alcance y SHA-256. Guardar `email_message_id` y logs del proveedor: la copia en
   el buzón del apoderado es evidencia fuera de nuestro control.
7. Revocación: link permanente en el portal del apoderado → registro `revocacion` →
   cuenta `suspendida_por_revocacion` → eliminación/anonimización según política de
   retención.

## 6. Cambios de política

- Cambio material → nueva versión congelada en `policies/` → campaña de re-consentimiento;
  las cuentas cuyos apoderados no re-autoricen dentro del plazo vuelven a
  `pendiente_consentimiento` para los scopes afectados.
- Cambio no material (tipografía, datos de contacto) → nueva versión congelada igualmente
  (el hash cambia), con nota en el manifiesto; no requiere re-consentimiento, decisión que
  debe validar asesoría legal caso a caso.

## 7. Retención de evidencia

Los `consent_records`, sellos y documentos congelados se conservan mientras exista el
tratamiento **más** el plazo de prescripción de acciones (definir con asesoría legal;
referencia: 5 años). La eliminación de datos del estudiante por revocación NO elimina el
registro del consentimiento/revocación, que es la prueba de licitud del tratamiento pasado.

## Pendientes (fuera de este repo)

- [ ] Definir certificadora acreditada Ley 19.799 y su `TSA_URL` (en curso)
- [ ] Implementar esquema y flujo en backend HumanOS
- [ ] Convenio tipo de encargo de tratamiento con colegios (legal)
- [ ] Texto definitivo del consentimiento NNA (borrador en `policies/drafts/`, requiere abogado)
- [ ] Generación de PDF congelado por versión (hoy se congela el HTML servido)
