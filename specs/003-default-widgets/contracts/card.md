# API Contract: Card Component

**Component Name**: `card`
**File**: `mvp/templates/cotton/card/index.html`
**Status**: Phase 1 Design (Refactored 2026-01-05)

## Refactoring Summary (v2.0)

The card component was completely refactored to eliminate deep conditional nesting and improve maintainability:

**Problems with v1.0:**
- 82 lines of deeply nested if/elif/else statements (6+ levels deep)
- Repeated HTML div tags with slight variations across branches
- Manual construction of collapse button HTML in template
- Named slots pattern (`name="tools"`, `name="footer"`) added complexity
- `class_` parameter (awkward workaround for Python keyword)

**Solutions in v2.0:**
- **11-line template** - Reduced from 82 lines by using single-expression class construction
- **Dedicated tool components** - `<c-card.actions.collapse />`, `<c-card.actions.maximize />`, `<c-card.actions.remove />`
- **Boolean control flags** - `collapsible`, `removable`, `maximizable` replace manual button construction
- **Standard Cotton slots** - Uses `{{ tools }}` and `{{ slot }}` instead of named slots
- **Always-render header** - Provides consistent structure, simplifies conditionals
- **Proper parameter naming** - `class` instead of `class_`
- **Removed footer** - Simplified to header + body only (footer rarely used in AdminLTE cards)
- **Removed fill="header"** - Two fill modes (outline, card) sufficient for 99% of use cases

## Component Signature

```django
<c-card
    title="string"
    icon="string"
    icon_class="string"
    variant="string"
    fill="string"
    collapsed="boolean"
    collapsible="boolean"
    removable="boolean"
    maximizable="boolean"
    class="string"
>
    <!-- Default slot: card body content -->

    <c-slot name="tools">
        <!-- Optional: Custom tool buttons -->
    </c-slot>
</c-card>
```

## Attributes

### Required Attributes

None. All attributes are optional.

### Optional Attributes

| Attribute | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `title` | string | `""` | Card header title | `"Monthly Revenue"` |
| `icon` | string | `""` | Icon name for c-icon component in header | `"graph-up-arrow"` |
| `icon_class` | string | `""` | Additional classes for the icon (default: `me-2 fs-5 text-muted`) | `"text-primary"` |
| `variant` | string | `"default"` | Color variant (primary, success, warning, danger, info, secondary, default) | `"primary"` |
| `fill` | string | `"outline"` | Fill style (outline, card) | `"card"` |
| `collapsed` | boolean | `""` | Initial collapsed state (requires collapsible=true) | `"true"` |
| `collapsible` | boolean | `""` | Enable collapse tool button | `"true"` |
| `compact` | boolean | `""` | Remove card-body padding (applies `p-0` class) | `"true"` |
| `removable` | boolean | `""` | Enable remove tool button | `"true"` |
| `maximizable` | boolean | `""` | Enable maximize tool button | `"true"` |
| `footer_class` | string | `""` | Additional classes for card-footer | `"text-end"` |
| `class` | string | `""` | Additional CSS classes | `"mb-3 shadow"` |

## Slots

### Default Slot (unnamed)

**Purpose**: Main card body content
**Required**: No (card can render with empty body)
**Location**: Rendered inside `.card-body`

**Example**:

```django
<c-card title="Example">
    <p>This goes in the card body.</p>
</c-card>
```

### Slot: `tools`

**Purpose**: Custom tool buttons in card header
**Required**: No
**Location**: Rendered inside `.card-tools` before automatic tool buttons
**Notes**: Header always renders, so tools always have a place to appear

**Example**:

```django
<c-card title="Example" collapsible>
    <c-slot name="tools">
        <button type="button" class="btn btn-tool">
            <i class="bi bi-gear"></i>
        </button>
    </c-slot>
    <p>Body content</p>
</c-card>
```

### Slot: `footer`

**Purpose**: Card footer content (action buttons, links, metadata)
**Required**: No
**Location**: Rendered inside `.card-footer`
**Notes**: Use `footer_class` attribute to add custom classes to footer div

**Example**:

```django
<c-card title="Confirm Action" footer_class="text-end">
    <p>Are you sure you want to proceed?</p>
    <c-slot name="footer">
        <button class="btn btn-sm btn-primary">Confirm</button>
        <button class="btn btn-sm btn-secondary">Cancel</button>
    </c-slot>
</c-card>
```

## Output Contract

### HTML Structure (Full)

```html
<div class="card [variant-fill-classes] [custom-classes]" {{ attrs }}>

    <!-- Header (always present for consistent structure) -->
    <div class="card-header d-flex align-items-center">
        <div class="d-inline-flex align-items-center">
            <c-icon name="{{ icon }}" class="me-2 fs-5 text-muted {{ icon_class }}" />
            <h3 class="card-title">[title]</h3>
        </div>
        <div class="card-tools ms-auto">
            [tools-slot]
            <button type="button" class="btn btn-tool"
                    data-lte-toggle="card-collapse"
                    aria-expanded="[true|false]"
                    aria-label="Toggle card">
                <c-icon name="[dash|plus]" data-lte-icon="[collapse|expand]" />
            </button>
        </div>
    </div>

    <!-- Body (always present) -->
    <div class="card-body [p-0 if compact]">
        [default-slot]
    </div>

    <!-- Footer (if footer slot present) -->
    <div class="card-footer {{ footer_class }}">
        [footer-slot]
    </div>
</div>
```

**Note**: The `{{ attrs }}` passthrough allows arbitrary HTML attributes (e.g., `id`, `data-*`, `aria-*`) to be passed directly to the card `<div>`, enabling integration with JavaScript frameworks, accessibility enhancements, and custom data attributes.

### Minimal Structure (No Title)

```html
<div class="card [variant-fill-classes] [custom-classes]">
    <div class="card-body">
        [default-slot]
    </div>
</div>
```

## CSS Class Generation

### Variant-Fill Class Combinations

| Fill | Variant | Card Classes | Header Classes |
|------|---------|-------------|----------------|
| outline | primary | `card-outline card-primary` | *(none)* |
| outline | success | `card-outline card-success` | *(none)* |
| outline | warning | `card-outline card-warning` | *(none)* |
| outline | danger | `card-outline card-danger` | *(none)* |
| outline | info | `card-outline card-info` | *(none)* |
| outline | secondary | `card-outline card-secondary` | *(none)* |
| outline | default | `card-outline` | *(none)* |
| header | primary | `card-outline card-primary` | `text-bg-primary` |
| header | success | `card-outline card-success` | `text-bg-success` |
| header | warning | `card-outline card-warning` | `text-bg-warning` |
| header | danger | `card-outline card-danger` | `text-bg-danger` |
| header | info | `card-outline card-info` | `text-bg-info` |
| header | secondary | `card-outline card-secondary` | `text-bg-secondary` |
| header | default | `card-outline` | *(none)* |
| card | primary | `card-primary` | *(none)* |
| card | success | `card-success` | *(none)* |
| card | warning | `card-warning` | *(none)* |
| card | danger | `card-danger` | *(none)* |
| card | info | `card-info` | *(none)* |
| card | secondary | `card-secondary` | *(none)* |
| card | default | *(none)* | *(none)* |

## Validation Rules

