# Data Model: AdminLTE 4 Widget Components

**Phase**: 1 - Design & Contracts
**Date**: January 5, 2026
**Feature**: [spec.md](./spec.md)

## Component Schemas

### 1. Info Box Component

**File**: `mvp/templates/cotton/info-box.html`

**Attributes**:

```python
{
    "icon": str,           # Icon name for c-icon component (e.g., "gear-fill")
    "icon_class": str,     # Optional additional classes for c-icon
    "text": str,           # Primary label text
    "number": str,         # Metric/statistic value
    "variant": str,        # Color variant: primary|success|warning|danger|info|secondary|default
    "bg": str,             # Background color class (overrides variant)
    "gradient": bool,      # Apply gradient effect (requires bg)
    "progress": int,       # Progress bar percentage (0-100)
    "description": str,    # Progress bar description text
    "class": str,          # Additional CSS classes
}
```

**Default Values**:

```python
{
    "variant": "default",
    "bg": "",
    "gradient": "",
    "progress": "",
    "description": "",
    "icon_class": "",
    "class": "",
}
```

**Slots**: None (content-only component)

**HTML Structure**:

```html
<div class="info-box [variant classes] [bg classes] [gradient] [custom classes]">
    <span class="info-box-icon" aria-hidden="true">
        <c-icon name="{{ icon }}" class="{{ icon_class }}" />
    </span>
    <div class="info-box-content">
        <span class="info-box-text">[text]</span>
        <span class="info-box-number">[number]</span>
        {% if progress %}
        <div class="progress" role="progressbar" aria-valuenow="[progress]" aria-valuemin="0" aria-valuemax="100">
            <div class="progress-bar" style="width: [progress]%"></div>
        </div>
        <span class="progress-description">[description]</span>
        {% endif %}
    </div>
</div>
```

**Validation Rules**:

- `icon` is required (component fails gracefully if missing)
- `text` is required
- `number` is required
- `progress` must be 0-100 if provided
- `variant` must be one of: primary|success|warning|danger|info|secondary|default
- `gradient` requires `bg` to be set

### 2. Small Box Component

**File**: `mvp/templates/cotton/small-box.html`

**Attributes**:

```python
{
    "heading": str,        # Main metric/number
    "text": str,           # Description label
    "icon": str,           # Icon name for c-icon component
    "icon_class": str,     # Optional additional classes for c-icon
    "bg": str,             # Background color variant: primary|success|warning|danger|info|secondary|default
    "link": str,           # Footer link URL
    "link_text": str,      # Footer link text
    "class": str,          # Additional CSS classes
}
```

**Default Values**:

```python
{
    "bg": "default",
    "link": "",
    "link_text": "More info",
    "icon_class": "",
    "class": "",
}
```

**Slots**: None (content-only component)

**HTML Structure**:

```html
<div class="small-box text-bg-[bg] [custom classes]">
    <div class="inner">
        <h3>[heading]</h3>
        <p>[text]</p>
    </div>
    <div class="small-box-icon" aria-hidden="true">
        <c-icon name="{{ icon }}" class="{{ icon_class }}" />
    </div>
    {% if link %}
    <a href="[link]" class="small-box-footer link-light link-underline-opacity-0 link-underline-opacity-50-hover">
        [link_text] <c-icon name="link-45deg" />
    </a>
    {% endif %}
</div>
```

**Validation Rules**:

- `heading` is required
- `text` is required
- `icon` is required
- `bg` must be one of: primary|success|warning|danger|info|secondary|default
- `link_text` uses default "More info" if not provided

### 3. Card Component

**File**: `mvp/templates/cotton/card.html`

**Attributes**:

```python
{
    "title": str,          # Card header title
    "icon": str,           # Optional icon name for c-icon component in header
    "icon_class": str,     # Optional additional classes for c-icon (default: me-2 fs-5 text-muted)
    "variant": str,        # Color variant: primary|success|warning|danger|info|secondary|default
    "fill": str,           # Fill style: outline|card
    "collapsed": bool,     # Initial collapsed state
    "collapsible": bool,   # Enable collapse tool button
    "compact": bool,       # Remove card-body padding (p-0)
    "removable": bool,     # Enable remove tool button
    "maximizable": bool,   # Enable maximize tool button
    "footer_class": str,   # Additional classes for card-footer
    "class": str,          # Additional CSS classes
}
```

**Default Values**:

