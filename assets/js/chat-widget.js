/*
 * Asistente Sinapsis — FAB + modal, fuente ÚNICA para TODAS las páginas.
 * (Antes el bloque vivía inline solo en index.html y el asistente
 * "desaparecía" al navegar a cualquier subpágina.)
 *
 * Inyecta el botón flotante y el modal con el chat propio embebido
 * (HumanOS Web Factory, grounded en Sinapsis, con voz). La página remota
 * permite este framing vía CSP frame-ancestors solo para sinapsis.in.
 * El iframe carga recién al primer clic (lazy). El href del FAB queda como
 * fallback (sin JS / clic con rueda abre QueBot en pestaña nueva). NO remover.
 */
(() => {
  if (document.getElementById("chatFab")) return; // idempotente
  const EN = document.documentElement.lang === "en";
  const T = EN
    ? {
        open: "Open Sinapsis assistant",
        label: "Assistant",
        title: "Sinapsis Assistant",
        sub: "Answers about our services · with voice",
        close: "Close assistant",
        frame: "Sinapsis Assistant",
      }
    : {
        open: "Abrir asistente Sinapsis",
        label: "Asistente",
        title: "Asistente Sinapsis",
        sub: "Responde sobre nuestros servicios · con voz",
        close: "Cerrar asistente",
        frame: "Asistente Sinapsis",
      };

  const host = document.createElement("div");
  host.innerHTML =
    '<a class="chat-fab" id="chatFab" href="https://quebot.sinapsis.in" target="_blank" rel="noopener" aria-label="' + T.open + '">' +
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
    "<span>" + T.label + "</span>" +
    "</a>" +
    '<div class="chat-modal-overlay" id="chatModalOverlay" role="dialog" aria-modal="true" aria-label="' + T.frame + '">' +
    '<div class="chat-modal">' +
    '<div class="chat-modal-header">' +
    '<div class="chat-modal-title">' + T.title + "<small>" + T.sub + "</small></div>" +
    '<button class="chat-modal-close" id="chatModalClose" aria-label="' + T.close + '">✕</button>' +
    "</div>" +
    '<iframe id="chatModalFrame" title="' + T.frame + '" data-src="https://www.humanos.eco/s/sinapsis/chat" allow="microphone; autoplay"></iframe>' +
    "</div></div>";
  while (host.firstChild) document.body.appendChild(host.firstChild);

  const fab = document.getElementById("chatFab");
  const overlay = document.getElementById("chatModalOverlay");
  const frame = document.getElementById("chatModalFrame");
  const close = document.getElementById("chatModalClose");
  if (!fab || !overlay || !frame || !close) return;
  const open = (e) => {
    e.preventDefault();
    if (!frame.src) frame.src = frame.dataset.src; // carga perezosa al primer clic
    overlay.classList.add("active");
  };
  const shut = () => overlay.classList.remove("active");
  fab.addEventListener("click", open);
  close.addEventListener("click", shut);
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) shut();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") shut();
  });
})();
