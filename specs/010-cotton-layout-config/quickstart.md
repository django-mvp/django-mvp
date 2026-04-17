# Quickstart: Cotton App Layout Configuration

**Branch**: `010-cotton-layout-config` | **Feature**: 010

> Get a fully configured AdminLTE 4 application shell using Cotton component
> attributes — no Python settings, no view context, just HTML template declarations.

---

## 1. Install django-mvp

```bash
pip install django-mvp
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_cotton",
    "mvp",
    # ...
]
```

## 2. Extend the Base Template

Create your project's `base.html`:

```html
{% extends "mvp/base.html" %}
```

This gives you the default AdminLTE 4 layout with no customisations — fluid header, non-fixed sidebar, no footer content.

## 3. Customise the Layout Shell

Override `{% block app %}` and declare your `<c-app>` with the desired attributes:
use kebab-case in template declarations. django-cotton will normalize these names
to snake_case inside component templates.

```html
{% extends "mvp/base.html" %}

{% block app %}
<c-app fixed-sidebar fixed-header sidebar-collapsible sidebar-expand="lg">
    <c-app.header>
        <c-slot name="right">
            {# Navbar widgets go here #}
        </c-slot>
    </c-app.header>

    <c-app.sidebar brand-text="My App" brand-url="/">
        {# Uses AppMenu by default — no slot override needed #}
    </c-app.sidebar>

    <c-app.main>
        {% block content %}{% endblock %}
    </c-app.main>

    <c-app.footer text="Copyright © 2026 My Company">
        <c-slot name="right">
            <span>v1.0.0</span>
        </c-slot>
    </c-app.footer>
</c-app>
{% endblock %}
```

## 4. Configure Sidebar Navigation

Register menu items in your app's `menus.py`:

```python
from mvp.menus import AppMenu, MenuGroup, MenuCollapse
from flex_menu import MenuItem

AppMenu.extend([
    MenuItem("Dashboard", url="/", icon="speedometer2"),
    MenuGroup("Content"),
    MenuItem("Articles", url="/articles/", icon="journal-text"),
    MenuCollapse("Users", icon="people", children=[
        MenuItem("All Users", url="/users/"),
        MenuItem("Add User", url="/users/add/"),
    ]),
])
```

The sidebar will render `AppMenu` automatically using the AdminLTE renderer.

## 5. Common Layout Recipes

### Fixed sidebar with collapsed initial state

```html
<c-app fixed-sidebar sidebar-collapsible collapsed sidebar-expand="lg">
```

### Fixed header and footer with fill mode

```html
<c-app fixed-header fixed-footer fill>
```

### Minimal — no fixed elements, no collapsible sidebar

```html
<c-app>
```

## 6. Attribute Quick Reference

| Attribute | Type | Default | What it does |
|-----------|------|---------|--------------|
| `fixed-sidebar` | bool | off | Pins sidebar on scroll |
| `fixed-header` | bool | off | Pins header on scroll |
| `fixed-footer` | bool | off | Pins footer on scroll |
| `sidebar-collapsible` | bool | off | Enables sidebar mini mode |
| `collapsed` | bool | off | Starts sidebar collapsed (needs `sidebar-collapsible`) |
| `sidebar-expand` | string | `"lg"` | Breakpoint for sidebar overlay |
| `fill` | bool | off | Constrains layout to viewport height |

## 7. Verify

Run the development server and navigate to your base page:

```bash
python manage.py runserver
```

Open browser DevTools → inspect `<body>`:
- With `fixed-sidebar`: body has class `layout-fixed`
- With `fixed-header`: body has class `fixed-header`
- With `sidebar-collapsible`: body has class `sidebar-mini`
