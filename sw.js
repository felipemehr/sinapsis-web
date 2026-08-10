/*
 * Service worker mínimo de sinapsis.in — existe para que el sitio cumpla los
 * criterios de instalabilidad PWA y los navegadores instalen la WebAPK firmada
 * (sin él, Samsung Internet empaqueta un APK local viejo que Google Play
 * Protect bloquea con "app no segura / versión anterior de Android").
 *
 * A PROPÓSITO no cachea nada: el sitio es estático y chico; sin caché no hay
 * versiones rancias que purgar. Si algún día se quiere offline, versionar acá.
 */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
// Handler de fetch presente (criterio de instalabilidad) pero passthrough:
// no responder desde el SW deja que la red siga su curso normal.
self.addEventListener("fetch", () => {});
