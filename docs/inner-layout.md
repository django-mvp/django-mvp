# Inner Layout System

The Inner Layout System provides a flexible, grid-based layout structure for creating sophisticated page layouts within Django MVP's main content area. It's inspired by AdminLTE 4's outer app-wrapper pattern but designed specifically for inner page content.

## Overview

The inner layout uses CSS Grid to create a consistent structure with four optional areas:

- **Toolbar** - Top area for page titles, actions, filters, and breadcrumbs
- **Main Content** - Center area that auto-fills available space
- **Footer** - Bottom area for pagination, summaries, and actions
- **Sidebar** - Right-side panel for filters, properties, or navigation

## Features

- ✨ **CSS Grid Layout** - Modern, flexible layout with named grid areas
- 📌 **Sticky Positioning** - Opt-in sticky toolbar, footer, and sidebar
- 📱 **Responsive Behavior** - Configurable breakpoints for sidebar auto-hide
- 🔄 **Sidebar Toggle** - Built-in collapse/expand functionality with sessionStorage persistence
- ♿ **Accessible** - Full ARIA support and keyboard navigation
- 🎨 **Customizable** - Template-driven configuration with minimal CSS required

## Basic Usage

### Simple Layout (Content Only)

```django
<c-page>
    <h1>Page Title</h1>
    <p>Your main content here...</p>
</c-page>
```

### Layout with Toolbar

```django
<c-page fixed_header>
    <c-page.toolbar>
        <h2>Dashboard</h2>
        <c-slot name="end">
            <button class="btn btn-primary">New Item</button>
        </c-slot>
    </c-page.toolbar>

    <div class="container-fluid">
        <p>Your main content here...</p>
    </div>
</c-page>
```

### Layout with Sidebar

```django
<c-page sidebar_expand="lg">
    <c-page.toolbar>
        <h2>Products</h2>
    </c-page.toolbar>

    <div class="row">
        <div class="col-12">
            <!-- Product list content -->
        </div>
    </div>

    <c-page.sidebar>
        <h6>Filters</h6>
        <form>
            <!-- Filter controls -->
        </form>
    </c-page.sidebar>
</c-page>
```

### Full Layout (All Areas)

```django
<c-page fixed_header
         fixed_footer
         fixed_sidebar
         sidebar_expand="lg"
         class="custom-layout">

    <c-page.toolbar>
        <h2>Data Table</h2>
        <c-slot name="end">
            <button class="btn btn-primary">Export</button>
        </c-slot>
    </c-page.toolbar>

    <div class="table-responsive">
        <!-- Your data table -->
    </div>

    <c-page.footer>
        <span>Showing 1-20 of 100</span>
        <c-slot name="end">
            <!-- Pagination controls -->
        </c-slot>
    </c-page.footer>

    <c-page.sidebar>
        <h6>Table Settings</h6>
        <!-- Column visibility, filters, etc. -->
    </c-page.sidebar>
</c-page>
```

## Configuration Attributes

### Main Component (`<c-page>`)

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `fixed_header` | boolean | `False` | Enable sticky positioning for toolbar |
| `fixed_footer` | boolean | `False` | Enable sticky positioning for footer |
| `fixed_sidebar` | boolean | `False` | Enable sticky positioning for sidebar |
| `sidebar_expand` | string | `"lg"` | Bootstrap breakpoint for responsive sidebar (`sm`, `md`, `lg`, `xl`, `xxl`) |
| `class` | string | `""` | Additional CSS classes for custom styling |

### Toolbar Component (`<c-page.toolbar>`)

| Slot | Description |
|------|-------------|
| (default) | Left-aligned content (title, breadcrumbs) |
| `end` | Right-aligned content (actions, buttons) |

**Example:**

```django
<c-page.toolbar>
    <h2>Dashboard</h2>
    <c-slot name="end">
        <button class="btn btn-primary">New Item</button>
    </c-slot>
</c-page.toolbar>
```

