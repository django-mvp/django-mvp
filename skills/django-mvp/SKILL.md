---
name: django-mvp
description: >-
  Build a Django project on django-mvp: a settings-configurable application shell, a Cotton
  component library, Python-declared menus, icons by name, and enhanced class-based views
  (list search/ordering/pagination, CRUD, delete flows, inline formsets, tables). Use when
  wiring django-mvp into a project, building pages, menus, views or forms with it, styling or
  theming it, or working out why the shell renders the way it does. Covers the current
  settings-driven DaisyUI 5 / Tailwind v4 design, not the removed AdminLTE/Bootstrap era.
---

# django-mvp

django-mvp provides an application shell configured from settings, a library of Cotton UI
components, class-based views that search, order, paginate and run CRUD, menus declared in
Python, and icons referenced by name. The stylesheet and the front-end runtime are
prebuilt and shipped with the package, so a project needs no Node build step.

This file is a map. Each section below is a summary plus a pointer. Load the reference for
the topic you are working on rather than reading everything. `references/…` is relative to
this file.

> **Version note.** The package migrated from AdminLTE 4 / Bootstrap 5 to DaisyUI 5 /
> Tailwind v4. If you see `settings.MVP`, `cotton_bs5`, an `adminlte` renderer, or a
> `<c-app>` composed by hand in a base template, that is the old API and it is gone.

## Critical decisions

Get these right before writing anything. Each one is a mistake that looks like it worked.

| Concern | Correct | Wrong, removed, or a trap |
|---|---|---|
| Layout configuration | `settings.MVP_CONFIG` plus the `mvp.context_processors.mvp_config` processor | `settings.MVP`; layout attributes on a hand-built `<c-app>` |
| Navbar widgets | `layout.navbar.mobile.end` and `layout.navbar.desktop.end` | a flat `layout.navbar.end` — accepted as a legacy shape, but it is copied into both and removed from the merged config |
| A plain content page | extend `mvp/base.html`, fill `{% block content %}` | re-composing the shell yourself |
| A page behind an MVP view | override the `page.*` blocks | overriding `content`, which the packaged page template has already filled |
| Icons | an `EASY_ICONS` default renderer, the `mvp.utils.BS5_ICONS` pack, your own names on top | assuming the pack covers every name the package uses — `account_center` is not in it |
| Menu renderers | `sidebar` → `SidebarRenderer`, `dock` → `MobileFooterNavRenderer` | `adminlte` → `AdminLTERenderer` |
| CRUD link visibility | `show_<action>_action` | `has_<action>_permission` — renamed in 0.16, still honoured, and still wins when both are set |
| Authorising a CRUD action | a permission mixin on the target view | the `show_*` flags, which only draw the link |
| Form rendering | crispy-forms with the tailwind pack, on every install | a `form_renderer` attribute — no such setting exists |
| Table ordering | `order_by` on the table class | `order_by` on the view — it raises `ImproperlyConfigured` |
| Menu classes | `AppMenu`, `MobileFooterMenu`, `MenuGroup`, `MenuCollapse` from `mvp.menus` | — |

## Reference map

| Load | When you are |
|---|---|
| `references/setup.md` | Installing the package: apps, context processors, form settings, error handlers, first page, verification |
| `references/config.md` | Setting anything in `MVP_CONFIG` — view names, brand resolvers, theme, sidebar, navbar, tables |
| `references/layout.md` | Changing the shell: which block wraps what, per-page overrides, full-height pages |
| `references/menus.md` | Declaring the sidebar or dock menu, choosing renderers, or asking why an item is not highlighted |
| `references/icons.md` | Registering icon names, or an icon is not drawing |
| `references/views.md` | Building template, home, list or detail views — attributes, hooks, context keys |
| `references/forms.md` | Building create, update or delete views, handling `?next=`, or adding inline formsets |
| `references/components.md` | Choosing a component or checking an attribute — the full catalogue |
| `references/styling.md` | Writing CSS classes, picking or writing a theme, or touching the front-end build |
| `references/integrations.md` | Using django-tables2, django-filter or htmx |
| `references/troubleshooting.md` | Something renders wrong, silently does nothing, or raises |

## Quickstart

Enough to boot. Every step has a reference behind it.

**1. Settings.** Your own apps go above `mvp` so your templates win. `mvp` goes above
`crispy_tailwind` so its help-text override wins.

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "your_app",
    "django_cotton",
    "easy_icons",
    "flex_menu",
    "mvp",
    "crispy_forms",
    "crispy_tailwind",
]
SITE_ID = 1

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",   # required by the shell
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "mvp.context_processors.mvp_config",            # required by the shell
    ]},
}]

