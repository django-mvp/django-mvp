# Tasks — 042 A side panel beside a page's content

**Branch**: `042-page-side-panel` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md) · **Sketch**: [sketch.md](sketch.md)

Every task follows Article I's test-first cycle. A task is done when its tests pass, the tree is
green, and the work is committed. Documentation for a public name lands in the task that introduces
it. A task that changes `assets/js/` runs `invoke build-js`; one that changes a template class or
`mvp/tailwind/base.css` runs `invoke build-stylesheet`; both commit the artifact. The prototype's
markup, classes and copy on `sketch/page-side` are the starting point for every template; the code
behind them is written here, test-first.

## Order

US-4 → US-1 → US-5 → US-2 → US-3, one at a time, in the feature worktree (plan, *Story order and
dispatch*).

---

## US-4 — A user is never left looking at content under the header (P3)

Issue: #574. Delivers FR-018, FR-019, SC-005.

### T001 — The header's height, published

**Files**: `assets/js/header_height.js`, `assets/js/index.js`, `mvp/tailwind/base.css`,
`mvp/static/js/django-mvp.js`, `mvp/static/css/django-mvp.css`,
`tests/test_components/test_header_height_e2e.py`, `docs/layout.md`, `CHANGELOG.md`

Browser tests first (`TestHeaderHeight`): following a link to an anchor below the fold leaves the
target's top at or below the header's bottom; tabbing to a control the page scrolled under the
header brings it out from under it; opening something that makes the header taller (add an element
to it in the test) updates `--mvp-header-height` to the header's new `offsetHeight`; a header
configured not to stick publishes `0px`; a page with no `.mvp-header` publishes `0px`. Then the
script (prototype, plus the no-header case) and the CSS. Docs: a "Header height" subsection in
`docs/layout.md` naming `--mvp-header-height` and how to use it in a project's own sticky element.

## US-1 — A developer puts a side panel beside a page's content (P1)

Issue: #571. Delivers FR-001–FR-007, FR-011, SC-001, SC-002.

### T002 — `root_attr` template filter

**Files**: `mvp/templatetags/mvp.py`, `tests/test_templatetags.py`

Tests (`TestRootAttr`): returns the attribute of the first element; ignores the same attribute on a
later or nested element; ignores the attribute's text inside content; `""` for a missing attribute,
an empty string, whitespace, text with no element, and a non-string. Then the filter, which stops
parsing at the first start tag.

### T003 — `<c-mvp.page.layout>`

**Files**: `mvp/templates/cotton/mvp/page/layout.html`, `tests/test_components/test_page_layout.py`

Tests: an empty or whitespace-only side slot draws the header and the content with no wrapper; with a
panel, the title comes first, a start panel before the content, an end panel after it; a text in the
panel's content that names the position does not move it; an empty header slot draws no header
wrapper; `class` reaches the wrapper. Component annotations per the code-documentation standard.

### T004 — `<c-mvp.page.side>` as a column, and its stylesheet

**Files**: `mvp/templates/cotton/mvp/page/side/index.html`, `mvp/tailwind/base.css`,
`mvp/static/css/django-mvp.css`, `tests/test_components/test_page_side.py`

Markup tests (`TestSidePanelLandmark`, `TestSidePanelOptions`): the root carries the panel's `id`,
and the `<aside>` inside it is `{id}-panel`, named by an `h2` holding the label; each width,
breakpoint, align, position and collapse lands as its data attribute and the breakpoint's variant
class; `breakpoint=False` writes no breakpoint attribute, no `*:mvp-page-side-wide` and no
`*:drawer-open`; sticky by default, `:sticky="False"` drops the attribute; the `<aside>` has
`tabindex="0"` in both collapse modes; a stacked panel draws no drawer, checkbox or close button. The drawer's markup here is the
prototype's with its inline `x-data` left out (T009 adds the module), and its close button's label
translated. Then the CSS from plan *Stylesheet*, including the filled-page rules.

### T005 — The `page.side` block

**Files**: `mvp/templates/page_view.html`, `tests/test_templates.py` (or the page view's existing
test module), `docs/layout.md` (Layer 2 block table)

Structure per plan *page_view.html*.

