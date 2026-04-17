# Inner Layout System - Quick Start Guide

**Version**: 1.0.0
**Date**: January 19, 2026
**Target Audience**: Django developers using django-mvp

## What is Inner Layout?

The Inner Layout system provides a CSS Grid-based nested layout structure for creating sophisticated page layouts within Django MVP. It gives you four configurable areas:

- **Toolbar** (top) - for page titles, filters, and action buttons
- **Main Content** (center) - your primary page content
- **Footer** (bottom) - for pagination, summaries, and actions
- **Secondary Sidebar** (right) - for properties, filters, or supplementary content

All areas support sticky positioning, independent scrolling, and responsive behavior.

## Installation

Inner layout is included with django-mvp. No additional installation required.

```python
# settings.py
INSTALLED_APPS = [
    'mvp',  # django-mvp already installed
    # ... other apps
]
```

## 5-Minute Tutorial

### 1. Basic Layout (Content Only)

Start with the simplest possible inner layout - just your main content:

```html
<!-- templates/myapp/simple_page.html -->
{% extends "mvp/base.html" %}

{% block content %}
  <c-page>
    <div class="container-fluid p-4">
      <h1>Welcome</h1>
      <p>This is your main content area.</p>
    </div>
  </c-page>
{% endblock %}
```

**Result**: A clean content area that fills the available space.

---

### 2. Add a Toolbar

Add a toolbar for page controls and actions:

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-page :fixed_header="True">
    <c-page.toolbar>
      <div class="d-flex justify-content-between align-items-center p-3 bg-light border-bottom">
        <h2 class="mb-0">My Dashboard</h2>
        <button class="btn btn-primary">Export Data</button>
      </div>
    </c-page.toolbar>

    <div class="container-fluid p-4">
      <!-- Your main content -->
      <table class="table">
        <thead><tr><th>Name</th><th>Email</th></tr></thead>
        <tbody>
          <tr><td>John Doe</td><td>john@example.com</td></tr>
        </tbody>
      </table>
    </div>
  </c-page>
{% endblock %}
```

**Result**: Toolbar sticks to the top when you scroll down (using `toolbar_fixed="True"`).

---

### 3. Add a Footer

Add a footer for pagination or summary information:

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-page :fixed_header="True" :fixed_footer="True">
    <c-page.toolbar>
      <div class="p-3 bg-light border-bottom">
        <h2>User List</h2>
      </div>
    </c-page.toolbar>

    <div class="container-fluid p-4">
      <table class="table">
        <!-- ... table content ... -->
      </table>
    </div>

    <c-page.footer>
      <div class="d-flex justify-content-between align-items-center p-3 bg-light border-top">
        <span>Showing 1-20 of 150 records</span>
        <nav aria-label="Page navigation">
          <ul class="pagination mb-0">
            <li class="page-item active"><a class="page-link" href="#">1</a></li>
            <li class="page-item"><a class="page-link" href="#">2</a></li>
            <li class="page-item"><a class="page-link" href="#">3</a></li>
          </ul>
        </nav>
      </div>
    </c-page.footer>
  </c-page>
{% endblock %}
```

**Result**: Footer sticks to the bottom when scrolling, toolbar stays at top.

---

### 4. Add a Secondary Sidebar

