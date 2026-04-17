---
name: demo-views
description: Guide for creating demo views in the django-mvp Demo App. Use when adding new demo pages to showcase components, layouts, or features — covers view creation, template structure, URL wiring, and sidebar menu registration. Emphasizes single configurable view classes with .as_view() attribute overrides instead of duplicating views.
---

# Creating Demo Views for the Demo App

The `demo/` app demonstrates django-mvp features. Each demo page follows a consistent pattern: one configurable view class, a template extending `base.html`, a URL pattern (with optional `.as_view()` overrides), and a sidebar menu entry.

## File Locations

| File | Purpose |
|---|---|
| `demo/views.py` | View classes |
| `demo/urls.py` | URL patterns |
| `demo/menus.py` | Sidebar menu items |
| `demo/templates/demo/<name>.html` | Page templates |
| `demo/templates/base.html` | Project-level base (extends `mvp/base.html`) |

## Step 1: Create the View

### Always include LayoutConfigMixin

Every demo view must inherit `LayoutConfigMixin` first — it reads query parameters for interactive layout configuration (fixed sidebar/header/footer, breakpoints, etc.):

```python
from django.views.generic import TemplateView
from demo.views import LayoutConfigMixin

class MyDemoView(LayoutConfigMixin, TemplateView):
    template_name = "demo/my_demo.html"
```

### One View, Many Configurations — Use .as_view() Overrides

**Do NOT create separate view classes for minor variations.** Instead, define one view with configurable class attributes and override them in `urls.py`:

```python
# views.py — ONE view class
class WidgetDemoView(LayoutConfigMixin, TemplateView):
    template_name = "demo/widget_demo.html"
    variant = "default"
    show_icons = True
```

```python
# urls.py — multiple URL patterns with .as_view() overrides
urlpatterns = [
    path("widgets/", WidgetDemoView.as_view(), name="widget_demo"),
    path("widgets/compact/", WidgetDemoView.as_view(variant="compact"), name="widget_demo_compact"),
    path("widgets/no-icons/", WidgetDemoView.as_view(show_icons=False), name="widget_demo_no_icons"),
]
```

Only create a separate view class when it needs **different methods or significantly different behavior**.

### View Patterns by Django Generic View Type

**TemplateView** — simplest; for static demos or component showcases:

```python
class MyDemoView(LayoutConfigMixin, TemplateView):
    template_name = "demo/my_demo.html"
```

**ListView** — for list/grid demos; combine with `MVPListViewMixin` and `PageModifierMixin`:

```python
from mvp.views import MVPListViewMixin, PageModifierMixin

class MyListDemo(LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, ListView):
    model = MyModel
    template_name = "mvp/list_view.html"
    list_item_template = "cards/my_card.html"
    paginate_by = 12
    grid = {"cols": 1, "md": 2}          # Override via .as_view(grid={...})
    search_fields = ["name", "description"]  # Optional
    order_by = [("name", "Name (A-Z)"), ("-name", "Name (Z-A)")]  # Optional
```

**CreateView / FormView** — for form demos:

```python
class MyFormDemo(LayoutConfigMixin, CreateView):
    model = MyModel
    fields = ["name", "description"]
    template_name = "mvp/form_view.html"
    extra_context = {"page_title": "My Form Demo"}
```

**FilterView** — for filterable list demos (django-filter):

```python
from django_filters.views import FilterView

class MyFilterDemo(LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, FilterView):
    model = MyModel
    template_name = "mvp/list_view.html"
    list_item_template = "cards/my_card.html"
    filterset_fields = ["category", "status"]
```

**SingleTableView** — for django-tables2 demos:

```python
from django_tables2 import SingleTableView

class MyTableDemo(LayoutConfigMixin, SingleTableView):
    model = MyModel
    table_class = MyTable
    template_name = "demo/my_table.html"
    paginate_by = 25
```

### Adding Extra Context

Use `get_context_data` when the template needs dynamic data. Always call `super()`:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["sample_items"] = [...]
    return context
```

For static context, prefer `extra_context`:

```python
class MyDemo(LayoutConfigMixin, TemplateView):
    template_name = "demo/my_demo.html"
    extra_context = {"page_title": "My Demo"}
