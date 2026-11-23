# Tasks — 049 Reorder a list by dragging

**Branch**: `049-reorder-list` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) ·
**Spec**: [spec.md](spec.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green and the work is committed. Documentation for a public name lands in the task that introduces
it, in `docs/reorder.md`. Tests mirror the source tree: `tests/test_ordering.py`,
`tests/test_components/test_reorder.py`, `tests/test_components/test_reorder_e2e.py`,
`tests/test_components/test_form_formset_order.py` and its e2e counterpart. Browser tests are the
exception Article XIV allows.

## Checklist

- [ ] T001 [US1] `mvp.ordering.save_order` and `InvalidOrder`
- [ ] T002 [US1] SortableJS in the bundle, the stylesheet port, and the licence kept in the build
- [ ] T003 [US1] `c-mvp.reorder` and `c-mvp.reorder.row`: markup, props, `mvpReorder` with drag and buttons
- [ ] T004 [US1] The three destinations: none, the form's field, a posted address
- [ ] T005 [US1] Two lists on one page stay independent, and added rows join
- [ ] T006 [US1] The row set: `can_order` rows, `ORDER` writing, the blank row, invalid re-render
- [ ] T007 [US1] The row set's layouts: stacked, tabular, the add control, removed rows, scripts off
- [ ] T008 [US1] ADR for reordering a row set
- [ ] T009 [US2] Touch, vibration, edge scrolling, Escape during a drag
- [ ] T010 [US2] The up and down buttons: edges, focus, announcement, Tab, positions, reduced motion, one row
- [ ] T011 [US2] Reorder mode and its controls
- [ ] T012 [US2] The start and end events
- [ ] T013 [US2] A refused or failed post: rollback, notice, overlapping posts
- [ ] T014 [US2] A list in a dialog, and scripts off
- [ ] T015 [US2] The demo page and the documentation pass

## Order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015.

---

## Phase 1 — User Story 1: A developer makes a list reorderable (P1)

Delivers FR-001–FR-009, SC-001, SC-002, SC-004, SC-005.

### Group 1

#### T001 — `mvp.ordering.save_order` and `InvalidOrder`

**Files**: `mvp/ordering.py`, `tests/test_ordering.py`, `docs/reorder.md`

`save_order(queryset, ids, *, field="position")` and `InvalidOrder(ValueError)` per the plan. Tests
(model: `demo.models.ProjectTask` gains `position`, see T015; until then a test model in
`tests/` is not allowed, so add `position = models.PositiveIntegerField(default=0)` and its
migration to `ProjectTask` here, ordered by `position` then `pk`): the records renumber `0..n-1` in
the given order; records outside the queryset keep their positions; identifiers arrive as strings
and are converted; a duplicate, an identifier outside the queryset and a record left out each
raise `InvalidOrder` and change no row; the whole save is one transaction. Start `docs/reorder.md`
with the helper (a how-to for saving a received order, and the reference for the function).

### Group 2

#### T002 — SortableJS in the bundle, the stylesheet port, and the licence kept in the build

**Files**: `package.json`, `package-lock.json`, `assets/js/index.js`, `assets/js/reorder.js`,
`mvp/tailwind/base.css`, `mvp/static/css/django-mvp.css` (rebuilt), `mvp/static/js/django-mvp.js`
(rebuilt), `tests/test_frontend_runtime.py` (new test class only)

`npm install --save-dev --save-exact sortablejs@1.15.7`. `assets/js/reorder.js` exports
`registerReorder(Alpine)` (empty `mvpReorder` for now) imported and called from `index.js` before
`Alpine.start()`. Port the reference styles into `mvp/tailwind/base.css` under package names
(`.mvp-reorder`, `.mvp-reorder-row`, the held row, the ghost, the sliding rows, the handle's
`touch-action: none`, the counter for the position), using daisyUI theme variables and no
hard-coded colours. `prefers-reduced-motion` switches the slide transition off. A test that the
built bundle names no `http://` or `https://` script or style source it loads at run time (SC-005)
and still carries the SortableJS licence comment.

#### T003 — `c-mvp.reorder` and `c-mvp.reorder.row`: markup, props, `mvpReorder` with drag and buttons

**Files**: `mvp/templates/cotton/mvp/reorder/index.html`, `mvp/templates/cotton/mvp/reorder/row.html`,
`assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt), `tests/test_components/test_reorder.py`,
`tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`, `docs/components.md`, `CONTEXT.md`

The two components with the props in the plan, using the repo's `@description` / `@prop` comment
convention. `mvpReorder` creates the Sortable instance (handle, draggable, fallback, scroll,
animation) and the buttons move a row. Markup tests: roots, `data-mvp-reorder-row`, the handle and
buttons' accessible names from `label`, hidden until active, no `id` required for `mode="always"`.
Browser tests: a mouse drag of a row by its handle puts it in a new place and the rows it passed
moved; a drag from outside the handle starts nothing; the buttons swap a row with its neighbour.

#### T004 — The three destinations: none, the form's field, a posted address

**Files**: `mvp/templates/cotton/mvp/reorder/index.html`, `mvp/templates/cotton/mvp/reorder/row.html`,
`assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt), `tests/test_components/test_reorder.py`,
`tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`

