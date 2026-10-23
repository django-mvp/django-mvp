---
name: demo-views
description: Guide for creating demo views in the django-mvp Demo App. Use when adding new demo pages to showcase components, layouts, or features — covers view creation, template structure, URL wiring, and sidebar menu registration. Emphasizes single configurable view classes with .as_view() attribute overrides instead of duplicating views.
---

# Creating Demo Views for the Demo App

The `demo/` app demonstrates django-mvp features. Each demo page follows a consistent pattern: one configurable view class, a template extending `page_view.html`, a URL pattern (with optional `.as_view()` overrides), and a sidebar menu entry.

## File Locations

| File | Purpose |
|---|---|
| `demo/views.py` | View classes |
| `demo/urls.py` | URL patterns |
| `demo/menus.py` | Sidebar menu items |
| `demo/templates/demo/<name>.html` | Page templates |
| `demo/templates/base.html` | Project-level base (extends `mvp/base.html`) |

## Step 1: Create the View

### Static pages: subclass DemoTemplateView

A page that shows components or layout, with no model behind it, uses `DemoTemplateView` from `demo/views.py`. It is an `MVPTemplateView` that looks for the template under `demo/` first and puts a Home crumb ahead of the page title:

```python
class MyDemoView(DemoTemplateView):
    template_name = "my_demo.html"
    page_title = "My Demo"
```

### One View, Many Configurations — Use .as_view() Overrides

**Do NOT create separate view classes for minor variations.** Define one view with configurable class attributes and pass the differences to `.as_view()`. Most static pages in the demo need no class of their own at all:

```python
# views.py
theme_customization_demo = DemoTemplateView.as_view(
    template_name="theme_customization.html",
    page_title="Theme Customization",
    extra_context={"themes": DEMO_THEMES},
)
```

```python
# urls.py — one class, several URLs
urlpatterns = [
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/many/", ProductManyPagesListView.as_view(), name="product-list-many"),
]
```

Only create a separate view class when it needs **different methods or significantly different behavior**.

### View Patterns by Page Type

Use the package's own views, so the demo shows what a project gets:

| Page | Base class | Template |
|---|---|---|
| Static page | `DemoTemplateView` | your own, extending `page_view.html` |
| List or grid | `MVPListView`, with a filterset for its search, sort and filters | `list_view.html` (the default) |
| Table | `MVPTableView` from `mvp.integrations.django_tables.views` | `table_view.html` (the default) |
| Create, update, form | `MVPCreateView`, `MVPUpdateView`, `MVPFormView` | `form_view.html` (the default) |
| Detail | `MVPDetailView` | `detail_view.html` (the default) |
| Delete | `MVPDeleteView` | `delete_view.html` (the default) |

```python
import django_filters

from mvp.filters import SearchFilter
from mvp.views.list import MVPListView


class MyFilter(django_filters.FilterSet):
    q = SearchFilter(fields=["name", "description"])

    class Meta:
        model = MyModel
        fields = ["category", "status"]


class MyFilterDemo(MVPListView):
    model = MyModel
    filterset_class = MyFilter
    page_lead = "Everything in the catalogue."
```

The page's title, lead and info text come from `page_title`, `page_lead` and `page_info` on the view.

### Adding Extra Context

Use `get_context_data` when the template needs dynamic data. Always call `super()`:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["sample_items"] = [...]
    return context
```

For static context, pass `extra_context` to `.as_view()` or set it on the class.

## Step 2: Create the Template

Templates live in `demo/templates/demo/`. A static page extends `page_view.html`, which draws the page title and leaves the body to you.

### Block Hierarchy

```
page_view.html (extends base.html → mvp/base.html)
├── title              — the browser tab title; defaults to the page title
└── content            — wraps <c-mvp.page>
    ├── page.header        — above the title; empty by default
    ├── page.content-wrapper
    │   ├── page.title         — the title row
    │   │   └── page.actions   — buttons at the end of the title row
    │   └── page.content       — the page body ← MOST COMMON OVERRIDE
    └── page.footer        — the toolbar at the foot of the page
```

The shell's own blocks (`app.navbar.end`, `app.sidebar`, `app.footer`, `extra_js` and the rest) come from `mvp/base.html`. The breadcrumb trail is drawn in the header from the view's `get_breadcrumbs()`, not from a template block.

### Typical Template (override page.content)

```django
{% extends "page_view.html" %}

{% block page.content %}
  <c-mvp.text muted>Some words about the demo.</c-mvp.text>
  <!-- demo content here -->
{% endblock page.content %}
```

### When to Override Other Blocks

| Block | Override when... |
|---|---|
| `page.content` | Always — the main demo content |
| `page.actions` | Page needs buttons in the title row |
| `page.footer` | Page needs content in the bottom toolbar |
| `page.title` | Page needs to replace the title row (rare) |
| `content` | Page needs to replace the entire `<c-mvp.page>` structure (rare) |
| `app` (from mvp/base.html) | Page needs to reconfigure the shell, such as its breakpoint (rare). Wrap `{{ block.super }}` in `{% with %}` rather than writing `<c-app>` by hand |
| `extra_js` | Page needs additional JavaScript |
| `app.navbar.end` | Page needs extra navbar widgets (rare — the defaults come from `MVP_CONFIG["layout"]["navbar"]["end"]`) |

### Template with Title-Row Actions

```django
{% extends "page_view.html" %}

{% block page.actions %}
  <c-button text="Action" variant="primary" size="sm" />
{% endblock page.actions %}

{% block page.content %}
  <!-- content -->
{% endblock page.content %}
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

1. ✅ View is `DemoTemplateView` or one of the package's own views, with `page_title` set
2. ✅ Only ONE view class exists per feature (variants use `.as_view()` overrides)
3. ✅ A static page's template extends `page_view.html` and fills `page.content`
4. ✅ URL pattern added in `demo/urls.py` with a named route
5. ✅ Sidebar menu entry added in `demo/menus.py` (standalone or within a group)
6. ✅ View name in `MenuItem` matches the URL pattern name
