# Views — deep reference

Concrete views come from `mvp.views`; the mixins live in their modules for composing your
own (standard Django, no factories):

```python
from mvp.views import (                       # concrete views + error handlers
    MVPTemplateView, MVPHomeView, MVPListView, MVPDetailView,
    MVPFormView, MVPCreateView, MVPUpdateView, MVPDeleteView,
    bad_request, permission_denied, not_found, server_error,
)
from mvp.views.base import PageMixin, BaseTemplateNameMixin, ModelInfoMixin
from mvp.views.list import SearchMixin, OrderMixin, SearchOrderMixin, MVPListViewMixin
from mvp.views.detail import CRUDDirectoryMixin, PageObjectMixin
from mvp.views.edit import NextURLMixin, MVPFormBase, MVPModelFormBase
```

---

## `PageMixin` — page chrome on every MVP view

Injects a `page` dict into context. Set static values as class attributes, or override the
`get_*` method for dynamic values.

| Attribute | Type | Default | Template |
|---|---|---|---|
| `page_title` | `str \| Promise` | `""` | `{{ page.title }}` |
| `page_subtitle` | `str \| Promise` | `""` | `{{ page.subtitle }}` |
| `page_class` | `str` | `""` | `{{ page.class }}` (always prefixed `mvp-page`) |
| `breadcrumbs` | `list[dict]` | `[]` | `{% for c in page.breadcrumbs %}` |

Each breadcrumb dict needs `"text"`; an optional `"href"` makes it a link (omit for the
current page). Dynamic example:

```python
class ProductDetailView(PageMixin, DetailView):
    def get_page_title(self):
        return self.object.name
    def get_breadcrumbs(self):
        return [{"text": "Home", "href": "/"},
                {"text": "Products", "href": "/products/"},
                {"text": self.object.name}]
```

---

## `MVPTemplateView` / `MVPHomeView`

`MVPTemplateView` = `PageMixin` + Django `TemplateView`. Wire informational pages directly:

```python
path("about/", MVPTemplateView.as_view(
    template_name="myapp/about.html",
    page_title="About Us", page_subtitle="Who we are",
    breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}],
), name="about")
```

`MVPHomeView` (subclass of `MVPTemplateView`) serves two templates from one URL, no
redirect:

| Attribute | Default | For |
|---|---|---|
| `landing_template_name` | `"mvp/landing.html"` | anonymous visitors |
| `dashboard_template_name` | `"mvp/dashboard.html"` | authenticated users |

`page_title` defaults to `_("Home")`. Context hooks: `get_landing_context(context)` and
`get_dashboard_context(context)`. Raises `ImproperlyConfigured` if `landing_template_name`
is `None` (any request) or `dashboard_template_name` is `None` (authenticated request).

---

## `CRUDDirectoryMixin` — sibling CRUD URLs

Builds a `directory` context dict of CRUD URLs for the model, each gated by a
`has_<action>_permission` flag. URL names come from `crud_views` (defaults to
`MVP_CONFIG["view_names"]`).

```python
class ProductDetailView(MVPDetailView):
    model = Product
    directory = ["list", "detail", "update", "delete"]
    has_list_permission   = True
    has_detail_permission = True    # NOT has_read_permission
    has_update_permission = True
    has_delete_permission = True
```

- All `has_*_permission` default to **`False`** — opt in per action. Each may be a bool or
  a `staticmethod`/method callable `(self, user) -> bool` for dynamic gating.
- The `directory` context key is **always present** (empty dict when all denied), so
  `{% if directory.update_url %}` is always safe.
- `crud_views` templates use `{model_name}` — override to change the naming convention:
  ```python
  crud_views = {"list": "catalogue:{model_name}-index", "detail": "catalogue:{model_name}-view", ...}
  ```
- `get_url_kwargs(action) -> dict | None` controls forwarded URL kwargs (override for
  nested URLs). Return `None` to suppress a URL silently (no `NoReverseMatch`), `{}` for
  collection actions (`list`/`create`) that need no kwargs.

`PageObjectMixin(CRUDDirectoryMixin, PageMixin)` is the shared base for all object-level
views: model resolution + permission-gated sibling URLs + page header/breadcrumbs. Its
`get_breadcrumbs()` builds a `[list link, current page]` trail; `get_page_class()` appends
`{model_name}-page`.

