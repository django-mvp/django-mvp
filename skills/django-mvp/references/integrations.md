# Integrations — reference

How django-mvp meets third-party packages: django-tables2, django-filter, htmx and
crispy-forms. Covers the guarded-module rule, the table view and its column classes,
the filter view's context additions, and the htmx form mixins.

## The model: guarded modules, not packaging extras

Views built on a third-party package live under `mvp.integrations` and are **not**
exported from `mvp.views`. Nothing in the core package imports them, so the dependency is
only needed when *you* import the integration. The guard is a `try/except ImportError`
around the third-party import at module level, re-raising `ImproperlyConfigured` with the
pip name and install command (built by `mvp.integrations.missing_dependency()`). No extra
to install, no settings flag, no runtime feature detection.

| Integration | Import from | Needs |
|---|---|---|
| django-tables2 | `mvp.integrations.django_tables.views` | `pip install django-tables2` |
| django-filter | `mvp.integrations.django_filters.views` | `pip install django-filter` |

## django-tables2

```python
# myapp/views.py
from mvp.integrations.django_tables.views import MVPTableView

class ProductTableView(MVPTableView):
    model = Product
    table_class = ProductTable
    search_fields = ["name", "sku"]
```

`MVPTableViewMixin` combines `MVPListViewMixin` (search, pagination, page chrome) with
django-tables2's `SingleTableMixin`. `MVPTableView` is that mixin over Django's
`ListView`. Use the mixin when you need a different base — composing it with `FilterView`
gives a filtered table view. The base template is `table_view.html`, which renders through
the `<c-addons.django-table>` component.

### Ordering belongs on the table class

A table view **must not declare `order_by`**. `MVPTableViewMixin.__init__` raises
`ImproperlyConfigured` if it finds one: a table already sorts through its own column
headers, against its own list of sortable columns, so a view-level ordering would be a
second surface for the same job.

```python
# myapp/tables.py — put the ordering here, not on the view
class ProductTable(tables.Table):
    class Meta:
        model = Product
        order_by = ("-created",)   # or set order_by on the table instance
```

### Actions, and the context key they arrive under

`actions` lists the controls in the bar above the table, defaulting to
`["search", "filter", "create"]` — a list view's set minus sort, dropped for the same
reason the `order_by` guard exists. Set `actions = ["search", "create"]` on the view to
change or reorder them.

The view puts that list in the context as **`table_actions`**, deliberately not
`actions`. Both `<c-toolbar>` and `<c-page.title>` expose a slot named `actions`, and a
Cotton slot falls through to the context variable of the same name when the caller fills
no slot — so a context key called `actions` prints its own repr into every toolbar on the
page. If you override `{% block page.actions %}` on a table page, pass `table_actions`.

### The full-screen layout

A table view renders edge to edge rather than sitting in a card inside a scrolling
document:

| Region | Behaviour |
|---|---|
| Title bar | Page title and the view's actions, above the table. The breadcrumb trail lives in this bar and its last crumb *is* the `<h1>`. |
| Table | Its own scroll region, owning both axes, so overflow never reaches the window. |
| Count and pagination | A bar pinned below the table: record range, then page links. |
| Heading and footer rows | Stay in view while the rows move under them. |
| Shell footer | Emptied on this layout — the viewport is fully spent on the table. |

**Existing table classes need no change.** The layout lives entirely in the view's base
template and the add-on component.

The scrolling element carries `tabindex="0"`, `role="region"` and an accessible name
(defaulting to "Scrollable table"). An overflow container is not a tab stop in Firefox or
Safari, so without those a keyboard-only reader cannot scroll the rows. The
component takes `label` and `role` so a page with two tables can name each one:

```django
{# myapp/templates/myapp/two_tables.html — one name per table #}
<c-addons.django-table :table="orders" label="Orders" class="flex-1 min-h-0" />
<c-addons.django-table :table="returns" label="Returns" class="flex-1 min-h-0" />
```

`<c-addons.django-table>` **no longer accepts `min_height`.** It is now the scroll region
and takes its height from the page. Remove the attribute, and mark the page `fill` if you
want the table to fill the screen.

