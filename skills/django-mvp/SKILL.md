---
name: mvp-app-shell
description: 'Step-by-step guide for integrating django-mvp into a Django project. Use when wiring up the AdminLTE 4 layout shell: INSTALLED_APPS setup, EASY_ICONS Bootstrap Icons config, FLEX_MENUS adminlte renderer, base template using Cotton component attributes, sidebar menu via AppMenu, dual-mode views, and error pages. Covers common pitfalls: wrong icon renderer, missing adminlte renderer registration.'
---

# django-mvp App Shell Integration

Covers wiring django-mvp into an existing Django project from zero to a fully navigable
AdminLTE 4 shell with sidebar, navbar, and error pages.

## Critical Decisions

| Decision | Correct Approach | Wrong Approach |
|----------|-----------------|----------------|
| Layout config | Cotton component attributes on `<c-app>` | `settings.MVP` dict (removed) |
| Icon renderer | Bootstrap Icons (`bi bi-*`) as default | Font Awesome as default (breaks mvp internals) |
| Menu autodiscovery | `AppMenu.extend([...])` in `menus.py` — no extra `ready()` needed | Manually importing menus in `apps.py` |
| `<c-app.sidebar>` menu | Rendered automatically via `{% render_menu "AppMenu" renderer="adminlte" %}` | Manually writing sidebar HTML |

---

## Step 1 — INSTALLED_APPS

`"mvp"` must come **before** `"django_cotton"` so its Cotton components are found:

```python
INSTALLED_APPS = [
    # ...
    "mvp",              # BEFORE django_cotton
    "django_cotton",
    "cotton_bs5",
    # ...
]
```

---

## Step 2 — EASY_ICONS (Bootstrap Icons)

django-mvp renders icons via `<c-icon name="..." />` which calls `{% icon name %}` with
no renderer hint — so the **default** renderer must have Bootstrap Icons. Preserve Font
Awesome under a separate key if needed.

See [./references/easy-icons-config.md](./references/easy-icons-config.md) for the
full configuration block including required django-mvp internal icons.

Key mapping pattern:
```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "icons": {
            "chevron_right": "bi bi-chevron-right",  # required by mvp
            "chevron_down": "bi bi-chevron-down",    # required by mvp
            "theme_light": "bi bi-sun",              # required by mvp
            "theme_dark": "bi bi-moon",              # required by mvp
            "theme_auto": "bi bi-circle-half",       # required by mvp
            "dropdown_check": "bi bi-check2",        # required by mvp
            # ... app icons ...
        },
    },
}
```

---

## Step 3 — FLEX_MENUS

The sidebar calls `{% render_menu "AppMenu" renderer="adminlte" %}`. That renderer key
must be registered:

```python
FLEX_MENUS = {
    "renderers": {
        "adminlte": "mvp.renderers.AdminLTERenderer",
    },
    "log_url_failures": DEBUG,
}
```

---

## Step 4 — Sidebar Menu (`menus.py`)

Extend `AppMenu` in the app's `menus.py`. `FlexMenuConfig.ready()` autodiscovers this
file — no `ready()` override needed in your `AppConfig`.

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu

AppMenu.extend([
    MenuItem("dashboard",
             view_name="home",
             extra_context={"label": "Dashboard", "icon": "speedometer2"}),
    MenuItem("section_name",
             view_name="url_name",
             extra_context={"label": "Section Label", "icon": "icon-name"}),
])
```

**Icon names** must be registered in `EASY_ICONS["default"]["icons"]`.

**Active state** is automatic: `AdminLTERenderer` sets `selected=True` when
`request.path == item.url` (exact match). The sidebar item template applies `.active`
accordingly.

**Visibility checks** — restrict items by auth state:
```python
from flex_menu.checks import user_is_authenticated
MenuItem("dashboard", view_name="home", check=user_is_authenticated, ...)
```

For nesting, see [./references/menu-patterns.md](./references/menu-patterns.md).

---

## Step 5 — Base Template

Extend `mvp/base.html` and override `{% block app %}` to compose the layout using
Cotton component attributes. **Do not use `settings.MVP`.**

```django
{% extends "mvp/base.html" %}
{% load easy_icons %}

{% block title %}My App{% endblock %}

