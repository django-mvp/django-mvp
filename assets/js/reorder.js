// Alpine.data("mvpReorder"), registered in index.js (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
import Sortable from "sortablejs";

const ROW = "[data-mvp-reorder-row]";
const HELD = "mvp-reorder-held";

// The state lives in this closure, not on the Alpine object: the list can sit inside another
// component, and a member name on both would shadow the outer one.
function reorder() {
  let root = null;
  let list = null;
  let sortable = null;
  let observer = null;
  let lastOrder = [];

  // The rows in their current order. The fallback clone a drag holds stays inside the list.
  function rows() {
    return [...list.children].filter((child) => child.matches(ROW) && !child.hidden && !child.classList.contains(HELD));
  }

  function order() {
    return rows().map((row) => row.dataset.mvpReorderValue);
  }

  function write(element, attribute, value) {
    if (value === null) {
      if (element.hasAttribute(attribute)) element.removeAttribute(attribute);
    } else if (element.getAttribute(attribute) !== value) {
      element.setAttribute(attribute, value);
    }
  }

  // Keeps what depends on a row's place in step with it: the edge buttons' disabled state, the
  // ids a posted answer's focus restore finds the buttons by, and the form field's name.
  function refresh() {
    const all = rows();
    const form = root.hasAttribute("data-mvp-reorder-form");
    all.forEach((row, index) => {
      const up = row.querySelector("[data-mvp-reorder-up]");
      const down = row.querySelector("[data-mvp-reorder-down]");
      const value = row.dataset.mvpReorderValue;
      if (up) write(up, "aria-disabled", index === 0 ? "true" : null);
      if (down) write(down, "aria-disabled", index === all.length - 1 ? "true" : null);
      if (root.id && value !== undefined) {
        if (up) write(up, "id", `${root.id}-${value}-up`);
        if (down) write(down, "id", `${root.id}-${value}-down`);
      }
      const input = row.querySelector("[data-mvp-reorder-input]");
      if (input && form) write(input, "name", root.dataset.mvpReorderName);
    });
  }

  // Called once a move is over, from either control.
  function changed() {
    const current = order();
    if (current.join("\n") === lastOrder.join("\n")) return;
    lastOrder = current;
  }

  function move(button, step) {
    if (button.getAttribute("aria-disabled") === "true") return;
    const row = button.closest(ROW);
    const all = rows();
    const neighbour = all[all.indexOf(row) + step];
    if (!neighbour) return;
    if (step < 0) neighbour.before(row);
    else neighbour.after(row);
    refresh();
    // Moving the row dropped the focus the button held.
    button.focus();
    changed();
  }

  return {
    active: false,

    init() {
      root = this.$el;
      list = root.querySelector("[data-mvp-reorder-list]");
      this.active = root.dataset.mvpReorderMode !== "on-demand";
      lastOrder = order();

      const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      sortable = new Sortable(list, {
        handle: "[data-mvp-reorder-handle]",
        draggable: ROW,
        animation: reduced ? 0 : 180,
        forceFallback: true,
        fallbackClass: HELD,
        ghostClass: "mvp-reorder-ghost",
        chosenClass: "mvp-reorder-chosen",
        scroll: true,
        scrollSensitivity: 72,
        delay: 0,
        disabled: !this.active,
        onStart: () => list.classList.add("mvp-reorder-sorting"),
        onEnd: () => {
          list.classList.remove("mvp-reorder-sorting");
          refresh();
          changed();
        },
      });

      observer = new MutationObserver(refresh);
      observer.observe(list, { childList: true });
      refresh();
    },

    destroy() {
      observer.disconnect();
      sortable.destroy();
    },

    moveUp(button) {
      move(button, -1);
    },

    moveDown(button) {
      move(button, 1);
    },
  };
}

export function registerReorder(Alpine) {
  Alpine.data("mvpReorder", reorder);
}
