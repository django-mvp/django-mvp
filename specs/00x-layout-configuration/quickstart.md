# Quickstart Guide: AdminLTE Layout Configuration

**Feature**: 002-layout-configuration
**Date**: January 13, 2026
**Audience**: Django developers using django-mvp

## Overview

Configure AdminLTE layout options (fixed sidebar, header, footer) using simple Cotton component attributes. The component now includes the body tag with layout classes applied directly.

## Prerequisites

- Django project with django-mvp installed
- Basic familiarity with Cotton components

## Usage

### Basic Layout Configuration

Use boolean attributes on `<c-app>` to control fixed positioning:

```html
<!-- Fixed sidebar only -->
<c-app fixed_sidebar>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}{% endblock %}
  </c-app.main>
</c-app>

<!-- Fixed header and sidebar -->
<c-app fixed_sidebar fixed_header>
  <!-- content -->
</c-app>

<!-- All fixed elements -->
<c-app fixed_sidebar fixed_header fixed_footer>
  <!-- content -->
</c-app>
```

### JavaScript Integration

Add custom JavaScript using the `javascript` slot:

```html
<c-app fixed_sidebar>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}{% endblock %}
  </c-app.main>

  <c-slot name="javascript">
    <script>
      console.log('Custom JavaScript loaded');
      // Your AdminLTE customizations
    </script>
  </c-slot>
</c-app>
```

## Layout Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `fixed_sidebar` | boolean | `false` | Sidebar stays visible during scroll |
| `fixed_header` | boolean | `false` | Header stays at top during scroll |
| `fixed_footer` | boolean | `false` | Footer stays at bottom during scroll |
| `sidebar_expand` | string | `"lg"` | Breakpoint: `sm`, `md`, `lg`, `xl`, `xxl` |
| `class` | string | `""` | Additional CSS classes for body |

## Common Examples

**Data Dashboard** (fixed navigation):

```html
<c-app fixed_sidebar fixed_header>
  <!-- Navigation stays visible for easy access -->
</c-app>
```

**Full-screen Report** (maximum content space):

```html
<c-app>
  <!-- All elements scroll naturally -->
</c-app>
```

**Mobile-responsive Sidebar**:

```html
<c-app sidebar_expand="md">
  <!-- Sidebar hidden on mobile, visible on medium+ screens -->
</c-app>
```

That's it! The layout classes are automatically applied to the body tag based on your component attributes.

## Overview

Configure AdminLTE 4 layout variations using boolean attributes on the `<c-app>` Cotton component to control which elements remain fixed during scrolling.

## Prerequisites

- Django project with `django-mvp` installed
- Base template extending `mvp/base.html` or using `<c-app>` component

## Basic Usage

### Default Layout (No Fixed Elements)

```django-html
{% extends "mvp/base.html" %}

{% block body %}
<c-app>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Welcome</h1>
      <p>All layout elements scroll with content.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
{% endblock %}
```

**Result**: Header, sidebar, and footer scroll naturally with page content.

---

### Fixed Sidebar

```django-html
<c-app fixed_sidebar>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Dashboard</h1>
      <p>Sidebar stays visible when scrolling.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
```

**Result**: Sidebar remains fixed with 100vh height and scrollable content. Header and footer scroll with content.

**CSS Classes Added**: `layout-fixed`

---

### Fixed Header

```django-html
<c-app fixed_header>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Reports</h1>
      <p>Header stays at top when scrolling.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
```

**Result**: Header remains fixed at top of viewport. Sidebar and footer scroll with content.

**CSS Classes Added**: `fixed-header`

---

### Fixed Footer

```django-html
<c-app fixed_footer>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Forms</h1>
      <p>Footer stays at bottom when scrolling.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
```

**Result**: Footer remains fixed at bottom of viewport. Header and sidebar scroll with content.

**CSS Classes Added**: `fixed-footer`

---

### Fixed Complete (All Elements Fixed)

```django-html
<c-app fixed_sidebar fixed_header fixed_footer>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Application</h1>
      <p>Only main content scrolls - all chrome is fixed.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
```

**Result**: Entire application frame stays fixed. Only the content area (`.app-content`) scrolls.

**CSS Classes Added**: `layout-fixed fixed-header fixed-footer`

---

## Advanced Usage

### Combining Fixed Elements

You can combine any subset of fixed attributes:

```django-html
<!-- Fixed sidebar + header (common for dashboards) -->
<c-app fixed_sidebar fixed_header>
  ...
</c-app>

<!-- Fixed header + footer (sandwich content) -->
<c-app fixed_header fixed_footer>
  ...
</c-app>
```

---

### Responsive Sidebar Expansion

Control when sidebar is visible vs off-canvas:

```django-html
<!-- Sidebar visible on medium screens and up -->
<c-app fixed_sidebar sidebar_expand="md">
  ...
</c-app>

<!-- Sidebar visible on extra-large screens only -->
<c-app fixed_sidebar sidebar_expand="xl">
  ...
</c-app>
```

**Breakpoint Values**: `sm`, `md`, `lg` (default), `xl`, `xxl`

**Note**: `sidebar_expand` and `fixed_sidebar` are independent:

- `sidebar_expand` controls responsive visibility
- `fixed_sidebar` controls sticky positioning when visible

