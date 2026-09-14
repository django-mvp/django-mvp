/*
 * The layout store — Alpine.store("layout", ...).
 *
 * Registered from assets/js/index.js, after Alpine.plugin(persist) and
 * before Alpine.start() — the persist plugin is what defines Alpine.$persist,
 * so a store registered any earlier could not hold a persisted property at
 * all. See index.js for where that happens.
 *
 * The ordering that keeps issue #178 fixed: Alpine calls a store's init()
 * synchronously while it registers stores, before it walks the DOM. By the
 * time init() below reads the drawer checkbox, the blocking pre-paint
 * script in mvp/templates/cotton/layout/sidebar/index.html has already set
 * its checked state. Once the checkbox itself binds to this store (T005),
 * the checked state Alpine then applies is the same value this store just
 * read from that checkbox — so nothing moves. See
 * specs/029-layout-state-store/decisions.md D5.
 *
 * A page that renders no shell (the entrance page, the error pages) has no
 * config payload and no drawer. The store still registers and reports the
 * package defaults, closed, rather than throwing.
 */

const CONFIG_SELECTOR = 'script[id$="-layout-config"]';

const DEFAULT_CONFIG = {
  breakpoint: "lg",
  persistent: false,
  breakpoint_px: null,
  collapse: "offcanvas",
  sticky: true,
  boost: false,
};

function findDrawerToggle() {
  const configScript = document.querySelector(CONFIG_SELECTOR);
  if (!configScript) {
    return null;
  }
  return document.getElementById(configScript.id.replace(/-layout-config$/, "-toggle"));
}

function parseConfig() {
  const configScript = document.querySelector(CONFIG_SELECTOR);
  if (!configScript) {
    return { ...DEFAULT_CONFIG };
  }
  try {
    return { ...DEFAULT_CONFIG, ...JSON.parse(configScript.textContent) };
  } catch (e) {
    return { ...DEFAULT_CONFIG };
  }
}

export function registerLayoutStore(Alpine) {
  Alpine.store("layout", {
    config: { ...DEFAULT_CONFIG },
    sidebarOpen: false,
    desktopOpen: Alpine.$persist(true).as("mvp-app-drawer-open"),
    isWide: false,
    headerStuck: false,

    init() {
      this.config = parseConfig();

      const toggle = findDrawerToggle();
      this.sidebarOpen = toggle ? toggle.checked : false;

      if (this.config.persistent && this.config.breakpoint_px) {
        const mq = window.matchMedia(`(min-width: ${this.config.breakpoint_px}px)`);
        this.isWide = mq.matches;
        mq.addEventListener("change", (event) => {
          this.isWide = event.matches;
        });
      }
    },
  });
}
