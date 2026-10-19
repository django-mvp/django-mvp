# Implementation Plan: A list page's search, sort and filters come from one filterset

**Branch**: `041-list-filters-from-a-filterset` · **Spec**: [spec.md](spec.md) · **Research**:
[research.md](research.md) · **Sketch**: [sketch.md](sketch.md) (approved 2026-10-19)

## Summary

The list view takes every search, sort and filter from one django-filter filterset, built by the
view itself from django-filter's public pieces. Two filters ship in a new public module,
`mvp.filters`: `SearchFilter` and `SortFilter`. `SearchMixin`, `OrderMixin`, `SearchOrderMixin`,
`MVPFilteredListView` and `mvp.integrations.django_filters` are deleted, and a view that still sets
`search_fields` or `order_by` is refused at import. A view names its toolbar fields with
`toolbar_filters`; the rest go into the filter modal. The screens are the approved sketch's:
toolbar fields in a `display: contents` form, Sort, Filter and Add at the end of the row, the
result count leading the chips above the results. daisy-cotton moves to 0.2, `c-mvp.modal` is
rebuilt on its `c-modal`, and the seven alerts that relied on the variant's icon name one.

## Technical Context

- Python 3.12–3.14, Django 5.2 / 6.0 / 6.1, django-filter 26 (now a runtime dependency),
  daisy-cotton 0.2, django-mvp-forms (unchanged floor; the lock carries 0.5.0, whose counted Tom
  Select the demo uses), Alpine (bundled).
- Tests: pytest with the Django test client and rendered-HTML assertions. pytest-playwright only
  for what needs a browser (Article XIV): closing the modal three ways without submitting, a
  choice applying on pick, a multi-select applying on close, a developer's widget applying when
  focus leaves it changed.
- Front-end assets: `mvp/static/css/django-mvp.css` (and `.br`) rebuilt with
  `invoke build-stylesheet` on this branch (Article XV). `mvp/static/js/list_view.js` is a plain
  static file and is edited directly.

## Constitution Check

| Article | Holds | How |
|---|---|---|
| I Testing | yes | every task test-first; browser tests only for the four behaviours above |
| II Simplicity, III Anti-abstraction | yes | two small Filter subclasses, one placement function, no registry, no per-field grow setting (research) |
| VI Documentation | yes | each story's docs land in the story that changes the name (tasks) |
| VII Dependency discipline | yes, with a justification | django-filter becomes a runtime dependency: ADR 0033 states why. `deptry`'s `DEP004` entry for `django_filters` is removed |
| XI Components are the public API | yes | new components under `cotton/mvp/page/list/filters/`; the removed `actions.search`, `actions.sort` and `actions.filter` are listed as breaking in the CHANGELOG |
| XIII Rendered markup is a contract | yes | the CHANGELOG lists the markup that changes: toolbar structure, `#filterForm` contents, the count row |
| XV Assets are build artifacts; nothing fetched at page load | yes | the package loads nothing for a developer's widget; the demo's Tom Select is the demo's |
| XVIII Views forward component attributes as a dict | yes | the toolbar fields are passed to their component as one dict each |

## Design

### The list view and its filterset (US-1)

`MVPListViewMixin` gains `filterset_class = None` and `filterset_fields = None`.

- `get_filterset_class()`: `filterset_class`, or `filterset_factory(model, fields=filterset_fields)`
  when only the fields are set, or `None`.
- `get_filterset()`: built once per request and cached on the view. `data=request.GET or None`,
  `request=request`, `queryset=` the view's base queryset (`super().get_queryset()`, before any
  filtering, so there is no recursion).
- `get_queryset()`: `filterset.qs` when there is a filterset, else the base queryset. Invalid
  values are dropped field by field by `BaseFilterSet.qs` itself (research).
- Context: `filter` and `filterset`, only when there is a filterset.
- `__init_subclass__` (design review SPEC-005, ARCH-001, SPEC-010) raises `ImproperlyConfigured`,
  naming the class and what it found, for any of:
  - a truthy `search_fields`, `max_search_words` or `order_by`, or a class that defines
    `get_search_fields` or `get_order_by_choices` (one tuple of names, one message shape). The
    message points to `SearchFilter` or `SortFilter` on a filterset; on a table view (a subclass of
    `SingleTableMixin`) the `order_by` message points to the table class's own `order_by` or
    `Meta.order_by` instead, since a table drops a `SortFilter` (FR-023).
  - a class that also inherits `django_filters.views.FilterMixin` (for example by composing
    `FilterView`): the list view builds its own filterset, so the message says to drop
    `FilterView` and set `filterset_class`.

`MVPListView = MVPListViewMixin + ListView`, unchanged in shape. `MVPTableViewMixin` keeps
`MVPListViewMixin` and gets the same filterset.