{% block app %}
  <c-app fixed_sidebar sidebar_expand="md">

    <c-app.header>
      My App
      <c-slot name="right">
        {# Primary action button — always visible #}
        <a href="{% url 'my_primary_action' %}" class="btn btn-success btn-sm me-2">
          {% icon "plus-circle" %} Quick Action
        </a>
        {# Account dropdown — see references/account-dropdown.md #}
      </c-slot>
    </c-app.header>

    {# Sidebar renders AppMenu automatically when no slot content is provided #}
    <c-app.sidebar brand_text="My App" />

    <c-app.main>{% block content %}{% endblock %}</c-app.main>

    <c-app.footer text="My App — description here." />

  </c-app>
{% endblock %}
```

### Key `<c-app>` attributes

| Attribute | Type | Effect |
|-----------|------|--------|
| `fixed_sidebar` | boolean flag | Sidebar stays in view while scrolling |
| `sidebar_expand` | string | Bootstrap breakpoint: `sm`, `md`, `lg` (default), `xl`, `xxl` |
| `fixed_header` | boolean flag | Navbar stays pinned at top |
| `fixed_footer` | boolean flag | Footer stays pinned at bottom |

**`sidebar_expand="md"`** expands the sidebar at ≥768px and collapses it below — the
typical mobile-first breakpoint.

### Sidebar slots

`<c-app.sidebar>` accepts no slot content when you want the auto-rendered menu.
To inject custom slot content above/below the menu, use named slots:
```django
<c-app.sidebar brand_text="My App">
  <c-slot name="before_menu"><p>custom content</p></c-slot>
</c-app.sidebar>
```

---

## Step 6 — Zero-Config Views: `PageView` and `HomeView`

django-mvp ships two ready-to-use view classes that require no model, form, or queryset.

### `PageView` — Plain layout-aware template view

Wire any informational page (About, FAQ, Terms, etc.) directly in `urls.py`:

```python
from mvp.views import PageView

urlpatterns = [
    path("about/", PageView.as_view(
        template_name="myapp/about.html",
        page_title="About Us",
        page_subtitle="Who we are",
        page_icon="info-circle",  # must be a registered EASY_ICONS name
        breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}],
    ), name="about"),
]
```

Create the template extending `page_view.html`:

```django
{# myapp/templates/myapp/about.html #}
{% extends "page_view.html" %}
{% block page.content %}
  <p>Welcome to our about page.</p>
{% endblock page.content %}
```

`PageView` is an alias for `MVPTemplateView`. Import from `mvp.views`.

### `HomeView` — Landing page for guests, dashboard for authenticated users

Serves different templates from the same URL with **no redirect**:

```python
from mvp.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(
        landing_template_name="myapp/landing.html",
        dashboard_template_name="myapp/dashboard.html",
    ), name="home"),
]
```

| Attribute | Default | Description |
|-----------|---------|-------------|
| `landing_template_name` | `"mvp/landing.html"` | Template for anonymous visitors |
| `dashboard_template_name` | `"mvp/dashboard.html"` | Template for authenticated users |

**Bundled defaults**: omit both attributes to use the built-in `mvp/landing.html` and `mvp/dashboard.html` templates. The landing template reads from `MVP_LANDING_PAGE_HERO` in settings.

**`ImproperlyConfigured` guard**: raises with a diagnostic message if `landing_template_name` is `None` (for any request), or if `dashboard_template_name` is `None` when an authenticated user requests the page.

**Extending with context hooks**:

```python
class AppHomeView(HomeView):
    landing_template_name = "myapp/landing.html"
    dashboard_template_name = "myapp/dashboard.html"

    def get_dashboard_context(self, context):
        context = super().get_dashboard_context(context)
        context["recent_items"] = MyModel.objects.order_by("-created")[:5]
        return context
```

`HomeView` is an alias for `MVPHomeView`. Import from `mvp.views`.

---

## Step 7 — Page Configuration (`PageMixin`)

All django-mvp view classes inherit `PageMixin`, which injects a `page` dict into every
template context. Set attributes as class-level assignments for static values, or override
the corresponding `get_*()` method for dynamic values.

### Attributes

| Attribute | Type | Default | Template access |
|-----------|------|---------|-----------------|
| `page_title` | `str \| Promise` | `""` | `{{ page.title }}` |
| `page_subtitle` | `str \| Promise` | `""` | `{{ page.subtitle }}` |
| `page_icon` | `str \| None` | `None` | `{{ page.icon }}` |
| `page_class` | `str` | `""` | `{{ page.class }}` (always prefixed with `"mvp-page"`) |
| `breadcrumbs` | `list[dict]` | `[]` | `{% for crumb in page.breadcrumbs %}` |

Each breadcrumb dict must have a `"text"` key. An optional `"href"` key makes it a link;
omitting `"href"` renders it as the current (non-linked) page indicator.

### Static configuration

```python
from mvp.views.base import MVPTemplateView

