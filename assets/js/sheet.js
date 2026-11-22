// Alpine.data("mvpSheet") and ("mvpSheetTrigger"), registered in index.js; the markup carries
// configuration only (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
// A trigger and a sheet find each other by id over one window event.
const OPEN_EVENT = "mvp-sheet-open";

// The sm breakpoint: from here up the dialog is centred and has no grab bar.
const WIDE_QUERY = "(min-width: 40rem)";

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

// The custom property the box reads as its bottom offset (FS-047).
const KEYBOARD_PROPERTY = "--mvp-sheet-keyboard";

// The gesture's numbers (FS-047). Speeds are in px/s, distances in px or rem.
const FLICK_VELOCITY = 500;
const VELOCITY_WINDOW_MS = 100;
const SAMPLES_KEPT = 30;
// A drag past the resting height by more than this share of it is nearer closed.
const CLOSE_FRACTION = 0.25;
// A fixed sheet follows a drag up by this share of it, to at most FIXED_FOLLOW_CAP_REM.
const FIXED_FOLLOW_FRACTION = 0.25;
const FIXED_FOLLOW_CAP_REM = 1.5;
const SETTLE_MS = 250;
const SETTLE_EASING = "ease-out";
// Movement under this is a tap, not a drag.
const DRAG_SLOP = 4;
// The click that ends a drag on the grab bar arrives within this time of the release.
const CLICK_GUARD_MS = 50;

const HANDLES = "[data-mvp-sheet-grab], [data-mvp-sheet-head]";

function firstViewName(sheet) {
  return sheet.querySelector("[data-mvp-sheet-view]")?.dataset.mvpSheetView ?? "";
}

function remInPixels() {
  return parseFloat(getComputedStyle(document.documentElement).fontSize);
}

