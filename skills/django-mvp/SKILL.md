---
name: django-mvp
description: 'Build and manage a Django web app with django-mvp: a settings-configurable DaisyUI 5 + Tailwind v4 app shell, django-cotton UI components, django-flex-menus navigation, django-easy-icons icons, and enhanced class-based views (search/order/pagination, CRUD, delete flows, error pages). Use when wiring django-mvp into a project (INSTALLED_APPS, MVP_CONFIG layout, EASY_ICONS packs, FLEX_MENUS renderers, mvp/base.html), building pages/menus/views, or debugging the shell. Covers the current settings-driven layout — NOT the removed AdminLTE/Bootstrap/settings.MVP era.'
---

# django-mvp

django-mvp gets a Django project to a polished, production-looking app fast: a
**settings-configurable application shell** (DaisyUI 5 + Tailwind CSS v4), a library of
**django-cotton** UI components, **enhanced class-based views** (search, ordering,
pagination, CRUD, delete flows), Python-defined **menus** (django-flex-menus), and
**icons by name** (django-easy-icons). Overriding principle: **things should just work**.

> **Version note.** django-mvp migrated FROM AdminLTE 4 / Bootstrap 5 TO DaisyUI 5 /
> Tailwind v4. If you see `settings.MVP`, `cotton_bs5`, an `adminlte` renderer,
> `sidebar_expand`, or `<c-app>` composed by hand in a base template — that is the old
> API. This skill documents the **current** settings-driven design.

## Critical decisions (get these right first)

| Concern | Correct (current) | Wrong (removed / stale) |
|---|---|---|
| Layout config | `settings.MVP_CONFIG` dict + `mvp.context_processors.mvp_config` | `settings.MVP` dict; Cotton attrs on a hand-built `<c-app>` |
| Icons | `EASY_ICONS["default"]["packs"] = ["mvp.utils.BS5_ICONS"]` + your own `"icons"` | Hand-listing every "required mvp icon" |
| Menu renderers | `sidebar` → `SidebarRenderer`, `dock` → `MobileFooterNavRenderer` | `adminlte` → `AdminLTERenderer` |
| Content pages | `{% extends "mvp/base.html" %}` then override `{% block content %}` | Re-composing `<c-app>…</c-app>` yourself |
| Error handlers | `mvp.views.bad_request` … `mvp.views.server_error` | assuming 500 must be self-contained HTML (it extends `mvp/error_base.html`) |
| Menu classes | `AppMenu`, `MobileFooterMenu`, `MenuGroup`, `MenuCollapse` from `mvp.menus` | — |

---

## Step 1 — INSTALLED_APPS + context processor

```python
INSTALLED_APPS = [
    # ...
    "django.contrib.sites",   # required (SITE_ID = 1)
    "django_cotton",          # Cotton template components
    "easy_icons",             # icon system
    "flex_menu",              # menu system
    "mvp",                    # django-mvp
    # ...
]
SITE_ID = 1
```

Register the context processor so `MVP_CONFIG` reaches every template as `mvp_config`:

```python
TEMPLATES = [{
    # ...
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",   # required by the shell
        # ...
        "mvp.context_processors.mvp_config",
    ]},
}]
```

---

## Step 2 — Icons (`EASY_ICONS` + `BS5_ICONS` pack)

