# Component API Contract: `<c-app>`

**Feature**: 002-layout-configuration
**Date**: 2026-01-13
**Component**: `mvp/templates/cotton/app/index.html`

## Overview

The `<c-app>` Cotton component is the root layout component that renders the HTML body tag with AdminLTE layout classes applied directly. It includes a JavaScript slot for user-provided scripts.

## Component Signature

```django
<c-app
    fixed_sidebar
    fixed_header
    fixed_footer
    sidebar_expand="lg"
    class=""
>
    {{ slot }}

    <c-slot name="javascript">
        <!-- User scripts go here -->
    </c-slot>
</c-app>
```

## Template Structure

**Component renders**:

```html
<body class="bg-body-tertiary [layout classes] [class]">
  <div class="app-wrapper">
    {{ slot }}
  </div>
  {{ javascript }}
</body>
```

## Attributes

### `fixed_sidebar` (boolean, optional, default=false)

**Purpose**: Makes the sidebar sticky during scrolling

**Effect**: Adds `.layout-fixed` class to `<body>` element

**CSS Behavior** (AdminLTE 4):

- Sidebar element gets `position: sticky`
- Sidebar height set to 100vh
- Sidebar content becomes independently scrollable

**Example**:

```django
<c-app fixed_sidebar>
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary layout-fixed sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

---

### `fixed_header` (boolean, optional, default=false)

**Purpose**: Makes the header sticky at top of viewport during scrolling

**Effect**: Adds `.fixed-header` class to `<body>` element

**CSS Behavior** (AdminLTE 4):

- Header element gets `position: sticky` with `top: 0`
- Header remains visible when scrolling down

**Example**:

```django
<c-app fixed_header>
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary fixed-header sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

---

### `fixed_footer` (boolean, optional, default=false)

**Purpose**: Makes the footer sticky at bottom of viewport during scrolling

**Effect**: Adds `.fixed-footer` class to `<body>` element

**CSS Behavior** (AdminLTE 4):

- Footer element gets `position: sticky` with `bottom: 0`
- Footer remains visible when scrolling

**Example**:

```django
<c-app fixed_footer>
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary fixed-footer sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

---

### `sidebar_expand` (string, optional, default="lg")

**Purpose**: Controls Bootstrap breakpoint at which sidebar transitions from off-canvas to visible

**Effect**: Adds `.sidebar-expand-{value}` class to `<body>` element

**Valid Values**:

- `"sm"` - 576px and up
- `"md"` - 768px and up
- `"lg"` - 992px and up (default)
- `"xl"` - 1200px and up
- `"xxl"` - 1400px and up

**CSS Behavior** (AdminLTE 4):

- Below breakpoint: Sidebar is off-canvas (hidden by default, togglable)
- At/above breakpoint: Sidebar is visible

**Independent of Fixed**: The `sidebar_expand` breakpoint is independent of `fixed_sidebar`. You can have a fixed sidebar that's also responsive.

**Example**:

```django
<c-app sidebar_expand="md">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary sidebar-expand-md">
  <div class="app-wrapper">...</div>
</body>
```

---

### `class` (string, optional, default="")

**Purpose**: Additional CSS classes to add to `<body>` element

**Effect**: Appends classes to body class list

**Example**:

```django
<c-app class="custom-theme dark-mode">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary sidebar-expand-lg custom-theme dark-mode">
  <div class="app-wrapper">...</div>
</body>
```

## Attribute Combinations

### Example 1: Fixed Complete Layout

All layout elements remain fixed, creating an "application frame":

```django
<c-app fixed_sidebar fixed_header fixed_footer sidebar_expand="lg">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary layout-fixed fixed-header fixed-footer sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

---

### Example 2: Fixed Sidebar + Header

Common for dashboards where navigation must remain accessible:

