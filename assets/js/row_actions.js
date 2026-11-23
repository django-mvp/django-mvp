// Alpine.data("mvpRowActions"), registered in index.js (docs/adr/0035). A row declares
// each action once, as an item of its menu; this script draws them again as the buttons
// a swipe reveals and moves the one menu between the dropdown and the row's sheet.
import { upgradeDropdown } from "./dropdown.js";

// The window event a sheet trigger raises; see assets/js/sheet.js.
const SHEET_OPEN_EVENT = "mvp-sheet-open";

const ACTION = "[data-mvp-row-action]";
const REQUEST = ["get", "post", "put", "patch", "delete"]
  .flatMap((verb) => [`[hx-${verb}]`, `[data-hx-${verb}]`])
  .join(", ");
const FAILURES = ["htmx:responseError", "htmx:sendError", "htmx:timeout"];

const SLOP = 8; // px before a press counts as a swipe or a scroll
const EDGE = 20; // px at either screen edge left to the system's back gesture
const FULL = 0.6; // share of the row's width past which a swipe presses the main action
const FLICK = 0.45; // px per ms that opens or closes the row whatever its offset
const BUTTON_REM = 4.75; // resting width of one button
const CUE_MS = 8; // the vibration as the main action's point is passed
const WHEEL_MS = 140; // a trackpad swipe ends after this long with no wheel event
const COMMIT_MS = 180; // the face slides out this long before the main action runs
const SWALLOW_MS = 400; // how long the click that ends a swipe is held back
const HINT_KEY = "mvp-row-hinted"; // what the browser keeps once it has seen the nudge
const HINT_REM = 4.5; // the furthest the nudge opens a row
const HINT_WAIT_MS = 700; // the page settles this long before the nudge, and holds it
const HINT_BACK_MS = 420; // the row's trip back

// What is shared by every row: the one that stands open, the swipe in progress and
// whether the click that ends it is still to be held back.
let open = null;
let drag = null;
let swallowClick = false;

// An action's tone: danger when the item is marked so, primary for the main action.
function toneOf(item) {
  if (item.hasAttribute("data-mvp-sheet-danger")) {
    return "danger";
  }
  return item.hasAttribute("data-mvp-row-main") ? "primary" : "neutral";
}

// The item's icon as a copy that can sit beside the original: no id may appear twice.
function iconOf(item) {
  const icon = item.querySelector("i, svg")?.cloneNode(true);
  if (icon) {
    icon.removeAttribute("id");
    icon
      .querySelectorAll("[id]")
      .forEach((inner) => inner.removeAttribute("id"));
  }
  return icon;
}

function buttonFor(item) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `mvp-row-button mvp-row-button-${toneOf(item)}`;
  button.setAttribute("data-mvp-row-button", "");
  if (item.hasAttribute("data-mvp-row-main")) {
    button.setAttribute("data-mvp-row-main", "");
    button.setAttribute("data-mvp-row-full", "");
  }
  const label = item.getAttribute("aria-label");
  if (label) {
    button.setAttribute("aria-label", label);
  }
  const icon = iconOf(item);
  if (icon) {
    button.append(icon);
  }
  const words = document.createElement("span");
  words.textContent = item.textContent.trim();
  button.append(words);
  button.addEventListener("click", () => item.click());
  return button;
}

function face(row) {
  return row.querySelector(":scope > .mvp-row-face");
}

function under(row) {
  return row.querySelector(":scope > .mvp-row-under");
}

function mainButton(row) {
  return under(row).querySelector("[data-mvp-row-main]");
}

function restOf(row) {
  const rem =
    parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
  return under(row).children.length * BUTTON_REM * rem;
}

// +1 on a left-to-right page and -1 on a right-to-left one, so every offset is measured
// towards the start of the line.
function directionOf(row) {
  return getComputedStyle(row).direction === "rtl" ? -1 : 1;
}

// A gesture that starts inside the row's own sheet or dropdown panel belongs to it.
function inLayerOf(row, target) {
  const layer = target.closest("dialog, [popover]");
  return Boolean(layer) && row.contains(layer);
}

function offsetOf(row) {
  return parseFloat(row.style.getPropertyValue("--mvp-row-x") || "0");
}

function place(row, x) {
  row.style.setProperty("--mvp-row-x", `${x}px`);
}

function setFull(row, on) {
  if (row.classList.contains("is-full") === on) {
    return;
  }
  row.classList.toggle("is-full", on);
  if (on && navigator.vibrate) {
    navigator.vibrate(CUE_MS);
  }
}

// Focus goes to the first thing in the face that is not the row's own control, else to
// that control when it is the one on show.
function focusFace(row) {
  const target = [
    ...face(row).querySelectorAll("a[href], button, input, select"),
  ].find((el) => !el.closest(".mvp-row-more"));
  const control = [...row.querySelectorAll(".mvp-row-more button")].find(
    (el) => el.offsetParent !== null,
  );
  (target || control)?.focus({ preventScroll: true });
}

