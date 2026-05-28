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

## Mobile Footer Navigation

`MobileFooterMenu` is an independent menu object for the mobile-only sticky footer nav
bar. It ships pre-populated with a sidebar toggle item and supports the same
django-flex-menus API as `AppMenu`.

### Register the renderer (settings.py)

Add `"mobile-footer-nav"` alongside the existing renderer keys:

```python
FLEX_MENUS = {
    "renderers": {
        "adminlte": "mvp.renderers.AdminLTERenderer",
        "mobile-footer-nav": "mvp.renderers.MobileFooterNavRenderer",  # ← add this
    },
    "log_url_failures": DEBUG,
}
```

### Add items to the menu (menus.py)

Import and mutate `MobileFooterMenu` in the same `menus.py` file as your `AppMenu` items:

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MobileFooterMenu

AppMenu.extend([...])  # existing sidebar items

MobileFooterMenu.children.append(
    MenuItem(
        name="my_footer_link",
        view_name="my_view_name",
        extra_context={"label": "My Page", "icon": "house"},
    )
)
```

**Removing the pre-populated sidebar toggle** — if you don't want the default toggle:

```python
MobileFooterMenu.children = [
    # Only your custom items here; sidebar toggle is excluded
    MenuItem("my_link", view_name="home", extra_context={"label": "Home", "icon": "house"}),
]
```

**Visibility checks** work identically to `AppMenu`:

```python
from flex_menu.checks import user_is_authenticated
MenuItem("my_link", view_name="home", check=user_is_authenticated, extra_context={...})
```

### Use the component (templates)

The footer nav renders automatically in `mvp/base.html`. Override the block to customise
or disable it:

```django
{# Disable the footer nav entirely #}
{% block app.mobile_footer_nav %}{% endblock app.mobile_footer_nav %}

{# Add custom CSS class #}
{% block app.mobile_footer_nav %}
  <c-app.mobile-footer-nav class="my-custom-modifier" />
{% endblock app.mobile_footer_nav %}
```

The `<c-app.mobile-footer-nav>` component renders a `<nav>` element with `show-on-mobile`
(hidden on desktop via the sidebar-expand breakpoint), `fixed-bottom` (pinned to viewport
bottom), `bg-body`, and `border-top` classes.

### Supported attributes

| Attribute | Type | Effect |
|-----------|------|--------|
| `class` | string | Extra CSS class(es) appended to the `<nav>` element |

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

## Step 6 — Zero-Config Views: `MVPTemplateView` and `HomeView`

django-mvp ships two ready-to-use view classes that require no model, form, or queryset.

### `MVPTemplateView` — Plain layout-aware template view

Wire any informational page (About, FAQ, Terms, etc.) directly in `urls.py`:

```python
from mvp.views import MVPTemplateView

urlpatterns = [
    path("about/", MVPTemplateView.as_view(
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

`MVPTemplateView` is an alias for `MVPTemplateView`. Import from `mvp.views`.

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
|-----------|------|---------|---------------|
| `page_title` | `str \| Promise` | `""` | `{{ page.title }}` |
| `page_subtitle` | `str \| Promise` | `""` | `{{ page.subtitle }}` |
| `page_icon` | `str \| None` | `None` | `{{ page.icon }}` |
| `page_class` | `str` | `""` | `{{ page.class }}` (always prefixed with `"mvp-page"`) |
| `page_caption` | `str` | `""` | `{{ page.caption }}` |
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
    page_caption = "Last updated January 2026"
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

django-mvp ships four production-ready, consistently styled error pages (400, 403, 404,
500) in `mvp/templates/`. Register them by wiring the four Django error handlers in your
root URLconf module.

### Handler Registration

In your **root URLconf** (the module pointed to by `ROOT_URLCONF` in settings):

```python
# myproject/urls.py  — root URLconf only, not app urls.py
handler400 = "mvp.views.error.bad_request"
handler403 = "mvp.views.error.permission_denied"
handler404 = "mvp.views.error.not_found"
handler500 = "mvp.views.error.server_error"
```

These string paths must be in the root URLconf — Django only reads handler variables
from that module, not from `include()`d apps.

### Template Block API

All four error templates extend `mvp/error_base.html`, which provides a
full-viewport centered layout **with no sidebar and no DB queries**. The base
template automatically renders the application logo above the heading. Override
these four named blocks to customise each page:

| Block | Purpose | Default |
|-------|---------|---------|
| `title` | `<title>` text (`{% block title %}` wrapper) | `"Error"` |
| `heading` | User-facing heading line | *(empty)* |
| `description` | Supporting paragraph with context / next steps | *(empty)* |
| `actions` | CTA buttons (`<c-button>` components) | *(empty)* |

> **No error code numbers on page.** The numeric HTTP status code is communicated
> via response headers and the page `<title>` only — not as a visible on-page element.

Example custom error page:

```django
{% extends "mvp/error_base.html" %}
{% load i18n %}
{% block title %}{% trans "404 — Page Not Found" %}{% endblock %}
{% block heading %}{% trans "Oops! Page not found." %}{% endblock %}
{% block description %}
  {% trans "We could not find that page." %}
{% endblock %}
{% block actions %}
  <c-button variant="outline-secondary" icon="arrow-left" href="/" text="{% trans \"Back to home\" %}" />
{% endblock %}
```

### 500 Page — `support_email` Context Variable

The `server_error` handler passes `support_email` to the template context, sourced
from `settings.DEFAULT_FROM_EMAIL` (empty string → `None`). Use it to conditionally
render a support contact button:

```django
{% block actions %}
  <div class="d-flex gap-2 justify-content-center flex-wrap">
    <c-button variant="primary" icon="arrow-left" href="/" text="{% trans "Back to dashboard" %}" />
    {% if support_email %}
      <c-button variant="outline-secondary" icon="life-preserver"
                href="mailto:{{ support_email }}" text="{% trans "Contact support" %}" />
    {% endif %}
  </div>
{% endblock %}
```

Set `DEFAULT_FROM_EMAIL` in `settings.py` to enable the contact button:

```python
DEFAULT_FROM_EMAIL = "support@yourdomain.com"
```

### DB Safety Constraint

`server_error` **must never touch the database**. The built-in handler satisfies
this: it uses only `getattr(settings, ...)` and `render()`. If you override it,
verify with `django_assert_num_queries(0)` in your test.

### Developer Preview Routes

Add preview routes so developers can inspect each error page without triggering a
real error:

```python
# demo/urls.py (or any app urls.py)
from django.conf import settings
from django.urls import path
from mvp.views import ErrorPagePreviewView  # or your own TemplateView subclass

urlpatterns += [
    path("errors/400/", TemplateView.as_view(template_name="400.html"), name="error-preview-400"),
    path("errors/403/", TemplateView.as_view(template_name="403.html"), name="error-preview-403"),
    path("errors/404/", TemplateView.as_view(template_name="404.html"), name="error-preview-404"),
    path(
        "errors/500/",
        TemplateView.as_view(
            template_name="500.html",
            extra_context={"support_email": settings.DEFAULT_FROM_EMAIL or None},
        ),
        name="error-preview-500",
    ),
]
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
- [ ] `/errors/400/`, `/errors/403/`, `/errors/404/`, `/errors/500/` → each previews correctly
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

## Step 11 — Safe Post-Submit Redirect (`NextURLMixin`)

`NextURLMixin` provides safe handling of the `?next=` parameter for all form views.
It is automatically composed into `MVPFormBase`, so every `MVPCreateView`,
`MVPUpdateView`, `MVPFormView`, and `MVPDeleteView` benefits without any extra setup.

### URL destination

Embed a same-origin URL in the query string:

```python
# In a list view template:
<a href="{% url 'product-create' %}?next={{ request.path }}">Add product</a>
```

After a successful save the user lands back at `request.path` — no custom view code
needed.

### CRUD shorthand destination

Use a shorthand key from `crud_views` as the `next` value:

```python
# Via query string:
<a href="{% url 'product-create' %}?next=detail">Create & view</a>

# Or hard-code in a link column:
<a href="{% url 'product-update' pk=obj.pk %}?next=list">Edit</a>
```

Supported shorthands (from `MVP_DEFAULT_VIEW_NAMES`):
`"list"`, `"detail"`, `"create"`, `"update"`, `"delete"`

Shorthand resolution follows the same permission gating as `CRUDDirectoryMixin`.
If a shorthand cannot be resolved (permission denied, URL pattern missing), a
`logger.warning` is emitted when `settings.DEBUG = True` and the fallback chain
continues.

### Template: preserving `next` across failed POST re-renders

The `form_view.html` base template includes a hidden input after the submit buttons:

```html
{% if next_url %}<input type="hidden" name="next" value="{{ next_url }}">{% endif %}
```

This ensures the destination survives form validation failures. The hidden input is
placed **after** the submit buttons so that when a user clicks a button (e.g. "Save
entry" with `name="next" value="list"`), the hidden field's value wins in Django's
`QueryDict` (last value wins for duplicate keys).

### `get_success_url()` priority chain

| Step | Source | Condition |
|------|--------|-----------|
| 1 | Validated same-origin `next` URL | POST data contains a `next` starting with `/` or `://` |
| 2 | CRUD shorthand via `resolve_crud_url()` | POST data `next` is a key in `crud_views` and resolves |
| 3 | `success_url` class attribute | Set explicitly on the view class |

`MVPFormView` raises `ImproperlyConfigured` at step 3 when `success_url` is not set —
this is intentional, matching Django's own `FormMixin` contract.

### Security behaviour

- **Open-redirect protection** is enforced via `url_has_allowed_host_and_scheme`.
- **Bare words** (e.g. `next=foobar`) that aren't recognized CRUD shorthands are
  rejected, preventing browsers from treating them as relative paths.
- **Cross-origin URLs** (e.g. `next=https://evil.com/`) are rejected and logged
  in `DEBUG=True` mode.
- **Logging** is performed by `logging.getLogger("mvp.views.edit")`. To suppress
  warnings in tests: `@override_settings(DEBUG=False)`.

---

## Step 12 — Zero-Config Model Create View (`MVPCreateView`)

`MVPCreateView` is the package's concrete create view. Set `model` and `fields` — everything else is derived automatically.

### Minimal usage

```python
# views.py
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug", "category", "description", "price"]
    has_list_permission = True
    has_detail_permission = True
    has_update_permission = True
```

Defaults provided automatically (no overrides needed):

| Attribute / Method | Default value | Source |
|--------------------|---------------|--------|
| `page_icon` | `"add"` | class attribute |
| `page_class` | `"mvp-form-page mvp-create-page"` | class attribute |
| `get_page_title()` | `"Create {VerboseName}"` e.g. `"Create Product"` | derived from `model._meta.verbose_name` |
| `success_message` | `"%(verbose_name)s successfully created."` | class attribute |
| `get_success_message()` | `"Product successfully created."` | title-cased verbose_name injected |

### `get_page_title()` — auto-derived title

When `page_title` is not set (or is an empty string), the title is derived from the model's `verbose_name`:

```python
# Product._meta.verbose_name == "product" → "Create Product"
# OrderLine._meta.verbose_name == "order line" → "Create Order Line"
```

Override by setting `page_title` on the subclass or passing a lazy translation string:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = [...]
    page_title = "Add a new product"          # exact string
    # or:
    page_title = _("Add a new product")       # lazy translated string
```

### `get_success_message()` — title-cased flash

Unlike `MVPModelFormBase.get_success_message()` (which uses lowercase `verbose_name`),
`MVPCreateView` injects a title-cased `verbose_name` so the default flash reads
`"Product successfully created."` rather than `"product successfully created."`.

Custom messages with `%(key)s` interpolation work as normal:

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = [...]
    success_message = "%(name)s was added to the catalogue."
```

Missing keys silently substitute `""` — no `KeyError` is raised.

### Breadcrumbs

The breadcrumb is inherited from `PageObjectMixin.get_breadcrumbs()`:

- **First item**: model's `verbose_name_plural.title()` (e.g. `"Products"`) with a link to the list URL when `has_list_permission` is truthy; rendered as plain text when falsy.
- **Second item**: current page title (`"Create Product"`) with no href.

Override the full breadcrumb list by defining `get_breadcrumbs()` on the subclass.

---

## Step 13 — Zero-Config Model Update View (`MVPUpdateView`)

`MVPUpdateView` is the package's concrete model update view. Set `model` and `fields` — everything else is derived automatically.

### Minimal usage

```python
# views.py
class ProductUpdateView(MVPUpdateView):
    model = Product
    fields = ["name", "slug", "price"]
    has_list_permission = True
    has_detail_permission = True
    has_delete_permission = True
```

Defaults provided automatically (no overrides needed):

| Attribute / Method | Default value | Source |
|--------------------|---------------|--------|
| `page_icon` | `"edit"` | class attribute |
| `page_class` | `"mvp-form-page mvp-update-page"` | class attribute |
| `get_page_title()` | `"Update {VerboseName}"` e.g. `"Update Product"` | derived from `model._meta.verbose_name` |
| `success_message` | `"%(verbose_name)s successfully updated."` | class attribute |
| `get_success_message()` | `"Product successfully updated."` | `verbose_name` key in template data |

### `get_page_title()` — model-aware title

The default `page_title` interpolation template is `_("Update %(verbose_name)s")`.
At runtime the `%(verbose_name)s` placeholder is replaced with the title-cased model
verbose name:

```python
# Product._meta.verbose_name == "product" → "Update Product"
# OrderLine._meta.verbose_name == "order line" → "Update Order Line"
```

Override by setting `page_title` on the subclass:

```python
class ProductUpdateView(MVPUpdateView):
    page_title = "Edit product details"
```

### `get_breadcrumbs()` — three-level breadcrumb

The update view always produces a **three-level** breadcrumb:

1. **List link** — model verbose_name_plural (e.g. `"Products"`), linked to the list URL when `has_list_permission` is truthy.
2. **Detail link** — `str(object)` (the object's string representation), linked to the detail URL when `has_detail_permission` is truthy; uses `resolve_crud_url("detail")` so the permission flag controls the link. Renders as plain text when `has_detail_permission` is falsy.
3. **Current page** — `get_page_title()` with no href.

Override by defining `get_breadcrumbs()` on the subclass.

### `get_delete_url()` — delete button visibility

The delete button in the form footer is controlled by `context["delete_url"]` (gated by `{% if delete_url %}` in the template):

- When `has_delete_permission = True` (and the delete view is registered), `get_delete_url()` returns the delete URL with `?back=<update_url>&next=<list_url>` params.
- When `has_delete_permission = False` (default), `get_delete_url()` returns `""` → the delete button is hidden.
- If the `back_url` reverse fails (`NoReverseMatch`), the method returns the delete URL with an empty `back` param rather than raising.

```python
class ProductUpdateView(MVPUpdateView):
    has_delete_permission = True   # shows Delete button
    # has_delete_permission = False  # hides Delete button (default)
```

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

---

## Step 14 — Zero-Config Model Delete View (`MVPDeleteView`)

`MVPDeleteView` handles four deletion scenarios through class attributes — no custom
template or view logic needed for common cases.

### Minimal usage

```python
# views.py
class ProductDeleteView(MVPDeleteView):
    model = Product
    has_list_permission = True
    has_detail_permission = True   # enables detail link in breadcrumb
```

Wire to a URL:

```python
urlpatterns = [
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
]
```

### Four deletion scenarios

| # | Scenario | Trigger |
|---|----------|---------|
| 1 | **Basic** — warning + Delete button | default |
| 2 | **Related objects summary** — preview cascade deletes | `show_related_objects = True` |
| 3 | **Protected** — hides Delete button, shows blocking records | auto-detected (PROTECT FK) |
| 4 | **Type-to-confirm** — user must type the object name | `require_confirmation = True` |

### Config attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_related_objects` | `bool` | `False` | Show cascade-deleted related records in a preview list. |
| `require_confirmation` | `bool` | `False` | Require user to type the object name before Delete is enabled. |
| `confirmation_label` | `str` | `"Type the name to confirm"` | Label for the confirmation input. |
| `related_objects_max_per_group` | `int` | `25` | Max items shown per related-object group; excess shown as "… and N more". |

### Override hooks

| Method | Default | Description |
|--------|---------|-------------|
| `get_confirmation_value()` | `str(self.object)` | String the user must type. Override to use e.g. `self.object.slug`. |
| `get_back_url()` | `?back` param or list URL | URL for the Go Back button. |
| `get_breadcrumbs()` | List → Detail → Delete | Three-item trail; detail link requires `has_detail_permission = True`. |
| `get_success_url()` | `?next=` → `success_url` → list URL | Does **not** fall back to `object.get_absolute_url()` (object no longer exists). |

### Defaults provided automatically

| Attribute / Method | Default value |
|--------------------|---------------|
| `page_icon` | `"delete"` |
| `page_class` | `"mvp-delete-page"` |
| `get_page_title()` | `"Delete {VerboseName}"` — e.g. `"Delete Product"` |
| `success_message` | `"%(verbose_name)s successfully deleted."` |

### Scenario 2: related objects preview

```python
class ArticleDeleteView(MVPDeleteView):
    model = Article
    show_related_objects = True
    related_objects_max_per_group = 10   # default 25
```

When `show_related_objects = True`, `context["related_objects"]` is a list of
`(label, objects, overflow)` tuples — one per related model group. The template
renders each group with an overflow note when `overflow > 0`.

### Scenario 4: type-to-confirm

```python
class ArticleDeleteView(MVPDeleteView):
    model = Article
    require_confirmation = True   # user must type str(article)

    def get_confirmation_value(self):
        return self.object.slug   # override: type slug instead of __str__
```

The Delete button is disabled via JavaScript until the input matches
`confirmation_value`. The form is validated server-side via `DeleteConfirmForm`
(from `mvp.forms`) which uses `clean_confirmation()` to compare against the expected
value — protection against JavaScript bypass.

### Redirect priority chain (`get_success_url()`)

1. Validated same-origin `?next=` URL (or CRUD shorthand such as `"list"`)
2. `success_url` class attribute (tried as CRUD shorthand first, then literal path)
3. List URL from `resolve_crud_url("list")`
4. Raises `ImproperlyConfigured`

`get_absolute_url()` is intentionally skipped — the object does not exist after deletion.

### Example — all options combined

```python
class OrderDeleteView(MVPDeleteView):
    model = Order
    show_related_objects = True
    require_confirmation = True
    related_objects_max_per_group = 5
    has_list_permission = True
    has_detail_permission = True

    def get_confirmation_value(self):
        return self.object.reference_number
```

---

## Step 15 — List Search and Ordering (`SearchMixin`, `OrderMixin`, `SearchOrderMixin`)

### SearchMixin — text search via `?q=`

`SearchMixin` adds Django admin-style multi-word OR search across declared model fields.

```python
class ProductListView(SearchMixin, ListView):
    model = Product
    search_fields = ["name", "description", "category__name"]
```

**Behaviour**:
- `?q=foo bar` returns records where any field contains `"foo"` OR `"bar"` (case-insensitive).
- Whitespace-only `?q=` is treated as empty — no filtering applied.
- When `search_fields` is `None` or not set, the mixin is a **complete no-op**.

**Context sentinels** (always injected, even when unconfigured):

| Variable | Type | Value when unconfigured | Value when configured |
|---|---|---|---|
| `is_searchable` | `bool` | `False` | `True` |
| `search_query` | `str` | `""` | Raw `?q=` value, or `""` |

Override `get_search_fields()` to compute the field list dynamically.

---

### OrderMixin — whitelist-only column ordering via `?o=`

**Breaking change (014)**: `order_by` entries changed from two-tuple
`(orm_expression, label)` to three-tuple `(public_key, label, orm_expression)`.

```python
class ProductListView(OrderMixin, ListView):
    model = Product
    order_by = [
        ("name_asc",   "Name (A–Z)",          "name"),
        ("name_desc",  "Name (Z–A)",          "-name"),
        ("newest",     "Newest First",         "-created_at"),
        ("price_asc",  "Price (Low to High)", "price"),
    ]
```

**Three-tuple format**: `(public_key, label, orm_expression)`

| Field | Description |
|---|---|
| `public_key` | Matched against `?o=`. Any URL-safe string. **Need not match a DB column name.** |
| `label` | Display text for the ordering UI dropdown. |
| `orm_expression` | Passed to `queryset.order_by()`. May be prefixed with `-` for descending. **Never URL-exposed.** |

**Security guarantee**: the raw `?o=` value is **never** passed to the ORM.
Only the `orm_expression` of the matching whitelist entry is used.
Unrecognised `?o=` values are silently ignored.

**Upgrade from two-tuple format**:

```python
# Before (two-tuple — broken):
order_by = [("name", "Name A-Z"), ("-name", "Name Z-A")]

# After (three-tuple — correct):
order_by = [
    ("name_asc",  "Name A-Z", "name"),
    ("name_desc", "Name Z-A", "-name"),
]
```

**Context variables** (only injected when `order_by` is configured):

| Variable | Type | Description |
|---|---|---|
| `order_by_choices` | `list[tuple[str, str, str]]` | Full three-tuple whitelist. Iterate with `{% for key, label, _ in order_by_choices %}`. |
| `current_ordering` | `str` | Matched `public_key` for the active `?o=`, or `""` if absent/unrecognised. |

Override `get_order_by_choices()` to compute the whitelist dynamically.

---

### SearchOrderMixin — combined search and ordering

Use `SearchOrderMixin` when you need both `?q=` search and `?o=` ordering:

```python
class ProductListView(SearchOrderMixin, ListView):
    model = Product
    search_fields = ["name", "description"]
    order_by = [
        ("name_asc",  "Name (A–Z)",  "name"),
        ("name_desc", "Name (Z–A)", "-name"),
    ]
```

`SearchOrderMixin(SearchMixin, OrderMixin)` — MRO is fixed. This guarantees:

1. `OrderMixin.get_queryset()` runs first (ordering applied to the base queryset).
2. `SearchMixin.get_queryset()` runs second (search + `distinct()` applied last).

This avoids the PostgreSQL `SELECT DISTINCT + ORDER BY on JOIN columns` error.

**`MVPListViewMixin` and `MVPListView`** already inherit `SearchOrderMixin` — add
`search_fields` and `order_by` attributes directly without mixing in anything extra.

---

### django_filters composition

Place `SearchOrderMixin` **left** of `FilterView` in the MRO:

```python
from django_filters.views import FilterView
from mvp.views.list import SearchOrderMixin

class ProductListView(SearchOrderMixin, FilterView):
    model = Product
    filterset_fields = ["category"]
    search_fields = ["name"]
    order_by = [("name_asc", "Name (A–Z)", "name")]
```

Or with `MVPListViewMixin`:

```python
class ProductListView(MVPListViewMixin, FilterView):
    model = Product
    filterset_fields = ["category"]
    search_fields = ["name"]
    order_by = [("name_asc", "Name (A–Z)", "name")]
```

Both `search_fields` and `order_by` are individually optional — omit either to leave that
dimension unconfigured (no-op).

---

## MVPListView — Concrete list view

`MVPListView` is the ready-to-use concrete class. Subclass it with only `model` to get a
fully functional, paginated, searchable, orderable list page.

```python
from mvp.views.list import MVPListView

class ProductListView(MVPListView):
    model = Product
    # That's it — paginated (24/page), searchable, orderable.
```

### Class attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `paginate_by` | `24` | Page size. 24 is divisible by 1, 2, 3, and 4 — safe for any grid column count. |
| `list_item_template` | `None` | Explicit path to the partial template for each item. When `None`, the path is derived from the model: `<app_label>/<model_name>_list_item.html`. |
| `grid` | `{}` | Responsive grid breakpoint dict, passed through to context as `grid_config` unchanged. |
| `empty_state_heading` | `_("There's nothing here yet")` | Heading shown when the queryset is empty. Set to `None` to suppress. |
| `empty_state_message` | `_("You haven't added any records yet…")` | Body text shown when empty. Set to `None` to suppress the paragraph. |
| `page_title` | `""` | Overrides the model-derived title. Falsy value falls back to `model._meta.verbose_name_plural.title()`. |
| `search_fields` | `None` | ORM field paths for `?q=` search (inherited from `SearchMixin`). |
| `order_by` | `None` | Three-tuple whitelist for `?o=` ordering (inherited from `OrderMixin`). |
| `directory` | `["create"]` | CRUD actions exposed from the list page. Only `"create"` is included by default. |

### Override hooks

| Method | Purpose |
|--------|---------|
| `get_list_item_template()` | Return the item partial path. Override for full control. |
| `get_empty_state_heading()` | Return the empty-state heading string (or `None`). |
| `get_empty_state_message()` | Return the empty-state message string (or `None`). |
| `get_grid_config()` | Return the grid breakpoint dict passed to context. |
| `get_page_title()` | Return the page title; falls back to `verbose_name_plural.title()`. |
| `get_breadcrumbs()` | Return the breadcrumb list. Default: Home + page title. |
| `get_search_fields()` | Inherited from `SearchMixin`. |
| `get_order_by_choices()` | Inherited from `OrderMixin`. |

### Context variables

| Key | Type | Description |
|-----|------|-------------|
| `list_item_template` | `str` | Resolved partial template path. |
| `empty_state` | `dict` | `{"heading": str\|None, "message": str\|None}`. |
| `grid_config` | `dict` | Grid breakpoint configuration (may be `{}`). |
| `directory` | `dict` | CRUD URLs. Only `create_url` is injected (when `has_create_permission=True`). |
| `search_query` | `str` | Active `?q=` value, or `""`. Always injected. |
| `is_searchable` | `bool` | Whether `search_fields` is configured. |
| `page` | `dict` | PageMixin metadata — `title`, `subtitle`, `icon`, `class`, `breadcrumbs`. |

### Item template naming convention

When `list_item_template` is not set, the path is derived automatically:

```
<app_label>/<model_name>_list_item.html
```

Examples:
- `Product` in app `shop` → `shop/product_list_item.html`
- `Category` in app `demo` → `demo/category_list_item.html`
- `Order` in app `sales` → `sales/order_list_item.html`

Override `list_item_template` for shared partials, or override `get_list_item_template()`
for full programmatic control.

### Using MVPListViewMixin for custom base class compositions

Subclass `MVPListViewMixin` (not `MVPListView`) when you need to compose with another
base class, such as `FilterView`:

```python
from mvp.views.list import MVPListViewMixin
from django_filters.views import FilterView

class ProductFilteredListView(MVPListViewMixin, FilterView):
    model = Product
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    list_item_template = "shop/product_card.html"
```

`MVPListViewMixin` does not declare `paginate_by` — set it on your subclass if needed.
`MVPListView` adds `paginate_by = 24` on top of the mixin.

---

## Brand Templatetags — `logo_url` and `icon_url`

Two template tags resolve brand assets (logo and icon SVGs) for a given theme. Both call
a configurable resolver function, making it easy to swap in per-tenant, thumbnail-aware,
or CDN-backed URLs without changing templates.

### Template usage

```django
{% load mvp %}

{# Logo — height is required #}
<img src="{% logo_url height=40 %}" alt="Logo" style="max-height: 40px; width: auto;">

{# Logo with explicit dark theme #}
<img src="{% logo_url height=40 theme="dark" %}" alt="Dark Logo">

{# Icon — height is required #}
<img src="{% icon_url height=32 %}" alt="Icon" style="max-height: 32px; width: auto;">

{# Icon with dark theme #}
<img src="{% icon_url height=32 theme="dark" %}" alt="Dark Icon">
```

The `request` object is extracted automatically from the Django template context
(`takes_context=True`). Template authors do not pass it explicitly.

### Tag argument contract

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `height` | `int` | **required** | Advisory max image height in pixels. Passed to resolver. |
| `theme` | `str` | `"light"` | Theme identifier. Passed to resolver. |

### Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `MVP_LOGO_RESOLVER` | `str` | `"mvp.utils.logo_url"` | Dotted import path to logo resolver callable |
| `MVP_ICON_RESOLVER` | `str` | `"mvp.utils.icon_url"` | Dotted import path to icon resolver callable |

Zero-config: both settings are optional. The bundled defaults return the SVG files from
`mvp/static/brand/` (`logo.svg`, `icon_light.svg`, `icon_dark.svg`).

### Default resolver behaviour

| Tag | `theme="light"` | `theme="dark"` | unknown theme |
|-----|----------------|---------------|---------------|
| `logo_url` | `brand/logo.svg` | `brand/logo.svg` (fallback) | `brand/logo.svg` |
| `icon_url` | `brand/icon_light.svg` | `brand/icon_dark.svg` | `brand/icon.svg` |

No dark logo asset is bundled — `logo_url` always falls back to the single `logo.svg`.

### Custom resolver

Point the setting to any callable with this signature:

```python
# myapp/branding.py
def get_logo_url(request, height, theme):
    """
    Args:
        request (HttpRequest | None): Current request, or None.
        height (int | None): Advisory max height in pixels.
        theme (str): Theme identifier, e.g. 'light' or 'dark'.

    Returns:
        str | None: URL string, or None/"" for no asset.
    """
    if hasattr(request, "user") and request.user.is_authenticated:
        return request.user.organisation.logo_url
    return static("brand/logo.svg")
```

```python
# settings.py
MVP_LOGO_RESOLVER = "myapp.branding.get_logo_url"
```

### Error behaviour

| Scenario | Behaviour |
|----------|-----------|
| Setting absent | Default resolver used silently |
| Setting present, import fails | `ImproperlyConfigured` raised on first tag call |
| Resolver returns `None` | Tag outputs empty string `""` |
| Resolver raises exception | Tag outputs `""` silently (no re-raise) |

### Output safety

Both tags return a **plain `str`** — not `SafeData`. Django auto-escaping applies
normally. Do not call `mark_safe()` in a custom resolver.
