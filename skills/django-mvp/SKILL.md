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

## Step 6 — Dual-Mode Home View

When the root URL must serve different content for authenticated vs. unauthenticated
users **at the same URL** (no redirect), override `get_template_names()`:

```python
class HomeView(View):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["home/authenticated.html"]
        return ["home/unauthenticated.html"]
```

- `home/authenticated.html` — extends `base.html` (gets full AdminLTE layout)
- `home/unauthenticated.html` — extends `mvp/base.html` directly, override `{% block app %}` to
  provide a public layout (no sidebar), with Sign In / Sign Up links only

If `login_required` middleware is active project-wide, exempt the home view:
```python
LOGIN_REQUIRED_IGNORE_VIEW_NAMES = ["home"]
```

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
