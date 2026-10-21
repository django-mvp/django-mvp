# Implementation Plan: A side panel beside a page's content

**Branch**: `042-page-side-panel` · **Spec**: [spec.md](spec.md) · **Research**: [research.md](research.md)
· **Sketch**: [sketch.md](sketch.md) · **Epic**: #569 · **PR**: #570

## Summary

A page fills one new block, `page.side`, with `<c-mvp.page.side>`. `<c-mvp.page.layout>` lays the
title, content and panel out together: a CSS grid from the panel's breakpoint, a column below it.
Below the breakpoint the panel is daisyUI's drawer, kept inside the panel and driven by a registered
Alpine component, or it stacks. The package publishes the sticky header's height as
`--mvp-header-height` and pads the document's scroll by it. Every list and table page draws the
filterset fields its toolbar does not in `<c-mvp.page.list.filters.panel>`, whose fields join the
toolbar's form through the `form` attribute; the filter modal is removed.

## Technical context

Python 3.12+, Django 5.2–6.1, django-cotton 2.8, daisy-cotton 0.2, django-filter 26, htmx 2.0.10,
Alpine 3.16 (bundled, `assets/js/` → `mvp/static/js/django-mvp.js`), Tailwind v4 + daisyUI 5
(`mvp/tailwind/base.css` → `mvp/static/css/django-mvp.css`). Tests: pytest, pytest-django,
BeautifulSoup for markup, pytest-playwright (Chromium) for what needs a browser (Article XIV).

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every task test-first; markup contracts with the test client, browser tests only for scrolling, sticking, focus, `inert`, media queries and form submission |
| II/III Simplicity | No new dependency, no base class. One template filter, three components, one JS module, one view attribute dict |
| VI/XVII Docs | Each story updates the `docs/` page for the names it introduces, plus CHANGELOG |
| XI Components | `c-mvp.page.side`, `c-mvp.page.side.toggle`, `c-mvp.page.layout`, `c-mvp.page.list.filters.panel` under `cotton/mvp/` |
| XII Config | Every option is a component attribute; the list page's come through one view dict |
| XIII Markup contract | Landmark, name, order and ARIA asserted per component |
| XV Artifacts | `invoke build-js` and `invoke build-stylesheet` re-run and committed in each task that changes their inputs |
| XVI Compatibility | The modal's removal and the context-key renames are CHANGELOG breaking entries |
| XVIII Attr dict | `filter_panel_attrs`, replaced not merged |
| ADR 0013 | The panel's `<aside>` is the scroller: `tabindex="0"`, named by its heading |
| ADR 0014 | Widths are a fixed set of three, by name; the header height never reaches markup |
| ADR 0021 | One static CSS rule per breakpoint, keyed on attributes the panel renders |
| ADR 0032 | Package templates call components with `only` where they read nothing else |

## Design

### Markup of `<c-mvp.page.side>`

Attributes: `label` (required), `id` (default `page-side`), `width` `sm|md|lg` (default `md`),
`breakpoint` `lg|xl|2xl|False` (default `xl`), `collapse` `drawer|stack` (default `drawer`), `align`
`title|content` (default `title`), `position` `start|end` (default `end`), `:sticky` (default
`True`), `class`.

```
<div class="mvp-page-side {bp}:mvp-page-side-wide {class}"
     data-mvp-side-width data-mvp-side-breakpoint (only when breakpoint) data-mvp-side-collapse
     data-mvp-side-position data-mvp-side-align [data-mvp-side-sticky]
     [x-data="mvpPageSide({ id, breakpoint })"   — drawer only, configuration only]>
  drawer:  <div class="drawer drawer-{start|end} {bp}:drawer-open">
             <input type="checkbox" class="drawer-toggle" tabindex="-1" aria-hidden="true" x-ref="toggle">
             <div class="drawer-content"></div>
             <div class="drawer-side z-40">
               <label class="drawer-overlay" aria-hidden="true" @click.prevent="close()"></label>
               <aside id="{id}" class="mvp-page-side-panel …" aria-labelledby="{id}-label" tabindex="0">
                 heading row: <h2 id="{id}-label"> + close button (aria-label "Close {label}")
                 {slot}
               </aside>
           </div></div>
  stack:   <aside id="{id}" class="mvp-page-side-panel" aria-labelledby="{id}-label" [tabindex="0" when sticky]>
             <h2 id="{id}-label">  {slot}
           </aside>
</div>
```