1. **Required Validation**:
   - No strictly required attributes
   - `title` recommended if using tools (tools won't render without header)

2. **Type Validation**:
   - `collapsed` is boolean (presence = true)

3. **Dependency Validation**:
   - Tools slot requires `title` to be present (no header = no tools area)
   - Icon renders only if both `icon` and `title` are present

4. **Attribute Validation** (recommended but not enforced):
   - `variant` should be one of: primary, success, warning, danger, info, secondary, default
   - `fill` should be one of: outline, header, card

## Accessibility

### ARIA Attributes

- `aria-expanded="true|false"` on collapse button (reflects collapsed state)
- `aria-label="Toggle card"` on collapse button (describes action)
- `data-lte-icon="collapse|expand"` on button icon (AdminLTE JS state management)

### Keyboard Navigation

- Collapse button is keyboard focusable (`<button>`)
- Enter/Space activates collapse toggle

### Screen Reader Announcements

- Card title is announced as heading level 3
- Collapse button announces "Toggle card" and expanded state
- Icon in title is decorative (marked `aria-hidden="true"`)

## Examples

### Example 1: Basic Card

**Input**:

```django
<c-card title="Monthly Revenue">
    <p>Revenue data goes here...</p>
</c-card>
```

**Output**:

```html
<div class="card card-outline">
    <div class="card-header">
        <h3 class="card-title">Monthly Revenue</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>Revenue data goes here...</p>
    </div>
</div>
```

### Example 2: Card with Icon

**Input**:

```django
<c-card title="Sales Report" icon="graph-up-arrow">
    <p>Sales charts and data...</p>
</c-card>
```

**Output**:

```html
<div class="card card-outline">
    <div class="card-header">
        <h3 class="card-title">
            <c-icon name="graph-up-arrow" />
            Sales Report
        </h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>Sales charts and data...</p>
    </div>
</div>
```

### Example 3: Colored Header

**Input**:

```django
<c-card
    title="Important Notice"
    variant="warning"
    fill="header"
>
    <p>This is an important warning message.</p>
</c-card>
```

**Output**:

```html
<div class="card card-outline card-warning">
    <div class="card-header text-bg-warning">
        <h3 class="card-title">Important Notice</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>This is an important warning message.</p>
    </div>
</div>
```

### Example 4: Filled Card

**Input**:

```django
<c-card
    title="Danger Zone"
    variant="danger"
    fill="card"
>
    <p>Delete all data permanently.</p>
</c-card>
```

**Output**:

```html
<div class="card card-danger">
    <div class="card-header">
        <h3 class="card-title">Danger Zone</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>Delete all data permanently.</p>
    </div>
</div>
```

### Example 5: With Footer

**Input**:

```django
<c-card title="User Profile">
    <p>User details and information...</p>
    <c-slot name="footer">
        <button class="btn btn-primary">Save</button>
        <button class="btn btn-secondary">Cancel</button>
    </c-slot>
</c-card>
```

**Output**:

```html
<div class="card card-outline">
    <div class="card-header">
        <h3 class="card-title">User Profile</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>User details and information...</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Save</button>
        <button class="btn btn-secondary">Cancel</button>
    </div>
</div>
```

### Example 6: With Custom Tools

**Input**:

```django
<c-card title="System Status">
    <c-slot name="tools">
        <button type="button" class="btn btn-tool">
            <c-icon name="gear" />
        </button>
        <button type="button" class="btn btn-tool">
            <c-icon name="arrow-clockwise" />
        </button>
    </c-slot>
    <p>System metrics and status...</p>
</c-card>
```

**Output**:

```html
<div class="card card-outline">
    <div class="card-header">
        <h3 class="card-title">System Status</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool">
                <c-icon name="gear" />
            </button>
            <button type="button" class="btn btn-tool">
                <c-icon name="arrow-clockwise" />
            </button>
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="true" aria-label="Toggle card">
                <c-icon name="dash" data-lte-icon="collapse" />
            </button>
        </div>
    </div>
    <div class="card-body">
        <p>System metrics and status...</p>
    </div>
</div>
```

### Example 7: Initially Collapsed

**Input**:

```django
<c-card
    title="Expandable Section"
    collapsed="true"
>
    <p>This content is initially hidden.</p>
</c-card>
```

**Output**:

```html
<div class="card card-outline" data-lte-card-widget="collapse">
    <div class="card-header">
        <h3 class="card-title">Expandable Section</h3>
        <div class="card-tools">
            <button type="button" class="btn btn-tool" data-lte-toggle="card-collapse" aria-expanded="false" aria-label="Toggle card">
                <c-icon name="plus" data-lte-icon="expand" />
            </button>
        </div>
    </div>
    <div class="card-body" style="display: none;">
        <p>This content is initially hidden.</p>
    </div>
</div>
```

### Example 8: No Header (Simple Card)

**Input**:

```django
<c-card class="shadow">
    <p>Simple card without header.</p>
</c-card>
```

**Output**:

```html
<div class="card shadow">
    <div class="card-body">
        <p>Simple card without header.</p>
    </div>
</div>
```

## Error Handling

### Missing Attributes

- Missing `title`: No header rendered, card becomes simple wrapper
- Missing `icon`: Title renders without icon
- Missing slots: Component renders without those sections

### Invalid Attribute Values

- Invalid `variant`: No variant classes applied (falls back to default)
- Invalid `fill`: May apply incorrect classes or fall back to default
- Invalid `collapsed`: Treated as false if not exactly "true"

## CSS Dependencies

### Required AdminLTE 4 Classes

- `.card`
- `.card-header`
- `.card-title`
- `.card-tools`
- `.card-body`
- `.card-footer`
- `.card-outline`
- `.card-{variant}` (primary, success, etc.)
- `.card-outline-{variant}`

### Required Bootstrap 5 Classes

- `.text-bg-{variant}` (for header fill)
- `.btn`
- `.btn-tool`

### Required Icon Component

- c-icon component for icon rendering

## JavaScript Dependencies

### AdminLTE 4 Card Widget

Card collapse functionality requires AdminLTE 4 JavaScript:

- `data-lte-toggle="card-collapse"` - Triggers collapse toggle
- `data-lte-card-widget="collapse"` - Initializes collapsed state
- `data-lte-icon="collapse|expand"` - Icon state management
- `aria-expanded` - Updated by AdminLTE JS

Without AdminLTE JS, collapse button renders but does nothing.

## Testing Requirements

### Unit Tests Required

1. ✅ Renders basic card with title and body
2. ✅ Renders card without title (simple card)
3. ✅ Renders with icon in title
4. ✅ Applies variant-fill classes correctly (outline/header/card)
5. ✅ Renders footer when footer slot present
6. ✅ Omits footer when footer slot empty
7. ✅ Renders custom tools in tools slot
8. ✅ Collapse button shows correct icon (dash vs plus) based on collapsed state
9. ✅ Applies `display: none` to body when collapsed
10. ✅ Includes correct ARIA attributes
11. ✅ Applies custom classes via class attribute

### Integration Tests Required

1. ✅ Works within Bootstrap grid layouts
2. ✅ Multiple cards render independently
3. ✅ CSS classes resolve correctly with AdminLTE 4 CSS
4. ✅ Collapse functionality works with AdminLTE JS loaded

## Known Limitations

1. **Heading Level**: Card title always uses `<h3>`. Not customizable.
2. **Collapse Icon**: Always uses dash/plus icons. Not customizable.
3. **Tools Position**: Tools always appear before collapse button. Order not customizable.
4. **JavaScript Dependency**: Collapse requires AdminLTE 4 JS to be loaded.

## Version History

- **v1.0** (Phase 1): Initial contract definition with nested conditionals and named slots
- **v2.0** (2026-01-05): Complete refactoring for maintainability
  - Replaced 80+ lines of nested conditionals with 11-line single-expression template
  - Removed `fill="header"` option (only outline and card remain)
  - Changed from named slots (`tools`, `footer`) to standard Cotton slots
  - Removed footer slot entirely (simplified to header + body only)
  - Added dedicated tool sub-components: `<c-card.actions.collapse />`, `<c-card.actions.maximize />`, `<c-card.actions.remove />`
  - Added boolean flags: `collapsible`, `removable`, `maximizable` control automatic tool rendering
  - Changed `class_` to `class` (proper Cotton parameter naming)
  - Header now always renders (provides consistent structure for tools)
  - Icon and title are optional within always-present header
- **v2.1** (2026-01-05): Practical enhancements based on real-world usage
  - Added `compact` attribute - removes card-body padding (`p-0` class) for tables, maps, and full-width content
  - Added `footer_class` attribute - allows custom classes on card-footer
  - Restored footer slot support via `<c-slot name="footer">` (accidentally removed in v2.0 refactoring due to template complexity)
  - Added `{{ attrs }}` passthrough on card div for HTML attributes (id, data-*, aria-*, etc.)
  - Enhanced card header layout with flexbox (`d-flex align-items-center`) for proper vertical alignment
  - Enhanced icon styling with default classes (`me-2 fs-5 text-muted`) and separate wrapper (`d-inline-flex align-items-center`) for better spacing control
  - Card tools right-aligned with `ms-auto` for consistent positioning
  - Single-line CSS class construction replaces multi-branch conditionals
