// Alpine.data("mvpReorder"), registered in index.js (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
import htmx from "htmx.org";
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
  let owner = null;

  // The rows in their current order. The fallback clone a drag holds stays inside the list, and
  // a row a form set has removed stays in the document, hidden.
  function rows() {
    return [...list.children].filter(
      (child) =>
        child.matches(ROW) &&
        !child.hidden &&
        child.style.display !== "none" &&
        !child.classList.contains(HELD),
    );
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

  // Whether a person has changed a row's own fields, which is what a form's own change check
  // reads. Both ORDER and DELETE are left out: one is written here, the other by the row.
  function edited(row) {
    return [...row.querySelectorAll("input, select, textarea")].some((control) => {
      if (control.matches("[data-mvp-reorder-order]") || control.name.endsWith("-DELETE")) return false;
      if (control.matches("[type=checkbox], [type=radio]")) return control.checked !== control.defaultChecked;
      if (control.tagName === "SELECT") {
        const options = [...control.options];
        const preset = options.some((option) => option.defaultSelected);
        return options.some((option, index) => option.selected !== (preset ? option.defaultSelected : !control.multiple && index === 0));
      }
      return control.value !== control.defaultValue;
    });
  }

  // A row set keeps ORDER in a hidden input in each row. Rows that were saved, and rows a field
  // has changed in, are numbered 1..n in the order shown; every other row stays blank, so an
  // untouched extra row is still left out by the set.
  function writeOrder() {
    let number = 0;
    rows().forEach((row) => {
      const input = row.querySelector("[data-mvp-reorder-order]");
      if (!input) return;
      const wanted = input.hasAttribute("data-mvp-reorder-saved") || edited(row);
      const value = wanted ? String((number += 1)) : "";
      if (input.value !== value) input.value = value;
    });
  }

  // Keeps what depends on a row's place in step with it: the edge buttons' disabled state, the
  // ids a posted answer's focus restore finds the buttons by, the form field's name and the
  // ORDER values of a row set.
  function refresh() {
    const all = rows();
    const form = root.hasAttribute("data-mvp-reorder-form");
    all.forEach((row, index) => {
      const up = row.querySelector("[data-mvp-reorder-up]");
      const down = row.querySelector("[data-mvp-reorder-down]");
      const value = row.dataset.mvpReorderValue;
      // A row can hold its controls twice, one for each width.
      row.querySelectorAll("[data-mvp-reorder-up]").forEach((button) => write(button, "aria-disabled", index === 0 ? "true" : null));
      row.querySelectorAll("[data-mvp-reorder-down]").forEach((button) => write(button, "aria-disabled", index === all.length - 1 ? "true" : null));
      if (root.id && value !== undefined) {
        if (up) write(up, "id", `${root.id}-${value}-up`);
        if (down) write(down, "id", `${root.id}-${value}-down`);
      }
      const input = row.querySelector("[data-mvp-reorder-input]");
      if (input && form) write(input, "name", root.dataset.mvpReorderName);
    });
    writeOrder();
  }

  // A row's own style changes when a form set removes it, and that changes which rows count.
  function watch() {
    [...list.children].filter((child) => child.matches(ROW)).forEach((row) => {
      observer.observe(row, { attributes: true, attributeFilter: ["style"] });
    });
  }

  // The answer replaces the root, so the list on the page is always the server's.
  function post(ids) {
    const token = root.querySelector("[name=csrfmiddlewaretoken]");
    htmx.ajax("POST", root.dataset.mvpReorderUrl, {
      source: root,
      target: root,
      swap: "outerHTML",
      values: { [root.dataset.mvpReorderName]: ids },
      headers: { "X-CSRFToken": token ? token.value : "" },
    });
  }

  // Called once a move is over, from either control.
  function changed() {
    const current = order();
    if (current.join("\n") === lastOrder.join("\n")) return;
    lastOrder = current;
    if (root.dataset.mvpReorderUrl) post(current);
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

      observer = new MutationObserver(() => {
        watch();
        refresh();
      });
      observer.observe(list, { childList: true });
      watch();
      refresh();
      owner = root.closest("form");
      if (owner) owner.addEventListener("submit", writeOrder, { capture: true });
    },

    destroy() {
      if (owner) owner.removeEventListener("submit", writeOrder, { capture: true });
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
