# Research: FS-042 — A side panel beside a page's content

Read against `origin/main` at `17788c4` (2026-10-21), after the shell's drawer selectors were scoped
to the shell's own drawer (#567), and against the approved prototype on `sketch/page-side`.

## Planning notes, answered

**Alpine components with real behaviour live in their own module.** Adopted. The panel's open,
close, focus, Escape, containment and widen-to-close handling becomes `Alpine.data("mvpPageSide")`
and the button `Alpine.data("mvpPageSideToggle")`, both in `assets/js/page_side.js`, registered
from `assets/js/index.js` before `Alpine.start()`, as `layout.js` is. The templates pass
configuration only. The bundle is rebuilt with `invoke build-js` (Article XV).

**The prototype is the starting point.** Adopted. Its markup, classes, copy and the stylesheet
rules Sam approved are kept. Everything behind them is rebuilt test-first, and every item under
"What the sketch faked" is a task (plan, *Sketch debt*).

**The drawer stays inside the panel; the shell's nested-drawer selectors are a defect of their own.**
Adopted. #567 already scoped `is-drawer-open`, `is-drawer-close` and the `.mvp-page-fill` rules to
the shell's own drawer (`[data-mvp-breakpoint] > .drawer-content`), and
`tests/test_components/test_nested_drawers_e2e.py` guards it. Nothing is left in the way; this
feature adds a nested-panel case to that test rather than fixing anything.

**`breakpoint=False`, not `"never"`.** Adopted. The panel writes `data-mvp-side-breakpoint` only when
`breakpoint` is truthy, so a panel with `False` matches no column rule and is a drawer at every
width.

**List panel fields join the toolbar's form through the `form` attribute, set by the view.**
Adopted. `FilterContextMixin` sets `widget.attrs["form"] = "filterForm"` on every panel field's
widget. Django deep-copies each field and its widget per form instance (`BaseForm.__init__`,
`Field.__deepcopy__`), so this never leaks between requests; `get_toolbar_field()` already sets
widget attributes the same way. A `MultiWidget` (a range filter) hands its `attrs` to every
sub-widget (`django/forms/widgets.py`, `MultiWidget.get_context`), and a choice widget to every
option, so a range or a set of checkboxes joins too. A Tom Select control keeps its original
`<select>`, which carries the attribute and is what submits. `list_view.js` reads `form.elements`,
which includes form-associated controls outside the form. This supersedes FS-041's note that every
field sits inside the form.

**`drawer-end` shrinks the panel in a column; keep the stretch.** Adopted, as the prototype has it.

**Focus moves into the drawer once it is visible; `inert` for containment.** Adopted. On open, every
sibling of every ancestor of the panel up to `<body>` is made `inert`, and exactly those are released
on close or when the component is destroyed (a list swap replaces the panel). Focus waits for the
drawer side's computed `visibility` to be `visible`, as the prototype found.

**Find a cleaner seam than searching the rendered slot.** Adopted, partly. The layout still has to
learn the side from the panel, because the panel carries its own configuration (FR-001) and a Cotton
slot reaches the layout as rendered HTML. Instead of a substring test over the whole slot, a
template filter reads one attribute off the slot's **first element** with the standard library's
`html.parser`. A string inside the panel's content (a code sample showing the attribute) can no
longer move it. Alternatives rejected: a `position` attribute on the layout too (two places to keep
in step, and FR-001's one component), CSS `order` (breaks FR-006's reading order), drawing the slot
twice (duplicate ids).

## What the prototype faked, and how it is met

| Faked | Met by |
|---|---|
| List panel is a demo template with a second form copying toolbar values | `list_view.html` and `table_view.html` draw `<c-mvp.page.list.filters.panel>`; its fields carry `form="filterForm"` |
| Layout finds the side by substring search | `root_attr` filter on the slot's first element |
| Drawer behaviour inline in `x-data` | `assets/js/page_side.js` |
| No focus containment; open drawer survives widening | `inert` walk; `matchMedia` change closes it |
| Column scroller not focusable or named | the panel's `<aside>` is the scroller, `tabindex="0"`, named by its heading (ADR 0013) |
| Filled pages not handled | `.mvp-page-fill .mvp-page-layout` rules: full-height grid, no stick |
| No `breakpoint=False` | as above |
| No tests, docs, reference entry, changelog | tasks in every story |

## The list region and the panel

A list page's htmx swap replaces `#mvp-list` only (`hx-select`), and the panel sits outside it,
beside the content. After a swap the panel's clear link (present only when a panel filter is
applied, and keeping the toolbar's current values) is stale. Every element that issues the swap —
the filter form, the chips, the pager, the empty state's Clear all, and the panel's own clear link —
also carries `hx-select-oob="#<panel id>"`, so the panel is replaced from the same response.
`mvp/partial.html` already renders the whole `content` block, so the panel is in the response.
The panel's id is a view attribute, `filter_panel_id = "filters"`, beside `list_region_id`, because
three templates and the toggle have to name it.

