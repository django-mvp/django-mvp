
## 2026-10-19T11:46:13Z · Forge · PLAN

Plan written: research.md answers every planning note; plan.md, tasks.md (T001-T028, US-1..US-5 in order). Spec refined after the sketch.

## 2026-10-19T12:11:08Z · Implementer US1 · T001

**Did**: pinned daisy-cotton (>=0.2,<0.3) with uv add (0.2.0 locked); passed `icon` to the seven alerts (login error, development notice, messages, formset non-form errors, delete page's protected, permanent and related-objects alerts). The related-objects alert takes `related_objects_attrs.icon`, else its variant.
**Verified**: new tests red (13 failed) before the templates changed; then `uv run pytest -q -p no:randomly tests/test_views/test_edit.py tests/test_views/test_account.py tests/test_components/test_messages.py tests/test_components/test_form_formset.py` 283 passed. Whole suite after the upgrade: 9 failed, 2208 passed, 1 skipped; the delete-page alert-layout e2e failure is now fixed by the icons.
**Next**: T002, c-mvp.modal on c-modal.
**Watch**: tests/test_components/test_icon.py::TestIconAnswersDaisyCottonComponents asserts that a bare `<c-alert variant='success'>` draws an icon, which 0.2 removed by design; not fixable in code and not in the retirement table, reported to Forge. Error-page axe e2e tests fail on CDN access (environment); a tom-select CDN script in demo/templates/base.html (sketch) fails the third-party-script e2e test.

## 2026-10-19T12:13:05Z · Implementer US1 · T002

**Did**: rebuilt c-mvp.modal on daisy-cotton 0.2's c-modal (isolated with `only`): the title names the dialog through aria-label and is drawn once by the card; size/position/closable/class and the three slots keep their behaviour. New tests/test_components/test_modal.py. docs/components.md's row updated.
**Verified**: against the pre-sketch component (ee2d896) the no-form, type=button and name tests failed (3 failed); with the sketch only the name test failed; after the rebuild `uv run pytest -q -p no:randomly tests/test_components/test_modal.py` 15 passed. Modal callers (page info, language switcher, create action, list/table pages, modal e2e): 452 passed, 1 failed (the expected TestAppliedFilterCountOnATableView, retired at T009).
**Next**: T003, django-filter as a runtime dependency.
**Watch**: c-modal's close button sits at end-2/top-2 where the old one sat at end-3/top-3.

## 2026-10-19T12:14:28Z · Implementer US1 · T003

**Did**: moved django-filter (>=26.1,<27) into [project].dependencies, out of the dev group and DEP004; demo settings list django_filters in INSTALLED_APPS (tests inherit it); ADR 0033; README install steps and Optional integrations; ROADMAP R16; integrations.md intro; CHANGELOG breaking entry.
**Verified**: `uv run deptry .` Success, no dependency issues; pre-commit on the changed files passed.
**Next**: T004, SearchFilter.
**Watch**: integrations.md's django-filter section still describes MVPFilteredListView until T008 deletes the module.

## 2026-10-19T12:16:22Z · Implementer US1 · T004

**Did**: SearchFilter(CharFilter) in mvp/filters.py, rebuilt test-first: `fields`, `max_words=10`, default label, OR of icontains across words and fields, `.distinct()`, no-op on an empty term or no fields. tests/test_filters.py::TestSearchFilter holds the SearchMixin cases (the old ones go at T007).
**Verified**: against a stub filter 10 of 13 failed; implemented, 13 passed. Probes: dropping `.distinct()` fails the join test; dropping the word limit fails both word-limit tests.
**Next**: T005, SortFilter.
**Watch**: SortFilter is still the sketch until T005.

## 2026-10-19T12:17:29Z · Implementer US1 · T005

**Did**: SortFilter(ChoiceFilter) rebuilt test-first: `options` of (key, label, columns), choices from the keys, no empty choice, default label, orders by one column or a sequence. tests/test_filters.py::TestSortFilter.
**Verified**: against a stub 4 of 7 failed; implemented, `uv run pytest -q -p no:randomly tests/test_filters.py` 20 passed. Probe: ordering by only the first column of a sequence first passed the tie test (SQLite rowid order hid it); the option's tiebreak became `-pk` and the probe now fails it.
**Next**: T006, the list view builds its filterset.
**Watch**: nothing.

## 2026-10-19T12:22:04Z · Implementer US1 · T006

**Did**: MVPListViewMixin gains `filterset_class`/`filterset_fields`, `get_filterset_class()` (declared, or generated from the fields), `get_filterset()` (built once per request on the base queryset, `data=request.GET or None`, `request=`), `get_queryset()` returning `filterset.qs`, and `filter`/`filterset` in the context only when there is one. New TestListFilterset (10 tests). The table mixin's sketch override takes the new signature and drops sort filters only on first build (decisions.md "get_filterset takes an optional class").
**Verified**: 7 of 10 red before the code; 10 passed after. Probes: emptying the list on an invalid form fails the three bad-value tests; always generating a filterset fails the no-filterset test. Wider non-e2e run over list/integrations/components/table/demo/templates: 1133 passed, 3 failed (the two expected retirements and the test_icon concern).
**Next**: T007, refuse the removed settings.
**Watch**: the first wider run had 59 failures from the table override's old signature; fixed in this commit.

## 2026-10-19T12:27:04Z · Implementer US1 · T007

**Did**: deleted SearchMixin, OrderMixin and SearchOrderMixin; MVPListViewMixin.__init_subclass__ refuses a truthy search_fields/max_search_words/order_by, a defined get_search_fields/get_order_by_choices (message names the class, the setting and SearchFilter/SortFilter; a table view's order_by points to its table's Meta.order_by) and any class inheriting FilterMixin. Retired the T007 rows: the mixin test classes and stubs deleted, TestDjangoFiltersComposition/NoOpCases, TestSearchSortControlsWithoutFilterSet (now TestFilterFormFollowsTheFilterset), TestActionsFollowViewConfiguration and the context-keys test rewritten onto a filterset. Shared helpers `_list_page`, `_filtered_list_page` and TestFilterDisplay._view rewritten onto a filterset (arrange only, no assertion changed). Table mixin's own order_by refusal removed; demo views off FilterView (decisions.md "The table's own order_by refusal goes with the mixins").
**Verified**: TestRemovedSettings 8 of 13 red first; after: the T007 classes plus TestTableViewOrdering 28 passed. tests/test_views/test_list.py: 102 passed, 21 failed (TestListRefinements and TestListResultCount, T008's rows; TestListPageBlocks page.search/summary/controls, T010's). mypy clean.
**Next**: T008.
**Watch**: tests/test_table_layout.py (its helper declares search_fields; T024's row) and tests/test_integrations.py::TestTableViewActions::test_search_still_draws_when_the_view_configures_it (T023's row) are now refused at class definition and stay red past this story. tests/test_components/test_sidebar_boost.py's language-switcher e2e test finds two elements by the label "Select a language" since T002 named the dialog.

## 2026-10-19T12:30:31Z · Implementer US1 · T008

**Did**: deleted mvp/integrations/django_filters/. FilterContextMixin: a SortFilter is never an applied filter (sketch marker replaced), `clear_filters_url` keeps the sort, new `get_sort_label()` and `sort_label` context; get_refinements has no special search entry, so a SearchFilter is an ordinary refinement with its own label (FR-008). Retired the T008 rows: TestListRefinements and TestListResultCount rewritten onto a filterset (FR-008 test with a labelled search), test_integrations' isolation test (django_filters allowed in core views), the three filtered-list-view tests and the clear-link test rewritten onto MVPListView with a filterset, the import test deleted, TestFilterChromeOnAComposedView rewritten as TestFilterChromeOnAFilteredListView. New TestTheSortIsNeverAFilter. docs/integrations.md's django-filter section rewritten.
**Verified**: 3 of the new tests red before the code (clear_filters_url dropping o; sort_label). Probe: removing the SortFilter skip in get_active_filters fails 5 tests. `uv run pytest -q -p no:randomly tests/test_views/test_list.py tests/test_integrations.py`: 160 passed, 4 failed (TestListPageBlocks page.search/summary/controls for T010; TestTableViewActions search test, T023's row).
**Next**: T009, the filter modal.
**Watch**: docs/integrations.md's django-tables2 section still shows search_fields on a table view; fixed with the docs at T011.

## 2026-10-19T12:32:56Z · Implementer US1 · T009

**Did**: c-mvp.page.list.filters.modal's sketch description replaced (markup kept); deleted actions/search.html, sort.html, filter.html and their three test files (T009's rows); actions/index.html loses the stand-in form and the removed actions' props (default ['create']); list_view.html's old toolbar path no longer calls the deleted components (its blocks go at T010). New tests/test_components/test_list_filter_modal.py: the button (type=button, opens the dialog, badge count), the dialog (every given field once, only those, no nested form, one submit), nothing with no fields, the list page's modal holding every filterset field and sitting in #filterForm, the badge not in a filled page, and the header z-index override moved from the filter action's tests.
**Verified**: the sketch modal already passed, so each behaviour was probed by mutation: dropping the fields guard (2 failed), the button's type (1), a nested form plus doubled fields (3), an always-drawn badge (1). `uv run pytest -q -p no:randomly tests/test_components/test_list_filter_modal.py` 13 passed. Non-e2e suite: 2038 passed, 42 failed (test_table_layout 37 and TestTableViewActions 1, US-5 rows; TestListPageBlocks 3, T010; test_icon 1).
**Next**: T010, one toolbar.
**Watch**: the modal's close-restore script keeps its SKETCH marker; T018 moves it into list_view.js. table_view.html's no-filterset branch still names the deleted components and is now unreachable (T024).

## 2026-10-19T12:34:43Z · Implementer US1 · T010

**Did**: list_view.html has one toolbar: the filter form (only when the view has a filterset) holding the toolbar fields and the modal, then the end group (sort, Filter button, Add); the old toolbar path and the page.search/page.controls blocks are gone; page.refinements draws the count row (summary in page.summary, sort_label, chips) for every list. toolbar.html's `bare` prop documented, its marker replaced. TestListPageBlocks' page.search/page.controls cases deleted (T010's row). New TestListPageOneToolbar (one #filterForm holding the modal, inside the toolbar; create dialog not in it; a no-filterset page has the toolbar with Add and no form; one count).
**Verified**: before the template change TestListPageOneToolbar passed already except a fixture mistake of mine (Add is a dialog button when the view has a create form), and the page.summary block case failed; the template change is a removal with these tests and the existing TestListPageToolbar/EmptyState/Pagination as its net. After: `uv run pytest -q -p no:randomly tests/test_views/test_list.py tests/test_components/test_list_filter_modal.py tests/test_components/test_page_list.py tests/test_templates.py` 363 passed.
**Next**: T011, the demo and the docs.
**Watch**: the formdata script in list_view.html keeps its SKETCH marker for T018.

## 2026-10-19T12:39:49Z · Implementer US1 · T011

**Did**: demo's product list views on ProductFilter with the sketch markers removed (demo/filters.py, demo/views.py; the sketch's en-dash sort labels kept with `noqa: RUF001`). docs/views.md: "Searching, sorting and filtering with a filterset" (SearchFilter, SortFilter, `q`/`o`, filterset_fields, bad values, the sort never a filter) and "Moving search_fields and order_by into a filterset"; layout, context keys, refinement keys and blocks tables made true. docs/components.md, docs/integrations.md (table example, panel blocks, sorting), docs/troubleshooting.md, README, CONTEXT.md (filterset, sort, refinement, toolbar, toolbar filter, filter modal; mixins; component tree), skills/django-mvp/SKILL.md, .github/skills/demo-views/SKILL.md. CHANGELOG breaking entries under Unreleased.
**Verified**: the docs' Python examples (filterset, filterset_fields, the refused "before", the "after", README/SKILL shape, both table examples) executed against the branch: `uv run python -I /tmp/fs041check/check_docs.py` printed "all docs examples ran". pre-commit on the changed files passed.
**Next**: the story's full verify.
**Watch**: the custom-toolbar table demo page overrides page.controls, which table_view.html no longer reaches with a filterset (T026).

## 2026-10-19T12:52:05Z · Implementer US5 · T023

**Did**: MVPTableViewMixin.get_filterset rebuilt from the sketch as tested code: every SortFilter is deleted from the request's filterset instance before its form is built, names kept on `dropped_filters` (FilterContextMixin skips them in `toolbar_filters`). SortFilter imported at module top; SKETCH marker gone. Retired the T023 row: TestTableViewActions.test_search_still_draws_when_the_view_configures_it now configures search through a filterset (`SortedProductFilter`, `toolbar_filters=["q"]`). New TestTableViewDropsTheSort: scenarios 1, 2, 3, 5 plus column sort unaffected.
**Verified**: `uv run pytest tests/test_integrations.py -q -p no:randomly` → 39 passed. The new tests passed first run against the sketch code, so the mechanism was probed: removing the deletion failed scenarios 1 and 2; deleting without recording `dropped_filters` failed scenario 3 (ImproperlyConfigured). TestTableViewOrdering already green from US-1 (no change needed).
**Next**: T024, the table panel.
**Watch**: the toolbar's placement code in mvp/views/list.py still carries SKETCH markers (US-2's).