The `<aside>` is the landmark (FR-002) and, in a sticky column, the scroller: the outer element
sticks, the `<aside>` carries the `max-height` and `overflow-y: auto` (FR-007, ADR 0013). A closed
drawer's `<aside>` is inside daisyUI's hidden `.drawer-side`, so it is neither shown nor reachable
(FR-008). Breakpoint variants are written out whole so the stylesheet build finds them.

### `<c-mvp.page.layout>`

Slots: `header`, default, `side`. With `side|slot_is_empty`, it draws `{{ header }}{{ slot }}` and
nothing else (FR-001, SC-002, US5-2). Otherwise:

```
<div class="mvp-page-layout flex flex-col gap-3 {class}">
  [<div class="mvp-page-header">{header}</div>   — only when header is not empty]
  [{side} when position is start]
  <div class="mvp-page-main flex min-w-0 flex-col gap-3">{slot}</div>
  [{side} when position is not start]
</div>
```

`position` comes from `side|root_attr:"data-mvp-side-position"`, a new filter in
`mvp/templatetags/mvp.py` that returns one attribute of the first element of an HTML string, parsed
with `html.parser.HTMLParser`, or `""`. The grid's areas and the drawer's side come from the panel's
own data attributes, in CSS.

### Stylesheet (`mvp/tailwind/base.css`)

The prototype's rules, kept: `--mvp-header-height` with its `4rem` fallback under `:where(:root)`,
`html { scroll-padding-top }`, the three widths, the `mvp-page-side-wide` utility undoing the drawer
in a column (with the `drawer-end` stretch), the grid's areas by position and align, 2.5rem gap, the
column 1rem below the header, the toggle hidden on a page with no drawer panel and from the panel's
breakpoint. Added:

- the `max-height` and `overflow-y: auto` move from the sticky element to its `<aside>`;
- `.mvp-page-fill .mvp-page-layout` (FR-011): `flex: 1; min-height: 0`, rows `auto minmax(0, 1fr)`,
  `.mvp-page-main` keeps the fill chain (`flex: 1; min-height: 0`), and the column is
  `position: static`, stretched to the row, its `<aside>` scrolling with no `max-height`;
- the column's `<aside>` focus ring.

### `assets/js/page_side.js`

`registerPageSide(Alpine)`, called from `index.js` before `Alpine.start()`:

- `mvpPageSide({ id, breakpoint })` — `open()` on a window `mvp-page-side-open` event naming its
  id: remember the opener, check the toggle, make every sibling of every ancestor up to `<body>`
  `inert` (remembering exactly those), dispatch `mvp-page-side-changed {id, open: true}`, focus the
  close button once the drawer side's computed visibility is `visible` (FR-009). `close()` on
  Escape, the close button and the overlay: uncheck, release `inert`, dispatch, return focus to the
  opener. A `matchMedia` listener for the breakpoint (`lg` 64rem, `xl` 80rem, `2xl` 96rem; none for
  `False`) closes an open drawer without moving focus when the query starts matching (FR-010).
  `destroy()` releases `inert` and removes its listeners (a list swap replaces an open panel).
- `mvpPageSideToggle(id)` — `expanded` bound to `aria-expanded`; click dispatches
  `mvp-page-side-open`; listens for `mvp-page-side-changed` with its id.

### Header height (`assets/js/header_height.js`)

The prototype's script, with one change: no `.mvp-header` on the page publishes `0px`.

### The list and table pages

