/*
 * PWA de sinapsis.in: registro del service worker + botón "Instalar app".
 * Incluido en TODAS las páginas (<script defer src="/assets/js/pwa.js">).
 *
 * El botón solo aparece si el navegador dispara `beforeinstallprompt`
 * (instalable y no instalada aún) — así nunca ofrece instalar en iOS/desktop
 * sin soporte ni cuando ya está instalada.
 */
(() => {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }

  let deferredPrompt = null;
  const EN = document.documentElement.lang === "en";

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (document.getElementById("pwaInstallBtn")) return;
    const btn = document.createElement("button");
    btn.id = "pwaInstallBtn";
    btn.type = "button";
    btn.textContent = EN ? "\u{1F4F2} Install app" : "\u{1F4F2} Instalar app";
    btn.setAttribute("aria-label", EN ? "Install Sinapsis as an app" : "Instalar Sinapsis como aplicación");
    btn.style.cssText =
      "position:fixed;left:16px;bottom:16px;z-index:900;padding:10px 14px;" +
      "border-radius:999px;border:1px solid #d0d7de;background:#fff;color:#0a3d62;" +
      "font:600 14px/1 Inter,system-ui,sans-serif;box-shadow:0 2px 10px rgba(0,0,0,.12);cursor:pointer";
    btn.addEventListener("click", async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice.catch(() => {});
      deferredPrompt = null;
      btn.remove();
    });
    document.body.appendChild(btn);
  });

  window.addEventListener("appinstalled", () => {
    const btn = document.getElementById("pwaInstallBtn");
    if (btn) btn.remove();
    deferredPrompt = null;
  });
})();
