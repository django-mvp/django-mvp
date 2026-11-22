// Alpine.data("mvpSheet") and ("mvpSheetTrigger"), registered in index.js; the markup carries
// configuration only (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
// A trigger and a sheet find each other by id over one window event.
const OPEN_EVENT = "mvp-sheet-open";

// The sm breakpoint: from here up the dialog is centred and has no grab bar.
const WIDE_QUERY = "(min-width: 40rem)";

// The custom property the box reads as its bottom offset (FS-047).
const KEYBOARD_PROPERTY = "--mvp-sheet-keyboard";

function firstViewName(sheet) {
  return sheet.querySelector("[data-mvp-sheet-view]")?.dataset.mvpSheetView ?? "";
}

function sheet() {
  return {
    view: "",
    returnTo: null,
    media: null,
    onOpen: null,
    onClose: null,
    onWide: null,
    onViewport: null,
    onFocusin: null,

    init() {
      this.view = firstViewName(this.$el);
      this.onOpen = (event) => {
        const detail = event.detail ?? {};
        if (detail.id === this.$el.id) {
          this.open(detail);
        } else if (this.$el.open) {
          // The sheet taking over decides where focus goes, not the one it closes.
          this.returnTo = null;
          this.$el.close();
        }
      };
      this.onClose = () => this.afterClose();
      window.addEventListener(OPEN_EVENT, this.onOpen);
      this.$el.addEventListener("close", this.onClose);
    },

    destroy() {
      this.stopListening();
      window.removeEventListener(OPEN_EVENT, this.onOpen);
      this.$el.removeEventListener("close", this.onClose);
    },

    show(name) {
      this.view = name;
    },

    open({ view, returns, opener }) {
      const names = [...this.$el.querySelectorAll("[data-mvp-sheet-view]")].map(
        (element) => element.dataset.mvpSheetView,
      );
      this.view = names.includes(view) ? view : firstViewName(this.$el);
      this.returnTo = (returns && document.getElementById(returns)) || opener || null;
      if (!this.$el.open) {
        this.$el.showModal();
        this.startListening();
      }
    },

    afterClose() {
      this.stopListening();
      this.view = firstViewName(this.$el);
      this.resetHeight();
      const target = this.returnTo;
      this.returnTo = null;
      target?.focus();
    },

    // The two heights belong to the drag; a change of width or a close drops back to rest.
    resetHeight() {
      delete this.$el.dataset.height;
    },

    startListening() {
      this.media = window.matchMedia(WIDE_QUERY);
      this.onWide = () => this.resetHeight();
      this.media.addEventListener("change", this.onWide);

      const viewport = window.visualViewport;
      if (viewport) {
        this.onViewport = () => this.followKeyboard();
        viewport.addEventListener("resize", this.onViewport);
        viewport.addEventListener("scroll", this.onViewport);
        this.followKeyboard();
      }
      this.onFocusin = (event) => this.bringIntoView(event.target);
      this.$el.addEventListener("focusin", this.onFocusin);
    },

    stopListening() {
      this.media?.removeEventListener("change", this.onWide);
      this.media = null;
      const viewport = window.visualViewport;
      if (viewport && this.onViewport) {
        viewport.removeEventListener("resize", this.onViewport);
        viewport.removeEventListener("scroll", this.onViewport);
      }
      this.onViewport = null;
      if (this.onFocusin) {
        this.$el.removeEventListener("focusin", this.onFocusin);
        this.onFocusin = null;
      }
      this.$el.style.removeProperty(KEYBOARD_PROPERTY);
    },

    // What the on-screen keyboard covers: the layout viewport leaves the keyboard's space in,
    // the visual viewport does not.
    followKeyboard() {
      const viewport = window.visualViewport;
      const covered = Math.max(0, window.innerHeight - viewport.height - viewport.offsetTop);
      this.$el.style.setProperty(KEYBOARD_PROPERTY, `${covered}px`);
      const active = document.activeElement;
      if (active && this.$el.contains(active)) {
        this.bringIntoView(active);
      }
    },

    bringIntoView(element) {
      if (element.matches("input, textarea, select, [contenteditable]")) {
        element.scrollIntoView({ block: "nearest" });
      }
    },
  };
}

function sheetTrigger() {
  return {
    onClick: null,

    init() {
      this.onClick = (event) => {
        const { for: id, view, returns } = this.$el.dataset;
        if (!document.getElementById(id)?.hasAttribute("data-mvp-sheet")) {
          return;
        }
        event.preventDefault();
        window.dispatchEvent(
          new CustomEvent(OPEN_EVENT, { detail: { id, view, returns, opener: this.$el } }),
        );
      };
      this.$el.addEventListener("click", this.onClick);
    },

    destroy() {
      this.$el.removeEventListener("click", this.onClick);
    },
  };
}

export function registerSheet(Alpine) {
  Alpine.data("mvpSheet", sheet);
  Alpine.data("mvpSheetTrigger", sheetTrigger);
}
