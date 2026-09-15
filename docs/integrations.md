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

Don't put a context key called `actions` on a table page. The bar above and the one below
the table are plain flex rows rather than `<c-toolbar>`, because a toolbar renders
`{{ actions }}` in its trailing slot, and a Cotton slot falls through to the context
variable of the same name when the caller fills no slot — a page whose context carries an
`actions` key would print its repr there instead.

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

The width and wrapping classes a column can name are in
[Styling](styling.md#column-behaviour-classes).

### Columns that identify the row

A column carrying the record's icon, its name or its reference does not hold one of
the row's values, it says which row this is. Name those columns on the table's `Meta`
and their body cells render as `<th scope="row">` instead of `<td>`:

```python
class SampleTable(tables.Table):
    icon = tables.TemplateColumn(template_name="sample/icon.html", verbose_name="")
    name = tables.Column()
    depth = tables.Column()

    class Meta:
        row_headers = ("icon", "name")
```

A single name may be given on its own: `row_headers = "name"`. The cell keeps the
column's `td` attributes, so a column loses none of its width behaviour by becoming a
row header. Naming a column the table does not have raises `ImproperlyConfigured` when
it renders, rather than being ignored.

Two things follow. A screen reader announces the rest of the row against a row header,
so "1250 metres" is read as the depth of the sample the header names rather than as a
number in a grid. And daisyUI's `table-pin-cols` selects on exactly this markup, so a
column declared here is one that can be kept in view while a wide table scrolls
sideways. Add that class to the table area to turn the pinning on:

```django
{% block page.content %}
  <c-addons.django-table :table="table" class="flex-1 min-h-0 table-pin-cols" />
{% endblock page.content %}
```

### A column with no heading

A column whose heading resolves to nothing renders an empty heading cell. The cell
stays, so the column keeps its width and its position in the row, and an orderable
column keeps the control that sorts by it — a column worth sorting is a column worth
naming, and hiding the name is not a request to take the sort away. `verbose_name=""`
is the usual way to say it.

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
badge the number of active filters. When at least one filter is applied, it also injects
`clear_filters_url` — the current list URL with only the filterset's own fields removed,
preserving an active search (`?q=`) or ordering (`?o=`) and resetting pagination. The
filter modal shows a "Clear filters" link next to "Apply filters" whenever that URL is
present.

`applied_filters` comes from `get_active_filters()`, which reads the filterset form's
`cleaned_data` and drops `None`, `""`, `[]`, `()` and `False` — what an untouched filter
field cleans to. Override the hook on the view when one of those values is a real choice
in your filterset, an unchecked boolean the user deliberately picked, say.

`MVPFilteredListView` is shorthand for `MVPListViewMixin` plus `FilterView`. Compose
those yourself — which is what you do to add filtering to a table view — and the badge
and the clear link come with it:

```python
from django_filters.views import FilterView

from mvp.integrations.django_tables.views import MVPTableViewMixin


class ProductTableView(MVPTableViewMixin, FilterView):
    model = Product
    table_class = ProductTable
    filterset_fields = ["name", "category__name", "status"]
```

## htmx

```bash
pip install django-htmx
```

The htmx mixins live in `mvp.views.htmx`, not `mvp.integrations`, and aren't a guarded
module: they import `django_htmx` directly, so importing the module without
**django-htmx** installed raises a plain `ImportError` rather than the `ImproperlyConfigured`
the integrations above raise.

The htmx *library* is a separate matter from the package. It ships in django-mvp's bundled
front-end runtime and runs on every page, so there's no script tag to add — which also
means `hx-*` attributes are live anywhere in your markup. Strip them along with anything
else you already sanitize on a page that renders HTML you didn't author.

`HtmxMixin` is the lightweight base, usable on any view. It injects `htmx_enabled = True`
into the context on every request, htmx or not, so a template can render `hx-*` attributes
conditionally. It never reads `request.htmx` itself, so it works without
`django_htmx.middleware.HtmxMiddleware` registered.

| Attribute | Default | Purpose |
|---|---|---|
| `htmx_trigger` | `None` | Event name, or a `{name: params}` dict, sent as an `HX-Trigger` family header. Falsy means no header. |
| `htmx_trigger_after` | `"receive"` | Phase the event fires in: `"receive"`, `"settle"` or `"swap"`. |

`HtmxFormMixin` subclasses `HtmxMixin` and adds htmx-aware form handling. Put it *before*
the base view class so its `form_valid()` and `form_invalid()` intercept first:

```python
from mvp.views import MVPCreateView
from mvp.views.htmx import HtmxFormMixin


class ProductCreateView(HtmxFormMixin, MVPCreateView):
    model = Product
    fields = ["name", "price"]
    htmx_success_component = "ui.product-created"
    htmx_trigger = {"product-created": {}}
    success_url = "list"
```

Unlike the plain mixin, this one needs `HtmxMiddleware` in `MIDDLEWARE`: its `form_valid()`
and `form_invalid()` branch on `request.htmx`, which that middleware sets.

| Attribute | Default | Purpose |
|---|---|---|
| `htmx_success_component` | `None` | Cotton component for the success partial, dot notation: `"ui.product-created"` → `cotton/ui/product_created.html`. |
| `htmx_success_components` | `()` | Allowlist of `(alias, component)` pairs the requesting element may choose between via an `X-Success-Component` request header. |
| `htmx_form_component` | `"form"` | Cotton component for the form-error partial. |
| `htmx_redirect_on_success` | `False` | Return a client-side redirect to the success URL instead of a partial. |

The client picks an allowlisted component with the header, matched against the aliases:

```django
<form hx-post="{% url 'product-create' %}"
      hx-headers='{"X-Success-Component": "list"}'>
```

An unknown alias, or no header, falls through to `htmx_success_component`. Resolving
neither raises `ImproperlyConfigured` unless `htmx_redirect_on_success` is set.

On a valid htmx POST the form saves, the Django message queue is drained so messages don't
reappear on the next full-page load, and either a client redirect or the rendered success
partial goes back with any trigger headers attached. An invalid form re-renders the form
component at HTTP 200. Both paths delegate straight to `super()` when the request isn't
from htmx, so the view keeps working as an ordinary form view.

## Crispy forms

Form rendering isn't an integration in the sense above: `django-crispy-forms` and
`crispy-tailwind` are required dependencies, installed with the package, not an
optional third-party package you opt into. Their `INSTALLED_APPS` entries and settings
are part of the required setup — see
[Getting Started — configure form rendering](getting-started.md#configure-form-rendering).

See [Views — forms](views.md#forms-create--update--generic) for the renderer
resolution order.

Give a form a `helper` whose `Layout` — `Fieldset`, `Row`/`Column`, `HTML`, and the
rest of `crispy_forms.layout` — controls the markup instead. The demo's Complex
Form page (`/forms/complex/`) is a worked example. A `Fieldset`'s `<legend>`
carries the same divider styling as a formset's own heading, for a consistent
look between the two ways a form groups its fields.

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