### The two filters (US-1)

`mvp/filters.py`, public, documented in `docs/views.md`:

- `SearchFilter(CharFilter)`: `fields=` the ORM paths, `max_words=10`; label defaults to
  "Search". `filter()` ORs `icontains` across fields and words, `.distinct()`, and is a no-op on
  an empty term or no fields.
- `SortFilter(ChoiceFilter)`: `options=` `(key, label, columns)` triples, `columns` one expression
  or a sequence; label defaults to "Sort"; `empty_label=None`. `filter()` orders by the matching
  option's columns. An unknown key fails the field's choice validation and never reaches
  `filter()`.

### Applied filters (US-1, US-3)

`FilterContextMixin` stays and is the one place filter state is computed:

- `get_active_filters()` skips every `SortFilter`.
- `get_refinements()` drops its special "search" entry: a `SearchFilter` is an applied filter like
  any other, labelled by its own label (FR-008). `search_query` and `is_searchable` leave the
  context.
- New context: `sort_label`, the label of the chosen sort option, or `""`.

### Placement (US-2)

`toolbar_filters: list[str] = []` on `MVPListViewMixin`. A `FilterContextMixin` method,
`get_toolbar_field(filterset, name)` (design review ARCH-002: an override hook, documented in T015,
so a project can draw a filter class the table below does not cover), returns one dict per
toolbar field:

| `kind` | When | Extra keys |
|---|---|---|
| `widget` | the field's widget is not its field class's default widget (and it is not a `SortFilter`) | `bound` |
| `search` | `SearchFilter` | `value` |
| `sort` | `SortFilter` | `value`, `choices` `[(key, label, selected)]` |
| `toggle` | `BooleanFilter` | `checked` |
| `multichoice` | `MultipleChoiceFilter`, `ModelMultipleChoiceFilter` | `choices` |
| `choice` | `ChoiceFilter`, `ModelChoiceFilter` | `value`, `choices` |
| `text` | `CharFilter` | `value` |
| anything else | `ImproperlyConfigured` naming the view, the field and the filter's class, and saying it belongs in the modal (FR-013) | |

Every dict carries `name` and `label`. A `widget` field's widget gets daisyUI's `select w-full`
or `input w-full` class, and an `aria-label` equal to the filter's label, when it has none
(design review SPEC-004, FR-014).