`form`: each row renders a hidden input named `name` holding `value`; moving a row moves its input,
so the form submits identifiers in document order (FR-004). `url`: the list emits `{% csrf_token %}`
and, on a move that changed the order, posts as the plan says, and the answer replaces the root.
Tests: rendered hidden inputs; a form submitted after moves delivers the identifiers in the
new order to a test view (`request.POST.getlist`); a posted order reaches a test view with the
CSRF token and the response replaces the list; a view that hands the order and its queryset to
`save_order` stores it (SC-002). A list with neither sends nothing.

#### T005 — Two lists on one page stay independent, and added rows join

**Files**: `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_reorder_e2e.py`

Reordering one of two lists on a page changes neither the other's order nor its inputs (FR-009).
A row appended to the list after load, and rows arriving in an htmx swap of the list's contents,
are draggable and have working buttons, with the edge buttons' disabled state updated.

### Group 3

#### T006 — The row set: `can_order` rows, `ORDER` writing, the blank row, invalid re-render

**Files**: `mvp/templates/cotton/mvp/form/formset/index.html`, `mvp/templates/cotton/mvp/form/formset/row.html`,
`mvp/templatetags/mvp.py`, `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_form_formset_order.py`, `tests/test_components/test_form_formset_order_e2e.py`,
`docs/formsets.md`

