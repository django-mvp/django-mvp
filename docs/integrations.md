# Integrations

django-mvp integrates with third-party packages the same way across the board:
**guarded modules, not packaging extras.** Each integration lives in its own module
under `mvp.integrations`, is never imported by the core package, and only requires its
third-party dependency when *you* import it. Importing without the dependency raises
`ImproperlyConfigured` with install instructions.

```text
mvp/integrations/
├── django_tables/     requires django-tables2
└── django_filters/    requires django-filter
```

## django-tables2

```bash
pip install django-tables2
```

```python
from mvp.integrations.django_tables.views import MVPTableView


class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    search_fields = ["name"]
```

`MVPTableView` combines the full MVP list behavior (search, pagination, page chrome)
with django-tables2 rendering via the `table_view.html` base template and the
[`c-addons.django-table`](components.md#actions-user-misc) component.
`MVPTableViewMixin` is available for composing with other view classes.

The page fills the screen: the rows scroll in a region of their own with the heading
row — and the footer row, where the table declares one — staying in view, while the
title bar above and the count and pagination below stay put.

### Actions and sorting

The bar above the table draws the same controls a list page does, and decides on them
the same way: each one appears when the view configures the thing it drives. Give the
view `search_fields` and the search box appears, a `FilterSet` and the filter dialog
does, `show_create_action` and the add button does. There is no list to override.

No sort control appears on a table page, and that is a consequence rather than a
separate decision. A table view raises `ImproperlyConfigured` if you declare `order_by`
on it, so the ordering choices the sort menu draws from are never there. A table
already sorts through its own column headers, against the sortable columns the table
class defines, and an ordering on the view as well would give the same table two
competing sources for it. Put the ordering on the table class, as its own `order_by` or
`Meta.order_by`.

The refusal happens as the class is defined, so a view that declares an ordering fails
when Django imports the module holding it, naming the class in the message. You find out
at startup rather than the first time someone opens that page.

### Pagination

The table paginates, and the count and links below it describe the table's page.
`paginate_by` sets the page size as it does on any list view:

```python
class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    paginate_by = 50
```

The view does not paginate a second time. With one page, the row query and any
`select_related` or `prefetch_related` on it run once per page rather than twice, and
the count under the table describes the rows above it. That holds under a column sort
too, which is applied when the table is built.

Two things follow for anything that reads the context:

- `page_obj` is the table's page, so its `object_list` holds table rows rather than
  model instances. Each row carries its instance as `row.record`.
- `object_list` and `<model>_list` hold the view's whole queryset rather than a page of
  it. Nothing evaluates it unless a template asks, so it costs nothing, but render rows
  from the table and not from there.

Leaving `paginate_by` unset means no pagination: the table renders every row, and the
count and links go with it. `table_pagination = False` says the same thing explicitly,
and wins where a view sets both.

A `?page=` that names no page, whether past the last one or not a number at all, is a
404 rather than a quiet fall back to the first or last page. An absent or empty one is
page one.

### Inferred column alignment

The shipped table template aligns a column by the kind of model field behind it, with
nothing to declare:

| Column holds | Alignment |
|---|---|
| Text (`CharField`, `TextField`, a date, a foreign key, …) | Leading (`text-start`) |
| A number (`IntegerField`, `DecimalField`, `FloatField`) | Trailing (`text-end`) |
| A boolean, or a column with no model field behind it that isn't orderable — an action column of buttons or links | Centred (`text-center`) |

It declines rather than guesses: a table built over data that isn't a queryset has no
model to resolve a field from, and a column whose accessor resolves to no field but
*is* orderable is a plain unresolvable column, not an action column — its kind can't be
determined either way. Both render with no alignment class imposed, exactly as they did
before this inference existed.

An explicit alignment class in a column's own `attrs` always wins:

```python
class ProductTable(tables.Table):
    # Text by default, pinned to the right instead.
    sku = tables.Column(attrs={"td": {"class": "text-end"}})
```

## django-filter

```bash
pip install django-filter
```

```python
from mvp.integrations.django_filters.views import MVPFilteredListView


class ProductListView(MVPFilteredListView):
    model = Product
    filterset_class = ProductFilter   # or filterset_fields = [...]
    search_fields = ["name"]
```

On top of `MVPListView` behavior, the view injects `applied_filters` /
`applied_filter_count` into the context, which the list page's filter button uses to
badge the number of active filters.

## Crispy forms

Form rendering isn't an integration in the sense above: `django-crispy-forms` and
`crispy-tailwind` are required dependencies, installed with the package, not an
optional third-party package you opt into. Their `INSTALLED_APPS` entries and settings
are part of the required setup — see
[Getting Started — configure form rendering](getting-started.md#configure-form-rendering).

See [Views — forms](views.md#forms-create--update--generic) for the renderer
resolution order.

## Writing your own integration

Follow the same pattern in your project (or in a PR):

```python
# mvp/integrations/<package>/views.py
from mvp.integrations import missing_dependency

try:
    from some_package import Something
except ImportError as e:
    raise missing_dependency("<package>", "some-package") from e
```

django-mvp deliberately only ships integrations for packages used across its author's
projects — anything else belongs in your own codebase, following this pattern.
