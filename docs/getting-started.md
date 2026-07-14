# Getting Started

## Installation

```bash
pip install django-mvp
```

Add the required apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.sites",
    "django_cotton",   # Cotton template components
    "easy_icons",      # Icon system
    "flex_menu",       # Menu system
    "mvp",             # django-mvp
    ...
]
```

Add the context processor so layout configuration reaches every template:

```python
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "mvp.context_processors.mvp_config",
            ],
        },
    },
]
```

## Configure icons

django-mvp resolves icon names through
[django-easy-icons](https://github.com/SamuelJennings/django-easy-icons). The package
ships a Bootstrap Icons pack (`mvp.utils.BS5_ICONS`) covering every icon its own
components use — include it and add your own names on top:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],
        "icons": {
            # your app's icons
            "dashboard": "bi bi-speedometer2",
            "invoices": "bi bi-receipt",
        },
    },
}
```

The bundled pack registers common icons under several synonyms — `add`, `plus` and
`create` all resolve to the same glyph, as do `delete`/`remove`/`trash`,
`person`/`user`/`account`, `settings`/`gear`/`cog`, and more — so callers can reach for
whichever name reads best. You can do the same in your own `"icons"` block by declaring
comma-separated keys (whitespace is ignored):

```python
"icons": {
    "dashboard, home, overview": "bi bi-speedometer2",
}
```

`mvp/base.html` loads the Bootstrap Icons webfont from a CDN by default; override the
`head` block to self-host it.

## Configure menu renderers

The sidebar and mobile dock render menus through
[django-flex-menus](https://github.com/SamuelJennings/django-flex-menus) — register
django-mvp's renderers in settings:

```python
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
}
```

## Your first page

Templates extend `mvp/base.html`, which renders the full app shell (sidebar, navbar,
content area, footer, mobile dock):

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-container>
    <h1>Hello!</h1>
  </c-container>
{% endblock %}
```

For a complete page with title, breadcrumbs and consistent structure, use an MVP view
instead of a bare `TemplateView` — see [Views](views.md):

```python
from mvp.views import MVPTemplateView


class DashboardView(MVPTemplateView):
    template_name = "dashboard.html"
    page_title = "Dashboard"
```

## Add menu items

Create `menus.py` in your app and register it in `AppConfig.ready()` — the sidebar
renders the `AppMenu` automatically. See [Navigation](navigation.md).

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard",
             extra_context={"label": "Dashboard", "icon": "dashboard"}),
])
```

## Configure the layout

Layout behavior is controlled from settings — no template edits required:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {"breakpoint": "lg", "collapse": "offcanvas"},
        "navbar": {"end": ["actions.theme-controller"]},
    },
}
```

See [Layout](layout.md) for every option.

## Error pages

Wire django-mvp's styled error handlers in your root `urls.py`:

```python
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```