Tests: a page with no `page.side` renders no `.mvp-page-layout`, no drawer and no toggle, and its
title and content sit where they did before (assert against the structure `main` draws today, not
only absences); a page filling it with a panel draws the layout; a block holding only whitespace
counts as empty; a project page that empties `page.title` still lays out the panel beside the content.

### T006 — The column in a browser

**Files**: `tests/test_components/test_page_side_e2e.py`, a test-only template or URL if needed

Browser tests (`TestSideColumn`), at a width above `xl`: a sticky panel stays directly under the
header while the page scrolls, also after the header grows; a non-sticky one scrolls away; a panel
taller than the space under the header scrolls on its own and its `<aside>` takes focus by Tab and
scrolls by keyboard; on a filled page the panel is the page's height and does not stick; with
`dir="rtl"` a start panel is on the right. Alignment and widths are ruled by eye and not tested
(testing standard §1).

### T007 — Documentation and the demo page

**Files**: `docs/layout.md` ("Side panel" section), `docs/components.md` (Page structure),
`CONTEXT.md` (Side block, Side panel, Page layout, with one line telling the page layout apart
from the app shell's Layout), `CHANGELOG.md`, `skills/django-mvp/SKILL.md`
(routing line only), `demo/templates/demo/layout/side.html`, `demo/views.py`, `demo/urls.py`,
`demo/menus.py`, `tests/test_demo/` (the page renders with its panel)

The demo page is the prototype's "Layout › Side Panel", with every option switchable from its
form. The docs example is an "On this page" panel in `page.side`, with one attribute per option,
and a second example for a template that does not extend the page template, calling
`<c-mvp.page.layout>` itself (FR-012, from US-5).

## US-5 — A developer adds a side panel to a template of their own (P3)

Issue: #575. Delivers FR-012, by T003 (the layout is a component of its own, tested directly) and
T007 (its docs example).

### T008 — Confirm the page layout stands alone

**Files**: none beyond T003's and T007's

No new tests: T003 tests `<c-mvp.page.layout>` called directly, with and without a panel, and T005
tests `page_view.html`, which calls it. Done when T003's tests cover US5-1 and US5-2 and T007's
docs carry the stand-alone example; record those test ids as this task's evidence.

## US-2 — A user opens the panel on a narrow screen (P1)

Issue: #572. Delivers FR-008–FR-010, SC-003.

### T009 — The drawer's behaviour and the panel button

**Files**: `assets/js/page_side.js`, `assets/js/index.js`,
`mvp/templates/cotton/mvp/page/side/index.html`, `mvp/templates/cotton/mvp/page/side/toggle.html`,
`mvp/tailwind/base.css`, both artifacts, `tests/test_components/test_page_side.py`

Markup tests: a drawer panel's root carries `x-data="mvpPageSide({...})"` with its id and the
breakpoint's width in rem from `BREAKPOINT_WIDTHS` (none with `breakpoint=False`) and no behaviour
inline; the toggle is a `<button type="button">` with `aria-controls` naming the
panel, `aria-expanded="false"`, its text and icon, and a badge only when `count` is above zero; it
carries `x-data="mvpPageSideToggle(...)"`. Then the module per plan *assets/js/page_side.js* and the
toggle's visibility rules.

### T010 — The drawer in a browser

**Files**: `tests/test_components/test_page_side_e2e.py`

Browser tests (`TestSideDrawer`), below the breakpoint: the panel is hidden and the button shown;
activating the button opens the panel from its own side, dims the page, makes everything outside
the panel `inert`, moves focus into it and sets `aria-expanded="true"`; Escape, the close button
and the dimmed page each close it, return focus to the button and set `aria-expanded="false"`;
Tab past the last control never puts focus outside the panel; at and above the breakpoint the
button is hidden; a drawer with no button on the page is not shown and nothing in it takes focus;
a stacked panel is shown below the breakpoint with no button (its order is T004's markup test);
`breakpoint=False` is a drawer at a wide width; widening past the breakpoint with the drawer open
closes it and leaves nothing `inert` (one breakpoint is enough: the width comes from the template);
removing an open panel from the page releases `inert`.

### T011 — Documentation

**Files**: `docs/layout.md` (the drawer, the button, `collapse`, `breakpoint=False`),
`docs/components.md` (the toggle), `CONTEXT.md` (Panel button), `CHANGELOG.md`

## US-3 — A user filters a list from a side panel (P2)

Issue: #573. Delivers FR-013–FR-017, SC-004. Changes the pre-existing tests in plan *Tests retired
or renamed by this feature*, and no others.

### T012 — The view publishes the panel

**Files**: `mvp/views/list.py`, `tests/test_views/test_list.py`

Rename the context keys and retire the old names in the tests (plan table), and reword the
docstrings that still say "filter modal". New tests: every panel
field's widget carries `form="filterForm"`, including a range (MultiWidget) filter, a multiple-choice
filter and a filter with a developer's own widget; a toolbar field does not; `filter_panel_attrs`
and `filter_panel_id` are in context with their defaults, and a subclass's dict replaces the default;
a filterset whose fields are all in the toolbar gives an empty `panel_fields`.

### T013 — `<c-mvp.page.list.filters.panel>`

**Files**: `mvp/templates/cotton/mvp/page/list/filters/panel.html` (new),
`mvp/templates/cotton/mvp/page/list/filters/modal.html` (deleted),
`tests/test_components/test_list_filter_panel.py` (new), `tests/test_components/test_list_filter_modal.py`
(deleted), `mvp/templates/cotton/mvp/page/list/actions/index.html` (description)

Tests: each field drawn once inside a side panel labelled Filters, at the start and aligned with the
content by default when given the view's default dict, following width, position, align and
breakpoint (including `False`) from attributes; Apply is `type="submit"` with `form="filterForm"`;
Clear only with `clear_url`, carrying the htmx attributes of the region named by its `region` prop
and `hx-select-oob`; the actions
sit in a foot that stays at the panel's bottom; nothing drawn with no fields; no `<form>` inside.

### T014 — The list page

**Files**: `mvp/templates/list_view.html`, `mvp/templates/cotton/mvp/page/list/empty.html`,
`tests/test_views/test_list.py`, `tests/test_integrations.py`,
`tests/test_demo/test_list_filter_pages.py`, `tests/test_components/` (the empty state's module)

Tests: the fields not named for the toolbar are in the panel and there is no `filterModal`; the
button sits in the toolbar where the Filter button was, with `panel_applied_count` as its badge; no
panel and no button when every field is in the toolbar; the filter form, chips, pager and the empty
state's Clear all carry `hx-select-oob="#filters"`; a subclass's `filter_panel_attrs` reaches the
panel.

### T015 — The table page

**Files**: `mvp/templates/table_view.html`, `mvp/templates/django_tables2/bootstrap5-mvp.html`,
`tests/test_table_layout.py`

Tests: the non-toolbar fields are in the side panel beside the table, inside the filled page, at the
start, aligned with the content; the button replaces the Filter button in the toolbar; no panel when
every field is in the toolbar; the heading row carries `hx-select-oob` naming the panel. A browser test in `tests/test_table_layout_e2e.py`: the panel is the
height of the table's area, does not stick, and scrolls on its own; the table still fills the page, and the empty header row adds no gap above the toolbar.

### T016 — Filtering from the panel in a browser

**Files**: `mvp/static/js/list_view.js`, `tests/test_list_filters_e2e.py` (the table cases may sit
in `tests/test_table_layout_e2e.py`)

Remove the modal's close handler. Browser tests (`TestFilterPanel`): applying from the panel narrows
the list, keeps the search and the sort, drops empty fields from the address and lands on page one;
a toolbar change keeps the panel's values; the panel's clear removes its filters and keeps the
toolbar and the sort; after any of these the panel shows the response's state (its clear link
appears and disappears); with `breakpoint=False` the filters are behind the button at a wide width;
with more filters than fit, scrolling the panel keeps Apply and Clear in view; a field with a
developer's own widget in the panel is submitted with the form; applying from an open drawer at a
narrow width leaves the drawer closed, the button `aria-expanded="false"` and nothing `inert`; on a
table page, sorting by a heading after applying from the panel and then clearing keeps the new
sort.

### T017 — Documentation

**Files**: `docs/views.md` (filter panel, `filter_panel_attrs`, `filter_panel_id`, renamed context),
`docs/integrations.md` (table page block rows), `docs/components.md` (list components),
`CONTEXT.md` (Filter panel replaces Filter modal, with one line telling it apart from the table
page's `page.panel` block; Toolbar), `README.md` if it names the modal,
`CHANGELOG.md` (breaking: modal removed, context keys renamed)