CRISPY_TEMPLATE_PACK = "tailwind"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]

FLEX_MENUS = {"renderers": {
    "sidebar": "mvp.renderers.SidebarRenderer",
    "dock": "mvp.renderers.MobileFooterNavRenderer",
}}

EASY_ICONS = {"default": {
    "renderer": "easy_icons.renderers.ProviderRenderer",
    "config": {"tag": "i"},
    "packs": ["mvp.utils.BS5_ICONS"],
    "icons": {"dashboard, overview": "bi bi-speedometer2"},  # comma keys are aliases
}}
```

**2. Layout.** `MVP_CONFIG` is deep-merged over the package defaults, so set only what you
change. Resolution order everywhere is component attribute, then `MVP_CONFIG`, then the
package default.

```python
# settings.py
MVP_CONFIG = {
    "layout": {
        "sidebar": {"breakpoint": "lg", "collapse": "icons", "title": "Acme"},
        "navbar": {"desktop": {"end": ["actions.theme-controller", "actions.login"]}},
    },
    "theme": {"default": "mvp", "choices": ["mvp", "mvp-dark", "dracula"]},
}
```

**3. A menu.** Declared in Python, in an app's `menus.py`. Pass `extra_context` as a
keyword argument.

```python
# your_app/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuGroup

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard",
             extra_context={"label": "Dashboard", "icon": "dashboard"}),
    MenuGroup(name="admin", extra_context={"label": "Administration"}, children=[
        MenuItem(name="users", view_name="user-list",
                 extra_context={"label": "Users", "icon": "people"}),
    ]),
])
```

**4. A page.** Extend the base template and fill the content block. The sidebar, header,
main region, footer and mobile dock are assembled for you.

```html
<!-- your_app/templates/dashboard.html -->
{% extends "mvp/base.html" %}
{% block content %}
  <c-container>
    <c-section title="Dashboard" icon="dashboard">
      <c-grid md="2" xl="4">
        <c-card title="Orders">150 new</c-card>
      </c-grid>
    </c-section>
  </c-container>
{% endblock content %}
```

**5. A list page.** The view supplies search, ordering, pagination, an empty state and the
page chrome. Ordering choices are three-tuples of a public key, a label, and the ORM
expression. The query-string value is matched against the public key, never passed to the ORM.

```python
# your_app/views.py
from mvp.views import MVPListView

class ProductListView(MVPListView):
    model = Product
    search_fields = ["name", "description"]
    order_by = [("name_asc", "Name (A-Z)", "name"), ("newest", "Newest first", "-created")]
    grid = {"md": 2, "xl": 3}
```

**6. Error pages.** Django reads these only from the module named by `ROOT_URLCONF`.

```python
# urls.py
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

## Rules that are easy to get wrong

- **The `show_<action>_action` flags draw links, nothing more.** The update and delete views
  never see them. Real authorisation goes on those views, through `LoginRequiredMixin`,
  `PermissionRequiredMixin`, `UserPassesTestMixin`, or an object-level permission library.
- **A shown action with no registered route raises `NoReverseMatch`.** The link is not
  quietly dropped.
- **Menu items highlight on exact URL equality with the request path.** A detail page does
  not light up its list item.
- **`{% block content %}` is already consumed** on any page rendered by an MVP view. Override
  the `page.*` blocks instead.
- **Not every Tailwind class ships.** Shadow utilities, physical inline-axis utilities
  (`pl-`, `mr-`, `text-left`), arbitrary values, and classes assembled at render time from
  values outside the shipped safelist are absent from the prebuilt stylesheet and fail
  silently. Use the logical forms (`ps-`, `me-`, `text-start`). Assembly itself is fine
  where the values are safelisted. `<c-grid md="2" xl="4">` builds `md:grid-cols-2` at
  render time and works, because the grid column counts are on the shipped safelist.
- **htmx, Alpine and the theme switcher are already bundled.** Do not add a CDN tag for any
  of them.
- **A form view built on a plain, non-model `Form` raises `ImproperlyConfigured`.** The page
  machinery resolves the model's metadata. Use a `ModelForm`, or set the model on the view.
- **Component attributes are the supported customisation surface.** Beyond them, override the
  component's template at the same path in your own project rather than reaching for utility
  classes.
