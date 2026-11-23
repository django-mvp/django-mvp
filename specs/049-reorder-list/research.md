# Research: Reorder a list by dragging

Research and planning fill this file. Only the checks the specification depends on are here yet.

## Assumptions checked

- **Alpine and htmx ship with the package.** `package.json` bundles `alpinejs` 3.16.1 and
  `htmx.org` 2.0.10 into `mvp/static/js/django-mvp.js`, loaded by `mvp/templates/mvp/base.html`.
  A drag library joins the same bundle, which keeps goal G14.
- **Alpine's Sort plugin matches the bundled Alpine.** `@alpinejs/sort` is published at 3.16.1,
  the version the package bundles.
- **`c-mvp.form.formset` does nothing with `ORDER` today.** Neither the row set's templates
  (`mvp/templates/cotton/mvp/form/formset/index.html`, `row.html`) nor `mvp/static/js/formset.js`
  refer to `ORDER` or `can_order`. `row.html` renders every visible field except `DELETE` through
  crispy, so an ordered formset shows `ORDER` as a number field today. That is the behaviour
  FR-021 keeps for a page without scripts, and the field FR-001 fills.
- **Rows are never re-indexed.** `formset.js` keeps a monotonic counter and hides removed rows
  rather than detaching them (ADR 0004). Reordering moves rows in the document and writes `ORDER`
  values, so it changes neither the counter nor any row's index.

## Planning notes, each answered

1. **The engine: adopted, SortableJS used directly.** SortableJS 1.15.7 (MIT) provides every
   behaviour FR-010 to FR-013 names: the held row following the pointer while the others move
   aside (`animation`, a fallback clone), page scrolling near the screen's edge (its auto-scroll
   is part of the default build, `scrollSensitivity` and `scrollSpeed` are options), a start only
   from a handle (`handle`), a start delay of zero on touch with the handle carrying
   `touch-action: none`, and dynamic children (the `draggable` selector is read on each drag, so
   rows added later work with no registration). It does not give a cancel on Escape: that is a
   small addition, recorded under Risks in `plan.md`. Alpine's Sort plugin wraps the same library
   and adds an `x-sort` directive family that this feature does not need. Everything the list needs
   beyond a plain sort (a reorder mode that switches dragging on and off, a start and end
   announcement, a rollback, a cancel) is an option or a callback of SortableJS itself, so using
   it directly in one registered Alpine component (ADR 0035) is fewer moving parts than a plugin
   plus escape hatches into it. Hand-written pointer code is not needed: nothing in the
   requirements is out of the library's reach.
2. **Every asset vendored: adopted.** `sortablejs` joins `alpinejs`, `htmx.org` and the others as
   a pinned development dependency, imported in `assets/js/index.js` and bundled into
   `mvp/static/js/django-mvp.js`, the committed artifact. Its licence header (`@license MIT`)
   is a legal comment, which esbuild keeps at the end of a bundled file. Nothing is fetched at run
   time (FR-008, SC-005).
3. **`can_order`, the position field, ADR 0004: adopted.** Rows stay in the document and are never
   re-indexed. Reordering moves a row's element and rewrites its `ORDER` value, so `TOTAL_FORMS`,
   the counter and every `name` and `id` are untouched. A bound, invalid formset lists its forms
   by index, not by order, so the row set shows them sorted by their submitted `ORDER` value
   (display only).
4. **Events for the row-actions feature: adopted.** `mvp:reorder-start` and `mvp:reorder-end`,
   dispatched on the list element, bubbling, with `detail.source` set to `drag`, `button` or
   `mode`. Documented in `docs/reorder.md`.
5. **Edit mode like a phone's music app: adopted.** A list in `mode="on-demand"` starts reordering
   from any element carrying `data-mvp-reorder-start="<list id>"`, and ends it from one carrying
   `data-mvp-reorder-end="<list id>"` or on Escape.
6. **`prefers-reduced-motion`: adopted.** SortableJS's `animation` option is set to 0 while the
   media query matches, and the package's slide transition is switched off in the same query.