function shut(row, { focus = false } = {}) {
  row.classList.remove(
    "is-open",
    "is-full",
    "is-dragging",
    "is-committing",
    "is-hinting",
  );
  place(row, 0);
  under(row).inert = true;
  if (open === row) {
    open = null;
  }
  if (focus) {
    focusFace(row);
  }
}

function reveal(row) {
  if (open && open !== row) {
    shut(open);
  }
  row.classList.remove("is-dragging", "is-full");
  row.classList.add("is-open");
  place(row, -restOf(row));
  under(row).inert = false;
  open = row;
}

function fold(row) {
  if (open === row) {
    open = null;
  }
  row.style.height = `${row.offsetHeight}px`;
  row.getBoundingClientRect(); // the height is set before it changes, so it animates
  row.classList.add("is-folded");
  row.style.height = "0px";
  under(row).inert = true;
}

function unfold(row) {
  shut(row);
  row.classList.remove("is-folded");
  row.style.height = "";
}

function commit(row) {
  const button = mainButton(row);
  row.classList.remove("is-dragging");
  row.classList.add("is-committing");
  place(row, -row.offsetWidth);
  open = null;
  setTimeout(() => button.click(), COMMIT_MS);
}

function holdClick() {
  swallowClick = true;
  setTimeout(() => {
    swallowClick = false;
  }, SWALLOW_MS);
}

// A list is off while the developer has switched it off, while a reorder announces
// that it has started on it, or while an on-demand reorder list is in its mode.
const OFF = "[data-mvp-rows-off], [data-mvp-rows-paused], [data-reordering]";

function isOff(row) {
  return Boolean(row.closest(OFF));
}

// An open row in the list goes shut and a swipe under way in it is let go.
function shutWithin(list) {
  if (open && list.contains(open)) {
    shut(open);
  }
  if (drag && list.contains(drag.row)) {
    shut(drag.row);
    drag = null;
  }
  if (wheel && list.contains(wheel.row)) {
    clearTimeout(wheel.timer);
    shut(wheel.row);
    wheel = null;
  }
}

// A start is written on the element that announced it and an end takes it away, so a
// list an answer replaces cannot leave a count behind.
function announce(event) {
  const list = event.target;
  if (event.type === "mvp:reorder-start") {
    list.setAttribute("data-mvp-rows-paused", "");
    shutWithin(list);
  } else {
    list.removeAttribute("data-mvp-rows-paused");
  }
}

// A browser that cannot keep the answer is treated as having seen the nudge, so a page
// never repeats it.
function hinted() {
  try {
    return Boolean(localStorage.getItem(HINT_KEY));
  } catch {
    return true;
  }
}

function remember() {
  try {
    localStorage.setItem(HINT_KEY, "1");
  } catch {
    // Nothing to keep it in: the next page looks again and finds the same.
  }
}

function inView(row) {
  const box = row.getBoundingClientRect();
  return box.height > 0 && box.top >= 0 && box.bottom <= innerHeight;
}

// The first list a touch screen shows with swipeable rows nudges its first row open and
// back, once in this browser, so the buttons under it are seen to be there.
function nudge() {
  if (!matchMedia("(pointer: coarse)").matches || hinted()) {
    return;
  }
  const row = document.querySelector("[data-mvp-row-ready]");
  if (!row || isOff(row) || !inView(row)) {
    return;
  }
  remember();
  const rem =
    parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
  row.classList.add("is-hinting");
  under(row).inert = false;
  // A touch on the row while it moves ends the nudge: shut() takes the class away.
  const still = () => row.classList.contains("is-hinting");
  setTimeout(() => {
    if (still()) {
      place(row, -Math.min(restOf(row), HINT_REM * rem));
    }
    setTimeout(() => {
      if (still()) {
        place(row, 0);
      }
      setTimeout(() => {
        if (still()) {
          row.classList.remove("is-hinting");
          under(row).inert = true;
        }
      }, HINT_BACK_MS);
    }, HINT_WAIT_MS);
  }, HINT_WAIT_MS);
}

// A touch on a row that is being nudged ends the nudge where it stands.
function shutHint(row) {
  if (row.classList.contains("is-hinting")) {
    shut(row);
  }
}

