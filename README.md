# Django MVP

[![Tests](https://github.com/SamuelJennings/django-mvp/actions/workflows/tests.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/tests.yml)
[![Build](https://github.com/SamuelJennings/django-mvp/actions/workflows/build.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/build.yml)
[![Release](https://github.com/SamuelJennings/django-mvp/actions/workflows/on-release-main.yml/badge.svg)](https://github.com/SamuelJennings/django-mvp/actions/workflows/on-release-main.yml)
[![PyPI](https://img.shields.io/pypi/v/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![codecov](https://codecov.io/gh/SamuelJennings/django-mvp/branch/main/graph/badge.svg)](https://codecov.io/gh/SamuelJennings/django-mvp)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-mvp.svg)](https://pypi.org/project/django-mvp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AdminLTE 4 for Django** - A modern, responsive admin dashboard template system built with Django Cotton, providing AdminLTE 4 layouts and components for building production-ready data-centric applications.

> **Note:** This project is currently in active development. Version 1.0 will introduce AdminLTE 4 integration with breaking changes from previous versions.

## Overview

Django MVP brings the powerful [AdminLTE 4](https://github.com/colorlibhq/AdminLTE) admin dashboard template to Django as a collection of reusable [django-cotton](https://github.com/wrabit/django-cotton) components. It provides:

- **AdminLTE 4 Layout System** - Full implementation of AdminLTE's grid-based layout structure
- **Configuration-Driven Design** - Control layout and appearance via Django settings
- **Cotton Component Library** - AdminLTE-specific components (cards, boxes, widgets, etc.)
- **Bootstrap 5 Foundation** - Built on Bootstrap 5 with [django-cotton-bs5](https://github.com/SamuelJennings/django-cotton-bs5) for base components
- **Production-Ready** - Designed for data-centric applications, admin interfaces, and dashboards

### What's Included

Django MVP provides **AdminLTE-specific components only**. Standard Bootstrap 5 components (buttons, modals, forms, etc.) are provided by the separate `django-cotton-bs5` package. This includes:

- **AdminLTE Layouts** - App wrapper, sidebar, header, main content area, footer
- **AdminLTE Widgets** - Info boxes, small boxes, cards, direct chat
- **AdminLTE Components** - Specialized components unique to AdminLTE
- **View Mixins** - Python helpers for common patterns (search, ordering, pagination)
- **Menu Integration** - Renderers for [django-flex-menus](https://github.com/SamuelJennings/django-flex-menus)

## Architecture

Django MVP mirrors AdminLTE 4's grid-based layout structure:

```
.app-wrapper (grid container)
├── .app-sidebar (navigation)
├── .app-header (top navbar)
├── .app-main (content area)
│   ├── .app-content-header (page header/breadcrumbs)
│   └── .app-content (main content)
└── .app-footer (optional footer)
```

## Installation

```bash
pip install django-mvp
```

Add required apps to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "django_cotton",      # Cotton template components
    "cotton_bs5",         # Bootstrap 5 components
    "easy_icons",         # Icon system
    "flex_menu",          # Optional: menu system
    "mvp",                # Django MVP
    ...
]
```

### Add Context Processor

Add the MVP context processor to make configuration available in all templates:

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

### Configure Icons

Django MVP uses Bootstrap Icons via `django-easy-icons`:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "icons": {
            # Core Actions
            "add": "bi bi-plus-circle",
            "create": "bi bi-plus-circle",
            "edit": "bi bi-pencil",
            "delete": "bi bi-trash",
            "save": "bi bi-floppy",
            "cancel": "bi bi-x-circle",
            "view": "bi bi-eye",
            # Navigation
            "arrow-right": "bi bi-arrow-right",
            "chevron_down": "bi bi-chevron-down",
            "chevron_up": "bi bi-chevron-up",
            "search": "bi bi-search",
            "filter": "bi bi-funnel",
            "person": "bi bi-person",
            "calendar": "bi bi-calendar3",
            "settings": "bi bi-gear",
            "theme_light": "bi bi-sun",
            "theme_dark": "bi bi-moon",
            "github": "bi bi-github",
        },
    },
}
```

## Template Hierarchy

Django MVP follows a simple template hierarchy:

1. **`base.html`** - Foundation HTML structure with AdminLTE CSS/JS
2. **`mvp/base.html`** - AdminLTE app-wrapper layout structure
3. **Your templates** - Extend `mvp/base.html` and override blocks

Example page template:

```html
{% extends "mvp/base.html" %}

{% block content %}
  <div class="container-fluid">
    <h1>Your Page Content</h1>
  </div>
{% endblock %}
```

### Customizing Layouts

Create a custom base layout in your project to override blocks:

```html
{# templates/layouts/base.html in your project #}
{% extends "mvp/mvp/base.html" %}

{% block extra_css %}
  <link rel="stylesheet" href="{% static 'css/custom.css' %}">
{% endblock %}
```

## Layout Configuration

Django MVP provides flexible layout control through the `<c-app>` component with boolean attributes for fixed positioning of sidebar, header, and footer elements.

### Fixed Sidebar Layout

Make the sidebar sticky during vertical scrolling:

```django
{% load cotton %}
<c-app fixed_sidebar>
    {% block content %}
        <h1>Dashboard</h1>
    {% endblock %}
</c-app>
```

**Effect**: Sidebar remains visible on the left while scrolling through content.
**Best for**: Admin dashboards and data-centric applications.

### Fixed Header Layout

Keep the navigation bar at the top:

```django
<c-app fixed_header>
    {% block content %}
        <h1>Long Article</h1>
    {% endblock %}
</c-app>
```

**Effect**: Top navigation bar stays fixed at the top.
**Best for**: Applications with important navigation or branding.

### Fixed Footer Layout

Keep the footer visible at the bottom:

```django
<c-app fixed_footer>
    {% block content %}
        <h1>Terms of Service</h1>
    {% endblock %}
</c-app>
```

**Effect**: Footer remains at the bottom while scrolling.
**Best for**: Copyright notices or action buttons that should remain accessible.

### Combining Fixed Elements

Multiple attributes can be used together:

```django
<!-- Admin dashboard with fixed sidebar and header -->
<c-app fixed_sidebar fixed_header>
    {% block content %}
        <h1>Admin Panel</h1>
    {% endblock %}
</c-app>

<!-- Complete fixed layout (sidebar, header, footer) -->
<c-app fixed_sidebar fixed_header fixed_footer>
    {% block content %}
        <h1>Full Fixed Layout</h1>
    {% endblock %}
</c-app>
```

### Responsive Sidebar Control

Control when the sidebar expands from mobile drawer to visible sidebar:

```django
<!-- Sidebar expands on tablets and above (768px) -->
<c-app sidebar_expand="md">
    {% block content %}
        <h1>Mobile-Optimized App</h1>
    {% endblock %}
</c-app>

<!-- Sidebar expands on wide screens (1200px) -->
<c-app sidebar_expand="xl">
    {% block content %}
        <h1>Wide Layout App</h1>
    {% endblock %}
</c-app>
```

**Available breakpoints**: `sm` (576px), `md` (768px), `lg` (992px, default), `xl` (1200px), `xxl` (1400px)

### Per-Page Layout Overrides

Different pages can use different layout configurations:

```django
{# templates/dashboard.html - needs navigation visible #}
{% load cotton %}
<c-app fixed_sidebar fixed_header>
    <h1>Dashboard</h1>
</c-app>

{# templates/article.html - immersive reading experience #}
{% load cotton %}
<c-app>
    <h1>Article Title</h1>
    <p>Content...</p>
</c-app>
```

For complete layout documentation, see [App Component Reference](docs/components/app.md).

## Navigation Menus

Django MVP provides a configurable navigation menu system using [django-flex-menus](https://github.com/SamuelJennings/django-flex-menus) with AdminLTE 4 sidebar styling. Menus are defined in Python and automatically rendered in the sidebar.

### Basic Menu Setup

1. **Import and extend the default AppMenu** in your app's `menus.py` file:

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu

# Add menu items to the global AppMenu
AppMenu.children.extend([
    MenuItem(
        name="dashboard",
        extra_context={
            "label": "Dashboard",
            "view_name": "dashboard",
            "icon": "speedometer2"
        }
    ),
    MenuItem(
        name="users",
        extra_context={
            "label": "User Management",
            "view_name": "user-list",
            "icon": "people",
            "badge": "12",
            "badge_classes": "text-bg-primary"
        }
    ),
])
```

1. **Import the menus in your app's `apps.py`**:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        # Import menus to register them
        from . import menus
```

### Hierarchical Menu Groups

Create organized menu sections with nested items:

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu

# Single menu items (appear at top)
AppMenu.children.extend([
    MenuItem(
        name="dashboard",
        extra_context={
            "label": "Dashboard",
            "view_name": "dashboard",
            "icon": "house"
        }
    ),
])

# Menu groups (appear after singles)
user_management = MenuItem(
    name="user_management",
    extra_context={
        "group_header": "User Management",  # Creates section header
        "icon": "people"
    },
    children=[
        MenuItem(
            name="user_list",
            extra_context={
                "label": "All Users",
                "view_name": "user-list",
                "icon": "person"
            }
        ),
        MenuItem(
            name="user_roles",
            extra_context={
                "label": "Roles & Permissions",
                "view_name": "user-roles",
                "icon": "shield"
            }
        ),
    ]
)

AppMenu.children.append(user_management)
```

### Menu Features

**Single Menu Items**: Direct links that appear at the top of the sidebar

- `label`: Display text
- `view_name`: Django URL name for reverse() lookup
- `icon`: Bootstrap icon name (via django-easy-icons)
- `badge`: Optional badge text
- `badge_classes`: CSS classes for badge styling

**Menu Groups**: Collapsible sections with headers and nested items

- `group_header`: Section header text
- `children`: List of child MenuItem objects
- Automatically uses `nav-treeview` and `menu-open` classes

**Active State Detection**: Automatically highlights current page menu items based on URL matching.

### Icon Configuration

Menu icons use [django-easy-icons](https://github.com/SamuelJennings/django-easy-icons) with Bootstrap Icons. Configure available icons in `settings.py`:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "icons": {
            "house": "bi bi-house",
            "people": "bi bi-people",
            "person": "bi bi-person",
            "shield": "bi bi-shield",
            "gear": "bi bi-gear",
            "speedometer2": "bi bi-speedometer2",
        },
    },
}
```

### Cotton Components (Optional)

For custom menu implementations, use the included Cotton components:

```django
{% load cotton %}

{# Complete menu structure #}
<c-app.sidebar.menu>
    <c-app.sidebar.menu.group label="MAIN NAVIGATION">
        <c-app.sidebar.menu.item label="Dashboard" href="/" icon="house" active=True />
        <c-app.sidebar.menu.item label="Users" icon="people" badge="5">
            <c-app.sidebar.menu.item label="All Users" href="/users/" />
            <c-app.sidebar.menu.item label="Add User" href="/users/add/" />
        </c-app.sidebar.menu.item>
    </c-app.sidebar.menu.group>
</c-app.sidebar.menu>
```

For detailed menu system documentation, see [Navigation Guide](docs/navigation.md).

## Quick Start

### Basic Page Template

```html
{% extends "mvp/base.html" %}

{% block content %}
  <div class="app-content">
    <div class="container-fluid">
      <h1>Welcome to My Application</h1>
      <p>Your content here...</p>
    </div>
  </div>
{% endblock %}
```

### With Page Header and Breadcrumbs

```html
{% extends "mvp/base.html" %}

{% block page_header %}
  <div class="app-content-header">
    <div class="container-fluid">
      <div class="row">
        <div class="col-sm-6">
          <h3 class="mb-0">Dashboard</h3>
        </div>
        <div class="col-sm-6">
          <ol class="breadcrumb float-sm-end">
            <li class="breadcrumb-item"><a href="/">Home</a></li>
            <li class="breadcrumb-item active">Dashboard</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
{% endblock %}

{% block content %}
  <div class="app-content">
    <div class="container-fluid">
      <!-- Your dashboard content -->
    </div>
  </div>
{% endblock %}
```

## AdminLTE Components

Django MVP provides Cotton components for AdminLTE-specific widgets. Standard Bootstrap components (buttons, modals, forms, etc.) should use `django-cotton-bs5`.

**Available Components:**

- [Info Box](docs/components/info-box.md) - Display metrics with icons and optional progress bars
- [Small Box](docs/components/small-box.md) - Prominent dashboard summary widgets with action links
- [Card](docs/components/card.md) - Flexible content containers with collapsible sections

### Info Box

Display key metrics with icons and optional progress indicators:

```html
<c-info-box
  icon="box-seam"
  text="New Orders"
  number="150"
  variant="primary" />

<!-- With progress bar -->
<c-info-box
  icon="add"
  text="Downloads"
  number="114,381"
  variant="info"
  progress="70"
  description="70% Increase in 30 Days" />

<!-- Box fill mode (entire box colored) -->
<c-info-box
  icon="briefcase"
  text="Sales"
  number="13,648"
  variant="success"
  fill="box" />
```

### Small Box

Create prominent summary cards for dashboard overviews:

```html
<c-small-box
  heading="150"
  text="New Orders"
  icon="cart"
  variant="success" />

<!-- With action link -->
<c-small-box
  heading="53%"
  text="Bounce Rate"
  icon="chart"
  variant="warning"
  link="/stats/"
  link_text="View details" />
```

### Card

Build flexible content containers with headers, bodies, and footers:

```html
<!-- Basic card -->
<c-card title="Monthly Report" variant="primary">
  Card content here
</c-card>

<!-- With icon and tools -->
<c-card title="Revenue" icon="chart" variant="success" fill="header">
  <c-slot name="tools">
    <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse">
      <c-icon name="dash" />
    </button>
  </c-slot>

  Revenue details and charts...

  <c-slot name="footer">
    Last updated: January 2026
  </c-slot>
</c-card>

<!-- Collapsible card -->
<c-card title="Options" collapsed>
  <c-slot name="tools">
    <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse">
      <c-icon name="plus" />
    </button>
  </c-slot>

  Expandable content...
</c-card>
```

**Fill Modes for Cards:**

- `fill="outline"` (default) - Colored border only
- `fill="header"` - Colored header background
- `fill="card"` - Entire card colored

See the [component documentation](docs/components/) for complete API references, examples, and accessibility guidelines.

### Navbar Widgets

Django MVP provides interactive navbar widgets for common application features:

- [User Profile](docs/navbar-widgets.md#user-profile-widget) - Display user info with dropdown menu
- [Notifications](docs/navbar-widgets.md#notifications-widget) - Real-time notification center with badge
- [Messages](docs/navbar-widgets.md#messages-widget) - Message inbox preview with unread count
- [Theme Switcher](docs/navbar-widgets.md#theme-switcher-widget) - Toggle between light/dark/auto themes
- [Custom Widgets](docs/custom-navbar-widgets.md) - Create application-specific widgets (tasks, alerts, shopping cart)
- [Fullscreen Toggle](docs/navbar-widgets.md#fullscreen-widget) - Browser fullscreen mode toggle

Add widgets to the navbar via the `navbar_right` block:

```html
{% extends "mvp/base.html" %}

{% block navbar_right %}
  {# Fullscreen toggle #}
  <c-navbar.fullscreen-widget />

  {# Theme switcher #}
  <c-navbar.theme-switcher-widget />

  {# Messages #}
  <c-navbar.messages-widget
    unread_count="3"
    messages=messages />

  {# Notifications #}
  <c-navbar.notifications-widget
    unread_count="5"
    notifications=notifications />

  {# User profile #}
  <c-navbar.user-profile-widget
    user=request.user
    avatar_url=user.profile.avatar_url
    member_since="Jan 2024" />
{% endblock %}
```

**Custom Widget Example:**

```html
{# templates/navbar_widgets/tasks_widget.html #}
<c-navbar.custom-widget
  icon="check2-square"
  dropdown_id="tasks-dropdown"
  badge_count="{{ tasks_count }}"
  badge_color="danger">

  <c-slot name="children">
    {% for task in tasks %}
      <a href="{{ task.get_absolute_url }}" class="dropdown-item">
        <i class="bi bi-circle{{ task.is_complete|yesno:'-fill,,' }}"></i>
        {{ task.title }}
        <span class="float-end text-muted text-sm">{{ task.due_date|timesince }}</span>
      </a>
    {% endfor %}

    <div class="dropdown-divider"></div>
    <a href="{% url 'tasks:list' %}" class="dropdown-item dropdown-footer">
      See All Tasks
    </a>
  </c-slot>
</c-navbar.custom-widget>
```

See the [navbar widgets documentation](docs/navbar-widgets.md) and [custom widget tutorial](docs/custom-navbar-widgets.md) for complete API references, usage patterns, and accessibility guidelines.

## View Mixins

Python mixins for common patterns:

### SearchMixin

Django admin-style multi-field search:

```python
from mvp.views import SearchMixin
from django.views.generic import ListView

class ProjectListView(SearchMixin, ListView):
    model = Project
    search_fields = ["title", "description", "owner__username"]
```

### OrderMixin

Dropdown-based result ordering:

```python
from mvp.views import OrderMixin
from django.views.generic import ListView

class ProjectListView(OrderMixin, ListView):
    model = Project
    order_fields = {
        "title": "Title A-Z",
        "-title": "Title Z-A",
        "-created": "Newest First",
        "created": "Oldest First",
    }
```

### Form View Mixins

MVPFormView provides automatic form renderer detection and AdminLTE card layout for forms. It intelligently detects django-crispy-forms, django-formset, or falls back to Django's standard rendering.

**Basic Form View:**

```python
from mvp.views import MVPFormView
from myapp.forms import ContactForm

class ContactFormView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/success/"
    page_title = "Contact Us"
```

**Create View (Model Forms):**

```python
from mvp.views import MVPCreateView
from myapp.models import Product

class ProductCreateView(MVPCreateView):
    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock"]
    success_url = "/products/"
    page_title = "Add New Product"
```

**Update View (Edit Forms):**

```python
from mvp.views import MVPUpdateView
from myapp.models import Product

class ProductUpdateView(MVPUpdateView):
    model = Product
    fields = ["name", "slug", "category", "description", "price", "stock"]
    success_url = "/products/"
    page_title = "Edit Product"
```

**Explicit Renderer Override:**

```python
class ContactFormView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/success/"
    page_title = "Contact Us"
    form_renderer = "crispy"  # Override auto-detection: "crispy", "formset", or "django"
```

**Renderer Detection Priority:**

1. `form_renderer` attribute (if set)
2. django-crispy-forms (if installed)
3. django-formset (if installed)
4. Django standard form rendering (fallback)

All form views automatically use AdminLTE card layout with consistent styling, CSRF protection, and responsive design.

## Requirements

- Python 3.12 or 3.13
- Django 5.2 or 6.0 (currently supported Django releases)
- django-cotton 2.3.1+
- django-cotton-bs5 0.9.0+
- django-easy-icons 0.5+
- AdminLTE 4.x (CSS/JS included)

## Design Philosophy

Django MVP provides:

1. **AdminLTE Layout System** - Grid-based app-wrapper structure
2. **Configuration-Driven** - Control via Django settings, not templates
3. **AdminLTE Components Only** - Standard BS5 components in django-cotton-bs5
4. **Production-Ready** - Built for data-centric dashboards and admin interfaces

## Use Cases

Ideal for:

- **Admin dashboards** with metrics and data visualization
- **Data management applications** requiring sophisticated layouts
- **Internal tools** with complex navigation structures
- **Research portals** managing datasets and projects
- **SaaS admin interfaces** with multi-tenant support

## Contributing

Contributions welcome! When adding components:

1. Focus on AdminLTE-specific components only
2. Use `<c-vars />` for default values
3. Include proper ARIA attributes
4. Support AdminLTE's data attributes and JS interactions
5. Add tests for new components

## Theming & Vendor SCSS

Django MVP compiles its styles through `django-compressor` and `django-libsass`.
The AdminLTE 4 SCSS sources are vendored into `mvp/static/adminlte/scss/`.

### Customize Theme Variables

There are two override files — use whichever fits the variable you need:

**`mvp/static/_bootstrap_variables.scss`** — Bootstrap design tokens and plain AdminLTE values:

```scss
// mvp/static/_bootstrap_variables.scss
$primary:   #2c5f2e;
$secondary: #606c38;
```

**`mvp/static/_adminlte_variables.scss`** — AdminLTE variables that reference Bootstrap tokens:

```scss
// mvp/static/_adminlte_variables.scss
$lte-sidebar-color: $primary;  // can safely reference Bootstrap vars here
```

All overrides in `_bootstrap_variables.scss` are imported **before** the vendor defaults,
so any variable you define takes precedence over Bootstrap and AdminLTE's `!default` values.
Overrides in `_adminlte_variables.scss` are injected after Bootstrap vars are resolved.

To provide **app-specific** overrides, create the same-named file in your app's static root
and list your app before `mvp` in `INSTALLED_APPS` (same pattern as Django template overrides).

### Refresh the Vendored SCSS Tree

When a new AdminLTE version is available, run:

```bash
invoke refresh-adminlte-scss
```

This will:

1. Install the latest AdminLTE 4 package with npm (`admin-lte@^4`).
2. Delete the current vendored SCSS tree in full (preventing stale files).
3. Copy the refreshed SCSS sources into `mvp/static/adminlte/scss/`.
4. Patch `adminlte.scss` to inject the `_adminlte_variables` override hook.

After the refresh, commit `package-lock.json` to pin the resolved version for
deterministic builds on CI and other machines.

> **Full docs**: See `specs/018-vendor-adminlte-scss/quickstart.md` for detailed
> override guidance, troubleshooting steps, and first-time timing protocols.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:

- [AdminLTE](https://github.com/colorlibhq/AdminLTE) - The admin dashboard template
- [django-cotton](https://github.com/wrabit/django-cotton) - Component system by @wrabit
- [django-cotton-bs5](https://github.com/SamuelJennings/django-cotton-bs5) - Bootstrap 5 components
- [Bootstrap 5](https://getbootstrap.com/) - CSS framework
