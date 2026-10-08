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
[`c-mvp.addons.django-table`](components.md#actions-user-misc) component.
`MVPTableViewMixin` is available for composing with other view classes.

The page fills the screen. Three bands stay put and one region scrolls between them:

1. **The toolbar.** A bar with the title and a count of the records, and a panel under
   it with the search box, the filter button, the add button and the search and
   filters that are applied.
2. **The table.** The rows scroll in a region of their own. The heading row stays at
   the top of it and the footer row, where the table declares one, at the bottom, so
   one scrollbar runs beside all three.
3. **The pager**, only when there is more than one page: the range shown and numbered
   pages on a wide screen, and Previous, a page picker and Next on a phone.

### The toolbar opens and closes

A button at the end of the bar closes the panel, which hands its height to the rows,
and opens it again. The choice is remembered in the browser, so a reader who works with
the toolbar closed keeps it closed. While a search or filter is applied, the bar says
how many, open or closed, so a closed toolbar never hides that the table is a subset.

A view with nothing to put in the panel, no `search_fields`, no `FilterSet` and no add
action, gets the bar alone, with no panel and no button.

### A table that does not fill the page

The footer row sits at the bottom of the region however few rows there are. With no
rows at all, the empty state is drawn between the heading row and the footer row: the
view's `empty_state_heading` and message for a table with no records, or the
nothing-matches message with a link that clears the search and filters.

### Putting your own controls in the toolbar

Each part of the toolbar is a block in `table_view.html`:

| Block | Holds |
| --- | --- |
| `page.header` | Empty. Anything here is drawn above the toolbar |
| `page.toolbar` | The whole toolbar |
| `page.title` | The start of the bar: the heading, the info icon, the count and the subtitle |
| `page.summary` | The count, inside `page.title` |
| `page.actions` | Empty. Anything here is drawn at the end of the bar, and stays when the panel is closed |
| `page.panel` | Everything in the panel |
| `page.search` | The search box, inside the panel |
| `page.controls` | The filter and add buttons, inside the panel |
| `page.refinements` | The applied search and filters, inside the panel |
| `page.content` | The table |
| `page.footer` | The pager |

```html
{% extends "table_view.html" %}
{% block page.controls %}
  <c-button size="sm" icon="export" text="Export" href="{% url 'product-export' %}" />
  {{ block.super }}
{% endblock page.controls %}
```

### Actions and sorting

The toolbar draws the same controls a list page does, and decides on them the same
way: each one appears when the view configures the thing it drives. Give the view
`search_fields` and the search box appears, a `FilterSet` and the filter button does,
`show_create_action` and the add button does. There is no list to override.

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

A context key called `actions` is safe on a table page. The toolbar is
`<c-mvp.page.table.toolbar>`, which declares each of its slots, so an unfilled one never
falls through to a context variable of the same name.

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
  <c-mvp.addons.django-table :table="table" class="flex-1 min-h-0 table-pin-cols" />
{% endblock page.content %}
```

With a column pinned, the footer row's cell under it is a row header as well, so a label
such as "Total" stays at the leading edge with the column. On a narrow screen a pinned
column is held to under half the width, and a longer value is cut with an ellipsis.

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
filter dialog, a panel that opens from the trailing edge of the screen, shows a "Clear
filters" link next to "Apply filters" whenever that URL is present.

`applied_filters` comes from `get_active_filters()`, which reads the filterset form's
`cleaned_data` and drops `None`, `""`, `[]`, `()` and `False` — what an untouched filter
field cleans to. Override the hook on the view when one of those values is a real choice
in your filterset, an unchecked boolean the user deliberately picked, say.

Each applied filter is also one of the page's
[refinements](views.md#what-the-view-tells-the-template), drawn under the toolbar as a
control that removes it. Three hooks on the view decide how one reads:

| Hook | Returns |
| --- | --- |
| `get_filter_label(filterset, name)` | The words that name the filter. Defaults to its form field's label |
| `get_filter_display(filterset, name, value)` | The value as text. A choice shows its label, a related record its string form, a range its two bounds |
| `get_filter_params(filterset, name)` | The query parameters the filter reads. One for most filters, one per input for a filter drawn with several, such as `price_min` and `price_max` for a `RangeFilter` |

`clear_filters_url` and each refinement's `remove_url` are built from
`get_filter_params()`, so a filter with its own parameter names is cleared correctly once
that hook names them.

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
| `htmx_form_component` | `"mvp.form"` | Cotton component for the form-error partial. |
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
`django-mvp-forms` are required dependencies, installed with the package, not an
optional third-party package you opt into. Their `INSTALLED_APPS` entries and settings
are part of the required setup — see
[Getting Started — configure form rendering](getting-started.md#configure-form-rendering).

See [Views — forms](views.md#forms-create--update--generic) for the renderer
resolution order.

Give a form a `helper` whose `Layout` — `Fieldset`, `Row`/`Column`, `HTML`, and the
rest of `crispy_forms.layout` — controls the markup instead. The demo's Complex
Form page (`/forms/complex/`) is a worked example. A `Fieldset` is drawn as a
daisyUI `fieldset` with its legend visible above the fields.

Every field and layout object is drawn by django-mvp-forms. Its
[README](https://github.com/django-mvp/django-mvp-forms#public-surface) lists what
each widget and layout object becomes, the size, colour and variant choices a form
or a field can state, and how to replace one of its templates.

A field whose widget ships its own template is drawn by that template. That covers
a third-party control such as django-tomselect, whose template renders a `<select>`
plus the script that configures it.

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