```

## Step 2: Create the Template

Templates live in `demo/templates/demo/` and extend `base.html`.

### Block Hierarchy

```
base.html (extends mvp/base.html, overrides "app")
├── navbar_widgets     — navbar widget components (top-right)
├── main               — wraps <c-page>; override to replace entire inner layout
│   ├── toolbar
│   │   └── toolbar_content
│   │       ├── breadcrumbs  — add breadcrumb items
│   │       └── toolbar_widgets — toolbar actions (right side)
│   ├── content        — main page content ← MOST COMMON OVERRIDE
│   └── footer         — page footer
├── app_footer         — app-level footer
└── extra_js           — additional scripts
```

### Typical Template (override breadcrumbs + content)

Most demo templates only need two blocks:

```django
{% extends "base.html" %}

{% block breadcrumbs %}
  <c-breadcrumbs.item text="My Demo" />
{% endblock breadcrumbs %}

{% block content %}
  <div class="container-fluid">
    <h2>My Demo</h2>
    <!-- demo content here -->
  </div>
{% endblock content %}
```

### When to Override Other Blocks

| Block | Override when... |
|---|---|
| `breadcrumbs` | Always — add the page breadcrumb |
| `content` | Always — the main demo content |
| `toolbar_widgets` | Page needs action buttons in the toolbar |
| `footer` | Page needs a custom footer or no footer |
| `main` | Page needs to replace the entire `<c-page>` structure (rare) |
| `app` (from mvp/base.html) | Page needs to reconfigure `<c-app>` props like breakpoints (rare) |
| `extra_js` | Page needs additional JavaScript |
| `navbar_widgets` | Page needs custom navbar widgets (rare — usually keep defaults) |

### Template with Toolbar Widgets

```django
{% extends "base.html" %}

{% block breadcrumbs %}
  <c-breadcrumbs.item text="My Demo" />
{% endblock breadcrumbs %}

{% block toolbar_widgets %}
  <button class="btn btn-sm btn-primary">Action</button>
{% endblock toolbar_widgets %}

{% block content %}
  <div class="container-fluid">
    <!-- content -->
  </div>
{% endblock content %}
```

## Step 3: Add the URL Pattern

In `demo/urls.py`, add the path. Import only what's needed:

```python
from .views import MyDemoView

urlpatterns = [
    # ... existing patterns ...
    path("my-demo/", MyDemoView.as_view(), name="my_demo"),
]
```

For configuration variants, override attributes via `.as_view()`:

```python
urlpatterns = [
    path("my-demo/", MyDemoView.as_view(), name="my_demo"),
    path("my-demo/alt/", MyDemoView.as_view(variant="alt"), name="my_demo_alt"),
]
```

## Step 4: Add the Sidebar Menu Entry

In `demo/menus.py`, add items using `AppMenu.extend()` or mutate existing groups. Read the `sidebar-menu` skill for full reference.

### Adding a standalone menu item

```python
AppMenu.extend([
    MenuItem(
        name="my_demo",
        view_name="my_demo",
        extra_context={"label": "My Demo", "icon": "star"},
    ),
])
```

### Adding to an existing MenuGroup

Use `AppMenu.get()` to find a group and add children:

```python
group = AppMenu.get("list_views")
if group:
    group.add(MenuItem(
        name="my_list_variant",
        view_name="my_list_variant",
        extra_context={"label": "My Variant", "icon": "circle"},
    ))
```

### Creating a new MenuGroup for related demos

```python
MenuGroup(
    name="my_demos_section",
    extra_context={"label": "MY DEMOS"},
    children=[
        MenuItem(name="demo_a", view_name="demo_a",
                 extra_context={"label": "Demo A", "icon": "circle"}),
        MenuItem(name="demo_b", view_name="demo_b",
                 extra_context={"label": "Demo B", "icon": "circle"}),
    ],
)
```

## Checklist

Before considering a demo view complete, verify:

1. ✅ View inherits `LayoutConfigMixin` as first parent
2. ✅ Only ONE view class exists per feature (variants use `.as_view()` overrides)
3. ✅ Template extends `base.html` and overrides `breadcrumbs` + `content` at minimum
4. ✅ URL pattern added in `demo/urls.py` with a named route
5. ✅ Sidebar menu entry added in `demo/menus.py` (standalone or within a group)
6. ✅ View name in `MenuItem` matches the URL pattern name