### Column behaviour classes

Applied the ordinary django-tables2 way, through a column's own `attrs`. No column class
to import, nothing to subclass.

| Class | Effect |
|---|---|
| `mvp-col-grow` | Claims whatever width is left once every other column has taken what it needs. |
| `mvp-col-shrink` | Takes no more width than its own content needs. |
| `mvp-col-wrap` | Lets cell text wrap onto more than one line. |
| `mvp-col-nowrap` | Keeps cell text on a single line. |
| `mvp-col-max-{xs,sm,md,lg,xl}` | Caps the column at `8rem` / `12rem` / `16rem` / `24rem` / `32rem` once its text may wrap. |

```python
# myapp/tables.py
import django_tables2 as tables

class ProductTable(tables.Table):
    name = tables.Column(attrs={"td": {"class": "mvp-col-grow"}})
    sku = tables.Column(
        # Heading is longer than the values, so the class goes on both cells.
        attrs={"td": {"class": "mvp-col-shrink"}, "th": {"class": "mvp-col-shrink"}}
    )
    description = tables.Column(attrs={"td": {"class": "mvp-col-wrap mvp-col-max-md"}})
```

Tables lay out with the browser's default `table-layout: auto`, which negotiates each
column's width across every cell in it, heading included. A width class on the `td` alone
looks like it did nothing whenever the heading is the long part — name it on the `th` too.
Wrap classes are the exception: the template asks for the heading cell's attributes with
wrapping disabled, and the tag only adds a wrap class when it is enabled, so a `th` receives
neither `mvp-col-wrap` nor `mvp-col-nowrap` and wraps by the browser's default. Headings are
excluded from the setting below rather than following it, which keeps a column from being
widened by its own title.

`mvp-col-grow` and `mvp-col-shrink` are opposites, and naming both is settled by the
stylesheet, not by your `attrs`: the two rules have the same specificity and set the same
property, so the one written later in the built CSS applies. That is `mvp-col-shrink`, every
time. Maximum width comes from the fixed set of names above rather than a number you supply,
so every class a table can use already exists in the built stylesheet.

### The project-wide wrap default

Whether a body cell wraps when its column names neither wrap class itself is a project
setting. Headings are outside it, as above:

```python
# settings.py — ships as False, so one row per record until you say otherwise
MVP_CONFIG = {"table": {"wrap": True}}
```

Resolution order: **the column's own class, then this setting, then the package default**
(no wrap).

### Inferred column alignment

The shipped table template aligns each column by the kind of model field behind it, with
nothing to declare. Every cell of a column takes the same alignment, so a heading always
sits over cells aligned the way it is.

| Column holds | Alignment |
|---|---|
| Text — char, text, date, foreign key, … | Leading |
| A number — integer, decimal, float | Trailing |
| A boolean | Centred |
| No resolvable model field and not orderable — an action column of buttons or links | Centred |

It declines rather than guesses. A table over data that is not a queryset has no model to
resolve a field from, and a column whose accessor resolves to no field but *is* orderable
is a plain unresolvable column, not an action column. Neither gets an alignment imposed.

An explicit alignment class in a column's `attrs` always wins, and declaring it on the
`td` alone is enough — the column's other cells are given the same class rather than an
inferred one.

## django-filter

```python
# myapp/views.py
from mvp.integrations.django_filters.views import MVPFilteredListView

class ProductListView(MVPFilteredListView):
    model = Product
    filterset_class = ProductFilter    # or filterset_fields = [...]
    search_fields = ["name"]
```

`MVPFilteredListView` is `MVPListViewMixin` over django-filter's `FilterView`. On top of
the list behaviour it adds two context keys, and only when a `filter` is in the context:

| Key | Value |
|---|---|
| `applied_filters` | Dict of the filters actually applied, keyed by filter name. |
| `applied_filter_count` | The length of that dict. |

The filter action on the list page reads them to badge the filter button with the number
of active filters.

