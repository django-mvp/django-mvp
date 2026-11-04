// The "Install this app" page: works out which device and browser the page is
// open in, offers the browser's own install prompt where there is one, and says
// so when the page is already open in the installed app.
//
// Chromium browsers announce that a site can be installed with a
// `beforeinstallprompt` event, fired once per page load and usually before the
// page has finished loading. The listener is attached when the bundle runs, so
// the event is not missed, and it only holds the prompt back on the install
// page itself: everywhere else the browser keeps its own install offer.

const PAGE_SELECTOR = "[data-mvp-install]";

let deferredPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
  if (!document.querySelector(PAGE_SELECTOR)) {
    return;
  }
  event.preventDefault();
  deferredPrompt = event;
  document.dispatchEvent(new CustomEvent("mvp:installable"));
});

window.addEventListener("appinstalled", () => {
  deferredPrompt = null;
  document.dispatchEvent(new CustomEvent("mvp:installed"));
});

function isStandalone() {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

// One of: "ios", "android", "safari", "firefox", "chromium".
function detectDevice() {
  const agent = navigator.userAgent;
  // iPadOS reports itself as a Mac; a touch screen gives it away.
  const iOS =
    /iPad|iPhone|iPod/.test(agent) ||
    (/Macintosh/.test(agent) && navigator.maxTouchPoints > 1);
  if (iOS) {
    return "ios";
  }
  if (/Android/.test(agent)) {
    return "android";
  }
  if (/Firefox\//.test(agent)) {
    return "firefox";
  }
  if (/Safari\//.test(agent) && !/Chrome\/|Chromium\/|Edg\//.test(agent)) {
    return "safari";
  }
  return "chromium";
}

export function registerInstallPage(Alpine) {
  Alpine.data("mvpInstall", () => ({
    device: null,
    installed: false,
    justInstalled: false,
    installable: false,

    init() {
      // SKETCH ONLY: ?device=<name> shows the page as that device sees it.
      const preview = new URLSearchParams(window.location.search).get("device");
      if (preview === "installed") {
        this.installed = true;
        return;
      }
      if (preview === "chromium-prompt") {
        this.device = "chromium";
        this.installable = true;
        return;
      }
      if (preview) {
        this.device = preview;
        return;
      }

      this.installed = isStandalone();
      this.device = detectDevice();
      this.installable = deferredPrompt !== null;
      document.addEventListener("mvp:installable", () => {
        this.installable = true;
      });
      document.addEventListener("mvp:installed", () => {
        this.installable = false;
        this.justInstalled = true;
      });
    },

    async install() {
      if (!deferredPrompt) {
        // SKETCH ONLY: the previewed prompt has nothing behind it.
        this.installable = false;
        this.justInstalled = true;
        return;
      }
      const prompt = deferredPrompt;
      deferredPrompt = null;
      prompt.prompt();
      const { outcome } = await prompt.userChoice;
      // A prompt can be shown once. Dismissed, the manual steps take its place.
      this.installable = false;
      if (outcome === "accepted") {
        this.justInstalled = true;
      }
    },
  }));
}