A formset built with `can_order` renders its rows inside a `mvpReorder` container (plan, "The row
set"). `ORDER` renders as a hidden input and is skipped in the visible loop. `mvpReorder` writes
`1..n` over visible rows for saved rows and for changed rows, and clears the rest (the blank extra
row stays blank, research, "Findings"). `formset_rows` sorts a bound formset's forms by the
submitted `ORDER`. Tests: a submitted page of moved rows reaches `formset.ordered_forms` in the
new order; a formset with an untouched blank extra row is still valid after rows moved; an invalid
submission renders in the person's order with every value kept; a formset without `can_order`
renders exactly as before (the existing formset tests stay green).

#### T007 — The row set's layouts: stacked, tabular, the add control, removed rows, scripts off

**Files**: `mvp/templates/cotton/mvp/form/formset/index.html`, `mvp/templates/cotton/mvp/form/formset/row.html`,
`mvp/templatetags/mvp.py`, `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_form_formset_order.py`, `tests/test_components/test_form_formset_order_e2e.py`,
`docs/formsets.md`

Stacked layout: the move cluster sits in the row header at its end. Tabular layout: a trailing
`auto` track from `sm` up (`formset_grid_style`) and `ORDER` left out of `formset_columns`. The
`noscript` field with the typed `ORDER` input in the cluster's place. A row added with the add
control lands last and moves like the others; a removed row is skipped by the buttons and by
dragging; `TOTAL_FORMS` and every row's index are unchanged by any move (ADR 0004). Tests assert
the markup for both layouts, the move-then-add-then-remove order, and the `noscript` field.

#### T008 — ADR for reordering a row set

**Files**: `docs/adr/NNNN-reordering-a-row-set-moves-rows-and-writes-order.md`

Decision: a reorder moves the row's element and rewrites `ORDER`; rows are never re-indexed, so
ADR 0004 holds. Records: the blank-row rule, the two copies of `ORDER` and the sort of a bound,
invalid set. `NNNN` is the next free number on `origin/main` after a fetch. Public markdown, no
internal handles.

---

## Phase 2 — User Story 2: A user reorders a list (P1)

Delivers FR-010–FR-021, SC-003, SC-006.

### Group 4

#### T009 — Touch, vibration, edge scrolling, Escape during a drag

**Files**: `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_reorder_e2e.py`

A touch drag from the handle moves the row and the page does not scroll; a touch drag anywhere
else scrolls the page; the start calls `navigator.vibrate` (stubbed in the test). Near the top or
bottom of the screen the page scrolls while the pointer stays there. Escape during a drag returns
the row to where it started and sends and announces nothing (plan, Risks). A right click or a
second finger on a handle starts no drag. A drag let go outside the list places the row where the
gap was.

#### T010 — The up and down buttons: edges, focus, announcement, Tab, positions, reduced motion, one row

**Files**: `assets/js/reorder.js`, `mvp/templates/cotton/mvp/reorder/row.html`,
`mvp/static/js/django-mvp.js` (rebuilt), `tests/test_components/test_reorder.py`,
`tests/test_components/test_reorder_e2e.py`

The first row's up and the last row's down are `aria-disabled` and do nothing. Focus stays on the
control used. The live region says the new position. Tab reaches every row's two buttons and Enter
and Space use them. The position number follows each move (it is a counter, no script). Under
`prefers-reduced-motion: reduce` the animation option is 0 and no transition applies (computed
style). A list with one row or none shows no handle and no buttons.

### Group 5

#### T011 — Reorder mode and its controls

**Files**: `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_reorder.py`, `tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`

`mode="on-demand"`: not reorderable until a `data-mvp-reorder-start` control is used; handles and
buttons appear; `data-mvp-reorder-end` or Escape ends it and they go. Escape inside an open dialog
that holds the list leaves the dialog's own handling alone. Dragging is disabled outside the mode.
The controls work for lists replaced by a posted answer (delegated handler).

#### T012 — The start and end events

**Files**: `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`

`mvp:reorder-start` and `mvp:reorder-end` on the root, bubbling, with `detail.source`, for a drag,
a button move and a mode, per the plan. A listener on an ancestor receives the start before the
change and the end after it. Documented with a worked listener.

#### T013 — A refused or failed post: rollback, notice, overlapping posts

**Files**: `assets/js/reorder.js`, `mvp/templates/cotton/mvp/reorder/index.html`,
`mvp/static/js/django-mvp.js` (rebuilt), `tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`

A response with an error status, and a request that cannot be sent, return the rows to the last
confirmed order and show and announce that the change was not saved. A second move while a post
is in flight aborts it; the latest order is the one shown and sent, and a late answer for an older
one does not reapply it.

### Group 6

#### T014 — A list in a dialog, and scripts off

**Files**: `assets/js/reorder.js`, `mvp/static/js/django-mvp.js` (rebuilt),
`tests/test_components/test_reorder.py`, `tests/test_components/test_reorder_e2e.py`, `docs/reorder.md`

A list inside a `dialog` returns to the order it had when the dialog opened when it is closed
without its form being submitted, and keeps the new order when the form is submitted. Scripts off:
a page loaded with JavaScript disabled shows the rows in the saved order with no handle and no
button, and a row set shows its typed `ORDER` fields (Playwright context with
`java_script_enabled=False`).

#### T015 — The demo page and the documentation pass

**Files**: `demo/component_docs.py`, `demo/views.py`, `demo/urls.py`, `demo/templates/demo/components/reorder.html`,
`demo/models.py`, `demo/migrations/`, `tests/factories.py`, `tests/test_demo/`, `docs/reorder.md`,
`docs/components.md`, `docs/formsets.md`, `docs/index.md`, `CONTEXT.md`, `README.md`, `CHANGELOG.md`

`components/reorder/` shows a row set built with `can_order`, a list in a form, a list that posts
as it changes (and a view that refuses a bad order so the rollback shows), and a list with a
reorder mode started from a button in a toolbar. Each works at phone and desktop width. The demo
persists with `save_order`. Browser-check every page at 390 and 1280 px. Make every example in
`docs/reorder.md` true against the branch. `CONTEXT.md` gains the terms (reorderable list, handle,
reorder mode, position field). `CHANGELOG.md` gains an `Unreleased` entry.