Add a right sidebar for properties or filters:

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-page :fixed_header="True" sidebar_expand="lg">
    <c-page.toolbar>
      <div class="p-3 bg-light border-bottom">
        <h2>Map View</h2>
      </div>
    </c-page.toolbar>

    <!-- Main content -->
    <div id="map" style="height: 100%;">
      <!-- Map component here -->
    </div>

    <c-page.sidebar>
      <div class="p-3">
        <h5>Map Properties</h5>
        <div class="mb-3">
          <label class="form-label">Zoom Level</label>
          <input type="range" class="form-range" min="1" max="20" value="10">
        </div>
        <div class="mb-3">
          <label class="form-label">Map Style</label>
          <select class="form-select">
            <option>Standard</option>
            <option>Satellite</option>
            <option>Terrain</option>
          </select>
        </div>
      </div>
    </c-page.sidebar>
  </c-page>
{% endblock %}
```

**Result**: Map fills main area, properties panel on the right. Sidebar hides on mobile/tablet (below `lg` breakpoint at 992px).

---

### 5. Full Layout with Toggle

Create a complete layout with all areas and a user toggle for the sidebar:

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-page
    :fixed_header="True"
    :fixed_footer="True"
    :sidebar_toggleable="True"
    sidebar_expand="lg"
    class="my-custom-layout">

    <c-page.toolbar collapsible>
      <h2 class="mb-0">Analytics Dashboard</h2>
      <c-slot name="end">
        <c-page.toolbar.widget icon="expand" />
        <button class="btn btn-sm btn-outline-secondary">Filters</button>
        <button class="btn btn-sm btn-primary">Export</button>
      </c-slot>
    </c-page.toolbar>

    <!-- Main content with widgets -->
    <div class="container-fluid p-4">
      <div class="row g-3">
        <div class="col-md-3">
          <c-small-box title="Total Users" value="2,500" icon="users" theme="primary" />
        </div>
        <div class="col-md-3">
          <c-small-box title="Revenue" value="$45,231" icon="dollar-sign" theme="success" />
        </div>
        <div class="col-md-3">
          <c-small-box title="Orders" value="1,234" icon="shopping-cart" theme="info" />
        </div>
        <div class="col-md-3">
          <c-small-box title="Growth" value="23%" icon="trending-up" theme="warning" />
        </div>
      </div>

      <div class="row mt-4">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <h5>Recent Activity</h5>
              <!-- Chart or table here -->
            </div>
          </div>
        </div>
      </div>
    </div>

    <c-page.sidebar collapsed>
      <div class="p-3">
        <h5>Date Range</h5>
        <form>
          <div class="mb-3">
            <label class="form-label">From</label>
            <input type="date" class="form-control">
          </div>
          <div class="mb-3">
            <label class="form-label">To</label>
            <input type="date" class="form-control">
          </div>

          <h5 class="mt-4">Filters</h5>
          <div class="mb-3">
            <label class="form-label">Status</label>
            <select class="form-select">
              <option>All</option>
              <option>Active</option>
              <option>Inactive</option>
            </select>
          </div>

          <button type="submit" class="btn btn-primary w-100">Apply Filters</button>
        </form>
      </div>
    </c-page.sidebar>

    <c-page.footer>
      <div class="d-flex justify-content-between align-items-center p-3">
        <span class="text-muted">Last updated: <strong>2 minutes ago</strong></span>
        <c-slot name="end">
          <button class="btn btn-sm btn-secondary">
            <i class="fas fa-sync-alt"></i> Refresh
          </button>
        </c-slot>
      </div>
    </c-page.footer>
  </c-page>
{% endblock %}
```

**Result**: Full-featured dashboard with toolbar (with toggle button), content area with widgets, filterable sidebar that users can toggle, and an auto-updating footer. The toggle button is rendered automatically when `sidebar_toggleable="True"` and toolbar has `collapsible` attribute.

---

## Configuration Options

### Main Component Attributes (`<c-page>`)

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `fixed_header` | boolean | `False` | Makes toolbar sticky to top when scrolling |
| `fixed_footer` | boolean | `False` | Makes footer sticky to bottom when scrolling |
| `fixed_sidebar` | boolean | `False` | Makes sidebar sticky when scrolling |
| `sidebar_expand` | string | `"lg"` | Bootstrap breakpoint for sidebar visibility (`sm`, `md`, `lg`, `xl`, `xxl`) |
| `class` | string | `""` | Additional CSS classes for the wrapper div |

**Note**: Use `:` prefix for boolean attributes: `:fixed_header="True"`

### Sub-Components

| Component | Description | Attributes |
| --- | --- | --- |
| `<c-page.toolbar>` | Top toolbar area | `collapsible` (boolean) - adds toggle button |
| `<c-page.footer>` | Bottom footer area | None |
| `<c-page.sidebar>` | Right sidebar area | `collapsed` (boolean) - initial collapsed state |
| `<c-page.toolbar.widget>` | Toolbar action widget | `icon` (string) - icon name |

### Slots

| Slot | Component | Description |
| --- | --- | --- |
| Default | All sub-components | Main content of the component |
| `end` | `<c-page.toolbar>`, `<c-page.footer>` | Content positioned at the right end |

---

## Common Patterns

### Data Table with Toolbar and Pagination

```html
<c-page :fixed_header="True" :fixed_footer="True">
  <c-slot name="toolbar">
    <div class="d-flex justify-content-between align-items-center p-3">
      <h2>Users</h2>
      <div>
        <input type="search" class="form-control d-inline-block w-auto me-2" placeholder="Search...">
        <button class="btn btn-primary">Add User</button>
      </div>
    </div>
  </c-slot>

  <c-page.toolbar>
    <h2>Data Table</h2>
  </c-page.toolbar>

  <table class="table table-hover">
    <!-- table rows -->
  </table>

  <c-page.footer>
    <nav class="p-3" aria-label="Table pagination">
      <ul class="pagination justify-content-center mb-0">
        <!-- pagination items -->
      </ul>
    </nav>
  </c-page.footer>
</c-page>
```

### Full-Screen Map with Properties Panel

```html
<c-page :sidebar_toggleable="True" sidebar_expand="lg">
  <c-page.toolbar collapsible>
    <h2>Location Map</h2>
    <c-slot name="end">
      <c-page.toolbar.widget icon="expand" />
    </c-slot>
  </c-page.toolbar>

  <div id="map" class="h-100"></div>

  <c-page.sidebar>
    <div class="p-3">
      <h5>Selected Location</h5>
      <!-- Property details -->
    </div>
  </c-page.sidebar>
</c-page>
```

### Form with Sidebar Help

