/*
 * The side panel's drawer — Alpine.data("mvpPageSide") and
 * Alpine.data("mvpPageSideToggle").
 *
 * Registered from assets/js/index.js before Alpine.start(). The markup in
 * mvp/templates/cotton/mvp/page/side/ carries configuration only (the
 * panel's id and the breakpoint in rem); everything the drawer does is here.
 *
 * A drawer panel and its button find each other by id through two window
 * events, so the button can sit anywhere on the page:
 *   mvp-page-side-open     {id, opener}  the button asks a panel to open
 *   mvp-page-side-changed  {id, open}    a panel reports that it opened or closed
 *
 * While the drawer is open every sibling of every ancestor of the panel is
 * made `inert`, which keeps focus and clicks inside the panel without a focus
 * trap. The dimmed overlay is a sibling of the panel and stays live, so a
 * click on it closes the drawer.
 */

const OPEN_EVENT = "mvp-page-side-open";
const CHANGED_EVENT = "mvp-page-side-changed";

// daisyUI keeps the drawer side `visibility: hidden` until its transition
// reaches the end of the opening frame, and a hidden element cannot take focus.
const FOCUS_WAIT_MS = 1000;

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
        if (event.key === "Escape" && this.isOpen()) {
          this.close();
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

    // Everything outside the panel, remembering exactly what this drawer
    // marked so closing it never clears an `inert` something else set.
    hideOutside() {
      for (let node = this.$refs.close.closest(".drawer-side"); node && node !== document.body; node = node.parentElement) {
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
      const side = this.$refs.close.closest(".drawer-side");
      const until = performance.now() + FOCUS_WAIT_MS;
      const attempt = () => {
        if (!this.isOpen()) {
          return;
        }
        if (getComputedStyle(side).visibility === "visible") {
          this.$refs.close.focus();
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
