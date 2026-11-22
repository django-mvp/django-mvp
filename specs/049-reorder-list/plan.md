# Implementation Plan: Reorder a list by dragging

**Branch**: `049-reorder-list` · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)

## Summary

Two Cotton components, `c-mvp.reorder` (the list) and `c-mvp.reorder.row` (one row), one Alpine
component, `mvpReorder`, registered from the bundle, and one Python helper, `mvp.ordering.save_order`.
`mvpReorder` drives SortableJS 1.15.7 directly. The row set (`c-mvp.form.formset`) reuses the same
component and the same row controls when its formset was built with `can_order`. The look is
ported from the agreed reference markup and styles (given to each dispatch from the run record,
not named in the repository) and cleaned to this package's standards.

## Technical context

- Python 3.12+, Django 5.2, 6.0 and 6.1. SortableJS 1.15.7 as a pinned development dependency,
  bundled by esbuild into the committed `mvp/static/js/django-mvp.js`.
- Browser behaviour (drag, touch, keyboard, Escape, rollback, dialog) is tested in `*_e2e.py`
  modules with Playwright, the exception Article XIV allows. Markup, the helper and the row set's
  server side are tested from rendered HTML and the Django test client.
- Front-end assets are committed artifacts: `npm run build:js:prod` after editing `assets/js/`
  and `invoke build-stylesheet` after editing `mvp/tailwind/base.css`.

## Constitution check

| Article | Applies | How |
|---|---|---|
| I Testing | yes | test-first per task. Appearance and wording untested. Behaviour, security and markup hooks tested |
| II Simplicity | yes | one component, one row, one helper. No settings, no base class, no mixin |
| III Anti-abstraction | yes | SortableJS used as it is. No wrapper layer over it |
| V Security | yes | the helper refuses any order that is not exactly the allowed records. The posted order carries the CSRF token |
| VI Documentation | yes | `docs/reorder.md`, `docs/formsets.md`, `docs/components.md`, `CONTEXT.md`, `CHANGELOG.md`, in the groups that introduce each name |
| VII Dependencies | yes | SortableJS justified in research. `deptry` untouched (a JavaScript dependency) |
| VIII i18n | yes | every label and announcement is a translatable string passed in from the template |
| XI Components are the public API | yes | new `c-mvp.reorder`, `c-mvp.reorder.row`. `c-mvp.form.formset` gains behaviour only for `can_order` |
| XIII Rendered markup is a contract | yes | the `data-` hooks the script reads are tested |
| XV Committed artifacts | yes | the bundle and stylesheet are rebuilt and committed |

## The public surface

### `c-mvp.reorder` (the list)

Renders the list element (`ol` by default) inside a root that carries `x-data="mvpReorder(...)"`.

| Prop | Meaning |
|---|---|
| `id` | required when `mode="on-demand"`, so controls can name the list |
| `label` | the list's accessible name |
| `name` | the field name for the order, default `order`. Used by the form destination and as the posted parameter |
| `form` | boolean. The rows carry a hidden input named `name` holding the row's identifier, so the surrounding form submits the order (destination 2) |
| `url` | an address the order is posted to on every change (destination 3). The answer replaces the component's root |
| `mode` | `always` (default) or `on-demand` |
| `class`, `attrs` | as every component |

A list with neither `form` nor `url` still reorders and announces its events, and sends nothing.
That is the case for a developer who reads the DOM themselves, and for the row set, which
supplies its own destination.

### `c-mvp.reorder.row`

`<li>` with the position number (a CSS counter), the slot (the title), up and down buttons and
the handle at the end. Props: `value` (the identifier, required for `form` and `url`), `label`
(the row's name, used in the buttons' accessible names and in announcements; required, because
the slot's content cannot be read reliably), `class`. The up and down buttons and the handle are hidden
until the list is active (`hidden` attribute, set by Alpine). Without scripts they stay hidden
(D7).

### Events, on the list's root element, bubbling

`mvp:reorder-start` and `mvp:reorder-end`, `detail: { source: "drag" | "button" | "mode" }`. A drag
and a button move each fire a pair. A reorder mode fires one pair around the whole mode. Inside a
mode the drags fire their own pairs, so a listener counts starts and ends.

### Reorder mode controls

Any element with `data-mvp-reorder-start="<list id>"` starts the mode. Any element with
`data-mvp-reorder-end="<list id>"` ends it. One delegated click handler on `document`, registered
once. Escape ends the mode when no drag is under way and the list is not inside an open dialog
that would take the Escape itself.

### `mvp.ordering.save_order(queryset, ids, *, field="position")`

Converts each identifier with the primary key's `to_python`, refuses (raises `InvalidOrder`, a
`ValueError`, saves nothing) an order with a duplicate, an identifier outside the queryset or a
record of the queryset left out. Otherwise numbers the records `0, 1, 2, ...` in the order given
in one `bulk_update` inside a transaction, touching only the queryset's records. Returns the
records in the new order. The developer's queryset is the access rule (D2).