A swap while the drawer is open replaces the open panel with a closed one. The old component's
`destroy()` releases the `inert` it set. Focus goes where it goes today when the filter modal's
Apply swaps the region: the swapped content. Parity, recorded in `decisions.md`.

The FS-041 "put the modal's fields back on close" handler in `list_view.js` goes with the modal.
Under FR-017 a value set in the panel and not yet applied is sent with the next toolbar change, by
design.

## The table page

`table_view.html` overrides `content` and draws a filled page (`<c-mvp.page fill>`), with its own
toolbar holding the title, so `page_view.html`'s side block never reaches it. It declares its own
`page.side` block and lays out with `<c-mvp.page.layout>` inside `<c-mvp.page.content gap="0">`: the
default slot is the region (header, toolbar, table, pager); the header slot is empty. FR-011's rules
make the grid fill the page's height with the panel as a full-height, non-sticky, scrolling column.
The existing filled-page flex chain (ADR 0015) continues through `.mvp-page-main`.

## Naming

- `<c-mvp.page.side>` — the side panel; `<c-mvp.page.side.toggle>` — its button;
  `<c-mvp.page.layout>` — the page layout (the prototype's names; CONTEXT.md gains "Side panel",
  "Panel button", "Page layout").
- `<c-mvp.page.list.filters.panel>` replaces `<c-mvp.page.list.filters.modal>`. "Filter panel"
  replaces "Filter modal" in CONTEXT.md.
- Context keys `modal_fields`, `modal_applied_count`, `clear_modal_url` are renamed
  `panel_fields`, `panel_applied_count`, `clear_panel_url`. A pre-1.0 rename recorded in the
  CHANGELOG (Article XVI); keeping "modal" would name a thing that no longer exists.
- View attributes: `filter_panel_attrs` (Article XVIII, default
  `{"position": "start", "align": "content"}`, replaced not merged) and `filter_panel_id`.
- The table toolbar's existing `page.panel` block (its filter row) keeps its name; it is a row of
  the toolbar, unrelated.

## Header height

`assets/js/header_height.js` from the prototype: a `ResizeObserver` on `.mvp-header` writes
`--mvp-header-height` on `:root`, `0px` when the header's computed position is not `sticky`. One
change: with no `.mvp-header` on the page (the entrance pages) it writes `0px` instead of leaving the
`4rem` fallback. `html { scroll-padding-top: var(--mvp-header-height) }` makes the browser's own
scroll to an anchor and to a focused control clear the header (FR-019; CSSOM View applies the
scroll-padding to every scroll-into-view). ADR 0014 governs sizes reaching markup; this value is set
on the document's style by script and never written into a template.

## Breakpoints

Tailwind v4's defaults, which the stylesheet already uses: `lg` 64rem, `xl` 80rem, `2xl` 96rem. The
stylesheet writes one static rule per value (ADR 0021). The script needs the same widths only to
close an open drawer on widening; it maps the three names to `(min-width: …rem)` queries.

## What already exists

```
side block in page_view.html            · 1, needed · FR-001
side panel component                    · 7, new    · searched mvp/templates/cotton, daisy-cotton 0.2 (c-drawer)
drawer markup inside the panel          · 7, new    · daisy-cotton c-drawer (site-packages/daisy_cotton/templates/cotton/drawer/index.html) puts its checkbox in the tab order with its own label and has no hook to take it out; daisyUI's drawer classes are used as they are
panel button                            · 7, new    · daisy-cotton c-drawer.button is a <label> for the checkbox; the panel needs a real button that reports aria-expanded
page layout component                   · 7, new    · nothing in mvp/templates/cotton/mvp/page lays out a side column
empty-slot test                         · 2, repo   · mvp/templatetags/mvp.py slot_is_empty
first element's attribute               · 4, stdlib · html.parser.HTMLParser
list filter panel component             · 2, repo   · replaces cotton/mvp/page/list/filters/modal.html; fields drawn with crispy's as_crispy_field as the modal did
panel fields, count, clear URL          · 2, repo   · FilterContextMixin.get_context_data (modal_* today)
fields joining the form                 · 5, browser · the form attribute
region refresh of the panel             · 3, package · htmx hx-select-oob (htmx.org 2.0.10)
focus containment                       · 5, browser · the inert attribute
close on widening                       · 5, browser · window.matchMedia
focus into view under the header        · 5, browser · scroll-padding-top
header height                           · 5, browser · ResizeObserver; script kept from the prototype
Alpine registration                     · 2, repo   · assets/js/layout.js pattern
scrollable region rule                  · 2, repo   · ADR 0013
filled page height chain                · 2, repo   · mvp/tailwind/base.css .mvp-page-fill rules, ADR 0015
view attribute dict                     · 2, repo   · Article XVIII, related_objects_attrs precedent
```

## Baseline

`kit/forge verify` on the branch after the rebase: lint, types, build, conformance and docs green;
1853 tests pass. Four browser tests in `tests/test_views/test_error.py::TestErrorPagesAccessibilityE2E`
fail here because their browser cannot fetch axe-core from a CDN through this machine's proxy. CI on
`main` at `17788c4` is green, so they are environmental, not this feature's.
