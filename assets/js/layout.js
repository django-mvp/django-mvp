/*
 * The layout store — Alpine.store("mvp", ...).
 *
 * Registered from assets/js/index.js, after Alpine.plugin(persist) and
 * before Alpine.start() — the persist plugin is what defines Alpine.$persist,
 * so a store registered any earlier could not hold a persisted property at
 * all. See index.js for where that happens.
 *
 * Named "mvp" rather than "layout": it is a global in a namespace the
 * consuming project also writes to, and "layout" is a word a project would
 * plausibly claim for a store of its own — a second registration under the
 * same name would replace the first silently. Grouped by the component the
 * value belongs to (sidebar, header), the same shape LayoutConfig.as_dict()
 * emits — see mvp/layout.py.
 *
 * The ordering that keeps issue #178 fixed: Alpine calls a store's init()
 * synchronously while it registers stores, before it walks the DOM. By the
 * time init() below reads the drawer checkbox, the blocking pre-paint
 * script in mvp/templates/cotton/mvp/layout/sidebar/index.html has already set
 * its checked state. The checkbox's own x-model binding is applied during
 * Alpine's later DOM walk, and it writes back the value this store already
 * read from that same checkbox — so nothing moves. See
 * specs/029-layout-state-store/decisions.md D5.
 *
 * A page that renders no shell (the entrance page, the error pages) has no
 * config payload and no drawer. The store still registers and reports the
 * package defaults, closed, rather than throwing.
 */

const CONFIG_SELECTOR = 'script[id$="-layout-config"]';

// Must be a state the server could actually resolve: a shell-less page
// reports these, and the docs promise they are the package defaults.
const DEFAULT_CONFIG = {
  sidebar: {
    breakpoint: "lg",
    persistent: true,
    breakpointPx: 1024,
    collapse: "offcanvas",
    boost: false,
  },
  header: {
    sticky: true,
  },
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
  const defaults = { sidebar: { ...DEFAULT_CONFIG.sidebar }, header: { ...DEFAULT_CONFIG.header } };
  if (!configScript) {
    return defaults;
  }
  try {
    const parsed = JSON.parse(configScript.textContent);
    return {
      sidebar: { ...defaults.sidebar, ...parsed.sidebar },
      header: { ...defaults.header, ...parsed.header },
    };
  } catch (e) {
    return defaults;
  }
}

// The blocking pre-paint script is the single definition of the persisted
// default and storage key (FR-006): read its resolved values off the
// checkbox rather than restating either as a literal here.
function persistedDesktopOpen(toggle) {
  const key = toggle?.dataset.mvpPersistKey;
  if (!key) {
    // No key means no persistent drawer on this page, so there is nothing
    // to remember — naming one here would seed a storage entry under a
    // persistent drawer's key from a page that has none.
    return { key: null, initial: true };
  }
  let initial = true;
  if (toggle.dataset.mvpPersistOpen !== undefined) {
    try {
      initial = JSON.parse(toggle.dataset.mvpPersistOpen);
    } catch (e) {}
  }
  return { key, initial };
}

export function registerLayoutStore(Alpine) {
  const toggle = findDrawerToggle();
  const { key, initial } = persistedDesktopOpen(toggle);

  Alpine.store("mvp", {
    sidebar: {
      ...DEFAULT_CONFIG.sidebar,
      open: false,
      // Persisted only where a persistent drawer published a key: nothing
      // remembers an overlay drawer's state, and nothing should write one.
      desktopOpen: key ? Alpine.$persist(initial).as(key) : initial,
    },
    header: { ...DEFAULT_CONFIG.header, stuck: false },
    isWide: false,

    init() {
      // Merged field by field, not replaced wholesale: `sidebar.desktopOpen`
      // is a $persist interceptor Alpine already resolved into a storage-
      // backed getter/setter, and reassigning the object would discard that.
      const config = parseConfig();
      Object.assign(this.sidebar, config.sidebar);
      Object.assign(this.header, config.header);
      this.sidebar.open = toggle ? toggle.checked : false;

      if (this.sidebar.persistent && this.sidebar.breakpointPx) {
        const mq = window.matchMedia(`(min-width: ${this.sidebar.breakpointPx}px)`);
        this.isWide = mq.matches;
        mq.addEventListener("change", (event) => {
          this.isWide = event.matches;
        });
      }

      // Mirrors open into the persisted desktop state at/above the breakpoint
      // only, the same guard the drawer's own $watch used before this state
      // moved into the store. Alpine.watch never fires on registration.
      Alpine.watch(
        () => this.sidebar.open,
        (value) => {
          if (this.isWide) {
            this.sidebar.desktopOpen = value;
          }
        },
      );
    },

    // Called after a boosted navigation replaces <body> with a fresh,
    // server-closed drawer: re-derive the resting position rather than
    // carrying over a stale sidebar.open (a mobile overlay left open, say).
    rebindAfterNavigation() {
      this.sidebar.open = this.isWide && this.sidebar.desktopOpen;
      // The header's handler only writes on the next scroll event, and the
      // swapped-in page starts at the top. Without this the shadow survives a
      // navigation that scrolled the reader back up (FR-007).
      this.header.stuck = window.scrollY > 0;
    },
  });
}
