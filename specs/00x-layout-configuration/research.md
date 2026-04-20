# Phase 0 Research: AdminLTE Layout Configuration System

**Feature**: 002-layout-configuration
**Date**: January 13, 2026
**Status**: UPDATED - Simple Cotton Solution

## Critical Discovery: Body Class Requirement

**BREAKING CHANGE**: Original assumption that layout classes could be placed on `.app-wrapper` div is **INCORRECT**. AdminLTE CSS requires layout classes on `<body>` tag.

**AdminLTE CSS Analysis**: AdminLTE 4 uses direct descendant selectors that expect classes on the `<body>` element:

```scss
// AdminLTE source selectors - require body classes
.layout-fixed .app-main-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.fixed-header .app-header {
  position: sticky;
  top: 0;
  z-index: $lte-zindex-fixed-header;
}

.fixed-footer .app-footer {
  position: sticky;
  bottom: 0;
  z-index: $lte-zindex-fixed-footer;
}
```

**Required Body Classes**:

- `layout-fixed` - Fixed sidebar positioning
- `fixed-header` - Sticky header behavior
- `fixed-footer` - Sticky footer behavior
- `sidebar-expand-{breakpoint}` - Responsive sidebar (sm, md, lg, xl, xxl)
- `bg-body-tertiary` - Theme background

## Simple Cotton Solution

**Decision**: Move `<body>` tag into `<c-app>` component with layout classes applied directly

**Rationale**:

1. **Simplicity**: Uses Cotton's existing attribute system, no new infrastructure needed
2. **Performance**: Zero runtime overhead - pure CSS solution
3. **Maintainability**: All layout logic in one component template
4. **Cotton Patterns**: Leverages natural Cotton component composition

## Implementation Pattern

**Cotton Component Structure**:

```html
<!-- cotton/app/index.html -->
<c-vars class fixed_sidebar fixed_header fixed_footer sidebar_expand="lg" />
<body class="bg-body-tertiary{% if fixed_sidebar %} layout-fixed{% endif %}{% if fixed_header %} fixed-header{% endif %}{% if fixed_footer %} fixed-footer{% endif %} sidebar-expand-{{ sidebar_expand }} {{ class }}">
  <div class="app-wrapper">
    {{ slot }}
  </div>
  {{ javascript }}
</body>
```

**Template Usage**:

```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head><!-- head content --></head>
<c-app fixed_sidebar fixed_header>
  <c-app.header />
  <c-app.sidebar />
  <c-app.main>{% block content %}{% endblock %}</c-app.main>
  <c-slot name="javascript">
    <script src="adminlte.js"></script>
  </c-slot>
</c-app>
</html>
```

**Benefits**:

- No Python code changes needed
- Uses Cotton's built-in attribute handling
- JavaScript can be injected via slots
- Body classes applied directly where needed

## Testing Strategy

**Simple Testing Approach**:

- **Component Tests**: Render Cotton component with different attributes using `django_cotton.cotton_render()`
- **Visual Tests**: pytest-playwright to verify layout behavior in browser
- **No infrastructure tests needed**: No context processors or template tags to test
- **Global Variables**: Thread safety concerns (TECHNICAL ISSUES)

## Component Integration Pattern

**Decision**: Custom template tag for component-to-context data flow

**Pattern**:

```html
<!-- Cotton component: cotton/adminlte/app.html -->
<c-vars fixed_sidebar fixed_header fixed_footer sidebar_expand="lg" />
{% load layout_tags %}
{% set_layout_config fixed_sidebar=fixed_sidebar fixed_header=fixed_header %}
<div class="app-wrapper">{{ slot }}</div>
```

**Rationale**:

- Cotton components can use template tags to store data in request context
- Clean separation between component rendering and layout logic
- Maintains component expressiveness while respecting template inheritance

**Alternatives Considered**:

- **Direct Context Manipulation**: Cotton components can't modify parent context (TECHNICAL LIMITATION)
- **Hidden Form Fields**: Unnecessary complexity for layout data (OVERENGINEERING)

## Key Findings

### 1. Existing Implementation

**Location**: `mvp/templates/cotton/app/index.html`

The `<c-app>` component already implements all required layout attributes:

```django-html
<c-vars class
        fixed_sidebar
        fixed_header
        fixed_footer
        sidebar_collapsible
        collapsed
        sidebar_expand="lg" />
<body class="bg-body-tertiary{% if fixed_sidebar %} layout-fixed{% endif %}{% if fixed_header %} fixed-header{% endif %}{% if fixed_footer %} fixed-footer{% endif %}{% if sidebar_collapsible %} sidebar-mini{% if collapsed %} sidebar-collapse{% endif %}{% endif %} sidebar-expand-{{ sidebar_expand }} {{ class }}">
  <div class="app-wrapper">{{ slot }}</div>
</body>
```

**Status**: ✅ All three layout attributes (`fixed_sidebar`, `fixed_header`, `fixed_footer`) are implemented and functional.

### 2. AdminLTE CSS Class Mapping

Based on [AdminLTE 4 Layout Behavior Analysis](../../../docs/adminlte-4-layout-behavior-analysis.md):

| Boolean Attribute | AdminLTE Body Class | Behavior |
|-------------------|---------------------|----------|
| `fixed_sidebar` | `.layout-fixed` | Sidebar uses `position: sticky`, 100vh height, scrollable content |
| `fixed_header` | `.fixed-header` | Header uses `position: sticky` at top of viewport |
| `fixed_footer` | `.fixed-footer` | Footer uses `position: sticky` at bottom of viewport |

**Combinations**:

- All three together = "Fixed Complete" layout (entire app frame fixed, only content scrolls)
- Any subset = Partial fixed layout

### 3. Cotton Component Patterns

**Boolean Attribute Pattern**:

```django-html
<!-- Declaration in <c-vars> -->
<c-vars fixed_sidebar fixed_header />

<!-- Conditional class application -->
{% if fixed_sidebar %} layout-fixed{% endif %}

<!-- Usage in templates -->
<c-app fixed_sidebar fixed_header>
  ...
</c-app>
```

**String Attribute Pattern** (for sidebar_expand):

```django-html
<!-- Declaration with default -->
<c-vars sidebar_expand="lg" />

<!-- Direct interpolation -->
sidebar-expand-{{ sidebar_expand }}

<!-- Usage -->
<c-app sidebar_expand="md">
  ...
</c-app>
```

### 4. Testing Approach

**Test Framework**: pytest-django with `django_cotton.cotton_render()`

**Example test structure** (from existing tests):

```python
from django_cotton import cotton_render
from django.template import RequestContext
from pytest_django.fixtures import rf

def test_fixed_sidebar_renders_layout_fixed_class(rf):
    """Test that fixed_sidebar attribute adds .layout-fixed to body element."""
    html = cotton_render(
        "app",
        context=RequestContext(rf.get("/"), {"fixed_sidebar": True})
    )
    assert 'class="bg-body-tertiary layout-fixed' in html
    assert '<div class="app-wrapper">' in html
```

### 5. Responsive Behavior

**Key Finding**: Fixed layout and responsive sidebar are independent concerns.

- `fixed_sidebar` → Controls sticky positioning (works at all viewport sizes)
- `sidebar_expand="lg"` → Controls when sidebar is visible vs off-canvas
- These can be combined: `<c-app fixed_sidebar sidebar_expand="md">`

**Breakpoint values**: `sm`, `md`, `lg` (default), `xl`, `xxl`

## Technology Decisions

### Decision 1: Component Attribute Approach (Already Implemented)

**Chosen**: Separate boolean attributes per layout element

**Rationale**:

- Maximum flexibility - can combine any fixed elements
- Clear, explicit syntax: `<c-app fixed_sidebar fixed_header>`
- Follows Bootstrap/AdminLTE conventions (each feature independently toggled)
- Already implemented and working in codebase

**Alternatives Considered**:

- Single `layout` attribute with combined values (e.g., `layout="fixed-sidebar fixed-header"`)
  - Rejected: Less flexible, requires string parsing, conflicts with potential CSS class usage
- Preset layouts (e.g., `layout="complete"`)
  - Rejected: Less flexible, requires maintaining preset definitions

### Decision 2: CSS Class Generation Location

**Chosen**: Generate classes directly in `<c-app>` component's `<body>` tag

**Rationale**:

- AdminLTE requires classes on body element for layout behavior
- Cotton components can render any HTML (including body)
- Keeps layout logic centralized in one component
- Already implemented pattern in codebase

**Alternatives Considered**:

- Context processor + base template
  - Rejected: Would require settings-based config, less flexible than component attributes
- JavaScript-based class injection
  - Rejected: Requires JS, increases complexity, breaks SSR

### Decision 3: Testing Strategy

**Chosen**: pytest-django unit tests with `cotton_render()`

**Rationale**:

- Fast, deterministic tests
- No browser overhead
- Can test all attribute combinations
- Follows project constitution (Test-First)

**Test Coverage Required**:

- Each individual fixed attribute renders correct class
- Combinations of fixed attributes work together
- Default behavior (no attributes)
- Edge case: contradictory attributes (e.g., `fixed_sidebar fixed_sidebar="false"`)

## Dependencies

### Existing Dependencies (No Changes)

- Django 4.2+
- django-cotton
- Bootstrap 5
- AdminLTE 4 CSS (via CDN in base.html)

### No New Dependencies Required

All functionality uses existing Cotton component patterns.

## Open Questions (Resolved)

1. ~~Component naming?~~ → Resolved: `<c-app>` (no `mvp` prefix)
2. ~~Attribute format?~~ → Resolved: Separate boolean attributes
3. ~~Fixed complete as separate option?~~ → Resolved: No, combine all three attributes
4. ~~Mobile behavior?~~ → Resolved: Fixed layout independent from sidebar_expand breakpoint
5. ~~Custom areas support?~~ → Resolved: Out of scope

## References

- [AdminLTE 4 Layout Behavior Analysis](../../../docs/adminlte-4-layout-behavior-analysis.md)
- [django-cotton Documentation](https://django-cotton.com/)
- [AdminLTE 4 Demo](https://adminlte.io/themes/v4/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)

## Demo View Requirements (Clarified 2026-01-06)

### Decision 4: Demo View Architecture

**Location**: `demo/` app within django-mvp package

**Rationale**:

- Keeps demo code separate from production package
- The `demo/` app already exists and is designed for this purpose
- Makes it clear these are reference implementations, not required components

### Decision 5: Demo View Content Strategy

**Fixed Properties Demo** (`/demo/layout-fixed/`):

- Form with 3 checkboxes (fixed_header, fixed_sidebar, fixed_footer)
- Submits via GET request to same page with query parameters
- Long-form content with multiple sections (2-3 viewport heights)
- Several dummy sidebar menu items (12-15) to demonstrate independent scrolling
- Minimal helper text explaining what to test
- Visual indicators showing current configuration state

**Responsive Breakpoint Demo** (`/demo/layout-responsive/`):

- Dropdown selector listing all breakpoints (sm, md, lg, xl, xxl)
- Submits GET request with `breakpoint` query parameter
- Same content structure as fixed properties demo
- Instructions to resize browser window to test breakpoint transitions
- Visual indicator showing currently selected breakpoint

**Content Structure** (both demos):

1. Helper text at top ("Scroll to test fixed elements" / "Resize window to test breakpoint")
2. Configuration form (checkboxes or dropdown)
3. Visual status indicator (current config, applied CSS classes)
4. 2-3 content sections with:
   - Section headings
   - Paragraphs (2-3 per section)
   - Sample data table
5. Sidebar with 12-15 dummy menu items grouped into categories

**Implementation Pattern**:

```python
def layout_fixed_demo(request):
    fixed_sidebar = request.GET.get('fixed_sidebar') == 'on'
    fixed_header = request.GET.get('fixed_header') == 'on'
    fixed_footer = request.GET.get('fixed_footer') == 'on'
    return render(request, 'demo/layout_fixed.html', {
        'fixed_sidebar': fixed_sidebar,
        'fixed_header': fixed_header,
        'fixed_footer': fixed_footer,
    })

def layout_responsive_demo(request):
    breakpoint = request.GET.get('breakpoint', 'lg')
    if breakpoint not in ['sm', 'md', 'lg', 'xl', 'xxl']:
        breakpoint = 'lg'
    return render(request, 'demo/layout_responsive.html', {
        'breakpoint': breakpoint,
        'breakpoints': ['sm', 'md', 'lg', 'xl', 'xxl'],
    })
```

## Next Steps (Phase 1)

1. Create data-model.md (minimal - only layout configuration entities)
2. Create contracts/ (N/A for this feature - no API)
3. Create quickstart.md (usage documentation with examples)
4. Update agent context with new technology decisions