function begin(event) {
  const row = event.target.closest("[data-mvp-row-ready]");
  if (open && open !== row) {
    shut(open);
  }
  if (!row || event.pointerType !== "touch" || inLayerOf(row, event.target)) {
    return;
  }
  if (isOff(row)) {
    return;
  }
  shutHint(row);
  if (event.target.closest(".mvp-row-under")) {
    return;
  }
  if (event.clientX < EDGE || event.clientX > innerWidth - EDGE) {
    return;
  }
  drag = {
    row,
    id: event.pointerId,
    dir: directionOf(row),
    x0: event.clientX,
    y0: event.clientY,
    base: offsetOf(row),
    axis: null,
    lastX: event.clientX,
    lastT: event.timeStamp,
    v: 0,
  };
}

function follow(event) {
  if (!drag || event.pointerId !== drag.id) {
    return;
  }
  const dx = event.clientX - drag.x0;
  const dy = event.clientY - drag.y0;
  if (!drag.axis) {
    if (Math.abs(dx) < SLOP && Math.abs(dy) < SLOP) {
      return;
    }
    drag.axis = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    if (drag.axis === "y") {
      drag = null;
      return;
    }
    drag.row.setPointerCapture?.(event.pointerId);
    drag.row.classList.add("is-dragging");
    under(drag.row).inert = false;
  }
  event.preventDefault();
  const { row, dir } = drag;
  const stop = restOf(row);
  let x = drag.base + dir * dx;
  if (x > 0) {
    x = Math.min(x * 0.2, 16); // a swipe the wrong way gives a little
  }
  if (!mainButton(row) && -x > stop) {
    x = -(stop + (-x - stop) * 0.25);
  }
  x = Math.max(x, -row.offsetWidth);
  place(row, x);
  setFull(row, Boolean(mainButton(row)) && -x > row.offsetWidth * FULL);
  const dt = event.timeStamp - drag.lastT;
  if (dt > 0) {
    drag.v = 0.8 * ((dir * (event.clientX - drag.lastX)) / dt) + 0.2 * drag.v;
  }
  drag.lastX = event.clientX;
  drag.lastT = event.timeStamp;
}

function settle(event, cancelled) {
  if (!drag || event.pointerId !== drag.id) {
    return;
  }
  const { row, axis, v } = drag;
  drag = null;
  if (!axis) {
    // A tap on an open row closes it and does nothing else.
    if (open === row && !cancelled) {
      holdClick();
      shut(row);
    }
    return;
  }
  holdClick();
  if (!cancelled && row.classList.contains("is-full")) {
    commit(row);
  } else if (v < -FLICK) {
    reveal(row);
  } else if (v > FLICK) {
    shut(row);
  } else if (-offsetOf(row) > restOf(row) / 2) {
    reveal(row);
  } else {
    shut(row);
  }
}

// The click that ends a swipe must not follow the link under the finger. A click the
// script dispatches itself, as the main action's press, is let through.
function swallow(event) {
  if (!swallowClick || !event.isTrusted) {
    return;
  }
  swallowClick = false;
  if (event.target.closest(".mvp-row-under")) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
}

// A two-finger swipe on a trackpad moves the row as a finger does.
let wheel = null;

function endWheel() {
  const { row, x } = wheel;
  clearTimeout(wheel.timer);
  wheel = null;
  if (row.classList.contains("is-full")) {
    commit(row);
  } else if (-x > restOf(row) / 2) {
    reveal(row);
  } else {
    shut(row);
  }
}

function turn(event) {
  const row = event.target.closest("[data-mvp-row-ready]");
  if (!row || inLayerOf(row, event.target) || isOff(row)) {
    return;
  }
  if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) {
    return;
  }
  event.preventDefault();
  if (wheel && wheel.row !== row) {
    endWheel();
  }
  if (!wheel) {
    if (open && open !== row) {
      shut(open);
    }
    wheel = { row, dir: directionOf(row), x: offsetOf(row) };
    row.classList.add("is-dragging");
    under(row).inert = false;
  }
  const width = row.offsetWidth;
  const hasMain = Boolean(mainButton(row));
  wheel.x = Math.min(0, Math.max(-width, wheel.x - wheel.dir * event.deltaX));
  if (!hasMain) {
    wheel.x = Math.max(wheel.x, -restOf(row) * 1.15);
  }
  place(row, wheel.x);
  setFull(row, hasMain && -wheel.x > width * FULL);
  clearTimeout(wheel.timer);
  wheel.timer = setTimeout(endWheel, WHEEL_MS);
}

function escape(event) {
  if (event.key !== "Escape" || !open) {
    return;
  }
  const row = open;
  // The key is claimed so that a dialog around the list stays open.
  event.preventDefault();
  shut(row, { focus: row.contains(document.activeElement) });
}

let listening = false;

function listen() {
  if (listening) {
    return;
  }
  listening = true;
  document.addEventListener("pointerdown", begin);
  document.addEventListener("pointermove", follow, { passive: false });
  document.addEventListener("pointerup", (event) => settle(event, false));
  document.addEventListener("pointercancel", (event) => settle(event, true));
  document.addEventListener("wheel", turn, { passive: false });
  document.addEventListener("click", swallow, true);
  document.addEventListener("keydown", escape);
  document.addEventListener("mvp:reorder-start", announce);
  document.addEventListener("mvp:reorder-end", announce);
  document.addEventListener("scroll", () => open && shut(open), {
    capture: true,
    passive: true,
  });
}