```html
<c-page sidebar_expand="lg">
  <c-page.toolbar>
    <h2>Account Settings</h2>
  </c-page.toolbar>

  <div class="container-fluid p-4">
    <form>
      <!-- Form fields -->
    </form>
  </div>

  <c-page.sidebar>
    <div class="p-3">
      <h5>Help</h5>
      <p class="text-muted">
        Fill out this form to update your account settings...
      </p>
    </div>
  </c-page.sidebar>
</c-page>
```

### Dashboard Without Sidebar

```html
<c-page :fixed_header="True">
  <c-page.toolbar>
    <h2>Overview</h2>
  </c-page.toolbar>

  <div class="container-fluid p-4">
    <!-- Full-width dashboard widgets -->
  </div>
</c-page>
```

---

## Responsive Behavior

### Default Behavior

- Sidebar hides below 992px (Bootstrap's 'lg' breakpoint)
- Toolbar and footer remain visible on all screen sizes
- Content area automatically adjusts to available space

---

## Tips & Best Practices

### ✅ Do's

1. **Use semantic content**: Put navigation in toolbar, pagination in footer
2. **Keep toolbars/footers reasonably sized**: Under 80px tall
3. **Enable toggle for info-dense sidebars**: Give users control over screen space
4. **Test on mobile**: Ensure content is usable without sidebar
5. **Use consistent styling**: Match toolbar/footer background colors

### ❌ Don'ts

1. **Don't nest inner layouts**: Not supported, causes layout issues
2. **Don't put heavy content in toolbar/footer**: These are sticky, keep them light
3. **Don't rely on sidebar for critical actions**: It hides on mobile
4. **Don't use if you don't need structure**: Simple pages don't need inner layout
5. **Don't override grid CSS**: Use provided attributes instead

---

## Troubleshooting

### Sidebar Not Showing

**Problem**: Sidebar component provided but not visible
**Solution**: Check viewport width is above the breakpoint. Default is `"lg"` (992px). Try using `sidebar_expand="md"` or `sidebar_expand="sm"` for smaller screens.

### Toolbar Not Sticky

**Problem**: Toolbar scrolls with content
**Solution**: Set `:fixed_header="True"` attribute on `<c-page>`

### Toggle Button Missing

**Problem**: Expected toggle button but it's not there
**Solution**: Set `:sidebar_toggleable="True"` on `<c-page>` AND add `collapsible` attribute to `<c-page.toolbar>`

### Content Not Scrolling

**Problem**: Content is cut off, no scrollbar
**Solution**: Inner layout manages scrolling automatically. Ensure the outer AdminLTE layout has proper height setup.

### Sidebar Visibility on Mobile

**Problem**: Sidebar shows/hides at wrong screen size
**Solution**: Default breakpoint is `"lg"` (992px). Use `sidebar_expand="md"` (768px) or `sidebar_expand="xl"` (1200px) as needed.

---

## Advanced Usage

### Dynamic Sidebar Breakpoint

```html
<!-- In your view context -->
context = {
    'is_desktop': True,  # Based on user agent or preference
}
```

```html
<!-- In template -->
{% if is_desktop %}
  <c-page sidebar_expand="lg">
{% else %}
  <c-page sidebar_expand="xl">
{% endif %}
  <c-page.sidebar>
    <!-- Sidebar content -->
  </c-page.sidebar>
</c-page>
```

### Conditional Sidebar Content

```html
<c-mvp.page_layout sidebar_visible="{% if user.is_staff %}true{% else %}false{% endif %}">
  <c-slot name="sidebar">
    <!-- Admin-only sidebar content -->
  </c-slot>
</c-mvp.page_layout>
```

### Custom Toggle Icon

```html
<!-- Override default toggle button with custom styling -->
<style>
  .page-sidebar-toggle {
    /* Custom button styles */
  }
</style>
```

---

## Next Steps

- **Learn more**: Read the [full component documentation](../docs/page-layout.md)
- **See API details**: Check [API contract](contracts/page_layout.md)
- **View examples**: Browse the [Demo App](../../demo/) for complete implementations
- **Get help**: Open an issue on [GitHub](https://github.com/SamuelJennings/django-mvp)

---

## FAQ

**Q: Can I use inner layout without the outer MVP layout?**
A: Yes, but it's designed to work within `mvp/base.html`. Outside that context, you'll need to manage styling yourself.

**Q: Can I have multiple inner layouts on one page?**
A: Technically yes, but not recommended. Each creates a grid container with sticky elements.

**Q: Does the sidebar support left-side positioning?**
A: No, only right-side. For left-side navigation, use the outer layout sidebar.

**Q: Can I change toolbar/footer sticky behavior?**
A: Not via attributes. The sticky behavior is fundamental to the design. If you need different behavior, don't use those slots.

**Q: Is inner layout compatible with HTMX?**
A: Yes! Inner layout is just HTML/CSS. Use HTMX to update content areas dynamically.

**Q: Can I animate the sidebar toggle?**
A: Yes! Add CSS transitions to `.page-sidebar` and `.sidebar-collapsed` class.

---

**Version**: 1.0.0 | **Last Updated**: January 19, 2026
