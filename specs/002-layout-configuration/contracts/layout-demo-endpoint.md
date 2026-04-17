# API Contract: Layout Demo Endpoint

**Endpoint**: `/layout/`
**Method**: GET
**Purpose**: Interactive layout configuration demo page

## Request Schema

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fixed_sidebar` | boolean | No | false | Enable fixed sidebar positioning |
| `fixed_header` | boolean | No | false | Enable fixed header positioning |
| `fixed_footer` | boolean | No | false | Enable fixed footer positioning |
| `sidebar_expand` | string | No | "lg" | Breakpoint for sidebar expansion |
| `sidebar_mini` | boolean | No | false | Enable collapsible sidebar |
| `sidebar_collapsed` | boolean | No | false | Initially collapse sidebar |

### Query Parameter Format

**Boolean Parameters**:

- `true` / `false` (case-insensitive)
- `1` / `0`
- Present without value = `true`
- Absent = `false`

**Breakpoint Parameter**:

- Must be one of: `sm`, `md`, `lg`, `xl`, `xxl`
- Invalid values default to `lg`
- Case-insensitive

### Example Requests

```http
GET /layout/ HTTP/1.1
# Default configuration

GET /layout/?fixed_sidebar=true HTTP/1.1
# Fixed sidebar only

GET /layout/?fixed_sidebar=true&fixed_header=true&sidebar_expand=md HTTP/1.1
# Fixed sidebar + header with medium breakpoint

GET /layout/?fixed_sidebar=true&fixed_header=true&fixed_footer=true HTTP/1.1
# All fixed elements (complete layout)
```

## Response Schema

### Success Response (200 OK)

**Content-Type**: `text/html`

**Response Body**: HTML page with:

- AdminLTE layout with applied configuration
- Configuration form reflecting current state
- Long-form content for scrolling behavior testing
- Navigation menu with demo page link

### Response Headers

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Cache-Control: no-cache
X-Frame-Options: DENY
```

### HTML Structure

```html
<!DOCTYPE html>
<html>
<head>
    <title>Layout Demo - AdminLTE Configuration</title>
    <!-- AdminLTE CSS -->
</head>
<body class="[generated-layout-classes]">
    <div class="app-wrapper">
        <aside class="app-sidebar">
            <!-- Navigation menu with Layout Demo link -->
        </aside>
        <header class="app-header">
            <!-- Header content -->
        </header>
        <main class="app-main">
            <div class="app-content">
                <!-- Demo content + configuration form -->
            </div>
        </main>
        <footer class="app-footer">
            <!-- Footer content if enabled -->
        </footer>
    </div>
</body>
</html>
```

### Body Class Examples

| Configuration | Generated Body Classes |
|---------------|----------------------|
| Default | `sidebar-expand-lg bg-body-tertiary` |
| Fixed sidebar | `layout-fixed sidebar-expand-lg bg-body-tertiary` |
| Fixed header | `fixed-header sidebar-expand-lg bg-body-tertiary` |
| Fixed footer | `fixed-footer sidebar-expand-lg bg-body-tertiary` |
| All fixed | `layout-fixed fixed-header fixed-footer sidebar-expand-lg bg-body-tertiary` |

## Error Handling

### Invalid Parameters

**Behavior**: Invalid parameter values are ignored and defaults are used

- Invalid `sidebar_expand` → defaults to `lg`
- Invalid boolean values → defaults to `false`
- Unknown parameters → ignored

**No HTTP errors for invalid layout parameters** - graceful degradation ensures page always loads.

### Server Errors

**500 Internal Server Error**: Only for system failures (template errors, missing dependencies)

```json
{
    "error": "Internal server error",
    "message": "Template rendering failed",
    "timestamp": "2026-01-13T10:30:00Z"
}
```

## Integration Points

### Navigation Menu

**Menu Item**:

- **Text**: "Layout Demo"
- **URL**: `/layout/`
- **Position**: Below "Dashboard" in sidebar menu
- **Icon**: Optional layout-related icon

### Form Handling

**Configuration Form**:

```html
<form method="GET" action="/layout/">
    <div class="form-check">
        <input type="checkbox" name="fixed_sidebar" value="true"
               {% if current_config.fixed_sidebar %}checked{% endif %}>
        <label>Fixed Sidebar</label>
    </div>
    <div class="form-check">
        <input type="checkbox" name="fixed_header" value="true"
               {% if current_config.fixed_header %}checked{% endif %}>
        <label>Fixed Header</label>
    </div>
    <div class="form-check">
        <input type="checkbox" name="fixed_footer" value="true"
               {% if current_config.fixed_footer %}checked{% endif %}>
        <label>Fixed Footer</label>
    </div>
    <div class="form-group">
        <label>Sidebar Breakpoint</label>
        <select name="sidebar_expand">
            <option value="sm" {% if current_config.sidebar_expand == 'sm' %}selected{% endif %}>Small (sm)</option>
            <option value="md" {% if current_config.sidebar_expand == 'md' %}selected{% endif %}>Medium (md)</option>
            <option value="lg" {% if current_config.sidebar_expand == 'lg' %}selected{% endif %}>Large (lg)</option>
            <option value="xl" {% if current_config.sidebar_expand == 'xl' %}selected{% endif %}>Extra Large (xl)</option>
            <option value="xxl" {% if current_config.sidebar_expand == 'xxl' %}selected{% endif %}>2X Large (xxl)</option>
        </select>
    </div>
    <button type="submit">Apply Configuration</button>
</form>
```

### URL Patterns

```python
# demo/urls.py
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('layout/', views.layout_demo, name='layout_demo'),
]
```

## Performance Requirements

- **Response Time**: < 200ms for typical configuration
- **Payload Size**: < 50KB HTML (excluding AdminLTE CSS/JS)
- **Caching**: No caching (configuration changes must be immediately visible)

## Security Considerations

- **No CSRF required**: GET requests with query parameters only
- **Input Sanitization**: All parameters validated and sanitized
- **XSS Prevention**: All user input escaped in templates
- **No sensitive data**: Layout configuration is not sensitive