---

### Per-Page Layout Override

Define layout in base template, override in specific pages:

**base.html**:

```django-html
{% extends "mvp/base.html" %}

{% block body %}
<c-app fixed_sidebar fixed_header>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}{% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
{% endblock %}
```

**fullscreen_report.html**:

```django-html
{% extends "base.html" %}

{# Override to remove fixed elements #}
{% block body %}
<c-app>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>
    {% block content %}
      <h1>Full Screen Report</h1>
      <p>No fixed elements for maximum content space.</p>
    {% endblock %}
  </c-app.main>
  <c-app.footer />
</c-app>
{% endblock %}
```

---

## CSS Classes Reference

| Attribute | Body CSS Class | AdminLTE Behavior |
|-----------|----------------|-------------------|
| `fixed_sidebar` | `.layout-fixed` | Sidebar `position: sticky`, 100vh height |
| `fixed_header` | `.fixed-header` | Header `position: sticky` at top |
| `fixed_footer` | `.fixed-footer` | Footer `position: sticky` at bottom |

## Common Patterns

### Dashboard (Fixed Sidebar + Header)

Best for data-heavy applications requiring constant navigation access:

```django-html
<c-app fixed_sidebar fixed_header sidebar_expand="lg">
  ...
</c-app>
```

### Application Frame (Fixed Complete)

Best for application-like experiences mimicking desktop software:

```django-html
<c-app fixed_sidebar fixed_header fixed_footer>
  ...
</c-app>
```

### Content-Focused (Fixed Header Only)

Best for content sites where header search/navigation should remain accessible:

```django-html
<c-app fixed_header>
  ...
</c-app>
```

### Simple Site (No Fixed Elements)

Best for traditional scrolling websites with simple navigation:

```django-html
<c-app>
  ...
</c-app>
```

## Troubleshooting

### Sidebar not staying fixed on mobile

**Problem**: Fixed sidebar blocks content on small screens.

**Solution**: Use `sidebar_expand` to control when sidebar is visible:

```django-html
<c-app fixed_sidebar sidebar_expand="lg">
```

### Layout elements overlapping

**Problem**: Fixed elements covering content.

**Solution**: This is typically an AdminLTE CSS issue. Verify AdminLTE 4 CSS is properly loaded in your base template.

### Classes not appearing on body element

**Problem**: Custom CSS classes need to be added to body.

**Solution**: Use the `class` attribute:

```django-html
<c-app class="custom-theme dark-mode" fixed_sidebar>
```

## Testing Your Layout (Updated 2026-01-07)

### Interactive Layout Demo Page

Django-mvp provides a single unified interactive demo page for testing all layout configurations:

**URL**:

```http
http://localhost:8000/layout/
```

**Features**:

- **Split Layout Design**: Main content area on left, configuration sidebar on right
- **Fixed Properties**: Checkboxes to toggle `fixed_sidebar`, `fixed_header`, `fixed_footer`
- **Responsive Breakpoint**: Dropdown selector for all breakpoints (sm, md, lg, xl, xxl)
- **Form-Based Testing**: Form submits via GET with query parameters for bookmarkable configurations
- **Long-Form Content**: 2-3 viewport heights of scrollable content to demonstrate fixed element behavior
- **Dummy Sidebar Items**: 12-15 menu items to test independent sidebar scrolling
- **Visual Indicators**: Current configuration display showing applied CSS classes and active options
- **Helper Text**: Instructions explaining what to test and how to interact with the demo
- **Menu Integration**: Accessible via "Layout Demo" link in sidebar (below Dashboard)

**Example Configurations**:

```http
# Default layout (no query parameters)
http://localhost:8000/layout/

# Fixed sidebar only
http://localhost:8000/layout/?fixed_sidebar=on

# Fixed sidebar + header
http://localhost:8000/layout/?fixed_sidebar=on&fixed_header=on

# Fixed complete layout
http://localhost:8000/layout/?fixed_sidebar=on&fixed_header=on&fixed_footer=on

# Test responsive breakpoint
http://localhost:8000/layout/?breakpoint=md

# Combined configuration
http://localhost:8000/layout/?fixed_sidebar=on&fixed_header=on&breakpoint=xl
```

### Extensibility

The `/layout/` demo page is designed to be extended by future feature specs. When additional layout options are added (e.g., sidebar mini mode), they will be integrated into this same page rather than creating separate demo pages.

### Manual Testing Checklist

1. **Scroll Test**: Scroll down a long page - verify fixed elements stay in place
2. **Content Overflow**: Verify main content area scrolls independently
3. **Sidebar Scrolling**: If sidebar has many items, verify it scrolls independently
4. **Responsive Test**: Resize browser window to test breakpoint transitions
5. **Mobile Test**: Test on actual mobile device for off-canvas behavior
6. **Combination Test**: Try different combinations of fixed attributes
7. **Browser Test**: Verify behavior in Chrome, Firefox, Safari, Edge

## Next Steps

- Explore [AdminLTE 4 Layout Behavior Analysis](../../../docs/adminlte-4-layout-behavior-analysis.md) for detailed layout documentation
- Learn about sidebar mini functionality (future spec)
- Customize theme colors and branding