- `FilterContextMixin`: `modal_fields` → `panel_fields`, `modal_applied_count` →
  `panel_applied_count`, `clear_modal_url` → `clear_panel_url`. Each panel field's widget gets
  `attrs["form"] = "filterForm"` (FR-017). The `get_toolbar_field()` error names the filter panel.
- `MVPListViewMixin`: `filter_panel_attrs = {"position": "start", "align": "content"}` (FR-014,
  FR-016; replaced not merged, Article XVIII) and `filter_panel_id = "filters"`, both in context.
- `<c-mvp.page.list.filters.panel>` (replaces `filters/modal.html`): props `fields`, `clear_url`,
  `id`; forwards every other attribute to `<c-mvp.page.side label="Filters">`. Draws each field with
  `as_crispy_field`, then a foot that stays at the panel's bottom (`sticky bottom-0`) with Apply
  (`type="submit" form="filterForm"`) and, when `clear_url`, a Clear link carrying the region's htmx
  attributes. Draws nothing with no fields (FR-015).
- `list_view.html`: fills `page.side` with the panel when `panel_fields`; the toolbar's Filter button
  becomes `<c-mvp.page.side.toggle for=filter_panel_id text="Filters" icon="filter"
  :count="panel_applied_count">`, drawn only when `panel_fields`; the dialog is gone.
- `table_view.html`: declares its own `page.side` block and wraps the region in
  `<c-mvp.page.layout>` inside `<c-mvp.page.content gap="0">`; the toggle replaces the Filter button.
- Every element that swaps the region (filter form, chips, pager, the empty state's Clear all, the
  panel's Clear) also carries `hx-select-oob="#{{ filter_panel_id }}"`, so the panel is refreshed
  from the same response (research, *The list region and the panel*). Passed always: htmx skips an
  out-of-band selector the response does not contain.
- `list_view.js` loses the modal's close handler and `MODAL_ID`.

## Story order and dispatch

US-4 → US-1 → US-5 → US-2 → US-3, sequentially in the feature worktree. Three dispatches:
**A** US-4, US-1, US-5 (the column, the layout and the header height); **B** US-2 (the drawer);
**C** US-3 (the list and table pages). Each later dispatch builds on the previous one's accepted
commit.

## Tests retired or renamed by this feature

The spec removes the filter modal (FR-013) and renames what fed it, so these pre-existing tests are
changed in US-3, and only there. Each change keeps the behaviour under test where it survives.

| Test | Change |
|---|---|
| `tests/test_components/test_list_filter_modal.py` | Deleted; replaced by `test_list_filter_panel.py`. `TestTheOverrideBeatsTheHeader` (indicator z-index) moves with it if the panel's badge needs it, else is dropped with the modal's button |
| `tests/test_views/test_list.py` — `modal_*` assertions (lines ~970, 1765–2129) | Keys renamed to `panel_*`; `test_one_filter_form_holds_the_modal` becomes the panel's fields carrying `form="filterForm"` |
| `tests/test_table_layout.py` — `filterModal` tests (~416, 792–827) | Assert the panel and its button instead of the modal |
| `tests/test_integrations.py` — modal clear link and badge (~217, 280–289) | Assert the panel's clear link and the button's count |
| `tests/test_demo/test_list_filter_pages.py` — modal page classes | Assert the panel instead of the modal |
| `tests/test_list_filters_e2e.py` — `TestFilterModalCloses`, `TestFilterModalApplies` | Closes: removed (no modal, and FR-017 keeps unapplied panel values). Applies: rewritten against the panel |

## Sketch debt

Every item under "What the sketch faked" in `sketch.md` is a task: T013–T016 (list panel), T003
(seam), T009 (module), T009–T010 (containment, widening), T004 (named scroller), T004/T006 (filled
pages), T004 (`False`), and every task's tests and docs.

## Cost estimate

Three Sonnet dispatches, about $15–25 each: $45–75 in all, inside the $120 hard budget.