---

## `MVPDetailView`

Zero-config read-only detail page:

```python
class OrderDetailView(MVPDetailView):
    model = Order
    directory = ["list", "update"]
    has_list_permission = True
    has_update_permission = True   # controls the Edit button
```

Automatically: page title = `str(object)`; template = `<app>/<model>_detail.html` then
`detail_view.html` fallback; CSS classes `mvp-page mvp-detail-page <model>-page`.

---

## `NextURLMixin` — safe `?next=` redirects

Composed into `MVPFormBase`, so every create/update/form/delete view benefits.

- **`?next=/some/path/`** — validated same-origin URL (open-redirect safe via
  `url_has_allowed_host_and_scheme`); user returns there after save.
- **`?next=list`** (etc.) — a CRUD shorthand (`list`/`detail`/`create`/`update`/`delete`),
  resolved through the same permission gating as `CRUDDirectoryMixin`.
- Cross-origin URLs and unrecognized bare words are rejected (logged when `DEBUG=True`,
  logger `mvp.views.edit`).
- Templates preserve `next` across failed POST re-renders via a hidden input placed
  **after** the submit buttons (last value wins in Django's `QueryDict`).

---

## Form views: `MVPFormView` / `MVPCreateView` / `MVPUpdateView`

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "category", "price"]      # or form_class = ProductForm
    has_list_permission = True

class ProductUpdateView(MVPUpdateView):
    model = Product
    form_class = ProductForm
    has_delete_permission = True                # shows the footer Delete button
```

- **Renderer auto-detection** — crispy-forms or django-formset when installed, else
  Django default. Override with `form_renderer = "crispy" | "formset" | "django"`.
- **Titles / messages** derive from `model._meta.verbose_name`
  (`"Create Product"`, `"Product successfully created."`). Override `page_title` or
  `success_message` (supports `%(key)s` interpolation; missing keys → `""`, no `KeyError`).
- **`get_page_class()`** → `mvp-form-page mvp-create-page` / `mvp-update-page`.
- **Success URL chain** (`MVPModelFormBase.get_success_url()`): validated `?next=` →
  `success_url` (tried as CRUD shorthand then literal) → `object.get_absolute_url()`.
- **`MVPFormView`** (non-model): raises `ImproperlyConfigured` if `success_url` is unset,
  matching Django's `FormMixin` contract.
- **Breadcrumbs**: create = `[list, current]`; update = `[list, detail (str(object)),
  current]`, with the detail link gated by `has_detail_permission`.

---

## `MVPDeleteView`

Four scenarios via class attributes — no custom template for common cases:

| # | Scenario | Trigger |
|---|---|---|
| 1 | Basic (warning + Delete button) | default |
| 2 | Related-objects summary (preview cascade) | `show_related_objects = True` |
| 3 | Protected (hides Delete, lists blockers) | auto-detected (PROTECT FK) |
| 4 | Type-to-confirm | `require_confirmation = True` |

| Attribute | Default | Effect |
|---|---|---|
| `show_related_objects` | `False` | preview cascade-deleted records |
| `require_confirmation` | `False` | user must type the object name to enable Delete |
| `confirmation_label` | `_("Type the name to confirm")` | label for the confirm input |
| `related_objects_max_per_group` | `25` | cap per group; excess shown as "… and N more" |

- `get_confirmation_value()` defaults to `str(self.object)` — override (e.g. return
  `self.object.slug`). Confirmation is validated **server-side** via `DeleteConfirmForm`
  (`mvp.forms`), not just JS, so a JS bypass still fails.
- With `show_related_objects=True`, `context["related_objects"]` is a list of
  `(label, objects, overflow)` tuples.
- **Success URL chain**: validated `?next=` (or shorthand) → `success_url` (shorthand then
  literal) → list URL → `ImproperlyConfigured`. `get_absolute_url()` is intentionally
  **skipped** (the object no longer exists).
- Defaults: `page_class = "mvp-delete-page"`, title `"Delete {VerboseName}"`, message
  `"%(verbose_name)s successfully deleted."`.

---

## List views: search / order / pagination

### `SearchMixin` — `?q=` search

```python
class ProductListView(SearchMixin, ListView):
    model = Product
    search_fields = ["name", "description", "category__name"]
