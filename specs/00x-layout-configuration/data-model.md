# Data Model: AdminLTE Layout Configuration

**Feature**: 002-layout-configuration
**Date**: January 13, 2026
**Dependencies**: research.md

## Simple Cotton Approach

**Model**: Layout attributes are passed directly to Cotton component and applied to body class using Cotton's built-in template logic. No Python data structures needed.

## Cotton Component Attributes

### Layout Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `fixed_sidebar` | boolean | `false` | Sidebar stays visible during scroll |
| `fixed_header` | boolean | `false` | Header stays at top during scroll |
| `fixed_footer` | boolean | `false` | Footer stays at bottom during scroll |
| `sidebar_expand` | string | `"lg"` | Responsive breakpoint: `sm`, `md`, `lg`, `xl`, `xxl` |
| `class` | string | `""` | Additional CSS classes |

### Generated Body Classes

**Template Logic**:

```django
<body class="bg-body-tertiary{% if fixed_sidebar %} layout-fixed{% endif %}{% if fixed_header %} fixed-header{% endif %}{% if fixed_footer %} fixed-footer{% endif %} sidebar-expand-{{ sidebar_expand }} {{ class }}">
```

**Examples**:

- Default: `bg-body-tertiary sidebar-expand-lg`
- Fixed sidebar: `bg-body-tertiary layout-fixed sidebar-expand-lg`
- All fixed: `bg-body-tertiary layout-fixed fixed-header fixed-footer sidebar-expand-lg`

## JavaScript Slot

**Slot Declaration**: `{{ javascript }}` in component template
**Usage**: `<c-slot name="javascript">...</c-slot>` in template using component

## No Persistent Data

This feature requires no database tables or persistent storage. All configuration is ephemeral and exists only during template rendering.

## Core Entities

### LayoutConfig (Immutable Configuration)

**Purpose**: Immutable, validated layout configuration with body class generation capability.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

class BreakpointType(str, Enum):
    """Supported AdminLTE breakpoint values for sidebar expansion."""
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"
    XXL = "xxl"

@dataclass(frozen=True)
class LayoutConfig:
    """Immutable layout configuration with validation and body class generation."""

    fixed_sidebar: bool = False
    fixed_header: bool = False
    fixed_footer: bool = False
    sidebar_expand: BreakpointType = BreakpointType.LG
    sidebar_mini: bool = False
    sidebar_collapsed: bool = False

    def to_body_classes(self) -> str:
        """Generate AdminLTE body class string."""
        classes = []

        if self.fixed_sidebar:
            classes.append('layout-fixed')
        if self.fixed_header:
            classes.append('fixed-header')
        if self.fixed_footer:
            classes.append('fixed-footer')

        classes.append(f'sidebar-expand-{self.sidebar_expand.value}')

        if self.sidebar_mini:
            classes.append('sidebar-mini')
            if self.sidebar_collapsed:
                classes.append('sidebar-collapse')

        classes.append('bg-body-tertiary')

        return ' '.join(classes)
```

### LayoutState (Request-Scoped State)

**Purpose**: Mutable state stored in request object for template tag → context processor communication.

```python
@dataclass
class LayoutState:
    """Mutable layout state stored in request for template rendering."""

    component_config: Optional[LayoutConfig] = None
    view_config: Optional[LayoutConfig] = None
    query_config: Optional[LayoutConfig] = None
    final_config: Optional[LayoutConfig] = None
    body_classes: Optional[str] = None
```

## Validation Rules

### Layout Attribute Constraints

1. **Boolean Attributes**: `fixed_sidebar`, `fixed_header`, `fixed_footer`, `sidebar_mini`, `sidebar_collapsed`
   - Must be boolean values
   - Default to `False` if not specified
   - No mutual exclusions (all can be enabled simultaneously)

2. **Breakpoint Validation**: `sidebar_expand`
   - Must be one of: `sm`, `md`, `lg`, `xl`, `xxl`
   - Default to `lg` if invalid or not specified
   - Case-insensitive input, normalized to lowercase

3. **Logical Dependencies**:
   - `sidebar_collapsed` only meaningful when `sidebar_mini=True`
   - No error if `sidebar_collapsed=True` without `sidebar_mini`, but no effect

## State Transitions

### Configuration Resolution Flow

```text
1. Base Configuration (Django settings)
   ↓