`get_active_filters()` is the hook for changing what counts as applied. It reads the
filterset form's `cleaned_data` and skips `None`, `""`, `[]`, `()` and `False`. Override
it on the view when a skipped value is a real choice in your filterset — an unchecked
boolean the user deliberately selected, say.

## htmx

The htmx mixins live in `mvp.views.htmx` — under `mvp.views`, not `mvp.integrations`, and
not guarded by `missing_dependency()`. They import `django_htmx` directly, so importing
the module without **django-htmx** installed raises a plain `ImportError`. Install it with
`pip install django-htmx`.

`django_htmx.middleware.HtmxMiddleware` in `MIDDLEWARE` is the second requirement, but only
for `HtmxFormMixin`: its `form_valid()` and `form_invalid()` branch on `request.htmx`, which
that middleware sets. `HtmxMixin` never reads it, so the plain mixin works without the
middleware registered.

The htmx **library** is a separate matter: it ships with django-mvp in the bundled
front-end runtime and runs on every page, so you add no script tag. That also means
`hx-*` attributes are live anywhere in your markup — if a page renders HTML you did not
author, strip those along with everything else you already sanitize.

### `HtmxMixin`

The lightweight base, usable on any view. It injects `htmx_enabled = True` into the
context so templates can render htmx attributes conditionally. The key is set on every
request, htmx or not — it says the view opted in, not that this request came from htmx.

| Attribute | Default | Purpose |
|---|---|---|
| `htmx_trigger` | `None` | Event name, or a `{name: params}` dict, emitted as an `HX-Trigger` family header. Falsy means no header. |
| `htmx_trigger_after` | `"receive"` | Phase the event fires in: `"receive"`, `"settle"` or `"swap"`. |

### `HtmxFormMixin`

Subclasses `HtmxMixin` and adds htmx-aware form handling. Put it **before** the base view
class so its `form_valid()` and `form_invalid()` intercept first.

| Attribute | Default | Purpose |
|---|---|---|
| `htmx_success_component` | `None` | Cotton component name for the success partial, dot-notation: `"ui.product-created"` → `cotton/ui/product_created.html`. |
| `htmx_success_components` | `()` | Allowlist of `(alias, component)` pairs the requesting element may choose between. |
| `htmx_form_component` | `"form"` | Cotton component name for the form-error partial. |
| `htmx_redirect_on_success` | `False` | Return a client-side redirect to the success URL instead of a partial. |

```python
# myapp/views.py
from mvp.views import MVPCreateView
from mvp.views.htmx import HtmxFormMixin

class ProductCreateView(HtmxFormMixin, MVPCreateView):
    model = Product
    fields = ["name", "price"]
    htmx_success_component = "ui.product-created"
    htmx_success_components = (("list", "product.list-item"),)
    htmx_trigger = {"product-created": {}}
    success_url = "list"
```

The client picks an allowlisted component with the **`X-Success-Component`** request
header, matched against the aliases:

```django
{# myapp/templates/myapp/product_form.html #}
<form hx-post="{% url 'product-create' %}"
      hx-headers='{"X-Success-Component": "list"}'>
```

An unknown alias, or no header, falls through to `htmx_success_component`. Resolving
neither raises `ImproperlyConfigured` unless `htmx_redirect_on_success` is set.

On an htmx POST a valid form saves, the Django message queue is drained so messages do
not reappear on the next full-page load, and either a client redirect or the rendered
success partial goes back with any trigger headers attached. An invalid form re-renders
the form component at HTTP 200. Both paths delegate straight to `super()` when the
request is not from htmx, so the view keeps working as an ordinary form view.

## crispy-forms

Not an integration. `django-crispy-forms` and `crispy-tailwind` are **hard runtime
dependencies**, installed with django-mvp every time. There is nothing to opt into and no
guard to trip. Only the settings are your responsibility, and the `INSTALLED_APPS`
entries are load-bearing: Django resolves `{% load %}` libraries only from registered
apps, so without them `{% load crispy_forms_tags %}` still raises `TemplateSyntaxError`.

```python
# settings.py
INSTALLED_APPS = [..., "crispy_forms", "crispy_tailwind", ...]
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"
```

---

Back to [SKILL.md](../SKILL.md).