### Footer Component (`<c-page.footer>`)

| Slot | Description |
|------|-------------|
| (default) | Left-aligned content (status, counts) |
| `end` | Right-aligned content (pagination, actions) |

**Example:**

```django
<c-page.footer>
    <span>Showing 1-20 of 100</span>
    <c-slot name="end">
        <nav aria-label="pagination">
            <!-- Pagination -->
        </nav>
    </c-slot>
</c-page.footer>
```

### Sidebar Component (`<c-page.sidebar>`)

The sidebar accepts any content in its default slot.

**Example:**

```django
<c-page.sidebar>
    <h6>Filters</h6>
    <form>
        <div class="mb-3">
            <label>Status</label>
            <select class="form-select">
                <option>All</option>
                <option>Active</option>
                <option>Inactive</option>
            </select>
        </div>
    </form>
</c-page.sidebar>
```

## Sticky Positioning

Sticky positioning keeps elements visible while scrolling. Enable it per element:

```django
<c-page fixed_header fixed_footer fixed_sidebar>
    <!-- Content -->
</c-page>
```

- **Sticky Toolbar** - Remains at top while scrolling content
- **Sticky Footer** - Remains at bottom while scrolling content
- **Sticky Sidebar** - Remains visible while scrolling content

## Sidebar Toggle

The sidebar includes built-in toggle functionality when a sidebar is present:

```django
<c-page sidebar_expand="lg">
    <c-page.toolbar>
        <h2>My Page</h2>
    </c-page.toolbar>

    <div>Main content</div>

    <c-page.sidebar>
        <h6>Sidebar</h6>
    </c-page.sidebar>
</c-page>
```

**Features:**

- Toggle button automatically appears in toolbar when sidebar is present
- State persists across page reloads using sessionStorage
- Smooth collapse/expand animation
- Full keyboard accessibility (Enter/Space to toggle, Escape to close)
- ARIA attributes updated automatically

## Responsive Behavior

The sidebar automatically adapts to smaller screens based on the configured breakpoint:

```django
<c-page sidebar_expand="md">
    <!-- Below 768px (md), sidebar becomes an overlay -->
</c-page>
```

**Breakpoints:**

- `sm` - 576px
- `md` - 768px (default for mobile)
- `lg` - 992px (default)
- `xl` - 1200px
- `xxl` - 1400px

**Below Breakpoint:**

- Sidebar becomes a fixed overlay
- Backdrop appears behind sidebar
- Click backdrop or press Escape to close
- Toggle button allows opening/closing

## Integration with Outer Layout

The inner layout works seamlessly within Django MVP's outer AdminLTE layout:

```django
{% extends "mvp/base.html" %}

{% block content %}
    <c-page fixed_header>
        <c-page.toolbar>
            <h2>My Page</h2>
        </c-page.toolbar>

        <div class="container-fluid">
            <!-- Your content -->
        </div>
    </c-page>
{% endblock %}
```

The inner layout's toolbar is separate from the outer app-header, allowing for page-specific actions and navigation.

## Multiple Inner Layouts

You can use multiple inner layouts on the same page with independent configurations:

```django
{% block content %}
    <div class="row">
        <div class="col-lg-6">
            <c-page fixed_header>
                <c-page.toolbar>
                    <h3>Section 1</h3>
                </c-page.toolbar>
                <div>Content 1</div>
            </c-page>
        </div>

        <div class="col-lg-6">
            <c-page sidebar_expand="lg">
                <c-page.toolbar>
                    <h3>Section 2</h3>
                </c-page.toolbar>
                <div>Content 2</div>
                <c-page.sidebar>
                    <h6>Options</h6>
                </c-page.sidebar>
            </c-page>
        </div>
    </div>
{% endblock %}
```

Each layout maintains its own toggle state and configuration independently.

## Customization

### Custom CSS Classes

Add custom styling using the `class` attribute:

```django
<c-page class="my-custom-layout elevated-shadow">
    <!-- Content -->
</c-page>
```

### Custom Styles

Target the inner layout structure with CSS:

```css
/* Custom toolbar styling */
.page-layout.my-custom-layout .page-toolbar {
    background: linear-gradient(to right, #667eea 0%, #764ba2 100%);
    color: white;
}

/* Custom sidebar width */
.page-layout.wide-sidebar .page-sidebar {
    width: 400px;
}

/* Custom animations */
.page-layout.fancy-transitions .page-sidebar {
    transition: width 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

## Accessibility

The inner layout is fully accessible:

- **Semantic HTML** - Uses `<nav>`, `<aside>`, `<main>` elements
- **ARIA Attributes** - Proper roles and labels on all interactive elements
- **Keyboard Navigation** - Toggle button accessible via Tab, activated with Enter/Space
- **Screen Reader Support** - Meaningful labels and state announcements
- **Focus Management** - Visible focus indicators on all interactive elements
- **Reduced Motion** - Respects `prefers-reduced-motion` preference

## Troubleshooting

### Sidebar Toggle Not Working

**Problem:** Toggle button doesn't appear or doesn't work.

**Solution:**

1. Verify the sidebar slot is present (toggle button appears automatically)
2. Check that JavaScript is loaded (check browser console for errors)
3. Ensure `page-layout.js` is included in your template
4. Check browser console for errors

### Sticky Elements Not Sticking

**Problem:** Toolbar/footer/sidebar scroll with content instead of staying fixed.

**Solution:**

1. Verify the fixed attributes are present (e.g., `fixed_header`, not `fixed_header="True"`)
2. Check that the parent container has a defined height
3. Ensure there's enough content to scroll
4. Check CSS specificity - your custom styles may be overriding sticky positioning

### Sidebar Not Responsive

**Problem:** Sidebar doesn't hide on mobile devices.

**Solution:**

1. Check `sidebar_expand` value is valid (`sm`, `md`, `lg`, `xl`, `xxl`)
2. Verify the viewport meta tag exists in your base template
3. Test with browser DevTools responsive mode
4. Check that responsive CSS is being loaded

### Layout Overflow Issues

**Problem:** Content overflows or doesn't fill available space.

**Solution:**

1. Ensure parent container has a defined height
2. Check for conflicting CSS `height` or `max-height` rules
3. Verify the `.page-layout` has `height: 100%`
4. Use browser DevTools to inspect the grid structure

### Toggle State Not Persisting

**Problem:** Sidebar state doesn't persist across page reloads.

**Solution:**

1. Check browser console for sessionStorage errors
2. Verify JavaScript is enabled
3. Ensure cookies/storage are not blocked
4. Clear browser cache and test again

### Animation Flicker on Page Load

**Problem:** Sidebar appears to collapse/expand on page load.

**Solution:**
This was fixed in the implementation by adding `no-transition` class during restoration. If you still see this:

1. Clear browser cache
2. Ensure `page-layout.js` is up to date
3. Check browser console for JavaScript errors

## Performance Considerations

- **CSS Grid** - Hardware accelerated, excellent performance
- **SessionStorage** - Minimal overhead, isolated per tab
- **Transitions** - Uses `transform` and `opacity` for smooth 60fps animations
- **No JavaScript Required** - Basic layout works without JS (except toggle functionality)

## Browser Support

The inner layout works in all modern browsers:

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Android)

**Legacy Support:**

- CSS Grid is required (IE11 not supported)
- Falls back gracefully with basic layout if JavaScript disabled

## Examples

For complete working examples, see the [demo page](/page-layout/) in the Demo Application.

## Related Documentation

- [Django MVP Base Layout](./index.md)
- [Navbar Widgets](./navbar-widgets.md)
- [Django Cotton Documentation](https://django-cotton.com/)
- [AdminLTE 4 Documentation](https://adminlte.io/docs/4.0/)