// The speed of the last stretch of a drag, positive downwards.
function velocityOf(samples) {
  const last = samples[samples.length - 1];
  const first = samples.find((sample) => last.time - sample.time <= VELOCITY_WINDOW_MS);
  const span = last.time - first.time;
  return span > 0 ? ((last.y - first.y) / span) * 1000 : 0;
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
    onPointerDown: null,
    onPointerMove: null,
    onPointerEnd: null,
    onGrabClick: null,
    drag: null,
    animation: null,
    commit: null,
    clickGuard: false,

    init() {
      this.view = firstViewName(this.$el);
      this.resetHeight();
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

    get box() {
      return this.$el.querySelector(".mvp-sheet-box");
    },

    get grab() {
      return this.$el.querySelector("[data-mvp-sheet-grab]");
    },

    get fixed() {
      return this.$el.hasAttribute("data-mvp-sheet-fixed");
    },

    get height() {
      return this.$el.dataset.height === "full" ? "full" : "rest";
    },

    // A sheet opens at rest, or at full when the developer asked for it and did not fix it.
    resetHeight() {
      this.clearGesture();
      const asked = this.$el.hasAttribute("data-mvp-sheet-full") && !this.fixed;
      this.setHeight(asked ? "full" : "rest");
    },

    setHeight(name) {
      this.$el.dataset.height = name;
      if (this.fixed) {
        this.grab?.removeAttribute("aria-expanded");
      } else {
        this.grab?.setAttribute("aria-expanded", name === "full" ? "true" : "false");
      }
    },

    // Drop whatever a drag or a settle left on the box, without settling anywhere.
    clearGesture() {
      this.animation?.cancel();
      this.animation = null;
      this.commit = null;
      if (this.drag) {
        this.releaseCapture(this.drag);
        this.drag = null;
      }
      const style = this.box?.style;
      style?.removeProperty("height");
      style?.removeProperty("max-height");
      style?.removeProperty("transform");
    },

    releaseCapture({ handle, pointerId }) {
      if (handle.hasPointerCapture(pointerId)) {
        handle.releasePointerCapture(pointerId);
      }
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

      this.onPointerDown = (event) => this.press(event);
      this.onPointerMove = (event) => this.follow(event);
      this.onPointerEnd = (event) => this.release(event);
      this.onGrabClick = (event) => this.toggle(event);
      this.$el.addEventListener("pointerdown", this.onPointerDown);
      this.$el.addEventListener("pointermove", this.onPointerMove);
      this.$el.addEventListener("pointerup", this.onPointerEnd);
      this.$el.addEventListener("pointercancel", this.onPointerEnd);
      this.$el.addEventListener("lostpointercapture", this.onPointerEnd);
      this.$el.addEventListener("click", this.onGrabClick, true);
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
      if (this.onPointerDown) {
        this.$el.removeEventListener("pointerdown", this.onPointerDown);
        this.$el.removeEventListener("pointermove", this.onPointerMove);
        this.$el.removeEventListener("pointerup", this.onPointerEnd);
        this.$el.removeEventListener("pointercancel", this.onPointerEnd);
        this.$el.removeEventListener("lostpointercapture", this.onPointerEnd);
        this.$el.removeEventListener("click", this.onGrabClick, true);
        this.onPointerDown = null;
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

    // Where the box's top edge sits at each height, read from the layout as it is now.
    measure() {
      const box = this.box;
      const keyboard = parseFloat(this.$el.style.getPropertyValue(KEYBOARD_PROPERTY)) || 0;
      const current = this.height;
      const sizes = {};
      for (const name of ["rest", "full"]) {
        this.$el.dataset.height = name;
        sizes[name] = box.offsetHeight;
      }
      this.$el.dataset.height = current;
      const bottom = this.$el.clientHeight - keyboard;
      const hasFull = !this.fixed && sizes.full > sizes.rest;
      return {
        bottom,
        edge: this.$el.clientHeight,
        restHeight: sizes.rest,
        restTop: bottom - sizes.rest,
        fullTop: bottom - (hasFull ? sizes.full : sizes.rest),
        hasFull,
        from: hasFull ? current : "rest",
        startTop: bottom - box.offsetHeight,
      };
    },

    // A box whose top edge is at `top`: taller than rest while above it, shifted down below it.
    frame(geometry, top) {
      return {
        height: Math.max(geometry.restHeight, geometry.bottom - top),
        shift: Math.max(0, top - geometry.restTop),
      };
    },

    paint({ height, shift }) {
      const style = this.box.style;
      style.height = `${height}px`;
      style.maxHeight = `${height}px`;
      style.transform = `translateY(${shift}px)`;
    },

    press(event) {
      const handle = event.target.closest(HANDLES);
      if (this.drag || !handle || !event.isPrimary || event.button !== 0) {
        return;
      }
      if (window.matchMedia(WIDE_QUERY).matches) {
        return;
      }
      this.finishSettling();
      handle.setPointerCapture(event.pointerId);
      this.drag = {
        ...this.measure(),
        handle,
        pointerId: event.pointerId,
        startY: event.clientY,
        samples: [{ y: event.clientY, time: event.timeStamp }],
        top: null,
        moved: false,
      };
      this.drag.top = this.drag.startTop;
    },

    follow(event) {
      const drag = this.drag;
      if (!drag || event.pointerId !== drag.pointerId) {
        return;
      }
      drag.samples.push({ y: event.clientY, time: event.timeStamp });
      drag.samples.splice(0, drag.samples.length - SAMPLES_KEPT);
      const distance = event.clientY - drag.startY;
      drag.moved = drag.moved || Math.abs(distance) > DRAG_SLOP;
      if (!drag.moved) {
        return;
      }
      drag.top = this.follows(drag, drag.startTop + distance);
      this.paint(this.frame(drag, drag.top));
    },

    // Where the top edge is let to go: never above full, and for a fixed sheet only a little
    // above rest.
    follows(drag, top) {
      if (drag.hasFull) {
        return Math.max(top, drag.fullTop);
      }
      if (top >= drag.restTop) {
        return top;
      }
      const cap = FIXED_FOLLOW_CAP_REM * remInPixels();
      return drag.restTop - Math.min((drag.restTop - top) * FIXED_FOLLOW_FRACTION, cap);
    },

    release(event) {
      const drag = this.drag;
      if (!drag || event.pointerId !== drag.pointerId) {
        return;
      }
      this.drag = null;
      this.releaseCapture(drag);
      if (!drag.moved) {
        return;
      }
      this.guardClick();
      if (event.type === "pointerup") {
        drag.samples.push({ y: event.clientY, time: event.timeStamp });
      }
      this.settle(drag, this.target(drag), drag.top);
    },

    // The nearest of full, rest and closed by the top edge, or one step from where the drag
    // began when it was fast enough to be a flick.
    target(drag) {
      const steps = drag.hasFull ? ["full", "rest", "closed"] : ["rest", "closed"];
      const velocity = velocityOf(drag.samples);
      if (Math.abs(velocity) >= FLICK_VELOCITY) {
        const step = steps.indexOf(drag.from) + Math.sign(velocity);
        return steps[Math.min(Math.max(step, 0), steps.length - 1)];
      }
      if (drag.top >= drag.restTop + drag.restHeight * CLOSE_FRACTION) {
        return "closed";
      }
      if (drag.hasFull && drag.top < (drag.fullTop + drag.restTop) / 2) {
        return "full";
      }
      return "rest";
    },

    // Slide the box from `top` to `name`, then make that the state. Reduced motion skips the slide.
    settle(geometry, name, top) {
      const goals = { closed: geometry.edge, full: geometry.fullTop, rest: geometry.restTop };
      const start = this.frame(geometry, top);
      const end = this.frame(geometry, goals[name]);
      if (name === "closed") {
        end.height = start.height;
        end.shift = geometry.edge - (geometry.bottom - start.height);
      }
      this.commit = () => {
        this.animation?.cancel();
        this.animation = null;
        this.commit = null;
        if (name === "closed") {
          this.$el.close();
          return;
        }
        this.setHeight(name);
        this.clearGesture();
      };
      if (window.matchMedia(REDUCED_MOTION_QUERY).matches) {
        this.commit();
        return;
      }
      const keyframe = ({ height, shift }) => ({
        height: `${height}px`,
        maxHeight: `${height}px`,
        transform: `translateY(${shift}px)`,
      });
      this.animation = this.box.animate([keyframe(start), keyframe(end)], {
        duration: SETTLE_MS,
        easing: SETTLE_EASING,
        fill: "both",
      });
      this.animation.onfinish = this.commit;
    },

    finishSettling() {
      this.commit?.();
    },

    guardClick() {
      this.clickGuard = true;
      setTimeout(() => {
        this.clickGuard = false;
      }, CLICK_GUARD_MS);
    },

    // The grab bar switches between the heights; the click that ends a drag is not a tap.
    toggle(event) {
      if (!event.target.closest("[data-mvp-sheet-grab]")) {
        return;
      }
      if (this.clickGuard) {
        event.preventDefault();
        event.stopImmediatePropagation();
        return;
      }
      if (this.fixed || window.matchMedia(WIDE_QUERY).matches) {
        return;
      }
      this.finishSettling();
      const geometry = this.measure();
      if (geometry.hasFull) {
        this.settle(geometry, this.height === "full" ? "rest" : "full", geometry.startTop);
      }
    },
  };
}

function sheetTrigger() {
  return {
    onClick: null,

    init() {
      this.onClick = (event) => {
        // A modified or non-primary click is the browser's, such as opening the link in a tab.
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
          return;
        }
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
