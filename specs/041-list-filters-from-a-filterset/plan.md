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
- `__init_subclass__`: a truthy `search_fields` or `order_by` on the class raises
  `ImproperlyConfigured`, naming the class and the setting, and pointing to `SearchFilter` or
  `SortFilter` on a filterset.

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

`toolbar_filters: list[str] = []` on `MVPListViewMixin`. A function in `mvp/views/list.py`,
`describe_toolbar_field(view, filterset, name)`, returns one dict per toolbar field:

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
or `input w-full` class when it has none.

`FilterContextMixin.get_context_data()` adds, when there is a filterset:
`toolbar_fields` (in `toolbar_filters` order, duplicates dropped, the sort taken out),
`toolbar_sort` (the sort's dict or `None`), `modal_fields` (bound fields not in the toolbar),
`modal_applied_count`, and `clear_modal_url` (current URL without the modal fields' parameters
and the page number). A name the filterset lacks raises `ImproperlyConfigured` naming the view,
the name and the filterset class. Names a table view dropped (below) are skipped silently.

### Templates and components (US-1 to US-3)

New components, each with `@description`/`@prop` headers like the others:

- `c-mvp.page.list.filters.field`: one toolbar field, by `kind`, from the approved sketch.
- `c-mvp.page.list.filters.modal`: `part="button"` (the Filter button with the modal's applied
  count) or `part="dialog"` (the modal with every modal field, the modal's clear action and Apply).
- `c-mvp.page.list.toolbar`: keeps its props and gains `bare`, which draws its slot as the row.

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

`mvp/static/js/list_view.js`, loaded by `list_view.html` already:

- on the filter form's `formdata`, delete entries whose value is `""` or `"unknown"` (FR-028);
- on the filter modal's `close`, restore every input, select and textarea in it to its default
  and call `.sync()` on a select that has a `tomselect` property, without naming Tom Select
  anywhere else (FR-019);
- for each `[data-mvp-toolbar-field]` wrapper: remember its value on `focusin`, and on `focusout`
  to outside the wrapper submit the form if the value changed (FR-021, FR-027).

Choices, the sort and the toggle keep the sketch's Alpine (`requestSubmit()` on pick or change).

### Table pages (US-5)

`MVPTableViewMixin.get_filterset()` deletes every `SortFilter` from the instance's `filters`
before the form is built and records the names on `self.dropped_filters`, which placement skips.
The `__init_subclass__` refusal of `order_by` is removed (the list mixin's refusal covers it).

### Story order

**US-1 → US-2 → US-3 → US-4 → US-5, one at a time, in one worktree.** They share
`mvp/views/list.py`, `list_view.html` and `docs/views.md`, so they cannot run in parallel.

### Tests retired with the code they test

These pre-existing tests exercise code this feature deletes, and are deleted or rewritten by the
task named, on this plan's authority:

| Test | Task | Why |
|---|---|---|
| `tests/test_components/test_list_search_action.py` | T009 | `actions.search` is deleted |
| `tests/test_components/test_list_sort_action.py` | T009 | `actions.sort` is deleted |
| `tests/test_components/test_list_filter_action.py` | T009 | `actions.filter` is deleted; its behaviours move to `filters.modal` tests |
| `SearchMixin`/`OrderMixin`/`SearchOrderMixin` classes in `tests/test_views/test_list.py` | T008 | the mixins are deleted; their matching rules move to `tests/test_filters.py` |
| `TestOptionalIntegrations.test_django_filters_integration_imports`, `TestFilterChromeOnAComposedView`, `TestTableViewOrdering` in `tests/test_integrations.py` | T008, T024 | the module and the `order_by` refusal are deleted; their behaviours move to the new tests |
| search/sort references in `tests/test_table_layout.py` | T024 | the table panel's markup changes |

Any other pre-existing test that fails is a defect, not a retirement.