```

`?q=foo bar` → records where any field contains "foo" OR "bar" (case-insensitive).
Whitespace-only `?q=` = empty. When `search_fields` is unset it's a complete no-op.
Context (always injected): `is_searchable` (bool), `search_query` (str). Override
`get_search_fields()` for dynamic fields.

### `OrderMixin` — `?o=` whitelist ordering

Entries are **three-tuples** `(public_key, label, orm_expression)`:

```python
order_by = [
    ("name_asc",  "Name (A-Z)",          "name"),
    ("name_desc", "Name (Z-A)",          "-name"),
    ("newest",    "Newest First",         "-created_at"),
    ("price_asc", "Price (Low to High)", "price"),
]
```

| Field | Role |
|---|---|
| `public_key` | matched against `?o=`; any URL-safe string (need not be a column) |
| `label` | display text for the ordering UI |
| `orm_expression` | passed to `queryset.order_by()`; may start with `-`; **never URL-exposed** |

**Security:** the raw `?o=` value never reaches the ORM — only the matching entry's
`orm_expression`. Unrecognized values are ignored. Context (only when configured):
`order_by_choices` (the whitelist), `current_ordering` (matched `public_key` or `""`).
Override `get_order_by_choices()` for dynamic whitelists.

### `SearchOrderMixin`

`SearchOrderMixin(SearchMixin, OrderMixin)` — fixed MRO so ordering applies first and
search + `distinct()` last (avoids the Postgres `SELECT DISTINCT + ORDER BY on JOIN`
error). Both `search_fields` and `order_by` are independently optional.

Compose with `django_filters` by placing the mixin **left** of `FilterView`:

```python
class ProductListView(SearchOrderMixin, FilterView):  # or MVPListViewMixin
    model = Product
    filterset_fields = ["category"]
    search_fields = ["name"]
    order_by = [("name_asc", "Name (A-Z)", "name")]
```

### `MVPListView` — concrete list page

```python
class ProductListView(MVPListView):
    model = Product           # paginated 24/page, searchable, orderable, empty state
```

| Attribute | Default | Notes |
|---|---|---|
| `paginate_by` | `24` | (on `MVPListView`; `MVPListViewMixin` doesn't set it) — divisible by 1/2/3/4 |
| `list_item_template` | `None` | else `<app_label>/<model_name>_list_item.html` |
| `grid` | `{}` | breakpoint dict → context `grid_config` |
| `empty_state_heading` | `_("There's nothing here yet")` | `None` suppresses |
| `empty_state_message` | `_("You haven't added any records yet…")` | `None` suppresses |
| `page_title` | `""` | falls back to `verbose_name_plural.title()` |
| `search_fields` / `order_by` | `None` | from Search/Order mixins |
| `directory` | `["create"]` | only `create_url` injected (when `has_create_permission`) |
| `create_form_class` | `None` | set it (+ `has_create_permission`) for an inline create modal on the list page |

Override hooks: `get_list_item_template()`, `get_empty_state_heading/message()`,
`get_grid_config()`, `get_page_title()`, `get_breadcrumbs()`, `get_create_form()`.
Use `MVPListViewMixin` (not `MVPListView`) to compose with another base like `FilterView`.

---

## Error handlers

```python
# root urls.py
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

Templates `400/403/404/500.html` extend `mvp/error_base.html` (full-viewport, no sidebar,
no DB). Override blocks `title`, `heading`, `description`, `actions`. `server_error` passes
`support_email` (`settings.DEFAULT_FROM_EMAIL` or `None`) and must stay DB-free.

---

## htmx (`mvp.views.htmx.HtmxFormMixin`)

With django-htmx installed + middleware active, mix `HtmxFormMixin` **before** a form view.
Invalid htmx POST → re-renders only the form partial; success → `HX-Redirect` or a success
partial; events via `HX-Trigger`. Configure `htmx_form_component` /
`htmx_success_component` (Cotton component names). Non-htmx requests fall back to the
standard redirect flow.