class AboutView(MVPTemplateView):
    template_name = "about.html"
    page_title = "About Us"
    page_subtitle = "Our mission"
    page_icon = "info-circle"
    page_class = "about-page"
    breadcrumbs = [
        {"text": "Home", "href": "/"},
        {"text": "About"},  # no href = current page
    ]
```

### Dynamic configuration

Override the getter method when the value depends on the request, a resolved object,
or other runtime state:

```python
class ProductDetailView(PageMixin, DetailView):
    def get_page_title(self):
        return self.object.name

    def get_breadcrumbs(self):
        return [
            {"text": "Home", "href": "/"},
            {"text": "Products", "href": "/products/"},
            {"text": self.object.name},
        ]
```

---

## Step 8 — Error Pages

**`templates/404.html`** — extends `base.html` safely (Django runs context processors
for 404, so Cotton and menu rendering work):
```django
{% extends "base.html" %}
{% block content %}
  <h1>Page not found</h1>
  <a href="{% url 'home' %}">Back to home</a>
{% endblock %}
```

**`templates/500.html`** — must be self-contained with **no template inheritance**,
no context processors, no Cotton, no template tags. Django's 500 handler uses a bare
`Context()` with no processor injection:
```html
<!doctype html>
<html><head><title>Error</title></head>
<body style="font-family:sans-serif;max-width:600px;margin:4rem auto;padding:1rem">
  <h1>Something went wrong</h1>
  <p>Please try again later.</p>
  <a href="/">Return to home</a>
</body></html>
```

---

## Step 8 — Verify

```bash
poetry run python manage.py check          # catches missing app config issues
poetry run pytest                          # run test suite
```

Manual smoke-test checklist (visit in browser):
- [ ] `/` unauthenticated → landing page, no sidebar, Sign In/Sign Up visible
- [ ] `/` authenticated → dashboard, full sidebar, navbar Quick Action visible
- [ ] Each sidebar URL → HTTP 200, correct active item highlighted
- [ ] Navbar Quick Action → present on every authenticated page
- [ ] `/nonexistent/` → styled 404 page in full layout
- [ ] Mobile viewport (320px) → sidebar hidden, toggle button visible, layout not clipped

---

---

## Step 9 — CRUD Directory Mixin (`CRUDDirectoryMixin`)

`CRUDDirectoryMixin` removes URL wiring boilerplate from model-driven views. Declare
which CRUD actions to include, set a permission flag per action, and the mixin resolves
URLs automatically. Templates read from the `directory` context variable.

### Basic usage

```python
from mvp.views import MVPDetailView

class ProductDetailView(MVPDetailView):
    model = Product
    directory = ["list", "detail", "update", "delete"]

    # All permissions default to False — opt in per action:
    has_list_permission   = True
    has_detail_permission = True   # note: NOT has_read_permission
    has_update_permission = True
    has_delete_permission = True
```

In the template:

```django
{% if directory.update_url %}
  <a href="{{ directory.update_url }}" class="btn btn-primary">Edit</a>
{% endif %}
{% if directory.delete_url %}
  <a href="{{ directory.delete_url }}" class="btn btn-danger">Delete</a>
{% endif %}
{% if directory.list_url %}
  <a href="{{ directory.list_url }}">&larr; Back to list</a>
{% endif %}
```

The `directory` context key is **always present** — even when all permissions are
denied it is an empty dict. Use `{% if directory.update_url %}` safely without fallback.

### Permission attributes (all default to `False`)

| Attribute | Action |
|-----------|--------|
| `has_list_permission` | `"list"` |
| `has_detail_permission` | `"detail"` |
| `has_create_permission` | `"create"` |
| `has_update_permission` | `"update"` |
| `has_delete_permission` | `"delete"` |

> **Breaking change (006)**: `has_read_permission` was renamed to `has_detail_permission`.
> Using `has_read_permission` has no effect — the attribute is not checked by the mixin.

For dynamic gating use a `staticmethod` callable:

```python
class ProductUpdateView(MVPUpdateView):
    model = Product
    directory = ["list", "delete"]
    has_list_permission = True

    @staticmethod
    def has_delete_permission(user):
        return user.is_staff
```

### Override point: `get_url_kwargs(action: str) -> dict | None`

Controls which URL kwargs are forwarded for each action. Override for nested URLs:

```python
def get_url_kwargs(self, action: str) -> dict | None:
    project_pk = self.kwargs["project_pk"]
    if action in {"list", "create"}:
        return {"project_pk": project_pk}   # collection URLs need parent only
    pk = self.kwargs.get("pk")
    if pk is None:
        return None  # silently suppress — no object in scope
    return {"project_pk": project_pk, "pk": pk}