## Behaviour of `mvpReorder`

- **Engine.** `new Sortable(list, { handle, draggable, animation, forceFallback: true, fallbackClass, ghostClass, chosenClass, scroll: true, scrollSensitivity, scrollSpeed, delay: 0, disabled })`. `forceFallback` so every
  pointer, mouse or finger, runs the same code and the held row follows the pointer as a clone.
  `animation` is 0 under `prefers-reduced-motion: reduce`. The handle carries `touch-action: none`
  so a drag from the handle does not scroll and a touch anywhere else does. `onStart` calls
  `navigator.vibrate(8)` where it exists.
- **Rows** are the children matching `[data-mvp-reorder-row]` that are not hidden. A row-set row
  hidden by its removal is skipped by `rows()`.
- **Escape during a drag.** A keydown handler (registered while a drag is under way) records
  `cancelled`, restores the order taken at `onStart` and ends the drag. `onEnd` of a cancelled
  drag sends and announces nothing. See Risks.
- **Buttons** move the row with `before`/`after`, refresh, put focus back on the control used,
  and announce `Moved to position n of m` in a visually hidden `role="status"` region the
  component owns. The first row's up and the last row's down carry `aria-disabled="true"` and do
  nothing.
- **Refresh** (after every move, and on a childList or `style`/`hidden` mutation of the list, and
  on `input`/`change` inside it) sets the buttons' `aria-disabled`, hides the move controls of a
  list with fewer than two rows, and, for a row set, writes `ORDER`.
- **Mode.** `active` is `true` for `always` and set by the controls for `on-demand`. While
  `active` is false Sortable is `disabled` and the move controls are hidden. A `data-reordering`
  attribute on the root is the styling and listening hook.
- **Posting.** On a move that changed the order, `htmx.ajax("POST", url, { source: root, target: root, swap: "outerHTML", values: { [name]: ids }, headers: { "X-CSRFToken": token } })`.
  A newer move aborts the request in flight (`htmx.trigger(root, "htmx:abort")`) and the last
  answer wins. On `htmx:responseError` or `htmx:sendError` the rows go back to the last
  confirmed order (the order the server rendered), the live region says the change was not saved,
  and a visible `alert` inside the root says the same until the next move.
- **Dialog.** When the root is inside a `dialog`, its `close` event restores the order the list
  had when the dialog's form was last submitted or when the page loaded, unless the enclosing form
  was submitted.

## The row set

- `c-mvp.form.formset`, when `formset.can_order`, wraps its rows and the `<template>` in one
  container carrying `mvpReorder` (`mode="always"`, destination none). `formset.js` is not
  changed: the list observes its own children, so a row the add control inserts is picked up.
- `row.html` renders `ORDER` as a hidden input (`form.ORDER.as_hidden`), skips it in the visible
  loop, and puts the move cluster in the row header (stacked layout) or a trailing track
  (tabular layout, from `sm`, beside the remove column; `formset_grid_style` adds an `auto` track
  and `formset_columns` leaves `ORDER` out when `can_order`). Inside the same place a `noscript`
  holds the typed `ORDER` field.
- `mvpReorder` writes `ORDER` values `1..n` over the visible rows in document order, for every
  row that was saved and for any other row that a field other than `ORDER` and `DELETE` has
  changed in (`defaultValue`, `defaultChecked`, `defaultSelected`), and clears the others.
- A new template filter `formset_rows` returns `formset.forms` sorted by the submitted `ORDER`
  value when the formset is bound and `can_order`, otherwise unchanged. Garbage or blank values
  sort last, stable.

## Risks

- **Escape cancel on SortableJS.** The library has no cancel. The planned route is the order
  snapshot restored in `onEnd` after a synthetic `pointerup` on the document ends the fallback
  drag, tested in headless Chrome. If it cannot be made reliable the fallback is to restore the
  snapshot from a flag in `onEnd` and drop the synthetic event, recorded in `decisions.md`.
- **Nested Alpine scopes.** `mvpReorder` sits inside `mvpFormset`, and rows carry `mvpFormsetRow`.
  Expressions in templates resolve through the scope chain, methods do not, so the row's buttons
  call `mvpReorder` methods by name from template expressions only.

## Phases

1. **US1 Group 1.** The helper `save_order` and its page.
2. **US1 Group 2.** SortableJS in the bundle, the stylesheet port, the list and row components,
   the three destinations, the engine wired for drag and the buttons.
3. **US1 Group 3.** The row set with `can_order`.
4. **US2 Group 4.** Drag and keyboard behaviour: touch, vibration, scroll, Escape, announcements,
   focus, positions, reduced motion, one or no rows.
5. **US2 Group 5.** Reorder mode, the events, rollback and overlapping posts.
6. **US2 Group 6.** The dialog, scripts off, the demo and the documentation pass.

## ADR

One ADR: reordering a row set moves elements and writes `ORDER`, and never re-indexes. It follows
ADR 0004 and is written in Group 3. The number is the next free one on `origin/main` when the
branch is pushed for the merge gate.