`FilterContextMixin.get_context_data()` adds, when there is a filterset:
`toolbar_fields` (in `toolbar_filters` order, duplicates dropped, the sort taken out),
`toolbar_sort` (the sort's dict or `None`), `modal_fields` (bound fields not in the toolbar),
`modal_applied_count`, and `clear_modal_url` (current URL without the parameters of the modal's
fields other than a `SortFilter`, and without the page number: design review SPEC-002, FR-005,
FR-016). A name the filterset lacks raises `ImproperlyConfigured` naming the view,
the name and the filterset class. Names a table view dropped (below) are skipped silently.

### Templates and components (US-1 to US-3)

New components, each with `@description`/`@prop` headers like the others:

- `c-mvp.page.list.filters.field`: one toolbar field, by `kind`, from the approved sketch.
- `c-mvp.page.list.filters.modal`: `part="button"` (the Filter button with the modal's applied
  count) or `part="dialog"` (the modal with every modal field, the modal's clear action and Apply).
- `c-mvp.page.list.toolbar`: keeps its props and gains `bare`, which draws its slot as the row.

The toolbar's toggle and its multi-select list draw daisy-cotton's `c-form.toggle` and
`c-form.checkbox` (design review ARCH-003, Article XI). `c-mvp.modal` passes `aria-label` (its
title) to `c-modal` and never `title`, so the dialog has a name and one heading (ARCH-004).

`list_view.html`'s `page.toolbar` becomes the sketch's toolbar and its only toolbar. The
`page.search` and `page.controls` blocks go (they held the removed components); `page.toolbar`,
`page.refinements`, `page.results`, `page.empty` and `page.pagination` stay. `page.refinements`
draws the count row: summary, `sort_label`, then the chips. The old components
`actions.search`, `actions.sort`, `actions.filter` and `actions.index`'s stand-in form are deleted;
`actions.create` and `actions.share` stay.

`table_view.html`'s `page.panel` holds the filter form with the toolbar fields and the modal's
dialog, the Filter button at its end, then the chips. The bar keeps the count and Add.

### The modal (US-1, US-3)

daisy-cotton pin `>=0.2,<0.3`. `c-mvp.modal` keeps its props and slots and draws its card inside
`<c-modal ... only>` (ADR 0032). The seven alerts pass `icon` (research).

### Behaviour in the browser (US-3, US-4)

`mvp/static/js/list_view.js`, a new plain static file following `mvp/static/js/formset.js`'s
precedent. `list_view.html` already has a `<script>` tag for it, dangling since the file was
deleted in e4c0a8b (design review ARCH-005):

- on the filter form's `formdata`, delete entries whose value is `""`, and entries whose value is
  `"unknown"` only when they come from a `<select>` (Django's `NullBooleanSelect` empty choice:
  design review SPEC-003, FR-028);
- on the filter modal's `close`, restore every input, select and textarea in it to its default
  and call `.sync()` on a select that has a `tomselect` property, without naming Tom Select
  anywhere else (FR-019);
- for each `[data-mvp-toolbar-field]` wrapper: remember its value on `focusin`, and on `focusout`
  to outside the wrapper submit the form if the value changed (FR-021, FR-027).

Choices, the sort and the toggle keep the sketch's Alpine (`requestSubmit()` on pick or change).
Request values inside Alpine expressions stay behind `|escapejs`, or move to `data-` attributes.

`list_view.html` keeps writing `{{ filter.form.media }}`. A widget's own declared `Media` is the
widget's contract with Django's forms, not an asset the package loads (decisions.md, design review
SPEC-008); the demo's base template loads Tom Select itself.

### Table pages (US-5)

`MVPTableViewMixin` overrides the list mixin's `get_filterset()` and deletes every `SortFilter` from the instance's `filters`
before the form is built and records the names on `self.dropped_filters`, which placement skips.
The table's own `__init_subclass__` refusal of `order_by` is removed: the list mixin's refusal
covers it, with the table-specific message above.

### Story order

**US-1 → US-2 → US-3 → US-4 → US-5, one at a time, in one worktree.** They share
`mvp/views/list.py`, `list_view.html` and `docs/views.md`, so they cannot run in parallel.

### Tests retired with the code they test

These pre-existing tests exercise code or markup this feature deletes, and are deleted or
rewritten by the task named, on this plan's authority (design review SPEC-001). **Rewritten**
means the behaviour stays and the test moves onto a filterset; **deleted** means the behaviour
goes.

| Test | Task | Fate |
|---|---|---|
| `tests/test_views/test_list.py`: the module-level import of `SearchOrderMixin` and the stub views `_StubFilterView`, `_StubFilterViewNoSearch` | T007 | rewritten onto a filterset |
| `tests/test_views/test_list.py`: the `SearchMixin`, `OrderMixin`, `SearchOrderMixin` classes | T007 | deleted; matching rules move to `tests/test_filters.py` (T004, T005) |
| `tests/test_views/test_list.py`: `TestDjangoFiltersComposition`, `TestDjangoFiltersNoOpCases`, `TestMVPListViewMixinSearchOrdering`, `TestSearchSortControlsWithoutFilterSet`, `TestActionsFollowViewConfiguration` | T007 | rewritten onto a filterset where the behaviour stays (FR-006, FR-009), deleted where it was the mixins' |
| `tests/test_views/test_list.py`: the `search_fields` helper in `TestEmptyStateMessageRendering`, `TestListRefinements` (its search refinement becomes the FR-008 test), `TestListResultCount.test_counts_only_what_the_search_matches` | T008 | rewritten onto a filterset |
| `tests/test_views/test_list.py`: `TestListPageToolbar` (including "the toolbar stays when a search matches nothing", the spec's edge case) and `TestListPageBlocks`' `page.search`/`page.controls` cases | T010 | rewritten onto a filterset; the two removed blocks' cases deleted |
| `tests/test_integrations.py`: `TestIntegrationIsolation.test_core_views_have_no_optional_dependency_imports` | T008 | rewritten: core views may import django_filters, the others stay optional |
| `tests/test_integrations.py`: `TestOptionalIntegrations.test_django_filters_integration_imports`, `test_filtered_list_view_*` (three), `test_filter_action_template_renders_clear_link_only_when_filters_applied`, `TestFilterChromeOnAComposedView` | T008 | rewritten onto `MVPListView` with a filterset; the import test deleted |
| `tests/test_integrations.py`: `TestTableViewOrdering`, `TestTableViewActions.test_search_still_draws_when_the_view_configures_it` | T023 | rewritten: the refusal now comes from the list mixin with the table message; search through a filterset |
| `tests/test_components/test_list_search_action.py`, `test_list_sort_action.py`, `test_list_filter_action.py` | T009 | deleted with their components; the filter action's behaviours move to `test_list_filter_modal.py` |
| search/sort references in `tests/test_table_layout.py` | T024 | rewritten onto the table panel's new markup |

Any other pre-existing test that fails is a defect, not a retirement.
