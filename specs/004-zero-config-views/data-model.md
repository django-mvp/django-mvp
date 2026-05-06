# Data Model: Zero-Config Ready-to-Use Views

**Branch**: `004-zero-config-views` | **Date**: 2026-05-02

This feature introduces no database models. All entities are Python view classes and their configuration attributes.

---

## Entity 1: MVPTemplateView

**Location**: `mvp/views/base.py` (existing)

**Description**: A zero-config layout-aware template view. Renders any named template inside the standard AdminLTE layout shell (navbar, sidebar, content area) without requiring a model, form, or queryset.

### Class Hierarchy

```
django.views.generic.View
  └── django.views.generic.TemplateView
        └── mvp.views.base.MVPTemplateView
              (also mixes in: PageMixin)
```

### Configuration Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `template_name` | `str` | *(required)* | Path to the template to render. Standard Django `TemplateView` attribute. |
| `page_title` | `str \| Promise` | `""` | Text shown as the page heading in the layout chrome. |
| `page_subtitle` | `str \| Promise` | `""` | Secondary heading shown below the title. |
| `page_icon` | `str \| None` | `None` | Icon class string (e.g., `"fas fa-home"`). |
| `page_class` | `str` | `""` | Extra CSS class(es) appended to `"mvp-page"` on the page container. |
| `breadcrumbs` | `list[dict]` | `[]` | List of `{"text": str, "href": str (optional)}` dicts for breadcrumb navigation. |

### Override Hooks

| Method | Purpose |
|--------|---------|
| `get_page_title()` | Return dynamic page title. |
| `get_page_subtitle()` | Return dynamic page subtitle. |
| `get_page_icon()` | Return dynamic icon string or `None`. |
| `get_page_class()` | Return full CSS class string (always prefixes `"mvp-page"`). |
| `get_breadcrumbs()` | Return dynamic breadcrumb list. |
| `get_context_data(**kwargs)` | Inherited from `PageMixin`; adds `page` dict to context. |

### Context Variables

| Variable | Type | Description |
|----------|------|-------------|
| `page` | `dict` | Dict with keys: `title`, `subtitle`, `icon`, `class`, `breadcrumbs`. |
| `request.user` | `User \| AnonymousUser` | Injected by `django.contrib.auth.context_processors.auth`. |

### Validation Rules

- `template_name` must be set (either as class attribute or `as_view(template_name=…)`) — Django raises `ImproperlyConfigured` if not set.
- All `page_*` attributes are optional with safe defaults.

### HTTP Methods

- **GET**: Renders and returns the template. Always permitted (anonymous and authenticated).
- **All other methods**: Django returns `405 Method Not Allowed` via the base `View` class.

---

## Entity 2: MVPHomeView

**Location**: `mvp/views/base.py` (existing, modified)

**Description**: A dual-purpose view that serves a landing page to anonymous visitors and a dashboard to authenticated users, from the same URL, without redirects. Template selection is the only authentication-sensitive decision; the view itself does not require login.

### Class Hierarchy

```
django.views.generic.View
  └── django.views.generic.TemplateView
        └── mvp.views.base.MVPTemplateView
              └── mvp.views.base.MVPHomeView
```

### Configuration Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `landing_template_name` | `str` | `"mvp/landing.html"` | Template rendered for anonymous visitors. |
| `dashboard_template_name` | `str` | `"mvp/dashboard.html"` | Template rendered for authenticated users. |
| `page_title` | `str \| Promise` | `_("Home")` | Page title shown in layout chrome. |
| *(all PageMixin attributes)* | — | — | Inherited from `MVPTemplateView`. |

### Override Hooks

| Method | Purpose |
|--------|---------|
| `get_template_names()` | Returns `[landing_template_name]` or `[dashboard_template_name]` based on `request.user.is_authenticated`. Raises `ImproperlyConfigured` if the required attribute is `None`. |
| `get_landing_context(context)` | Populates extra context for anonymous users. Default injects `hero_content` from `MVP_LANDING_PAGE_HERO` setting. |
| `get_dashboard_context(context)` | Populates extra context for authenticated users. Default is a no-op (returns context unchanged). |
| `get_context_data(**kwargs)` | Calls `super()` then delegates to `get_landing_context()` or `get_dashboard_context()` based on auth state. |

### Context Variables

| Variable | Type | When Present | Description |
|----------|------|-------------|-------------|
| `page` | `dict` | Always | Layout page metadata (title, subtitle, icon, class, breadcrumbs). |
| `hero_content` | `dict` | Unauthenticated only | Dict with keys `title`, `subtitle`, `lead`, `image`. Sourced from `MVP_LANDING_PAGE_HERO` setting. |
| `request.user` | `User \| AnonymousUser` | Always | Via standard auth context processor. |

### Validation Rules

- **`landing_template_name` is always required.** If `None`, `ImproperlyConfigured` is raised for any request with message: *"`{ClassName}` requires `landing_template_name` to be set."*
- **`dashboard_template_name` is required when an authenticated user requests the page.** If `None`, `ImproperlyConfigured` is raised with message: *"`{ClassName}` requires `dashboard_template_name` to be set for authenticated users."*
- Both attributes default to the package's bundled templates (`mvp/landing.html`, `mvp/dashboard.html`), so out-of-the-box use without configuration is supported.

### HTTP Methods

- **GET**: Renders landing or dashboard template based on auth state. Always `200 OK`, never redirects.
- **All other methods**: Django returns `405 Method Not Allowed`.

### State Transitions

```
Request → is_authenticated?
  ├── No  → landing_template_name set? → No  → ImproperlyConfigured
  │                                   → Yes → render landing template (200 OK)
  └── Yes → dashboard_template_name set? → No  → ImproperlyConfigured
                                         → Yes → render dashboard template (200 OK)
```

---

## Entity 3: PageMixin

**Location**: `mvp/views/base.py` (existing — no changes)

**Description**: Mixin that injects a `page` context dict into any `TemplateView`. Consumed by `MVPTemplateView` and all views that inherit from it. Not modified by this feature.

### Attributes (summary)

`page_title`, `page_subtitle`, `page_icon`, `page_class`, `breadcrumbs` — all with getter method overrides. Context key: `page`.

---

## Entity 4: Bundled Templates

### mvp/landing.html

**Location**: `mvp/templates/mvp/landing.html` (created)
**Extends**: `page_view.html`
**Purpose**: Default landing page rendered by `MVPHomeView` for anonymous visitors.
**Key context**: `hero_content` dict (`title`, `subtitle`, `lead`, `image`).
**Override point**: `{% block page.content %}` — override in a project template to customise landing page content.

### mvp/dashboard.html

**Location**: `mvp/templates/mvp/dashboard.html` (created)
**Extends**: `page_view.html`
**Purpose**: Default dashboard rendered by `MVPHomeView` for authenticated users.
**Key context**: `request.user` (via auth context processor).
**Override point**: `{% block page.content %}` — override in a project template to customise dashboard content.

---

## Relationships

```
PageMixin
  └── used by → MVPTemplateView
                  └── extends → MVPHomeView

MVPTemplateView → renders → any developer-supplied template
MVPHomeView     → renders → mvp/landing.html (anonymous)
                         → mvp/dashboard.html (authenticated)

mvp/landing.html  → extends → page_view.html (layout shell)
mvp/dashboard.html → extends → page_view.html (layout shell)
```
