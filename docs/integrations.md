# Integrations

django-mvp integrates with third-party packages the same way across the board:
**guarded modules, not packaging extras.** Each integration lives in its own module
under `mvp.integrations`, is never imported by the core package, and only requires its
third-party dependency when *you* import it. Importing without the dependency raises
`ImproperlyConfigured` with install instructions.

```text
mvp/integrations/
└── django_tables/     requires django-tables2
```

django-filter is not one of them. It is a dependency of the package, because every list
page's search, sort and filters come from a filterset
([ADR 0033](adr/0033-django-filter-is-a-runtime-dependency.md)). Add `django_filters` to
`INSTALLED_APPS`.

## django-tables2

```bash
pip install django-tables2
```

```python
from mvp.integrations.django_tables.views import MVPTableView


class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter
```

`MVPTableView` combines the full MVP list behavior (filterset, pagination, page chrome)
with django-tables2 rendering via the `table_view.html` base template and the
[`c-mvp.addons.django-table`](components.md#actions-user-misc) component.
`MVPTableViewMixin` is available for composing with other view classes.

The page fills the screen. Three bands stay put and one region scrolls between them:

1. **The toolbar.** A bar with the title and a count of the records, and a row under it
   laid out as a list page's toolbar: the filter form with the filterset fields the view
   names in `toolbar_filters`, then, at the end of the row, the Filters button that opens
   the filter panel with the rest and the add button. The search and filters that are
   applied are listed under the filter form. The filter panel itself sits beside the
   table, at the start and level with the table, and scrolls on its own. The bar holds the
   title in the compact layout, the table page's default. In any other
   [title layout](layout.md#page-title) the title is drawn above the bar, and the bar keeps
   the count and the controls.
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

The button closes the filter form and the applied filters only. The Filters button, the add
button and the rest of `page.actions` move up into the bar, before the button, so they are
there with the panel closed and the button stays where it was. A view with no filterset has
no panel and no button to open one, and its controls sit in the bar.

### Surfaces and edges

The whole page is one surface. The toolbar, the heading row, the rows, the footer row
and the pager are all drawn in the page's own background, whatever surface the applied
theme puts the page on, so the page looks the same in every theme. A
`<c-mvp.addons.django-table>` you place yourself, inside a card for example, takes
`base-100` as its ground instead.

The parts are told apart by hairlines, in the weight DaisyUI gives the line between two
rows. The heading row also takes a small shadow while rows are scrolled under it, as the
app header does when it is stuck, and a [pinned column](#columns-that-identify-the-row)
takes one while the table is scrolled sideways. A row under the pointer is tinted with a
thin wash of the theme's text colour.

Four classes are there for a stylesheet of your own to select on:

| Class | On | When |
| --- | --- | --- |
| `mvp-table-page` | the page | always, on a table page |
| `mvp-table-pager` | the pager's bar | always |
| `mvp-table-over-top` | the scroll region | while the rows are scrolled down from the top |
| `mvp-table-over-side` | the scroll region | while the table is scrolled sideways |

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
| `page.title` | The title area: the eyebrow, heading, lead and info icon. In the compact layout, the default, it is the start of the bar; in any other layout it is drawn above the bar |
| `page.eyebrow`, `page.heading`, `page.lead`, `page.info` | One argument of the title each, inside `page.title`. See [Replacing one part of a page's title](layout.md#replacing-one-part-of-a-pages-title) |
| `page.summary` | The count, in the bar beside the title |
| `page.controls` | The end of the toolbar row: the Filters button, then `page.actions`. Shown with the panel closed |
| `page.actions` | The view's `page_actions`, then the add button, inside `page.controls`. Write `{{ block.super }}` to keep both |
| `page.panel` | The part of the toolbar the button closes: the filter form and the applied search and filters |
| `page.filters` | The filter form, inside `page.panel` |
| `page.side` | The filter panel beside the table. Drawn from the view's `panel_fields`; empty when every field is in the toolbar |
| `page.refinements` | The applied search and filters, inside `page.panel` |
| `page.content` | The table |
| `page.footer` | The pager |

```html
{% extends "table_view.html" %}
{% block page.actions %}
  <c-button icon="export" text="Export" href="{% url 'product-export' %}" />
  {{ block.super }}
{% endblock page.actions %}
```

`{{ block.super }}` is the view's actions and the add button, so where you write it decides
where they go: before your own actions, after them, or nowhere if you leave it out. `page.filters`,
`page.controls` and `page.actions` are the same blocks, holding the same controls in the
same order, as on a list page, so one override serves both.

### Actions and sorting

The toolbar draws the same controls a list page does, and decides on them the same
way: each one appears when the view configures the thing it drives. Give the view
a filterset and its search and filters appear,
`show_create_action` and the add button does. There is no list to override.

The filterset's fields are placed as on a list page. Those named in `toolbar_filters`
are drawn in the toolbar's panel, in that order, and every other field is in the filter
panel beside the table. Name them all and there is no filter panel and no Filters button:

```python
class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter
    toolbar_filters = ["q", "status"]
```

No sort control appears on a table page. A table view leaves out any `SortFilter` its
filterset declares: it is not drawn, a value for it in the address is ignored, and the
rows keep the table's own order. That holds when `toolbar_filters` names the sort too,
which is skipped without an error. So one filterset, sort and all, serves a list page
and a table page unchanged. The view
raises `ImproperlyConfigured` if you declare `order_by` on the view. A table
already sorts through its own column headers, against the sortable columns the table
class defines, and an ordering on the view as well would give the same table two
competing sources for it. Put the ordering on the table class, as its own `order_by` or
`Meta.order_by`.

A search or a filter keeps the order a column heading chose. The filter form carries it,
under the table's own sort parameter (`sort`, or the table's prefix and `sort`), and the
view publishes it to the page as `table_sort`, `""` when no heading has been chosen. A
project that overrides `page.filters` with a form of its own keeps the order the same way:

```django
{% if table_sort %}
  <input type="hidden" name="{{ table.prefixed_order_by_field }}" value="{{ table_sort }}">
{% endif %}
```

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

With [Cotton's context isolation](components.md#switching-on-cottons-context-isolation)
switched on, pass the empty state's values on the tag as well, the way the packaged
`table_view.html` does, or a table with no rows draws an empty state that knows nothing
of the search and filters applied.

With a column pinned, the footer row's cell under it is a row header as well, so a label
such as "Total" stays at the leading edge with the column. The column's edge is a
hairline down its whole height, with a small shadow beside it once the table has
scrolled sideways. On a narrow screen a pinned
column is held to under half the width, and a longer value is cut with an ellipsis.

### A column with no heading

A column whose heading resolves to nothing renders an empty heading cell. The cell
stays, so the column keeps its width and its position in the row, and an orderable
column keeps the control that sorts by it — a column worth sorting is a column worth
naming, and hiding the name is not a request to take the sort away. `verbose_name=""`
is the usual way to say it.

## django-filter

Installed with django-mvp. List `django_filters` in `INSTALLED_APPS`.

Every list view takes its search, its sort and its filters from one django-filter
filterset, declared on the view as `filterset_class` (or generated from
`filterset_fields`). There is no separate filtered list view: `MVPListView`, and every view
built on `MVPListViewMixin`, builds the filterset itself, so composing django-filter's
`FilterView` is refused. See [the list view's filterset](views.md#searching-sorting-and-filtering-with-a-filterset).

```python
from mvp.views import MVPListView


class ProductListView(MVPListView):
    model = Product
    filterset_class = ProductFilter   # or filterset_fields = [...]
```

The view puts `applied_filters` and `applied_filter_count` in the context, covering every
filter. When at least one is applied, it also puts `clear_filters_url` there: the current
list URL with the filterset's fields removed, except the sort, and with pagination reset.
Use these for your own controls. The list page's own Filters button badges
`panel_applied_count`, the applied filters that sit in the filter panel, and the panel's
Clear link is `clear_panel_url`, which keeps the toolbar's filters and the
search. The context table in [views](views.md#what-the-view-tells-the-template) lists them
all.

`applied_filters` comes from `get_active_filters()`, which reads the filterset form's
`cleaned_data` and drops `None` and empty values (an empty string, list or queryset),
which is what an untouched filter field cleans to. A number is always kept, so `0` from a
number filter counts as applied, and so is the `False` of a `BooleanFilter` whose
parameter is in the request: it only comes from a chosen "No". A `SortFilter` is never an
applied filter. Override the hook on the view when a dropped value is a real choice in
your filterset.

Each applied filter, a search among them, is also one of the page's
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

A table view takes a filterset the same way, and can take the list view's own. It leaves
out the filterset's sort, since the table's column headers sort it
([Actions and sorting](#actions-and-sorting)):

```python
from mvp.integrations.django_tables.views import MVPTableView


class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter   # the list view's, sort and all
    toolbar_filters = ["q", "status"]
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
