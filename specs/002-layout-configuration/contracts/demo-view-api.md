# View Contract: Layout Demo Page

**Feature**: 002-layout-configuration
**Date**: 2026-01-07
**View**: `example.views.layout_demo`
**URL**: `/layout/`

## Overview

The unified layout demo page provides an interactive interface for testing all AdminLTE layout configurations via a split-layout design with main content on the left and configuration form sidebar on the right.

## HTTP Contract

### Endpoint

```
GET /layout/
```

### Query Parameters

| Parameter | Type | Required | Default | Valid Values | Description |
|-----------|------|----------|---------|--------------|-------------|
| `fixed_sidebar` | string | No | (absent) | `"on"` or absent | When `"on"`, applies fixed sidebar layout |
| `fixed_header` | string | No | (absent) | `"on"` or absent | When `"on"`, applies fixed header layout |
| `fixed_footer` | string | No | (absent) | `"on"` or absent | When `"on"`, applies fixed footer layout |
| `breakpoint` | string | No | `"lg"` | `sm`, `md`, `lg`, `xl`, `xxl` | Sidebar expansion breakpoint |

### Request Examples

**Default layout (no parameters)**:

```
GET /layout/
```

**Fixed sidebar + header**:

```
GET /layout/?fixed_sidebar=on&fixed_header=on
```

**Fixed complete with medium breakpoint**:

```
GET /layout/?fixed_sidebar=on&fixed_header=on&fixed_footer=on&breakpoint=md
```

**Responsive behavior test**:

```
GET /layout/?breakpoint=sm
```

### Response

**Status Code**: 200 OK

**Content-Type**: text/html

**Template**: `demo/layout_demo.html`

**Context Variables**:

```python
{
    'fixed_sidebar': bool,      # True if query param = "on"
    'fixed_header': bool,       # True if query param = "on"
    'fixed_footer': bool,       # True if query param = "on"
    'breakpoint': str,          # Validated breakpoint value
    'breakpoints': list[str],   # Available breakpoint options
}
```

## View Implementation

### Function Signature

```python
def layout_demo(request: HttpRequest) -> HttpResponse:
    """
    Unified interactive layout configuration demo page.

    Allows testing all AdminLTE layout options via query parameters:
    - Fixed sidebar/header/footer via checkboxes
    - Responsive breakpoint via dropdown

    Returns HTML page with:
    - Left side: Main content area demonstrating scroll behavior
    - Right side: Configuration form for toggling options
    """
```

### Processing Logic

```python
def layout_demo(request):
    # Parse boolean checkboxes (present and "on" = checked)
    fixed_sidebar = request.GET.get('fixed_sidebar') == 'on'
    fixed_header = request.GET.get('fixed_header') == 'on'
    fixed_footer = request.GET.get('fixed_footer') == 'on'

    # Parse and validate breakpoint
    breakpoint = request.GET.get('breakpoint', 'lg')
    valid_breakpoints = ['sm', 'md', 'lg', 'xl', 'xxl']
    if breakpoint not in valid_breakpoints:
        breakpoint = 'lg'  # Fallback to default for invalid values

    return render(request, 'demo/layout_demo.html', {
        'fixed_sidebar': fixed_sidebar,
        'fixed_header': fixed_header,
        'fixed_footer': fixed_footer,
        'breakpoint': breakpoint,
        'breakpoints': valid_breakpoints,
    })
```

### Edge Cases

**Invalid breakpoint value**:

```
GET /layout/?breakpoint=invalid
```

→ Falls back to `breakpoint="lg"`

**Mixed query parameter formats**:

```
GET /layout/?fixed_sidebar=1&fixed_header=true
```

→ Both treated as unchecked (only `"on"` is recognized as checked)

**Empty query string**:

```
GET /layout/?
```

→ Same as no query parameters (all defaults applied)

## Template Contract

### Page Structure

```django-html
{% extends "mvp/base.html" %}

{% block content %}
<div class="row">
  <!-- Main Content (Left) -->
  <div class="col-lg-8">
    <div class="card">
      <div class="card-header">
        <h3>Layout Configuration Demo</h3>
        <p class="text-muted">Scroll to test fixed element behavior</p>
      </div>
      <div class="card-body">
        <!-- Long-form content (2-3 viewport heights) -->
        <!-- Multiple sections, headings, paragraphs, tables -->
      </div>
    </div>
  </div>

  <!-- Configuration Sidebar (Right) -->
  <div class="col-lg-4">
    <div class="card position-sticky" style="top: 1rem;">
      <div class="card-header">Configuration</div>
      <div class="card-body">
        <form method="get" action="{% url 'layout_demo' %}">
          <!-- Fixed Properties Checkboxes -->
          <div class="form-check">
            <input type="checkbox" name="fixed_sidebar"
                   {% if fixed_sidebar %}checked{% endif %}>
            <label>Fixed Sidebar</label>
          </div>
          <!-- ... other checkboxes ... -->

          <!-- Breakpoint Dropdown -->
          <select name="breakpoint">
            {% for bp in breakpoints %}
            <option {% if bp == breakpoint %}selected{% endif %}>
              {{ bp }}
            </option>
            {% endfor %}
          </select>

          <button type="submit">Apply Configuration</button>
        </form>

        <!-- Visual Indicators -->
        <div class="mt-3">
          <strong>Current Config:</strong>
          <ul>
            <li>Body classes: <code>{{ body_classes }}</code></li>
            <li>Breakpoint: <code>{{ breakpoint }}</code></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Required Elements

1. **Main content area** (left side, col-lg-8):
   - Long scrollable content (2-3 viewport heights minimum)
   - Multiple sections with headings
   - Helper text explaining what to test

2. **Configuration sidebar** (right side, col-lg-4):
   - Sticky positioning (`position-sticky`)
   - Form with GET method
   - Three checkboxes: fixed_sidebar, fixed_header, fixed_footer
   - Dropdown: breakpoint selector
   - Submit button
   - Visual indicators showing current state

3. **Form Behavior**:
   - Submit via GET (URL updates with query params)
   - Checkboxes pre-checked based on context variables
   - Dropdown pre-selected based on context variable
   - Form submits to same URL (`{% url 'layout_demo' %}`)

## Navigation Integration

### Menu Entry

**Location**: `demo/menus.py`

**Position**: Immediately below "Dashboard" menu item

**Definition**:

```python
from flex_menus import MenuItem

