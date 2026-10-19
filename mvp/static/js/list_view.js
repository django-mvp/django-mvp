/**
 * The list page's filter form (list_view.html, table_view.html).
 *
 * Both listeners sit on the document in the capture phase: neither `formdata`
 * nor a dialog's `close` bubbles, and capturing them there needs no element to
 * exist when this file runs.
 *
 * formdata — a field nobody set stays out of the address. An entry is dropped
 *   when its value is empty, or when it is "unknown" from a <select>: that is
 *   the empty choice of Django's NullBooleanSelect. A search for the word
 *   "unknown" is typed, not chosen, so it is kept (FS-041 FR-028).
 *
 * close — closing the filter modal without applying puts every field in it
 *   back as the page drew it, so a later toolbar change does not send what
 *   the reader abandoned (FS-041 FR-019). A select enhanced by a widget
 *   library that exposes itself as `select.tomselect` is told to redraw.
 *
 * focusin/focusout — a toolbar field that holds several values, or whatever
 *   widget the developer chose, is a [data-mvp-toolbar-field] wrapper naming
 *   its field. Its value is remembered when focus enters it, and the form is
 *   submitted when focus leaves it with a different value, so a list that
 *   opens applies once, on closing, and not at all when nothing changed
 *   (FS-041 FR-021, FR-027). The check waits a task: a widget may move focus
 *   inside itself through a moment where nothing in it has focus.
 */
(() => {
  const FORM_ID = "filterForm";
  const MODAL_ID = "filterModal";

  const chosenUnknown = (form) =>
    new Set(
      [...form.elements]
        .filter(
          (el) =>
            el.tagName === "SELECT" &&
            [...el.selectedOptions].some((option) => option.value === "unknown"),
        )
        .map((el) => el.name),
    );

  document.addEventListener(
    "formdata",
    (event) => {
      if (event.target.id !== FORM_ID) return;
      const data = event.formData;
      const fromSelect = chosenUnknown(event.target);
      const entries = [...data.entries()];
      for (const key of new Set(entries.map(([key]) => key))) data.delete(key);
      for (const [key, value] of entries) {
        if (value === "") continue;
        if (value === "unknown" && fromSelect.has(key)) continue;
        data.append(key, value);
      }
    },
    true,
  );

  const restore = (el) => {
    if (el.type === "checkbox" || el.type === "radio") {
      el.checked = el.defaultChecked;
    } else if (el.tagName === "SELECT") {
      for (const option of el.options) option.selected = option.defaultSelected;
      el.tomselect?.sync();
    } else {
      el.value = el.defaultValue;
    }
  };

  document.addEventListener(
    "close",
    (event) => {
      if (event.target.id !== MODAL_ID) return;
      event.target.querySelectorAll("input, select, textarea").forEach(restore);
    },
    true,
  );

  const started = new WeakMap();

  const valueOf = (wrapper) => {
    const form = wrapper.closest("form");
    const name = wrapper.dataset.mvpToolbarField;
    return form ? new FormData(form).getAll(name).join("\u0000") : "";
  };

  document.addEventListener("focusin", (event) => {
    const wrapper = event.target.closest?.("[data-mvp-toolbar-field]");
    if (wrapper && !started.has(wrapper)) started.set(wrapper, valueOf(wrapper));
  });

  document.addEventListener("focusout", (event) => {
    const wrapper = event.target.closest?.("[data-mvp-toolbar-field]");
    if (!wrapper) return;
    setTimeout(() => {
      if (wrapper.contains(document.activeElement)) return;
      if (!started.has(wrapper)) return;
      const changed = started.get(wrapper) !== valueOf(wrapper);
      started.delete(wrapper);
      if (changed) wrapper.closest("form").requestSubmit();
    });
  });
})();
