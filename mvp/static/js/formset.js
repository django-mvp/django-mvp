/**
 * Alpine components backing <c-mvp.form.formset> and <c-mvp.form.formset.row>.
 *
 * Registered on `alpine:init`, so this file has to run *before* Alpine does.
 * The packaged base template loads Alpine with `defer`, and a plain
 * (non-deferred) <script> in the body runs ahead of every deferred script, so
 * the tag the formset component emits is early enough. Adding `defer` to that
 * tag would miss the event and neither component would register.
 *
 * mvpFormset — the set as a whole. Two counters:
 *   total    monotonic. Seeds `__prefix__` substitution and TOTAL_FORMS, and
 *            is never decremented: Django reads a removed row's inputs back by
 *            index, so re-indexing would misalign every later row.
 *   visible  rows not marked for removal. This is what the add control
 *            compares against the cap, so a removed row gives its slot back.
 *
 * mvpFormsetRow — one row. A removed row is hidden, never detached: its inputs
 * stay in the document so the removal survives an invalid submission and the
 * re-render that follows.
 */
document.addEventListener("alpine:init", () => {
  Alpine.data("mvpFormset", (total = 0, maxNum = 1000) => ({
    total: total,
    visible: total,
    maxNum: maxNum,

    get canAddRow() {
      return this.visible < this.maxNum;
    },

    addRow() {
      if (!this.canAddRow) return;

      // `$root`, not `$el`. This method is called from the add control's
      // click handler, so `$el` is that button and the template is not
      // inside it. `$root` is the component's own root element either way.
      const template = this.$root.querySelector("template");
      const wrapper = document.createElement("div");
      wrapper.innerHTML = template.innerHTML
        .replaceAll("__prefix__", this.total)
        .trim();
      const row = wrapper.firstElementChild;

      template.before(row);
      Alpine.initTree(row);
      this.total++;
      this.visible++;
    },
  }));

  Alpine.data("mvpFormsetRow", (removed = false) => ({
    removed: removed,

    init() {
      // A row that arrived already marked for removal is not visible, so the
      // cap reflects what the user can actually see.
      if (this.removed) this.announceRemoval();
    },

    remove() {
      if (this.removed) return;
      this.removed = true;
      this.announceRemoval();
    },

    // The set owns `visible`, unreachable directly: Alpine 3 has no `$parent`
    // magic, so `this` inside an Alpine.data method is the row's own data,
    // not the scope chain. The event bubbles to the set's root instead.
    announceRemoval() {
      this.$dispatch("mvp-formset-row-removed");
    },
  }));
});