2. View-Level Override (via LayoutConfigMixin)
   ↓
3. Component-Level Override (via Cotton attributes)
   ↓
4. Query Parameter Override (via GET params)
   ↓
5. Final Configuration → Body Classes
```

**Precedence Order** (highest to lowest):

1. Query parameters (for demo/testing)
2. Cotton component attributes (page-level)
3. View configuration (view-level)
4. Django settings (global default)

## Entity Relationships

### Configuration Hierarchy

```text
Django Settings (MVP.layout)
    ↓ inherits
View Configuration (LayoutConfigMixin)
    ↓ inherits
Component Configuration (Cotton attributes)
    ↓ overrides
Query Configuration (GET parameters)
    ↓ produces
Final Configuration → Body Classes
```

### Request Lifecycle Objects

```text
HttpRequest
├── .GET (QueryDict) → LayoutConfig.from_query_params()
├── ._layout_state (LayoutState) → stores all configurations
└── context → mvp_body_classes (final output)

Cotton Component
├── fixed_sidebar, fixed_header, etc. → LayoutConfig.from_cotton_attrs()
└── template tag → stores in request._layout_state.component_config

Context Processor
├── reads request._layout_state
├── merges with Django settings
└── returns {'mvp_body_classes': str}
```

## Default Values

### System Defaults

```python
DEFAULT_LAYOUT_CONFIG = LayoutConfig(
    fixed_sidebar=False,     # Sidebar scrolls with content
    fixed_header=False,      # Header scrolls with content
    fixed_footer=False,      # Footer scrolls with content
    sidebar_expand='lg',     # Sidebar expands on large screens and up
    sidebar_mini=False,      # Full sidebar, not collapsible
    sidebar_collapsed=False  # Sidebar expanded by default
)
```

### AdminLTE CSS Classes Generated

- **Default**: `sidebar-expand-lg bg-body-tertiary`
- **Fixed Sidebar**: `layout-fixed sidebar-expand-lg bg-body-tertiary`
- **Fixed Header**: `fixed-header sidebar-expand-lg bg-body-tertiary`
- **Fixed Footer**: `fixed-footer sidebar-expand-lg bg-body-tertiary`
- **All Fixed**: `layout-fixed fixed-header fixed-footer sidebar-expand-lg bg-body-tertiary`

### Performance Characteristics

- **Configuration Resolution**: O(1) - simple attribute merging
- **Body Class Generation**: O(1) - string concatenation
- **Memory Usage**: Minimal - immutable configs, request-scoped state only
- **Thread Safety**: Full - immutable configurations, no shared mutable state

## Demo Page State Management

### Layout Demo State

**URL Pattern**: `/layout/?fixed_sidebar=true&fixed_header=true&sidebar_expand=lg`

**Query Parameters**:

- `fixed_sidebar` (boolean) - "true"/"false" checkbox state
- `fixed_header` (boolean) - "true"/"false" checkbox state
- `fixed_footer` (boolean) - "true"/"false" checkbox state
- `sidebar_expand` (string) - Breakpoint dropdown value

**Processing Logic**:

```python
def layout_demo_view(request):
    # Parse query parameters to LayoutConfig
    query_config = LayoutConfig.from_query_params(request.GET)

    # Store in request for context processor
    if not hasattr(request, '_layout_state'):
        request._layout_state = LayoutState()
    request._layout_state.query_config = query_config

    return render(request, 'demo/layout_demo.html', {
        'current_config': query_config,
        'breakpoints': list(BreakpointType)
    })
```