menu_items = [
    MenuItem(
        id="dashboard",
        label="Dashboard",
        url="/",
        icon="dashboard",
    ),
    MenuItem(
        id="layout_demo",
        label="Layout Demo",
        url="/layout/",
        icon="settings",  # Or appropriate icon
    ),
    # ... other menu items ...
]
```

### Requirements

- Must appear in sidebar menu on all Demo App pages
- Must be positioned directly below Dashboard link
- Must link to `/layout/` with no query parameters (default state)
- Must use appropriate icon (settings, tune, or similar)

## Testing Contract

### Test Cases

**Test 1: Default state (no query params)**

```python
def test_layout_demo_default_state(client):
    response = client.get('/layout/')
    assert response.status_code == 200
    assert response.context['fixed_sidebar'] is False
    assert response.context['fixed_header'] is False
    assert response.context['fixed_footer'] is False
    assert response.context['breakpoint'] == 'lg'
```

**Test 2: Fixed sidebar enabled**

```python
def test_layout_demo_fixed_sidebar(client):
    response = client.get('/layout/?fixed_sidebar=on')
    assert response.context['fixed_sidebar'] is True
    assert 'layout-fixed' in response.content.decode()
```

**Test 3: All fixed (complete layout)**

```python
def test_layout_demo_fixed_complete(client):
    response = client.get('/layout/?fixed_sidebar=on&fixed_header=on&fixed_footer=on')
    assert response.context['fixed_sidebar'] is True
    assert response.context['fixed_header'] is True
    assert response.context['fixed_footer'] is True
    assert 'layout-fixed' in response.content.decode()
    assert 'fixed-header' in response.content.decode()
    assert 'fixed-footer' in response.content.decode()
```

**Test 4: Custom breakpoint**

```python
def test_layout_demo_custom_breakpoint(client):
    response = client.get('/layout/?breakpoint=md')
    assert response.context['breakpoint'] == 'md'
    assert 'sidebar-expand-md' in response.content.decode()
```

**Test 5: Invalid breakpoint falls back to default**

```python
def test_layout_demo_invalid_breakpoint(client):
    response = client.get('/layout/?breakpoint=invalid')
    assert response.context['breakpoint'] == 'lg'
```

**Test 6: Menu item exists and points to correct URL**

```python
def test_layout_demo_menu_item(client):
    response = client.get('/')
    assert '/layout/' in response.content.decode()
    # Verify menu item appears below dashboard
```

## Extensibility for Future Specs

### Design for Extension

The layout demo page is designed to accommodate additional layout configuration options from future feature specs without requiring separate demo pages.

**Extension Pattern**:

1. Future spec adds query parameter handling to view
2. Future spec adds form control to configuration sidebar
3. Future spec updates context variables and template rendering

**Example: Adding Sidebar Mini (future spec 004)**:

```python
# View extension
sidebar_mini = request.GET.get('sidebar_mini') == 'on'
context['sidebar_mini'] = sidebar_mini

# Template extension (configuration sidebar)
<div class="form-check">
  <input type="checkbox" name="sidebar_mini"
         {% if sidebar_mini %}checked{% endif %}>
  <label>Sidebar Mini Mode</label>
</div>

# Template extension (app component)
<c-app
  {% if fixed_sidebar %}fixed_sidebar{% endif %}
  {% if sidebar_mini %}sidebar_mini{% endif %}
  breakpoint="{{ breakpoint }}">
```

This extensibility requirement is enforced by FR-019 in the feature specification.

## Success Criteria

- ✅ Single URL endpoint at `/layout/` handles all layout testing
- ✅ Query parameters control all layout options
- ✅ Form submission updates URL with new parameters
- ✅ Page layout uses left/right split (main content + config sidebar)
- ✅ Menu item appears below Dashboard in sidebar navigation
- ✅ All combinations of fixed properties are testable
- ✅ All breakpoint values are selectable via dropdown
- ✅ Visual indicators show current configuration state
- ✅ Design accommodates future layout option extensions
