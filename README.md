# Django MVP

[![Tests](https://github.com/django-mvp/django-mvp/actions/workflows/tests.yml/badge.svg)](https://github.com/django-mvp/django-mvp/actions/workflows/tests.yml)
[![Build](https://github.com/django-mvp/django-mvp/actions/workflows/build.yml/badge.svg)](https://github.com/django-mvp/django-mvp/actions/workflows/build.yml)
[![Publish](https://github.com/django-mvp/django-mvp/actions/workflows/publish.yml/badge.svg)](https://github.com/django-mvp/django-mvp/actions/workflows/publish.yml)
[![PyPI](https://img.shields.io/pypi/v/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![codecov](https://codecov.io/gh/django-mvp/django-mvp/branch/main/graph/badge.svg)](https://codecov.io/gh/django-mvp/django-mvp)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Get your Django project to a minimum viable product — fast.** django-mvp gives you a
polished, settings-configurable application layout (DaisyUI 5 + Tailwind CSS v4), a
library of reusable [django-cotton](https://github.com/wrabit/django-cotton) UI
components, and enhanced class-based views with search, ordering and pagination out of
the box. **Things should just work.**

> **Note:** django-mvp is in active development (0.x). Import paths and component APIs
> may change between minor versions — see the [CHANGELOG](https://github.com/django-mvp/django-mvp/blob/main/CHANGELOG.md).

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
  ordering and pagination; form pages rendered with crispy-forms; delete
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

## Scope & philosophy

django-mvp is an application UI framework for the Django apps you write yourself. It gives you
the application chrome, a library of components, and views that carry a model through to a
working set of pages, so that reaching a minimum viable product doesn't start with building a
UI layer.

It also fills in where Django stops. Django ships the backend machinery for formsets and leaves
you with nothing to render or drive them with, so this package renders them for you, with the
same look, validation and error placement every other page gets. Closing that kind of gap is
squarely the point of it.

Use it for admin dashboards, data-management tools, research portals, internal apps and SaaS
back-offices: anywhere you want a production-looking, data-centric Django application without
writing the front end first.

**What it deliberately is not:**

- **An admin theme.** It doesn't touch `django.contrib.admin`. django-unfold and django-daisy
  serve that audience well.
- **A component engine.** [django-cotton](https://github.com/wrabit/django-cotton) provides the
  syntax; this package provides components built with it.
- **A project scaffold.** You install it as a dependency and upgrade it, rather than generating
  a starter project you then own outright.
- **An authentication system.** Account management lives in
  [django-accounts-center](https://github.com/django-mvp/django-accounts-center), which builds
  on these components.
- **A JavaScript application.** Pages are server-rendered, with Alpine and htmx where
  interaction calls for it. No build step, no single-page frontend.
- **An API layer.** Django REST Framework and django-ninja already cover that ground.
- **Real-time infrastructure.** Websockets and Channels are out of scope.

**Principles, in the order they settle a close call:**

1. **Things should just work.** Sensible defaults, minimum ceremony, MVP first.
2. **Configuration before customization.** Views are configured declaratively, much as Django's
   admin classes are. When the packaged look isn't right, override the Cotton component and
   honour its attributes. Past that, bring your own CSS.
3. **Basic components, not a component framework.** Small attribute APIs and limited variation.
   A component earns its place here by being useful more than once, and a specialized one
   belongs in a package of its own. Cotton finds components in any installed app, so a
   component pack needs no registration.
4. **Integrate, don't reimplement.** Django's third-party ecosystem already covers a great deal
   of this ground, but most of those packages still leave you to adapt their output into your
   own templates before it looks like part of your application. Rather than rewriting
   well-established packages, django-mvp puts a consistent UI around them wherever it can.

Where the package is headed is a separate question, answered in [GOALS.md](https://github.com/django-mvp/django-mvp/blob/main/GOALS.md).

## Quick start

```bash
pip install django-mvp
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    "your_app",         # your apps above "mvp" — see below
    "django.contrib.sites",
    "django_cotton",
    "easy_icons",
    "flex_menu",
    "mvp",
    "crispy_forms",
    "crispy_tailwind",  # must come after "mvp" — see Getting Started
]
```

Order matters here. Django's template loader walks `INSTALLED_APPS` top to bottom and
takes the first copy of a name it finds, so **list your own apps above `mvp`** to
override any template django-mvp ships. This is the same rule projects already use to
override the Django admin's templates.

Note that it does not follow that `mvp` belongs at the bottom of the list. `mvp` has to
stay above `crispy_tailwind`, whose help-text template it overrides by the same
mechanism. Raise your own apps rather than lowering `mvp`. See
[Getting Started](docs/getting-started.md) for both halves of the rule.

```python
# settings.py, continued

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

CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"
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

Full walkthrough: [Getting Started](https://github.com/django-mvp/django-mvp/blob/main/docs/getting-started.md).

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
`<c-app.sidebar collapse="icons">`). Details: [Layout](https://github.com/django-mvp/django-mvp/blob/main/docs/layout.md).

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

Details: [Views](https://github.com/django-mvp/django-mvp/blob/main/docs/views.md).

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

Details: [Navigation](https://github.com/django-mvp/django-mvp/blob/main/docs/navigation.md).

## Optional integrations

Views that build on third-party packages live in guarded modules — no extras, and the
dependency is only required when you import the integration:

```python
from mvp.integrations.django_tables.views import MVPTableView      # django-tables2
from mvp.integrations.django_filters.views import MVPFilteredListView  # django-filter
```

Details: [Integrations](https://github.com/django-mvp/django-mvp/blob/main/docs/integrations.md).

## Styling & Theming

Django MVP is styled with **Tailwind CSS v4 + DaisyUI 5** and ships a prebuilt
stylesheet with the **complete DaisyUI component set** and every DaisyUI theme.
Most projects need **no build tooling** at all.

Set `MVP_CONFIG["theme"]["default"]` to any DaisyUI theme name (`dracula`,
`synthwave`, ...) and it applies with no build step and nothing fetched from
outside your project. Offer a choice of themes to visitors through
`MVP_CONFIG["theme"]["choices"]`, or write your own theme as a plain CSS file.
See [docs/theming.md](https://github.com/django-mvp/django-mvp/blob/main/docs/theming.md)
for the full variable reference and a worked example.

If your own templates use their own Tailwind utility classes, rebuild the CSS
with the generated entry file, which scans your templates *and* Django MVP's:

```bash
npm install -D tailwindcss @tailwindcss/cli daisyui
python manage.py mvp_tailwind > assets/tailwind.css
npx @tailwindcss/cli -i assets/tailwind.css -o static/css/app.css --minify
```

See [docs/styling.md](https://github.com/django-mvp/django-mvp/blob/main/docs/styling.md) for the full guide (two-tier model,
theming, and the packaged Tailwind preset).

## Documentation

Start at [docs/index.md](https://github.com/django-mvp/django-mvp/blob/main/docs/index.md): Getting Started · Layout · Components ·
Navigation · Views · Styling · Integrations.

## Requirements

- Python 3.12+
- Django 5.2+ (currently supported Django releases)
- django-cotton, django-flex-menus, django-easy-icons (installed automatically)

## Contributing

Contributions welcome! When adding components: use `<c-vars />` for defaults, no ghost
attributes, include ARIA attributes, and add tests (`tests/test_components/` renders
every packaged component). Rebuild the stylesheet with `invoke build-stylesheet` when
templates change classes, and commit the result — the built CSS ships in the wheel, and
CI only checks that it still compiles, so keeping it current is up to the author.

## License

MIT License — see [LICENSE](https://github.com/django-mvp/django-mvp/blob/main/LICENSE).

## Acknowledgments

Built with [django-cotton](https://github.com/wrabit/django-cotton) by @wrabit,
[DaisyUI](https://daisyui.com/), [Tailwind CSS](https://tailwindcss.com/),
[Alpine.js](https://alpinejs.dev/), [htmx](https://htmx.org/) and
[Bootstrap Icons](https://icons.getbootstrap.com/).
