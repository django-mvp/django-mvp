# Django MVP

[![Tests](https://github.com/SamuelJennings/django-mvp/actions/workflows/tests.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/tests.yml)
[![Build](https://github.com/SamuelJennings/django-mvp/actions/workflows/build.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/build.yml)
[![Release](https://github.com/SamuelJennings/django-mvp/actions/workflows/on-release-main.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/on-release-main.yml)
[![PyPI](https://img.shields.io/pypi/v/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![codecov](https://codecov.io/gh/SamuelJennings/django-mvp/branch/main/graph/badge.svg)](https://codecov.io/gh/SamuelJennings/django-mvp)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Get your Django project to a minimum viable product — fast.** django-mvp gives you a
polished, settings-configurable application layout (DaisyUI 5 + Tailwind CSS v4), a
library of reusable [django-cotton](https://github.com/wrabit/django-cotton) UI
components, and enhanced class-based views with search, ordering and pagination out of
the box. **Things should just work.**

> **Note:** django-mvp is in active development (0.x). Import paths and component APIs
> may change between minor versions — see the [CHANGELOG](CHANGELOG.md).

## What you get

- **A complete app shell** — sidebar, navbar, content area, footer, and mobile dock
  navigation, rendered around every page and configured from Django settings
  (pydata-sphinx-theme style): sidebar collapse breakpoint, offcanvas vs. icon-rail
  collapse, and navbar widgets are all `MVP_CONFIG` keys.
- **A Cotton component library** — cards, buttons, grids, menus, dropdowns, pagination,
  hero sections and more, with small consistent attribute APIs. Need more control?
  Override the component's template in your project — that's the intended extension
  path, not a bigger API.
- **Views that do the boring parts** — list pages with admin-style search, whitelisted
  ordering and pagination; form pages with automatic crispy-forms detection; delete
  flows with related-object summaries and type-to-confirm; styled error pages.
- **Menus in Python** — sidebar and mobile-dock navigation via
  [django-flex-menus](https://github.com/SamuelJennings/django-flex-menus), with active
  states, icons and badges handled for you.
- **Icons by name** — every icon resolves through
  [django-easy-icons](https://github.com/SamuelJennings/django-easy-icons); swap the
  icon set from settings without touching templates.
- **No build tooling required** — a prebuilt stylesheet ships with the package. When
  your own templates need their own Tailwind classes, one management command generates
  the build config.

## Quick start

```bash
pip install django-mvp
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django.contrib.sites",
    "django_cotton",
    "easy_icons",
    "flex_menu",
    "mvp",
]

TEMPLATES = [{
    ...
    "OPTIONS": {"context_processors": [
        ...
        "mvp.context_processors.mvp_config",
    ]},
}]

EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],   # icons used by mvp's own components
    },
}

FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
}
```

```html
{# templates/dashboard.html #}
{% extends "mvp/base.html" %}

{% block content %}
  <c-container>
    <c-section title="Dashboard" icon="home">
      <c-grid md="2" xl="4">
        <c-card title="Orders">150 new</c-card>
        <c-card title="Revenue">$12,400</c-card>
      </c-grid>
    </c-section>
  </c-container>
{% endblock %}
```

Full walkthrough: [Getting Started](docs/getting-started.md).

## Configure the layout from settings

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm|md|lg|xl|2xl — when the sidebar is persistent
            "collapse": "offcanvas",  # "offcanvas" (slide away) or "icons" (icon rail)
        },
        "navbar": {
            # Cotton component names, rendered at the right end of the navbar
            "end": ["actions.theme-controller", "actions.language-switcher"],
        },
    },
}
```

Per-page overrides use component attributes (`<c-app breakpoint="xl">`,
`<c-app.sidebar collapse="icons">`). Details: [Layout](docs/layout.md).

## Views in one line each

```python
from mvp.views import MVPListView, MVPCreateView, MVPUpdateView, MVPDeleteView


class ProductListView(MVPListView):
    model = Product
    search_fields = ["name", "description"]              # ?q= multi-word search
    order_by = [("name_asc", "Name (A-Z)", "name")]      # ?o= whitelisted ordering


class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "category", "price"]               # crispy-detected rendering
```

Details: [Views](docs/views.md).

## Menus in Python

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard",
             extra_context={"label": "Dashboard", "icon": "home"}),
])
```

Details: [Navigation](docs/navigation.md).

## Optional integrations

Views that build on third-party packages live in guarded modules — no extras, and the
dependency is only required when you import the integration:

```python
from mvp.integrations.django_tables.views import MVPTableView      # django-tables2
from mvp.integrations.django_filters.views import MVPFilteredListView  # django-filter
```

Details: [Integrations](docs/integrations.md).

## Styling & Theming

Django MVP is styled with **Tailwind CSS v4 + DaisyUI 5** and ships a prebuilt
stylesheet — most projects need **no build tooling**. Use the packaged
components (and DaisyUI themes for colors) and you're done.

Need a DaisyUI component the packaged CSS doesn't include (e.g. `progress`,
`skeleton`)? Every DaisyUI component is also published as a standalone CSS file
— add a `<link>` for it in a `styles` block override (CDN or self-hosted) and
it picks up your theme automatically. Still no build tooling. See
[docs/styling.md](docs/styling.md#adding-individual-daisyui-components--still-no-build).

If your own templates use their own Tailwind utility classes, rebuild the CSS
with the generated entry file, which scans your templates *and* Django MVP's:

```bash
npm install -D tailwindcss @tailwindcss/cli daisyui
python manage.py mvp_tailwind > assets/tailwind.css
npx @tailwindcss/cli -i assets/tailwind.css -o static/css/app.css --minify
```

See [docs/styling.md](docs/styling.md) for the full guide (two-tier model,
theming, and the packaged Tailwind preset).

## Documentation

Start at [docs/index.md](docs/index.md): Getting Started · Layout · Components ·
Navigation · Views · Styling · Integrations.

## Requirements

- Python 3.12+
- Django 5.2+ (currently supported Django releases)
- django-cotton, django-flex-menus, django-easy-icons (installed automatically)

## Design philosophy

1. **Things should just work** — sensible defaults, minimum ceremony, MVP first.
2. **Configuration-driven** — layout and behavior controlled via `settings.MVP_CONFIG`.
3. **Basic components, not a component framework** — small attribute APIs; extensive
   customization happens by overriding templates.
4. **Focused integrations** — only for packages the author reuses across projects;
   the guarded-module pattern makes rolling your own trivial.

## Use cases

Admin dashboards, data-management tools, research portals, internal apps, SaaS
back-offices — anywhere you want a production-looking, data-centric Django app without
building the UI layer first.

## Contributing

Contributions welcome! When adding components: use `<c-vars />` for defaults, no ghost
attributes, include ARIA attributes, and add tests (`tests/test_components/` renders
every packaged component). Rebuild the stylesheet with `invoke build-stylesheet` when
templates change classes — CI fails on drift.

## License

MIT License — see [LICENSE](LICENSE).

## Acknowledgments

Built with [django-cotton](https://github.com/wrabit/django-cotton) by @wrabit,
[DaisyUI](https://daisyui.com/), [Tailwind CSS](https://tailwindcss.com/),
[Alpine.js](https://alpinejs.dev/) and
[Bootstrap Icons](https://icons.getbootstrap.com/).