`<c-icon name="…">` calls easy-icons' `{% icon name %}` with no renderer hint, so the
**default** renderer must resolve every name mvp's own components use. Include the bundled
Bootstrap Icons pack (`mvp.utils.BS5_ICONS`) — it covers all internal names — then add
your app's icons on top:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],   # covers every icon mvp needs
        "icons": {
            # your app's icons — name → "bi bi-<glyph>"
            "dashboard, home, overview": "bi bi-speedometer2",  # comma keys = aliases
            "invoices": "bi bi-receipt",
        },
    },
}
```

`mvp/base.html` loads the Bootstrap Icons webfont from a CDN; override the `head` block to
self-host. Icon names appear in menus (`extra_context["icon"]`) and component `icon=`
attributes. See [references/icons.md](references/icons.md).

---

## Step 3 — Menu renderers (`FLEX_MENUS`)

The shell renders the sidebar and mobile dock through named flex-menus renderers. The
shell expects the `"sidebar"` and `"dock"` keys:

```python
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
    "log_url_failures": DEBUG,   # optional: warn on unresolved view_names
}
```

A third renderer, `mvp.renderers.NavRenderer`, is available for horizontal nav bars.

---

## Step 4 — Layout config (`MVP_CONFIG`)

`MVP_CONFIG` is deep-merged over the package defaults (`mvp/config.py`) — set only the
keys you change. Package defaults:

```python
MVP_CONFIG = {
    "view_names": {                       # CRUD URL-name templates (see Views)
        "list": "{model_name}-list", "detail": "{model_name}-detail",
        "create": "{model_name}-create", "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    },
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm | md | lg | xl | 2xl | never — when the sidebar becomes persistent
            "collapse": "offcanvas",  # "offcanvas" (slides away) | "icons" (icon rail)
            "title": None,            # text beside the brand icon (falsey = none)
            "footer": [],             # Cotton component NAMES in the sidebar footer
        },
        "navbar": {
            "end": ["actions.theme-controller", "actions.login"],  # Cotton NAMES at navbar right
            "sticky": True,           # True: pinned header | False: scrolls away
        },
    },
}
```

**Resolution order everywhere:** component attribute (per-page) → `MVP_CONFIG` (project) →
package default.

**`navbar.end` / `sidebar.footer` are Cotton component NAMES, not template paths.**
`"actions.theme-controller"` → `<c-actions.theme-controller />`;
`"myapp.notifications-bell"` → `templates/cotton/myapp/notifications_bell.html`. Any
component in your cotton directory works with no extra config. Bundled widgets:
`actions.theme-controller`, `actions.language-switcher`, `actions.language-switcher-modal`,
`actions.search`, `actions.login`.

Full option reference: [references/layout.md](references/layout.md).

---

## Step 5 — Your first page

Pages extend `mvp/base.html` and fill `{% block content %}`. The shell (sidebar, header,
content, footer, mobile dock) renders **automatically** — do not re-compose `<c-app>`.

```django
{% extends "mvp/base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
  <c-container>
    <c-section title="Dashboard" icon="dashboard">
      <c-grid md="2" xl="4">
        <c-card title="Orders">150 new</c-card>
        <c-card title="Revenue">$12,400</c-card>
      </c-grid>
    </c-section>
  </c-container>
{% endblock %}
```

For title/subtitle/breadcrumbs and page chrome, back the template with an MVP view
(Step 7) instead of a bare `TemplateView`.

### Base template blocks

`mvp/base.html` exposes these blocks for coarse control (override the component template
itself for anything deeper):

| Block | Replaces |
|---|---|
| `head`, `title`, `styles`, `extra_js` | document head / stylesheet links / scripts |
| `app` | the entire shell |
| `app.sidebar` | the sidebar (default `<c-app.sidebar />`) |
| `app.header` / `app.header.widgets` / `app.header.tray` | header / extra navbar-end content / row below navbar |
| `app.main` / `content` | main area / page content |
| `app.footer` | footer |

### Per-page layout override

`breakpoint` and `collapse` drive three regions that must agree (sidebar drawer, the
collapsed sidebar, and the navbar toggle). The shell resolves them **once** at the top of
`{% block app %}` from `breakpoint`/`collapse` context vars. Override for one page by
wrapping `{{ block.super }}`:

```django
{% block app %}
  {% with breakpoint="xl" collapse="icons" %}{{ block.super }}{% endwith %}
{% endblock %}
```

Either knob may be set alone. Setting `breakpoint`/`collapse` as attributes directly on
`<c-app>`/`<c-app.sidebar>` styles that component but does **not** reach the navbar toggle
— always resolve them in the `app` block (or from view context) so all three stay in sync.

---

## Step 6 — Menus (sidebar + mobile dock)

django-mvp renders two menus from Python: **`AppMenu`** (sidebar) and
**`MobileFooterMenu`** (mobile dock, pre-populated with a sidebar-toggle item). Define
them in an app's `menus.py` and import that module at startup.

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuGroup, MenuCollapse

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard",
             extra_context={"label": "Dashboard", "icon": "dashboard"}),

    # Non-clickable section header + its items
    MenuGroup(name="admin", extra_context={"label": "Administration"}, children=[
        MenuItem(name="users", view_name="user-list",
                 extra_context={"label": "Users", "icon": "people"}),
        MenuItem(name="settings", view_name="settings",
                 extra_context={"label": "Settings", "icon": "settings", "badge": "3"}),
    ]),

    # Collapsible group (<details>)
    MenuCollapse(name="reports", extra_context={"label": "Reports", "icon": "graph-up"},
                 children=[
        MenuItem(name="sales", view_name="report-sales",
                 extra_context={"label": "Sales"}),
    ]),
])
```

Ensure the module loads (either works):

```python
# myapp/apps.py
class MyappConfig(AppConfig):
    name = "myapp"
    def ready(self):
        from . import menus  # noqa: F401
```

`flex_menu`'s `FlexMenuConfig.ready()` also autodiscovers `menus.py` in installed apps, so
a top-level `AppMenu.extend([...])` call is picked up as long as `myapp` is in
`INSTALLED_APPS` and the module imports cleanly (import errors are silently swallowed).

**Item options:** `view_name=` (resolved with `reverse()`) or `url=` (external/hard-coded)
are `MenuItem` constructor args — not `extra_context`. `extra_context` keys: `label`
(text), `icon` (easy-icons name), `badge` (badge text). Active state is automatic (URL
match); in `collapse="icons"` mode each label becomes its hover tooltip.

**Mobile dock:** extend `MobileFooterMenu` the same way; it renders via `<c-app.dock>`
below the breakpoint and ships with a sidebar-toggle item.

More patterns (visibility checks, nesting, rendering menus elsewhere):
[references/menu-patterns.md](references/menu-patterns.md).

---

## Step 7 — Views

Concrete views are exported from `mvp.views`; the mixins they compose from live in their
modules (`mvp.views.base`, `.list`, `.edit`, `.detail`) for building your own — standard
Django, no factories.

```python
from mvp.views import (
    MVPTemplateView, MVPHomeView,
    MVPListView, MVPDetailView,
    MVPFormView, MVPCreateView, MVPUpdateView, MVPDeleteView,
)
```

Every MVP view mixes in `PageMixin`, which injects a `page` context dict (`title`,
`subtitle`, `class`, `breadcrumbs`). Set static values as class attributes
(`page_title`, `page_subtitle`, `page_class`, `breadcrumbs`) or override `get_page_*()` /
`get_breadcrumbs()` for dynamic ones. Each breadcrumb is a dict with `"text"` and optional
`"href"` (omit `href` for the current page).

### Home page

`MVPHomeView` serves a **dashboard** template to authenticated users and a **landing**
template to anonymous visitors — same URL, no redirect:

```python
class HomeView(MVPHomeView):
    landing_template_name = "myapp/landing.html"      # default: "mvp/landing.html"
    dashboard_template_name = "myapp/dashboard.html"  # default: "mvp/dashboard.html"

    def get_dashboard_context(self, context):
        context["recent"] = MyModel.objects.order_by("-created")[:5]
        return context
```

Omit both to use the bundled defaults. Raises `ImproperlyConfigured` if
`landing_template_name` is `None`, or if `dashboard_template_name` is `None` for an
authenticated request.

### Informational pages

```python
class AboutView(MVPTemplateView):
    template_name = "myapp/about.html"
    page_title = "About Us"
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "About"}]
```

### List pages

```python
class ProductListView(MVPListView):
    model = Product
    # done: paginated 24/page, empty state, page chrome

    search_fields = ["name", "description", "owner__username"]  # ?q= OR-across-fields
    order_by = [                                                # ?o= whitelist (3-tuple!)
        ("name_asc",  "Name (A-Z)",   "name"),
        ("newest",    "Newest first", "-created"),
    ]
    grid = {"md": 2, "xl": 3}                    # card grid breakpoints
    list_item_template = "shop/product_card.html"  # default: <app>/<model>_list_item.html
    create_form_class = ProductForm              # inline "create" modal on the list page
    has_create_permission = True
```

`order_by` entries are **three-tuples** `(public_key, label, orm_expression)` — the raw
`?o=` value is matched against `public_key` and never reaches the ORM. `SearchMixin`,
`OrderMixin`, `SearchOrderMixin` (from `mvp.views.list`) also apply to any plain
`ListView`; `MVPListViewMixin` composes with other bases (e.g. `FilterView`).

### Detail + CRUD URL wiring

`MVPDetailView` (via `CRUDDirectoryMixin`) builds a `directory` of sibling CRUD URLs,
each gated by a `has_<action>_permission` flag (all default `False`). URL names come from
`MVP_CONFIG["view_names"]` (`{model_name}-detail`, etc.).

```python
class ProductDetailView(MVPDetailView):
    model = Product
    directory = ["list", "detail", "update", "delete"]
    has_list_permission = True
    has_detail_permission = True
    def has_update_permission(self, user): return user.is_staff   # dynamic gate
    def has_delete_permission(self, user): return user.is_staff
```

Templates read `{% if directory.update_url %}…{% endif %}` (the `directory` key is always
present, empty when all denied).

### Forms: create / update / generic

```python
class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "category", "price"]
    has_list_permission = True

class ProductUpdateView(MVPUpdateView):
    model = Product
    form_class = ProductForm
    has_delete_permission = True   # shows the Delete button in the form footer
```

- **Renderer auto-detection** — crispy-forms or django-formset when installed, else
  Django's default. Override with `form_renderer = "crispy" | "formset" | "django"`.
- **Success URL chain** — a validated same-origin `?next=` (open-redirect safe, via
  `NextURLMixin`) wins; else explicit `success_url` → detail → list. `?next=` also accepts
  CRUD shorthands (`list`, `detail`, `create`, `update`, `delete`).
- Titles and success messages derive from the model's `verbose_name`.

### Delete flows

`MVPDeleteView` handles four scenarios via class attributes — no custom template needed:

| Scenario | Trigger |
|---|---|
| Basic (warning + Delete) | default |
| Related-objects summary | `show_related_objects = True` |
| Protected (blocks delete, lists blockers) | auto-detected (PROTECT FK) |
| Type-to-confirm | `require_confirmation = True` (override `get_confirmation_value()`) |

### htmx

With [django-htmx](https://django-htmx.readthedocs.io/) installed + middleware active,
`HtmxFormMixin` (`mvp.views.htmx`) upgrades form views: invalid POST re-renders the form
partial, success returns `HX-Redirect`/a partial, events go via `HX-Trigger`. Degrades
gracefully for non-htmx requests.

Deep API (PageMixin, CRUDDirectoryMixin, NextURLMixin, all mixins, delete internals,
MVPListView attribute/hook tables): [references/views.md](references/views.md).

---

## Step 8 — Error pages

Wire the four handlers in your **root** URLconf (Django only reads handler vars from the
`ROOT_URLCONF` module, not from `include()`d apps):

```python
# myproject/urls.py
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

(The dotted `mvp.views.error.bad_request` form also works — the handlers are re-exported
from `mvp.views`.)

All four templates (`400/403/404/500.html`) extend **`mvp/error_base.html`**: a
full-viewport centered layout, no sidebar, no DB queries, brand logo above the heading.
Override the named blocks to customize:

```django
{% extends "mvp/error_base.html" %}
{% block title %}404 — Not Found{% endblock %}
{% block heading %}Page not found{% endblock %}
{% block description %}We could not find that page.{% endblock %}
{% block actions %}<c-button variant="primary" icon="home" href="/" text="Home" />{% endblock %}
```

The 500 handler passes `support_email` (from `settings.DEFAULT_FROM_EMAIL`, else `None`)
and must **never touch the DB** — the shipped handler is DB-free; if you override it, keep
it that way (verify with `django_assert_num_queries(0)`).

**Preview routes** (inspect error pages without triggering real errors) — point plain
`TemplateView`s at `400.html`/`403.html`/`404.html`/`500.html`.

---

## Step 9 — Components (quick reference)

All UI is django-cotton components with small attribute APIs. `class` adds CSS classes;
other unknown attributes pass through to the root element. To go beyond the attributes,
**override the component template** at the same path in your project (`templates/cotton/…`).
Directory = namespace: `cotton/page/list/empty.html` → `<c-page.list.empty>`.

Common components:

- **Layout:** `c-container` (`fluid`, `fill`), `c-grid` (`cols`/`sm`…`xxl` counts 1–6/12,
  `gap`), `c-group`, `c-toolbar`, `c-divider`, `c-section` (`title`, `icon`, `level`;
  `actions` slot), `c-section.hero`.
- **Data display:** `c-card` (`title`, `icon`), `c-button` (`text`, `icon`, `variant`
  [DaisyUI colors], `size` sm/md/lg, `outline`, `ghost`), `c-badge`, `c-icon` (`name`),
  `c-text`, `c-alert`, `c-data-field`, `c-messages` (`dismissible`), `c-modal`,
  `c-dropdown`, `c-avatar`.
- **Navigation:** `c-menu` / `c-menu.item` / `c-menu.group` / `c-menu.collapse` /
  `c-menu.divider`, `c-breadcrumbs`, `c-pagination`, `c-dock` (normally rendered from
  Python menus — hand-build only when needed).
- **Actions/widgets:** `c-actions.theme-controller`, `c-actions.language-switcher`(`-modal`),
  `c-actions.search`, `c-actions.login`, `c-user.sidebar-menu`.
- **Addons:** `c-addons.share-dropdown`, `c-addons.django-table` (needs django-tables2).

Full table: `docs/components.md` in the package. Component naming/domain rules: `CONTEXT.md`.

---

## Step 10 — Styling (Tailwind v4 + DaisyUI 5)

Two tiers:

- **Tier 1 — no build.** The prebuilt stylesheet (`mvp/static/css/django-mvp.css`, loaded
  by `mvp/base.html`) covers every class mvp's components use. Customize via component
  **attributes** and template overrides that **reuse packaged components**. Theme changes
  (DaisyUI CSS-variable themes; `<c-actions.theme-controller>` for light/dark) stay Tier 1.
- **Tier 2 — own build.** The moment your own templates use their own Tailwind utility
  classes (`class="grid grid-cols-3"`), rebuild so Tailwind scans both your templates and
  mvp's:
  ```bash
  npm install -D tailwindcss @tailwindcss/cli daisyui
  python manage.py mvp_tailwind > assets/tailwind.css   # generates the entry file
  npx @tailwindcss/cli -i assets/tailwind.css -o static/css/app.css --minify
  ```
  Then load your stylesheet by overriding the `styles`/`head` block. `mvp_tailwind` imports
  the mvp preset (`mvp/tailwind/base.css`: drawer-state variants, breakpoint safelist,
  icon-rail CSS) and `@source`s both template trees. `--paths` prints just the package
  paths for manual wiring.

---

## Step 11 — Optional integrations (guarded modules, not extras)

Views built on third-party packages live under `mvp.integrations` and are **not** exported
from `mvp.views`. The dependency is required only when you import the integration
(otherwise `ImproperlyConfigured` with install hints):

```python
from mvp.integrations.django_tables.views import MVPTableView          # pip install django-tables2
from mvp.integrations.django_filters.views import MVPFilteredListView  # pip install django-filter
```

`MVPTableView` = full MVP list behavior + django-tables2 rendering. `MVPFilteredListView`
adds `applied_filters`/`applied_filter_count` (the list filter button badges the count).
`MVPTableViewMixin` / composing with `FilterView` are supported. **Crispy forms** is
runtime-detected (not guarded): `pip install django-crispy-forms crispy-tailwind`, add the
apps, set `CRISPY_TEMPLATE_PACK = "tailwind"`.

---

## Step 12 — Verify

```bash
python manage.py check      # catches missing app/config issues
pytest                      # or: python manage.py test
```

Smoke checklist:
- [ ] `/` anonymous → landing (no sidebar), Sign In visible; authenticated → dashboard + full shell
- [ ] Each sidebar item → 200, correct active highlight
- [ ] Icons render (no empty boxes) — every used name is registered
- [ ] `/nonexistent/` → styled 404 in the shell
- [ ] Mobile viewport → sidebar becomes overlay drawer; dock visible; hamburger works
- [ ] Sidebar `collapse="icons"` → rail shows icons + hover tooltips; toggle persists across loads

---

## Common pitfalls

- **"AppMenu items don't appear"** — `menus.py` must be in an `INSTALLED_APPS` app, call
  `AppMenu.extend([...])` at module level, and import cleanly (import errors are swallowed
  by autodiscover).
- **"Icons are empty boxes"** — the name isn't resolvable by the default renderer. Include
  `mvp.utils.BS5_ICONS` in `packs` and register app-specific names under `"icons"`.
- **"Sidebar renders but the menu is empty"** — `FLEX_MENUS["renderers"]["sidebar"]` must
  be set; check `view_name`s resolve (`log_url_failures=True` warns).
- **"Layout config does nothing"** — you're using `settings.MVP` (removed). Use
  `settings.MVP_CONFIG` and add `mvp.context_processors.mvp_config` to context processors.
- **"Per-page breakpoint/collapse doesn't move the navbar toggle"** — set them in the
  `app` block (or view context), not as attributes on `<c-app>`/`<c-app.sidebar>`.
- **"I'm hand-composing `<c-app>` in my page"** — don't. Extend `mvp/base.html` and fill
  `{% block content %}`; the shell is automatic.