function rowActions() {
  return {
    menu: null,
    panel: null,
    onSheetOpen: null,
    onSheetClose: null,
    onMenuClick: null,
    onBeforeSend: null,
    onFailure: null,

    init() {
      listen();
      const row = this.$el;
      this.menu = row.querySelector("[data-mvp-row-menu]");
      this.panel = this.menu.parentElement;
      row.querySelectorAll("[data-mvp-dropdown]").forEach(upgradeDropdown);
      this.buildUnder();
      this.followSheet();
      row.setAttribute("data-mvp-row-ready", "");
      nudge();
    },

    destroy() {
      if (open === this.$el) {
        shut(this.$el);
      }
      window.removeEventListener(SHEET_OPEN_EVENT, this.onSheetOpen);
      this.sheet?.removeEventListener("close", this.onSheetClose);
      this.menu?.removeEventListener("click", this.onMenuClick);
      this.menu?.removeEventListener("htmx:beforeSend", this.onBeforeSend);
      FAILURES.forEach((name) =>
        this.menu?.removeEventListener(name, this.onFailure),
      );
    },

    get sheet() {
      return this.$el.querySelector("[data-mvp-sheet]");
    },

    // The layer is inert while no row is open: a keyboard user reaches each action
    // through the menu, so these buttons add nothing to the tab order.
    buildUnder() {
      const under = document.createElement("div");
      under.className = "mvp-row-under";
      under.inert = true;
      this.menu.querySelectorAll(ACTION).forEach((item) => {
        under.append(buttonFor(item));
      });
      this.$el.querySelector(":scope > .mvp-row-face").after(under);
    },

    // The menu is moved, never copied, so the actions and what the developer gave them
    // stay once on the page.
    followSheet() {
      const sheet = this.sheet;
      this.onSheetOpen = (event) => {
        if (event.detail?.id === sheet.id) {
          sheet.querySelector("[data-mvp-row-sheet-body]").append(this.menu);
        }
      };
      this.onSheetClose = () => this.panel.append(this.menu);
      // The sheet closes after the action's own click has run, so a link or a form
      // still proceeds. The dropdown's panel closes the same way.
      this.onMenuClick = (event) => {
        const item = event.target.closest(ACTION);
        if (!item) {
          return;
        }
        this.afterAction(item);
        setTimeout(() => {
          if (sheet.open) {
            sheet.close();
          }
          if (this.panel.matches(":popover-open")) {
            this.panel.hidePopover();
          }
        });
      };
      // A request folds the row once it goes out, so a declined confirmation leaves the
      // row shown; one that fails puts the row back.
      this.onBeforeSend = (event) => {
        const item = event.target.closest(ACTION);
        if (item?.hasAttribute("data-mvp-row-leaves")) {
          fold(this.$el);
        }
      };
      this.onFailure = (event) => {
        if (event.target.closest(ACTION)) {
          unfold(this.$el);
        }
      };
      window.addEventListener(SHEET_OPEN_EVENT, this.onSheetOpen);
      sheet.addEventListener("close", this.onSheetClose);
      this.menu.addEventListener("click", this.onMenuClick);
      this.menu.addEventListener("htmx:beforeSend", this.onBeforeSend);
      FAILURES.forEach((name) =>
        this.menu.addEventListener(name, this.onFailure),
      );
    },

    // A chosen action takes the row out of the list or closes it.
    afterAction(item) {
      const row = this.$el;
      if (!item.hasAttribute("data-mvp-row-leaves")) {
        if (open === row || row.classList.contains("is-committing")) {
          setTimeout(() => shut(row));
        }
      } else if (!item.matches(REQUEST)) {
        fold(row);
      } else if (row.classList.contains("is-committing")) {
        // A request that never goes out, a declined confirmation, leaves nothing to
        // fold the row, so it is put back unless the request has folded it by then.
        setTimeout(() => {
          if (!row.classList.contains("is-folded")) {
            shut(row);
          }
        });
      }
    },
  };
}

// The one global: the developer's switch for a list and the way to shut an open row.
const rows = {
  off(list) {
    list.setAttribute("data-mvp-rows-off", "");
    shutWithin(list);
  },
  on(list) {
    list.removeAttribute("data-mvp-rows-off");
  },
  shut() {
    if (open) {
      shut(open);
    }
  },
};

export function registerRowActions(Alpine) {
  window.mvpRows = rows;
  Alpine.data("mvpRowActions", rowActions);
}