7. **The look is ported: adopted.** The supplied reference markup and styles are the source for
   the row (position number, title, up and down buttons, handle at the end), the lifted held row
   and the sliding rows. The mapping is in the run record and is given to every dispatch. It is
   not named here.

## Findings the plan builds on

- **A blank extra row must stay blank.** Django skips an extra row whose fields were not changed
  and validates one that was. A row with a value in `ORDER` counts as changed, so writing
  `ORDER` into an untouched blank row would make its required fields fail. Rows that were saved
  always get a value. A row added or extra only gets one when a field other than `ORDER` and
  `DELETE` differs from what the server rendered (`defaultValue`, `defaultChecked`,
  `defaultSelected`), which is the test `has_changed` makes.
- **Two copies of one field without scripts.** A row set's `ORDER` is rendered once as a hidden
  input (the one scripts fill and Django reads) and once, as the typed number field, inside a
  `noscript` element in the row's move column. Without scripts both submit and the later one,
  the typed value, wins in Django's request data. With scripts the `noscript` content is never
  parsed as elements, so only the hidden input exists (FR-001, FR-021).
- **CSRF for a posted order.** The base template configures none for htmx. The posting list
  emits `{% csrf_token %}` inside itself and sends that value as the `X-CSRFToken` header, which
  is the documented way for a script to read it and needs no cookie.
- **Focus after a move.** Moving an element in the document drops its focus. The list puts focus
  back on the control that was used. An edge move is shown with `aria-disabled`, not `disabled`,
  so the control keeps focus when it becomes the unusable one.
- **No packaged script tag.** The component's Alpine data is registered from the bundle before
  Alpine starts. The row set's own `formset.js` is unchanged except for one event it dispatches.

## What already exists

| Piece | Search stopped at | Found |
|---|---|---|
| Drag and drop, edge scroll, touch handling | a maintained package | SortableJS 1.15.7 |
| Up and down moves | the browser | `Element.before` and `Element.after` on the row |
| Position numbers on rows | the browser | CSS counters, no script |
| A row's remove control and counters | this repo | `mvp/static/js/formset.js`, ADR 0004 |
| Alpine data registration in the bundle | this repo | ADR 0035, `assets/js/page_side.js` as the model |
| Request and error handling for a posted order | an installed package | htmx (`htmx.ajax`, `htmx:responseError`, `htmx:sendError`) |
| CSRF token for a script | Django | `{% csrf_token %}` |
| Renumbering records | new code | `mvp/ordering.py`, one function. Django has `bulk_update`; the check that the order names exactly the allowed records is the new part |
| Hidden live region for announcements | this repo | check `sr-only` use in `assets/js/search.js` and reuse the pattern |
| Reorder component, row component, `mvpReorder` | new code | nothing in this repo or its packages reorders rows |
| Reorder mode controls | new code | two `data-` attributes read by one delegated click handler |

## Citations for the engine claims

Read from the published 1.15.7 package (`sortablejs-1.15.7.tgz`, the file the lockfile will resolve),
not its documentation:

- The module build the bundle imports (`modular/sortable.esm.js`, the package's `module` field)
  mounts the auto-scroll plugin and the remove and revert plugins (`Sortable.mount(new
  AutoScrollPlugin())`, line 3359), with `scrollSensitivity: 30` as its default (line 2432 of
  `Sortable.js`).
- `forceFallback: true` turns native dragging off (`this.nativeDraggable = options.forceFallback ?
  false : supportDraggable`, line 1132 of `Sortable.js`) and the fallback ends on `pointerup` or
  `pointercancel` on the document (lines 1319 to 1325), which is where the Escape plan hooks in.
- `draggable` is matched when a drag starts (line 1197), and the children Sortable counts skip any
  with `style.display === 'none'` (line 360), so a row hidden by its removal is already skipped.
- The licence is the file's first comment (`@license MIT`, lines 1 to 6 of the module build), and
  the package ships its `LICENSE` file.
