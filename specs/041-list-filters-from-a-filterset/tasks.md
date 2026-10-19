# Tasks — 041 A list page's search, sort and filters come from one filterset

**Branch**: `041-list-filters-from-a-filterset` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md) · **Sketch**: [sketch.md](sketch.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed. Documentation for a public name lands in the task
that introduces it. The approved sketch's markup and copy are kept; the code behind them is
rewritten test-first, replacing every `SKETCH (FS-041)` marker.

## Order

**US-1 → US-2 → US-3 → US-4 → US-5, one at a time, in one worktree** (plan, *Story order*).

---

## US-1 — A developer declares a list page's search, sort and filters on one filterset (P1)

Issue: #550. Delivers FR-001 to FR-009 and FR-020.

### T001 — daisy-cotton 0.2 and the alerts' icons

**Files**: `pyproject.toml`, `uv.lock`, `mvp/templates/mvp/account/login.html`,
`mvp/templates/mvp/account/_development_notice.html`, `mvp/templates/cotton/mvp/messages.html`,
`mvp/templates/cotton/mvp/form/formset/index.html`, `mvp/templates/delete_view.html`, tests next to
each template's existing tests.

Pin `daisy-cotton (>=0.2,<0.3)` with `uv add`. Test first: each of the seven alerts renders an icon
(the `<c-icon>` output inside `.alert`), then pass `icon` to each (research). Run the whole suite
once after the upgrade: any other failure from 0.2's whitespace change is fixed here.

### T002 — `c-mvp.modal` on daisy-cotton's `c-modal`

**Files**: `mvp/templates/cotton/mvp/modal.html`, `tests/test_components/` (the modal's tests)

Test first: rendered inside a `<form>`, the modal's markup holds no `<form>`; its close button and
backdrop are `type="button"`; the dialog is named by its title; `size`, `position`, `closable`,
`class` and the three slots behave as before. Then draw the card inside `<c-modal ... only>`
(ADR 0032). Every existing modal test stays green.

### T003 — django-filter is a runtime dependency

**Files**: `pyproject.toml` (move `django-filter>=26.1,<27` into `dependencies`, drop it from
`DEP004`), `docs/adr/0033-django-filter-is-a-runtime-dependency.md`, `README.md` (install steps
list `django_filters` in `INSTALLED_APPS`; "Optional integrations" no longer lists django-filter),
`docs/ROADMAP.md` (R16's line), `docs/integrations.md`, `demo/settings.py`, `tests/settings.py` if
it does not inherit it.

Test: `deptry` passes (part of lint), and a check that the demo's `INSTALLED_APPS` holds
`django_filters`.

### T004 — `SearchFilter`

**Files**: `mvp/filters.py`, `tests/test_filters.py`

Tests (class `TestSearchFilter`): any word in any field; each record once across a join; only the
first ten words (an eleventh word that alone would match matches nothing); empty term and no
fields are no-ops; the default label. Move the matching cases from the `SearchMixin` tests in
`tests/test_views/test_list.py` here (T008 retires the old ones).

### T005 — `SortFilter`

**Files**: `mvp/filters.py`, `tests/test_filters.py`

Tests (class `TestSortFilter`): orders by one column; a sequence of columns breaks ties (two pages
of a list sorted on a duplicated column hold every record exactly once); an unknown key is invalid
for the field and the queryset is unordered by it; the default label; no empty choice.

### T006 — The list view builds its filterset

**Files**: `mvp/views/list.py`, `tests/test_views/test_list.py` (new class `TestListFilterset`)

Plan, *The list view and its filterset*. Tests: a view with `filterset_class` narrows the list and
puts `filter` and `filterset` in the context; a view with `filterset_fields` only gets a generated
filterset (FR-007); a view with neither has no `filter` in its context and its page draws no
filter form (FR-006); a bad value for one filter is ignored and the others apply (FR-009); an
unknown sort key leaves the default order.

### T007 — Removed settings are refused

**Files**: `mvp/views/list.py`, `mvp/views/__init__.py`, `tests/test_views/test_list.py`

Delete `SearchMixin`, `OrderMixin`, `SearchOrderMixin` and their exports. Tests: defining a list
view subclass with `search_fields` or `order_by` raises `ImproperlyConfigured` naming the class,
the setting and the filter that replaces it (FR-002); a subclass with neither defines cleanly.

### T008 — One list view; the sort is never a filter

**Files**: delete `mvp/integrations/django_filters/`; `mvp/views/list.py`;
`tests/test_integrations.py`, `tests/test_views/test_list.py`

Retire the tests listed in plan, *Tests retired*, for this task. `FilterContextMixin`: skip
`SortFilter` in applied filters; the search is an ordinary refinement with the filter's label
(FR-008); `sort_label`. Tests: a set search, a set sort and two set filters give refinements for
the search and the two filters only (FR-005, US-1 scenario 4); "clear all" keeps the sort.

### T009 — The filter modal holds the filterset

**Files**: `mvp/templates/cotton/mvp/page/list/filters/modal.html` (new),
`mvp/templates/cotton/mvp/page/list/actions/` (delete `search.html`, `sort.html`, `filter.html`;
`index.html` loses the stand-in form), `mvp/templates/list_view.html`, `tests/test_components/`

Retire `test_list_search_action.py`, `test_list_sort_action.py`, `test_list_filter_action.py`.
New `tests/test_components/test_list_filter_modal.py`: `part="button"` draws a button of type
`button` that opens the dialog; `part="dialog"` draws every field it is given, each once, with no
nested form; nothing is drawn with no fields. With no `toolbar_filters`, the list page's modal holds
every field of the filterset (US-1 scenario 1, US-2 scenario 4).

### T010 — One toolbar

**Files**: `mvp/templates/list_view.html`, `mvp/templates/cotton/mvp/page/list/toolbar.html`

Remove the old toolbar path and the `page.search`/`page.controls` blocks; the toolbar is the
filter form, then the end group (Sort, Filter, Add). Tests: the page's `#filterForm` is one form,
Add's create dialog is not inside it, the toolbar is not drawn for an empty list with nothing
applied.

### T011 — The demo and the docs for US-1

**Files**: `demo/filters.py`, `demo/views.py`, `docs/views.md`, `docs/configuration.md`,
`docs/troubleshooting.md`, `docs/components.md`, `CONTEXT.md`, `CHANGELOG.md`,
`skills/django-mvp/SKILL.md`, `.github/skills/demo-views/SKILL.md`

Rewrite the demo's product list views on `ProductFilter` (from the sketch, without its markers).
`docs/views.md`: the filterset section with `SearchFilter` and `SortFilter`, examples named `q`
and `o`, and "Moving search_fields and order_by into a filterset". CHANGELOG under Unreleased,
breaking. Every docs example runs against the branch.

---

## US-2 — A developer chooses which filters appear in the toolbar (P1)

Issue: #551. Delivers FR-010 to FR-014, FR-025 and FR-027.

### T012 — Placement

**Files**: `mvp/views/list.py`, `tests/test_views/test_list.py` (class `TestToolbarPlacement`)

Plan, *Placement*. Tests: listed fields come back in order and are not modal fields; duplicates
drawn once; the sort is taken out to `toolbar_sort`; every kind in the plan's table; a widget the
developer chose gives `widget` and gains the `select w-full` class; an unknown name and an
undrawable filter (a `RangeFilter`) raise naming the view and the field (FR-013); every field
listed gives no modal fields (FR-011).

### T013 — The toolbar field component

**Files**: `mvp/templates/cotton/mvp/page/list/filters/field.html` (new), `tests/test_components/test_list_filter_field.py`

The sketch's markup per kind. Tests: each kind's control carries the filter's label as its
accessible name (FR-014); no choice, sort or multi-select control shows its chosen value (FR-025);
buttons inside are `type="button"`; the search's wrapper is the growing one; a `widget` field
draws its own widget inside a `[data-mvp-toolbar-field]` wrapper.

### T014 — The toolbar row

**Files**: `mvp/templates/list_view.html`

Tests (rendered page): toolbar fields in the order named, inside `#filterForm`; Sort, Filter and
Add in that order in the end group; no Filter button and no dialog when every field is in the
toolbar (US-2 scenario 3).

### T015 — Docs for US-2

**Files**: `docs/views.md`, `CHANGELOG.md`

`toolbar_filters`, what each kind of filter draws as, the error for one that cannot be drawn, and
that a developer's own widget is drawn as it is with no asset loaded by the package.

---

## US-3 — A user narrows a list from the toolbar and the filter modal (P2)

Issue: #552. Delivers FR-012, FR-015 to FR-020, FR-026 and FR-028.

### T016 — The modal's count and clear action

**Files**: `mvp/views/list.py`, `tests/test_views/test_list.py`

Tests: `modal_applied_count` counts only the modal's applied filters (US-3 scenario 5);
`clear_modal_url` drops the modal's parameters and the page and keeps the toolbar's and the sort
(scenario 6); the refinements' clear-all drops the search and every filter and keeps the sort
(scenario 7).

### T017 — The count row

**Files**: `mvp/templates/list_view.html`

Tests: the summary and `sort_label` lead the refinements row, above the results, and the toolbar
holds no summary (FR-026).

### T018 — The page's script

**Files**: `mvp/static/js/list_view.js`, remove inline scripts from the components

Plan, *Behaviour in the browser*: `formdata` cleanup, modal restore on close.

### T019 — Browser tests for US-3

**Files**: `tests/test_list_filters_e2e.py` (new, `pytest.mark.e2e`, `requires_browser`)

At 1440×900: choosing a toolbar choice updates the address (scenario 1); Enter in the search
submits (scenario 2); closing the modal by ✕, backdrop and Escape leaves the address unchanged and
the modal's fields restored (scenario 3); Apply sends the modal's and the toolbar's values
(scenario 4); a submitted address carries no empty parameters (FR-028); from page 2 a change lands
on page 1 (FR-012).

### T020 — Docs for US-3

**Files**: `docs/views.md`, `docs/components.md`

---

## US-4 — A user picks several values from a toolbar filter (P3)

Issue: #553. Delivers FR-021, FR-022 and FR-027's behaviour.

### T021 — The multi-select dropdown

**Files**: `field.html`, `list_view.js`, `tests/test_components/test_list_filter_field.py`

Tests: the dropdown lists every value with the chosen ones ticked; the button does not change with
the choice (FR-022).

### T022 — Applying on close

**Files**: `tests/test_list_filters_e2e.py`

Browser: ticking two values and moving focus away updates the address once (scenario 2); opening
and leaving without a change does not (scenario 4); a developer's own widget (the demo's counted
Category) applies when focus leaves it changed (US-2 scenario 9).

---

## US-5 — A developer uses one filterset on a list page and a table page (P2)

Issue: #554. Delivers FR-023 and FR-024.

### T023 — The table drops the sort

**Files**: `mvp/integrations/django_tables/views.py`, `tests/test_integrations.py`

Retire `TestTableViewOrdering`. Tests: a table view on a filterset with a `SortFilter` defines and
renders with no error and no sort control (scenario 1); a sort value is ignored and the table's
ordering stands (scenario 2); the sort named in `toolbar_filters` is skipped silently
(scenario 3); the same filterset on a list view still sorts (scenario 5).

### T024 — The table's panel

**Files**: `mvp/templates/table_view.html`, `tests/test_table_layout.py`

The sketch's panel: the filter form with the toolbar fields, the dialog, the Filter button at its
end, the chips. Retire the panel's search/sort assertions there. Tests: scenario 4.

### T025 — Docs for US-5

**Files**: `docs/integrations.md`

---

## Closing

### T026 — The custom-toolbar table page

**Files**: `demo/views.py`, `demo/templates/demo/table_custom_toolbar.html`

Convert it to a filterset; its demo test stays green.

### T027 — The demo's pages and seed

**Files**: `demo/views.py`, `demo/urls.py`, `demo/menus.py`, `demo/templates/base.html`,
`demo/management/commands/` (the seed), `tests/test_demo/`

The sketch's `/products/quick/` and `/products/modal-only/` pages and menu entries; the demo base
loads Tom Select and `mvp_forms/tomselect.css`; one seeded product with a long name. Tests: each
page renders with the expected toolbar and modal fields (`tests/test_demo/`).

### T028 — Assets and the last docs

**Files**: `mvp/static/css/django-mvp.css`, `.br`, `CHANGELOG.md`

`invoke build-stylesheet`; the CHANGELOG lists every removed name and changed markup.