## 2026-10-19T12:53:55Z · Implementer US5 · T024

**Did**: table_view.html's page.panel is the sketch's panel alone: the filter form (toolbar fields, the Filter button at its end, the filter modal inside the form), then the chips, now in `{% block page.refinements %}` so a project can still replace them. The old path (page.search, page.controls, the removed search/filter actions) is gone; a view with no filterset draws no panel. SKETCH marker removed; markup and copy unchanged. Retired the T024 row: tests/test_table_layout.py's helper declares search through `ProductTableFilter` + `toolbar_filters=["q"]` instead of `search_fields`, `search_fields=None` cases became `filterset_class=None`, and the `page.search`/`page.controls` block-override cases were deleted with their blocks. New scenario-4 tests in TestTableToolbar: toolbar fields in the panel's form, the rest in the modal, the Filter button in the panel and not the bar, no button when every field is in the toolbar, chips in the panel outside the form.
**Verified**: `uv run pytest tests/test_table_layout.py -q -p no:randomly` → 84 passed (before the template change: 1 failed, the page.refinements override). The new tests passed against the sketch branch, so probed by disabling it (`{% if False %}`): 15 TestTableToolbar tests failed. `uv run pytest tests/test_integrations.py tests/test_templates.py tests/test_demo -q -p no:randomly` → 280 passed. pre-commit on the two files: pass.
**Next**: T025 docs.
**Watch**: demo/templates/tests/table_view_part_override.html still defines page.search/page.controls (now unused; outside the story's files). The custom-toolbar demo page overrode page.controls, so it draws its Columns/Export buttons nowhere until T026.

## 2026-10-19T12:54:48Z · Implementer US5 · T025

**Did**: docs/integrations.md made true for US-5: the toolbar band names `toolbar_filters`, the Filter button and the chips; the block table gains `page.refinements`; "Actions and sorting" describes the panel/modal placement on a table page with an example, and that a `SortFilter` is not drawn, its address value ignored and the table's order kept, including when `toolbar_filters` names it; the django-filter section's table example now reuses the list view's filterset with `toolbar_filters`.
**Verified**: `uv run pre-commit run --files docs/integrations.md` → pass. Docs only; no test (wording).
**Next**: T026, the custom-toolbar table page.
**Watch**: `toolbar_filters` has no reference section in docs/views.md yet (US-2, T015), so integrations.md mentions it without a link.

## 2026-10-19T12:56:10Z · Implementer US5 · T026

**Did**: CustomToolbarTableView (/django-tables2/custom-toolbar/) now runs on the demo's ProductFilter with `toolbar_filters = ["q", "status", "priority"]`: its two filters and the search it lost at T007 are back in the panel, the rest of the filterset is behind Filter, the sort is dropped. Its template no longer hand-draws selects into the removed `page.controls` block; the Columns and Export buttons moved to `page.actions` (in the bar, before Add). No demo test existed for the page, so TestCustomToolbarDemoPage was added in tests/test_table_layout.py next to the other demo table page test.
**Verified**: new tests red first (no `q` in the panel; the search did not narrow the table), then `uv run pytest tests/test_table_layout.py tests/test_demo -q -p no:randomly` → 114 passed. pre-commit on the three files: pass.
**Next**: full verify, report.
**Watch**: the page now has a filter modal (ProductFilter's other fields), where before it had none. DataTablesView in demo/views.py still carries a `SKETCH (FS-041)` comment (left for T027/US-2).

## 2026-10-19T13:03:18Z · Implementer US-2 · T012

Did: replaced the sketch's describe_toolbar_field and toolbar/modal split with FilterContextMixin.get_toolbar_names() and get_toolbar_field(filterset, name), an override hook. The sort is its own kind ("sort") and goes to toolbar_sort; toolbar_filters = [] declared on MVPListViewMixin. A developer's widget gains "select w-full"/"input w-full" and aria-label = the filter's label unless it has its own. field.html reads kind "sort" instead of the sketch's sort flag, to keep the tree green.
Verified: uv run pytest tests/test_views/test_list.py::TestToolbarPlacement -q, 34 passed (4 red before the change: sort kind, aria-label, sort with own widget, override hook). Mutation probes (dedupe removed, class setdefault removed, empty-choice kept) each failed a test. tests/test_views/test_list.py tests/test_integrations.py tests/test_table_layout.py tests/test_components/test_list_filter_modal.py: 305 passed. mypy clean.
Next: T013, the toolbar field component.
Watch: modal_applied_count / clear_modal_url left as they were (US-3).

## 2026-10-19T13:05:13Z · Implementer US-2 · T013

Did: field.html loses its SKETCH marker and gains complete @description/@prop. The widget wrapper carries data-mvp-toolbar-field; the toggle draws c-form.toggle and the multi-select list c-form.checkbox (each checked/unchecked state is its own call, since cotton renders a False attribute as checked="False"). Sketch markup and copy otherwise kept.
Verified: uv run pytest tests/test_components/test_list_filter_field.py -q, 23 passed (the wrapper test was red before the change; the naming, value-hiding and type=button tests passed on the sketch's markup, which already met them). uv run pytest tests/test_components -q -m "not e2e": 638 passed, 1 skipped. No class changed, so no stylesheet build.
Next: T014, the toolbar row.
Watch: the widget's focus-out apply is still the sketch's inline Alpine; plan moves it to list_view.js in US-3.

## 2026-10-19T13:05:57Z · Implementer US-2 · T014

Did: new class TestListPageToolbarRow in tests/test_views/test_list.py: toolbar fields inside #filterForm in the order named and not in the modal; the sort, the Filter button and Add after the form, outside it, in that order (the sort's input names the form); the sort drawn once; every field in the toolbar leaves no Filter button and no dialog. list_view.html needed no change: it already drew the approved sketch's row.
Verified: uv run pytest tests/test_views/test_list.py::TestListPageToolbarRow -q, 5 passed. They passed on arrival, so probed by mutation: moving the sort after the Filter button failed the order test; reversing the toolbar loop failed the order-named test.
Next: T015, docs for US-2.
Watch: list_view.html's SKETCH formdata script is US-3's (FR-028), left as is.

## 2026-10-19T13:07:12Z · Implementer US-2 · T015

Did: docs/views.md gains "Choosing which filters go in the toolbar" (toolbar_filters, the sort at the end of the row, each kind's compact form, the accessible name, a developer's widget drawn as it is with no package asset, the ImproperlyConfigured cases, the get_toolbar_field() hook with an example and its dict keys), the layout list and the context-keys table (toolbar_fields, toolbar_sort, modal_fields). docs/components.md lists c-mvp.page.list.filters.field in both tables and its example draws the toolbar fields and sort. CHANGELOG entry under Unreleased.
Verified: the get_toolbar_field example ran against the branch (a throwaway render returned 200 with kinds ['search', 'range']; file deleted). uv run pre-commit run --files on the three pages passed.
Next: full verify, then report.
Watch: the CharFilter row says only "A text box": applying on Enter is FR-018, US-3's.

## 2026-10-19T13:11:31Z · Implementer US3 · T016

Did: tested modal_applied_count and clear_modal_url (TestFilterModalCountAndClear, 5 tests). clear_modal_url now keeps a SortFilter's parameter when the sort sits in the modal (design review SPEC-002); docstring documents both keys.
Verified: uv run pytest tests/test_views/test_list.py::TestFilterModalCountAndClear -q -> red 1 failed (sort dropped), then 5 passed; mutation probe (count all active / drop every field) -> 3 failed; tests/test_views/test_list.py -> 177 passed.
Next: T017 the count row.
Watch: nothing.

## 2026-10-19T13:12:46Z · Implementer US3 · T017

Did: TestListPageCountRow (5 tests): the summary leads the row holding the chips, the sort in use is named after it (and not when none is chosen), the row sits above the results, and the toolbar holds no count (FR-026). list_view.html's page.refinements row was already the sketch's markup, so no template change.
Verified: uv run pytest tests/test_views/test_list.py::TestListPageCountRow -q -> 5 passed; probe moving the summary and sort label into the toolbar -> 3 failed; restored. tests/test_views/test_list.py -> 182 passed.
Next: T018 list_view.js.
Watch: the tests pass on first run because the sketch already drew the row; the probe is the red evidence.
