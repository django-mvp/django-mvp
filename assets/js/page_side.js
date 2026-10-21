// Alpine.data("mvpPageSide") and ("mvpPageSideToggle"), registered in index.js; the markup carries
// configuration only (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
// The panel and its button find each other by id over these two window events.
const OPEN_EVENT = "mvp-page-side-open";
const CHANGED_EVENT = "mvp-page-side-changed";

// daisyUI keeps the drawer side `visibility: hidden` until its transition
// reaches the end of the opening frame, and a hidden element cannot take focus.
const FOCUS_WAIT_MS = 1000;

// With the rest of the page inert, Tab past the last control would leave the
// document for the browser's own chrome, so it wraps within the panel instead.
const TABBABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function canTakeFocus(element) {
  return element.tabIndex >= 0 && element.type !== "hidden" && element.checkVisibility();
}

function pageSide({ id, breakpointRem }) {
  return {
    opener: null,
    inerted: [],
    media: null,
    onOpen: null,
    onKeydown: null,
    onWide: null,

    init() {
      this.onOpen = (event) => {
        if (event.detail?.id === id) {
          this.open(event.detail.opener);
        }
      };
      this.onKeydown = (event) => {
        if (!this.isOpen()) {
          return;
        }
        if (event.key === "Escape") {
          this.close();
        } else if (event.key === "Tab") {
          this.wrapTab(event);
        }
      };
      window.addEventListener(OPEN_EVENT, this.onOpen);
      window.addEventListener("keydown", this.onKeydown);

      if (breakpointRem !== undefined && window.matchMedia) {
        this.media = window.matchMedia(`(min-width: ${breakpointRem}rem)`);
        this.onWide = (event) => {
          if (event.matches && this.isOpen()) {
            this.close({ restoreFocus: false });
          }
        };
        this.media.addEventListener("change", this.onWide);
      }
    },

    destroy() {
      this.release();
      window.removeEventListener(OPEN_EVENT, this.onOpen);
      window.removeEventListener("keydown", this.onKeydown);
      this.media?.removeEventListener("change", this.onWide);
    },

    isOpen() {
      return this.$refs.toggle.checked;
    },

    // Found in the DOM, not by x-ref: the aside is its own component when it sticks, and a ref
    // inside it belongs to that one.
    closeButton() {
      return this.$el.querySelector(".mvp-page-side-close");
    },

    open(opener) {
      if (this.isOpen()) {
        return;
      }
      this.opener = opener || document.activeElement;
      this.$refs.toggle.checked = true;
      this.hideOutside();
      this.announce();
      this.focusClose();
    },

    close({ restoreFocus = true } = {}) {
      if (!this.isOpen()) {
        return;
      }
      this.$refs.toggle.checked = false;
      this.release();
      this.announce();
      if (restoreFocus && this.opener?.isConnected) {
        this.opener.focus();
      }
      this.opener = null;
    },

    wrapTab(event) {
      const aside = this.closeButton().closest("aside");
      const tabbable = [...aside.querySelectorAll(TABBABLE)].filter(canTakeFocus);
      tabbable.unshift(aside);
      const first = tabbable[0];
      const last = tabbable[tabbable.length - 1];
      const active = document.activeElement;
      if (event.shiftKey && (active === first || !aside.contains(active))) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (active === last || !aside.contains(active))) {
        event.preventDefault();
        first.focus();
      }
    },

    // Everything outside the panel, remembering exactly what this drawer
    // marked so closing it never clears an `inert` something else set.
    hideOutside() {
      for (let node = this.closeButton().closest(".drawer-side"); node && node !== document.body; node = node.parentElement) {
        for (const sibling of node.parentElement.children) {
          if (sibling !== node && !sibling.inert) {
            sibling.inert = true;
            this.inerted.push(sibling);
          }
        }
      }
    },

    release() {
      for (const element of this.inerted) {
        element.inert = false;
      }
      this.inerted = [];
    },

    focusClose() {
      const side = this.closeButton().closest(".drawer-side");
      const until = performance.now() + FOCUS_WAIT_MS;
      const attempt = () => {
        if (!this.isOpen()) {
          return;
        }
        if (getComputedStyle(side).visibility === "visible") {
          // An end panel is still translated past the edge; scrolling to it would skip the slide.
          this.closeButton().focus({ preventScroll: true });
        } else if (performance.now() < until) {
          requestAnimationFrame(attempt);
        }
      };
      requestAnimationFrame(attempt);
    },

    announce() {
      window.dispatchEvent(new CustomEvent(CHANGED_EVENT, { detail: { id, open: this.isOpen() } }));
    },
  };
}

function pageSideToggle(id) {
  return {
    expanded: false,
    onChanged: null,

    init() {
      this.onChanged = (event) => {
        if (event.detail.id === id) {
          this.expanded = event.detail.open;
        }
      };
      window.addEventListener(CHANGED_EVENT, this.onChanged);
    },

    destroy() {
      window.removeEventListener(CHANGED_EVENT, this.onChanged);
    },

    open() {
      window.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: { id, opener: this.$root } }));
    },
  };
}

export function registerPageSide(Alpine) {
  Alpine.data("mvpPageSide", pageSide);
  Alpine.data("mvpPageSideToggle", pageSideToggle);
}