```python
{
    "variant": "default",
    "fill": "outline",
    "collapsed": "",
    "collapsible": "",
    "compact": "",
    "removable": "",
    "maximizable": "",
    "icon": "",
    "icon_class": "",
    "footer_class": "",
    "class": "",
}
```

**Slots**:

- **default**: Card body content (unnamed slot)
- **tools**: Card header tools/buttons (named slot, renders before automatic tool buttons)
- **footer**: Card footer content (named slot, v2.1 restored)

**HTML Structure** (v2.1):

```html
<div class="card [variant-fill classes] [custom classes]" {{ attrs }}>
    <!-- Header always present for consistent structure -->
    <div class="card-header d-flex align-items-center">
        <div class="d-inline-flex align-items-center">
            {% if icon %}
            <c-icon name="{{ icon }}" class="me-2 fs-5 text-muted {{ icon_class }}" />
            {% endif %}
            {% if title %}<h3 class="card-title">{{ title }}</h3>{% endif %}
        </div>
        <div class="card-tools ms-auto">
            {{ tools }}
            {% if collapsible %}<c-card.actions.collapse />{% endif %}
            {% if removable %}<c-card.actions.remove />{% endif %}
            {% if maximizable %}<c-card.actions.maximize />{% endif %}
        </div>
    </div>
    <div class="card-body {% if compact %}p-0{% endif %}">
        {{ slot }}
    </div>
    {% if footer %}
    <div class="card-footer {{ footer_class }}">
        {{ footer }}
    </div>
    {% endif %}
</div>
```

**Variant-Fill Class Mapping** (v2.1):

```python
# fill="outline" (default)
variant="primary" → "card-primary card-outline"
variant="default" → "card-outline"

# fill="card"
variant="primary" → "text-bg-primary"
variant="default" → "" (no variant classes)
```

**Validation Rules** (v2.1):

- `fill` must be one of: outline|card (header removed in v2.0)
- `variant` must be one of: primary|success|warning|danger|info|secondary|default
- `collapsed`, `collapsible`, `compact`, `removable`, `maximizable` are boolean (presence = true)
- `title` is optional (header always renders)
- `icon` requires `title` for proper layout
- `compact` useful for tables, maps, and full-width content
- Tool sub-components: `<c-card.actions.collapse />`, `<c-card.actions.maximize />`, `<c-card.actions.remove />`

## Entity Relationships

```text
info-box
  └─ icon (c-icon component)
  └─ progress (optional)

small-box
  └─ icon (c-icon component)
  └─ link (optional footer)

card
  ├─ icon (optional, c-icon component)
  ├─ tools (optional slot)
  ├─ body (default slot)
  └─ footer (optional slot)
```

## State Management

### Card Collapse State

- **Initial State**: Controlled by `collapsed` attribute
- **State Change**: Handled by AdminLTE JavaScript via `data-lte-toggle="card-collapse"`
- **Persistence**: Not persisted (page reload resets to initial state)
- **Accessibility**: `aria-expanded` attribute updated by AdminLTE JS

### Progress State (Info Box)

- **Static Only**: Progress percentage displayed, no dynamic updates
- **Update Pattern**: Requires component re-render with new `progress` value

## Accessibility Attributes

### Info Box

- `aria-hidden="true"` on icon span (decorative)
- `role="progressbar"` on progress bar container
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on progress bar

### Small Box

- `aria-hidden="true"` on icon SVG (decorative)

### Card

- `aria-expanded` on collapse button (managed by AdminLTE JS)
- `aria-label="Toggle card"` on collapse button
- `data-lte-icon` for icon state management

## CSS Class Dependencies

### Required AdminLTE 4 Classes

- `.info-box`, `.info-box-icon`, `.info-box-content`, `.info-box-text`, `.info-box-number`
- `.small-box`, `.inner`, `.small-box-icon`, `.small-box-footer`
- `.card`, `.card-header`, `.card-title`, `.card-tools`, `.card-body`, `.card-footer`
- `.card-outline`, `.card-primary`, `.card-success`, etc.

### Required Bootstrap 5 Classes

- `.text-bg-{variant}` (small-box backgrounds)
- `.progress`, `.progress-bar` (info-box progress)
- `.btn`, `.btn-tool` (card tools)
- `.link-light`, `.link-underline-*` (small-box footer links)

### Icon Classes

- Handled by c-icon component (django-easy-icons integration)
- Icon component accepts name attribute and optional class/data attributes