```

Returning `None` suppresses the URL silently (no `NoReverseMatch` attempted).
Returning `{}` reverses with no kwargs (valid for collection actions).

> **Breaking change (006)**: `get_lookup_kwargs()` was replaced by
> `get_url_kwargs(action: str) -> dict | None`. The new method is action-aware and
> returns `{}` for `"list"` / `"create"` by default, preventing `NoReverseMatch` on
> collection URLs when called from an object-level view.

### Custom URL naming via `crud_views`

Override `crud_views` if your project does not follow the `{model_name}-{action}` convention:

```python
crud_views = {
    "list":   "catalogue:{model_name}-index",
    "detail": "catalogue:{model_name}-view",
    "update": "catalogue:{model_name}-modify",
    "create": "catalogue:{model_name}-new",
    "delete": "catalogue:{model_name}-remove",
}
```

---

## Step 10 — Object Page Foundation (`PageObjectMixin` + `MVPDetailView`)

`PageObjectMixin` and `MVPDetailView` are the shared composition layer for all
object-level views (detail, create, update, delete).

### PageObjectMixin

`PageObjectMixin` merges three prior building blocks into a single inheritable base:

- **Model resolution** — from `ModelInfoMixin` via `CRUDDirectoryMixin`
- **Permission-gated sibling URLs** — from `CRUDDirectoryMixin`
- **Page header and breadcrumbs** — from `PageMixin`

```python
from mvp.views import PageObjectMixin
```

Key class attributes and methods:

| Attribute / Method | Description |
|---|---|
| `list_view_title = ""` | Override text for the breadcrumb back-link. Defaults to `verbose_name_plural.title()`. |
| `get_list_title()` | Returns `list_view_title` or the model's plural verbose name, title-cased. |
| `get_list_url()` | Returns the resolved list URL, or `""` when suppressed by permission gating. |
| `get_breadcrumbs()` | Two-item trail: `[{"text": list_title, "href": list_url}, {"text": page_title}]`. |
| `get_page_class()` | Appends `{model_name}-page` to the class string from `PageMixin.get_page_class()`. |

### MVPDetailView

`MVPDetailView` is the simplest concrete result — a zero-configuration read-only detail page:

```python
from mvp.views import MVPDetailView
from myapp.models import Order

class OrderDetailView(MVPDetailView):
    model = Order
```

Wire it to a URL:

```python
urlpatterns = [
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="myapp_order_detail"),
]
```

The rendered page automatically:

- Sets the page title to `str(order_instance)` (from `Order.__str__`).
- Applies CSS classes `mvp-page mvp-detail-page order-page` to the page container.
- Tries `myapp/order_detail.html` first, falls back to `detail_view.html`.

### Breadcrumb wiring via `has_list_permission`

```python
class OrderDetailView(MVPDetailView):
    model = Order
    directory = ["list"]
    has_list_permission = True
    list_view_title = "Active Orders"  # optional; defaults to verbose_name_plural.title()
```

Breadcrumb trail: `Active Orders  >  Order #42`

### Effective CSS classes

For a view with `model = Order`:

```
mvp-page  mvp-detail-page  order-page
```

`mvp-page` — always present (from `PageMixin`)
`mvp-detail-page` — action class set on `MVPDetailView.page_class`
`order-page` — model-name class appended by `PageObjectMixin.get_page_class()`

> **Full guide**: `specs/007-object-page-foundation/quickstart.md`

---

## Common Pitfalls

**"AppMenu items don't appear"**
- Confirm `menus.py` lives in an app that is in `INSTALLED_APPS`
- Confirm `AppMenu.extend([...])` is called at module level, not inside a function
- Check there are no import errors in `menus.py` (they're silently swallowed by autodiscover)

**"Icons not rendering / show as empty boxes"**
- Confirm the icon name is registered in `EASY_ICONS["default"]["icons"]`
- Confirm Bootstrap Icons CSS is loaded — `mvp/base.html` includes it automatically

**"Sidebar renders but menu is empty"**
- Confirm `FLEX_MENUS["renderers"]["adminlte"]` is set
- Confirm `view_name` values resolve — run `manage.py check` or catch `NoReverseMatch`

**"Layout uses settings.MVP"**
- The `settings.MVP` dict has been removed. Pass all config as Cotton component attributes on `<c-app>`.

**"500 page is broken / shows error"**
- The 500 template CANNOT extend any base template. Make it fully self-contained HTML.
