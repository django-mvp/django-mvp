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
 * script in mvp/templates/cotton/layout/sidebar/index.html has already set
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

// The package defaults, exactly as the server would resolve them. A page that
// renders no shell reports these, and the documentation promises they are the
// package defaults — so they have to be a state the server could actually
// produce. `lg` with persistent false and no width is not one of them.
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
// default and the storage key (FR-006): it resolves the value before first
// paint and renders both the key (data-mvp-persist-key) and the value it
// resolved (data-mvp-persist-open) onto the checkbox. Reading them here,
// rather than restating either as a literal, is what keeps the definition
// singular.
function persistedDesktopOpen(toggle) {
  const key = toggle?.dataset.mvpPersistKey;
  if (!key) {
    // No key means no persistent drawer on this page — a shell-less page, or
    // one whose sidebar is an overlay at every width. There is nothing to
    // remember, so the store holds a plain value and writes no storage entry.
    // Naming a key here would both restate the template's rule and seed an
    // entry under a persistent drawer's key from a page that has none.
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
      // Persisted only where a persistent drawer published a key to persist
      // under. Everywhere else this is an ordinary value: nothing on the page
      // remembers an overlay drawer's state, and nothing should write one.
      desktopOpen: key ? Alpine.$persist(initial).as(key) : initial,
    },
    header: { ...DEFAULT_CONFIG.header, stuck: false },
    isWide: false,

    init() {
      // Merged field by field, rather than replacing `this.sidebar`/
      // `this.header` wholesale: `sidebar.desktopOpen` above is a $persist
      // interceptor Alpine resolved into a storage-backed getter/setter when
      // this object was first handed to Alpine.store(), and reassigning the
      // object would discard that.
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

      // Mirrors the sidebar's open state into the persisted desktop state,
      // only at/above the breakpoint — the same guard the drawer's own
      // $watch used before this state moved into the store. Alpine.watch
      // does not fire on registration, only on a later change, so the
      // checkbox's already-correct initial state is never written back.
      Alpine.watch(
        () => this.sidebar.open,
        (value) => {
          if (this.isWide) {
            this.sidebar.desktopOpen = value;
          }
        },
      );
    },

    // Called from index.js's htmx:afterSettle handler when a boosted
    // navigation replaced <body>. The fresh drawer's checkbox is server-
    // rendered closed, and the drawer itself is a new element — so
    // re-derive the resting position rather than letting a stale
    // sidebar.open (a mobile overlay left open, say) carry over: open only
    // when the viewport is wide and the remembered desktop state says so.
    // This reproduces today's behaviour exactly — a mobile overlay closes
    // on navigation, a desktop sidebar does not.
    rebindAfterNavigation() {
      this.sidebar.open = this.isWide && this.sidebar.desktopOpen;
      // The header's handler only writes on the next scroll event, and the
      // swapped-in page starts at the top. Without this the shadow survives a
      // navigation that scrolled the reader back up (FR-007).
      this.header.stuck = window.scrollY > 0;
    },
  });
}
