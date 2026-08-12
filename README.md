# sinapsis-web

Sitio corporativo de Sinapsis SpA — https://sinapsis.in (GitHub Pages, dominio vía `CNAME`).

Sitio estático sin build: HTML + CSS compartido en `assets/css/site.css`.

## Estructura

- `index.html` — home ES (posicionamiento: consultoría híbrida; HumanOS producto principal)
- `en/index.html` — home EN
- Páginas legales ES: `privacy`, `datos-personales`, `cookies`, `terms`, `seguridad`, `ia-responsable`, `cumplimiento`
- Páginas legales EN: `en/privacy`, `en/terms`
- `assets/img/` — logo y favicons derivados del kit oficial; `og-image.png` para redes
- `policies/` — versiones congeladas de documentos legales con hashes y sellado de tiempo (ver `policies/README.md`)
- `docs/consent-evidence-design.md` — diseño del registro verificable de consentimientos NNA (backend HumanOS)

## Notas

- Las URLs `/privacy` y `/en/privacy` están referenciadas en la configuración de Google OAuth (QueBot) — no romperlas.
- GitHub Pages sirve `foo.html` en `/foo` (clean URLs). Localmente: `npx serve -l 4173 .` replica ese comportamiento.
- Deploy: push a `main` → GitHub Pages publica automáticamente.
- Textos legales: versiones corporativas iniciales con datos de identidad completos (RUT 78.327.684-4, domicilio Temuco, 2026-07-05); requieren revisión de asesoría legal.
