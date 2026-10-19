
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
