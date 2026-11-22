// Alpine.data("mvpReorder"), registered in index.js (docs/adr/0035-behaviour-lives-in-registered-alpine-components.md).
import htmx from "htmx.org";
import Sortable from "sortablejs";

const ROW = "[data-mvp-reorder-row]";
const HELD = "mvp-reorder-held";
const NOT_SAVED = "The new order was not saved";

// The mode of a list an answer is about to replace, by the list's id, for the list that
// replaces it to take up.
const handover = new Map();

// The state lives in this closure, not on the Alpine object: the list can sit inside another
// component, and a member name on both would shadow the outer one.
function reorder() {
  let root = null;
  let list = null;
  let sortable = null;
  let observer = null;
  let lastOrder = [];
  let owner = null;
  let state = null;
  let status = null;
  let snapshot = [];
  let cancelled = false;
  let dragging = false;
  let confirmed = [];
  let inflight = null;
  let aborted = false;
  let notice = null;

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
    // One row, or none, has nowhere to move.
    state.movable = all.length > 1;
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

  // The answer replaces the root, so the list on the page is always the server's. A post
  // still in flight is for an older order and is dropped.
  function post(ids) {
    stop();
    const token = root.querySelector("[name=csrfmiddlewaretoken]");
    htmx.ajax("POST", root.dataset.mvpReorderUrl, {
      source: root,
      target: root,
      swap: "outerHTML",
      values: { [root.dataset.mvpReorderName]: ids },
      headers: { "X-CSRFToken": token ? token.value : "" },
    });
  }

  // The row elements in their current order, hidden ones included.
  function rowElements() {
    return [...list.children].filter((child) => child.matches(ROW) && !child.classList.contains(HELD));
  }

  // Puts the rows in the given order, each in the place a row already occupies, so anything
  // else in the list keeps its position.
  function place(wanted) {
    const current = rowElements();
    if (current.length !== wanted.length) return;
    const marks = current.map((row) => {
      const mark = document.createComment("");
      row.before(mark);
      return mark;
    });
    current.forEach((row) => row.remove());
    marks.forEach((mark, index) => mark.replaceWith(wanted[index]));
  }

  // Returns the rows to the order the server last rendered.
  function rollback() {
    const byValue = new Map(rowElements().map((row) => [row.dataset.mvpReorderValue, row]));
    const wanted = confirmed.map((value) => byValue.get(value));
    if (wanted.includes(undefined)) return;
    place(wanted);
    lastOrder = confirmed;
    refresh();
  }

  function fire(kind, source) {
    root.dispatchEvent(new CustomEvent(`mvp:reorder-${kind}`, { bubbles: true, detail: { source } }));
  }

  function showNotice() {
    const message = notice ? notice.textContent.trim() : NOT_SAVED;
    if (notice) notice.hidden = false;
    status.textContent = message;
  }

  function hideNotice() {
    if (notice) notice.hidden = true;
  }

  // A move is beginning, from either control: the last failure is no longer news.
  function begin() {
    hideNotice();
  }

  function stop() {
    if (!inflight) return false;
    const request = inflight;
    inflight = null;
    request.abort();
    return true;
  }

  // Only events of the list's own request count: the list can hold other htmx elements.
  function own(event) {
    return event.target === root;
  }

  function sent(event) {
    if (own(event)) inflight = event.detail.xhr;
  }

  function finished(event) {
    if (own(event) && inflight === event.detail.xhr) inflight = null;
  }

  // A late answer for an order that a newer move has replaced is dropped, and the answer
  // that replaces the list hands the mode on to the list that takes its place.
  function answering(event) {
    if (!own(event)) return;
    if (inflight && event.detail.xhr !== inflight) {
      event.detail.shouldSwap = false;
      return;
    }
    if (event.detail.shouldSwap !== false && root.id) handover.set(root.id, state.active);
  }

  function failed(event) {
    if (!own(event)) return;
    inflight = null;
    rollback();
    showNotice();
  }

  function onDemand() {
    return root.dataset.mvpReorderMode === "on-demand";
  }

  // Escape ends the mode, unless a drag is under way (it takes the key itself) or the list is
  // in an open dialog, which takes the key itself.
  function leave(event) {
    if (event.key !== "Escape" || event.defaultPrevented || dragging) return;
    if (root.closest("dialog[open]")) return;
    state.endMode();
  }

  // Brings what follows the mode in step with it, and fires nothing.
  function applyMode() {
    sortable.option("disabled", !state.active);
    write(root, "data-reordering", onDemand() && state.active ? "" : null);
    document.removeEventListener("keydown", leave);
    if (onDemand() && state.active) document.addEventListener("keydown", leave);
  }

  // The library has no cancel, so Escape ends the drag with the event that would end it
  // and the end handler puts the rows back. The capture phase and preventDefault keep
  // an open dialog from taking the same key.
  function cancel(event) {
    if (event.key !== "Escape") return;
    event.preventDefault();
    event.stopPropagation();
    if (cancelled) return;
    cancelled = true;
    const pointer = sortable.options.supportPointer;
    const Kind = pointer ? PointerEvent : MouseEvent;
    document.dispatchEvent(new Kind(pointer ? "pointerup" : "mouseup", { bubbles: true, cancelable: true }));
  }

  // Called once a move is over, from either control. A drag that dropped an older post
  // sends the order again even when it changed nothing.
  function changed(again) {
    const current = order();
    if (!again && current.join("\n") === lastOrder.join("\n")) return;
    lastOrder = current;
    if (root.dataset.mvpReorderUrl) post(current);
  }

  // Says where the row now is. The sentence comes from the row's controls, translated by the
  // server; the words here are only for a list that does not carry it.
  function announce(row) {
    const all = rows();
    const moves = row.querySelector("[data-mvp-reorder-moves]");
    const sentence = (moves && moves.dataset.mvpReorderMoved) || "Moved to position {position} of {total}";
    status.textContent = sentence
      .replace("{position}", String(all.indexOf(row) + 1))
      .replace("{total}", String(all.length));
  }

  function move(button, step) {
    if (button.getAttribute("aria-disabled") === "true") return;
    const row = button.closest(ROW);
    const all = rows();
    const neighbour = all[all.indexOf(row) + step];
    if (!neighbour) return;
    begin();
    fire("start", "button");
    if (step < 0) neighbour.before(row);
    else neighbour.after(row);
    refresh();
    // Moving the row dropped the focus the button held.
    button.focus();
    announce(row);
    changed();
    fire("end", "button");
  }

  return {
    active: false,
    movable: true,

    init() {
      root = this.$el;
      state = this;
      status = document.createElement("div");
      status.setAttribute("role", "status");
      status.className = "sr-only";
      root.append(status);
      list = root.querySelector("[data-mvp-reorder-list]");
      const handed = root.id && handover.get(root.id);
      if (root.id) handover.delete(root.id);
      this.active = onDemand() ? Boolean(handed) : true;
      notice = root.querySelector("[data-mvp-reorder-alert]");
      lastOrder = order();
      confirmed = lastOrder;

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
        // A second finger, or any pointer after the first, starts no drag.
        filter: (event) => event.isPrimary === false || (event.touches && event.touches.length > 1),
        disabled: !this.active,
        onStart: () => {
          snapshot = rowElements();
          cancelled = false;
          dragging = true;
          begin();
          aborted = stop();
          fire("start", "drag");
          list.classList.add("mvp-reorder-sorting");
          document.addEventListener("keydown", cancel, { capture: true });
          if (navigator.vibrate) navigator.vibrate(8);
        },
        onEnd: () => {
          document.removeEventListener("keydown", cancel, { capture: true });
          list.classList.remove("mvp-reorder-sorting");
          dragging = false;
          const again = aborted;
          aborted = false;
          if (cancelled) {
            cancelled = false;
            place(snapshot);
            refresh();
            if (again && root.dataset.mvpReorderUrl) post(order());
          } else {
            refresh();
            changed(again && Boolean(root.dataset.mvpReorderUrl));
          }
          fire("end", "drag");
        },
      });

      observer = new MutationObserver(() => {
        watch();
        refresh();
      });
      observer.observe(list, { childList: true });
      watch();
      refresh();
      applyMode();
      root.addEventListener("htmx:beforeRequest", sent);
      root.addEventListener("htmx:afterRequest", finished);
      root.addEventListener("htmx:beforeSwap", answering);
      root.addEventListener("htmx:responseError", failed);
      root.addEventListener("htmx:sendError", failed);
      owner = root.closest("form");
      if (owner) owner.addEventListener("submit", writeOrder, { capture: true });
    },

    destroy() {
      root.removeEventListener("htmx:beforeRequest", sent);
      root.removeEventListener("htmx:afterRequest", finished);
      root.removeEventListener("htmx:beforeSwap", answering);
      root.removeEventListener("htmx:responseError", failed);
      root.removeEventListener("htmx:sendError", failed);
      document.removeEventListener("keydown", leave);
      if (owner) owner.removeEventListener("submit", writeOrder, { capture: true });
      document.removeEventListener("keydown", cancel, { capture: true });
      observer.disconnect();
      sortable.destroy();
      status.remove();
    },

    // The mode of an on-demand list, begun and ended by the controls a page places.
    startMode() {
      if (!onDemand() || state.active) return;
      fire("start", "mode");
      state.active = true;
      applyMode();
    },

    endMode() {
      if (!onDemand() || !state.active) return;
      state.active = false;
      applyMode();
      fire("end", "mode");
    },

    moveUp(button) {
      move(button, -1);
    },

    moveDown(button) {
      move(button, 1);
    },
  };
}

// One handler for every control, so a control works for a list an answer has replaced.
export function registerReorder(Alpine) {
  Alpine.data("mvpReorder", reorder);
  document.addEventListener("click", (event) => {
    const control = event.target.closest("[data-mvp-reorder-start], [data-mvp-reorder-end]");
    if (!control) return;
    const starting = control.hasAttribute("data-mvp-reorder-start");
    const id = control.getAttribute(starting ? "data-mvp-reorder-start" : "data-mvp-reorder-end");
    const target = document.getElementById(id);
    if (!target || !target.matches("[data-mvp-reorder]")) return;
    const list = Alpine.$data(target);
    if (starting) list.startMode();
    else list.endMode();
  });
}