```django
<c-app fixed_sidebar fixed_header sidebar_expand="lg">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary layout-fixed fixed-header sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

---

### Example 3: Responsive Fixed Sidebar

Fixed sidebar that appears at tablet breakpoint:

```django
<c-app fixed_sidebar sidebar_expand="md">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary layout-fixed sidebar-expand-md">
  <div class="app-wrapper">...</div>
</body>
```

---

### Example 4: Default (No Fixed Elements)

All elements scroll naturally with content:

```django
<c-app sidebar_expand="lg">
  ...
</c-app>
```

**Generated HTML**:

```html
<body class="bg-body-tertiary sidebar-expand-lg">
  <div class="app-wrapper">...</div>
</body>
```

## Slot Structure

The `<c-app>` component expects content to be provided via the default slot:

```django
<c-app fixed_sidebar>
  <c-app.header>
    <!-- Header content -->
  </c-app.header>

  <c-app.sidebar>
    <!-- Sidebar menu items -->
  </c-app.sidebar>

  <c-app.main>
    <!-- Main page content -->
  </c-app.main>

  <c-app.footer>
    <!-- Footer content -->
  </c-app.footer>
</c-app>
```

## Error Handling

### Invalid Attribute Values

**Scenario**: Invalid `sidebar_expand` value

```django
<c-app sidebar_expand="invalid">
```

**Behavior**: Generates invalid CSS class `.sidebar-expand-invalid` which has no effect. Layout degrades gracefully to default behavior.

**Recommendation**: Document valid values; no runtime validation needed.

---

### Contradictory Boolean Values

**Scenario**: Explicit false value on boolean attribute

```django
<c-app fixed_sidebar="false">
```

**Behavior**: Cotton may interpret "false" string as truthy. Avoid explicit boolean values.

**Recommendation**: Use presence/absence pattern only:

- ✅ `<c-app fixed_sidebar>` (fixed)
- ✅ `<c-app>` (not fixed)
- ❌ `<c-app fixed_sidebar="false">` (ambiguous)

## CSS Dependencies

**Required**: AdminLTE 4 CSS must be loaded in base template

**Location**: Typically loaded via CDN in `base.html`:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/admin-lte@4/dist/css/adminlte.min.css">
```

**Note**: All layout behavior is provided by AdminLTE CSS. This component only generates the appropriate CSS classes.

## Browser Compatibility

Sticky positioning supported in:

- Chrome 56+
- Firefox 59+
- Safari 13+
- Edge 16+

All modern browsers support the CSS used by AdminLTE 4.

## Testing Contract

### Component Rendering Tests

Test that attributes correctly generate CSS classes:

```python
from django_cotton import cotton_render
from django.template import RequestContext
import pytest

def test_fixed_sidebar_adds_layout_fixed_class(rf):
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {"fixed_sidebar": True})
    )
    assert 'class="bg-body-tertiary layout-fixed' in html

def test_fixed_header_adds_fixed_header_class(rf):
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {"fixed_header": True})
    )
    assert 'fixed-header' in html

def test_all_fixed_attributes_combine(rf):
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {
            "fixed_sidebar": True,
            "fixed_header": True,
            "fixed_footer": True,
        })
    )
    assert 'layout-fixed' in html
    assert 'fixed-header' in html
    assert 'fixed-footer' in html

def test_sidebar_expand_breakpoint(rf):
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {"sidebar_expand": "md"})
    )
    assert 'sidebar-expand-md' in html

def test_default_sidebar_expand_is_lg(rf):
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {})
    )
    assert 'sidebar-expand-lg' in html
```

## Change Log

**2026-01-06**: Initial contract definition based on existing implementation in `mvp/templates/cotton/app/index.html`

## Related Documentation

- [AdminLTE 4 Layout Behavior Analysis](../../../docs/adminlte-4-layout-behavior-analysis.md)
- [data-model.md](./data-model.md) - Layout configuration entities
- [quickstart.md](./quickstart.md) - Usage examples and developer guide
