# Research: Cotton App Layout Configuration

**Branch**: `001-app-components` | **Date**: 2026-04-17

## 1. AdminLTE 4 Body-Class Layout System

### Decision
All AdminLTE 4 layout behaviour is driven by CSS classes on the `<body>` element. The `<c-app>` component already renders the `<body>` tag and translates Cotton attributes into the correct classes.
Template declarations use kebab-case attributes (for example, `fixed-sidebar`), and django-cotton normalizes them to snake_case for component consumption.

### Body-Class Reference (from AdminLTE 4 docs + source analysis)

| CSS Class | Trigger | Effect |
|-----------|---------|--------|
| `.layout-fixed` | `fixed-sidebar` | Sidebar becomes `position: sticky` |
| `.fixed-header` | `fixed-header` | Navbar sticks to top of viewport |
| `.fixed-footer` | `fixed-footer` | App footer sticks to bottom of viewport |
| `.sidebar-mini` | `sidebar-collapsible` | Enables mini-sidebar (icon-only) toggle mode |
| `.sidebar-collapse` | `collapsed` (with `sidebar-collapsible`) | Sidebar starts in collapsed/icon-only state |
| `.sidebar-expand-{bp}` | `sidebar-expand` | Breakpoint at which sidebar transitions from drawer to expanded. Valid: `sm`, `md`, `lg` (default), `xl`, `xxl` |
| `.sidebar-open` | JS runtime | AdminLTE JS adds dynamically when sidebar is open |
| `.bg-body-tertiary` | hardcoded in base | Default AdminLTE body background |
| `dir="rtl"` on `<html>` | Not yet exposed | Right-to-left layout (future consideration) |

### Rationale
The existing `<c-app>` template already maps attributes to body classes correctly. The critical insight from the user is that **all** configuration must flow through Cotton component attributes because body classes live on the `<body>` element, which is rendered by `<c-app>`.

### Alternatives Considered
- **Settings-based config** (rejected by user): Would require context processors to pass classes. Adds indirection and is explicitly ruled out.
- **View-based config via `:attrs`** (rejected by user): Created coupling between Python views and template rendering. Demo app may still use view context for dynamic demos only.

---

## 2. Base Template vs Application Shell Declaration

### Decision
The project uses a two-layer template architecture:

1. **`mvp/base.html`** — The HTML document skeleton. Owns `<html>`, `<head>`, static asset loading (CSS, JS, fonts), and the `{% block app %}` that delegates the application shell.
2. **`<c-app>` (via `{% block app %}`)** — The application shell declaration. Owns `<body>` (and therefore all body classes), and composes `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>`.

### Rationale
This separation is correct because:
- `base.html` handles concerns that are **shared across all page types** (meta tags, stylesheets, scripts).
- `<c-app>` handles concerns that are **configurable per-integration** (layout mode, sidebar behaviour, branding).
- Integrators extend `mvp/base.html` in their own `base.html`, override `{% block app %}`, and declare their application shell with the desired attributes.

### Current Implementation Pattern (demo app)
```html
{% extends "mvp/base.html" %}
{% block app %}
  <c-app fixed-sidebar sidebar-expand="lg">
    <c-app.header>...</c-app.header>
    <c-app.sidebar brand-text="My App" />
    <c-app.main>{% block content %}{% endblock %}</c-app.main>
    <c-app.footer />
  </c-app>
{% endblock app %}
```

---

## 3. Component Hierarchy and Attribute Ownership

### Decision
Each component owns a specific set of attributes. Attributes must not be passed through intermediary dicts or `:attrs` — they are declared directly on the component tag.
User-facing template attributes are documented in kebab-case; django-cotton exposes them inside components as snake_case variables.

### Component → Attribute Map (Current + Recommended)

**`<c-app>` — Body-level wrapper**
| Attribute | Type | Default | Body Class |
|-----------|------|---------|------------|
| `fixed-sidebar` | bool | `False` | `.layout-fixed` |
| `fixed-header` | bool | `False` | `.fixed-header` |
| `fixed-footer` | bool | `False` | `.fixed-footer` |
| `sidebar-collapsible` | bool | `False` | `.sidebar-mini` |
| `collapsed` | bool | `False` | `.sidebar-collapse` (requires `sidebar-collapsible`) |
| `sidebar-expand` | string | `"lg"` | `.sidebar-expand-{value}` |
| `fill` | bool | `False` | `.fill` on `.app-wrapper` |
| `class` | string | `""` | Extra classes on `<body>` |

**`<c-app.header>` — Top navbar**
| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `class` | string | `"bg-body"` | Extra CSS classes on `<nav>` |
| `border` | bool | `True` | Bottom border on navbar |
| `container-class` | string | `"container-fluid"` | Inner container class |

**`<c-app.sidebar>` — Sidebar**
| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `brand-text` | string | `"Django MVP"` | Brand text in sidebar header |
| `brand-logo` | string | `""` | Full logo image path |
| `brand-icon` | string | `""` | Icon image path (for collapsed state) |
| `brand-url` | string | `"/"` | Brand link URL |
| `class` | string | `""` | Extra classes on `<aside>` |

**`<c-app.main>` — Main content area**
| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `fill` | bool | `False` | (currently unused, placeholder) |

**`<c-app.footer>` — Site footer**
| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `text` | string | `"Copyright © 2026"` | Default copyright text |
| `class` | string | `""` | Extra classes on `<footer>` |

### Rationale
Direct attribute declaration gives integrators a single, visible, greppable configuration surface. No hidden dicts, no Python config, no context processor indirection.

---

## 4. Menu System Integration

### Decision
Sidebar navigation uses `django-flex-menus` with the `AdminLTERenderer`. Menu data is defined in Python (`menus.py`) and rendered automatically by `<c-app.sidebar>` via `{% render_menu "AppMenu" renderer="adminlte" %}`.

### Rationale
- Menu registration is a Python concern (authorization, ordering, dynamic items) owned by the host application and external packages like `django-flex-menus`.
- The `<c-app.sidebar>` component provides a default slot that renders `AppMenu`; integrators can override the slot for custom navigation.
- Authorization/visibility is evaluated by the menu system, not by layout components (per spec clarification).

### Alternatives Considered
- Rendering menus via Cotton component attributes: Rejected. Menu trees are too complex for attribute-based declaration; Python-based menu builders are the correct abstraction.

---

## 5. Configuration Validation and Error Handling

### Decision
No feature-level validation is performed on Cotton attribute values. Invalid values pass through to django-cotton which applies its own attribute handling semantics.

### Rationale
Per spec clarification, this is explicitly out of scope. django-cotton already handles unknown/invalid attributes by either ignoring them or passing them through as HTML attributes.

---

## 6. Responsive Behaviour

### Decision
Responsive behaviour is controlled by the `sidebar-expand` attribute on `<c-app>`, which maps directly to AdminLTE 4's `.sidebar-expand-{breakpoint}` class. All valid Bootstrap 5 breakpoints are supported: `sm`, `md`, `lg`, `xl`, `xxl`.

### Rationale
AdminLTE 4 handles all responsive CSS through its built-in breakpoint classes. No custom responsive logic is needed in django-mvp.

---

## 7. Theme and Color Mode

### Decision
Theme switching (light/dark/auto) is handled by the `<c-navbar.widgets.theme-switcher>` widget component and `localStorage`. It is independent of layout configuration and uses the `data-bs-theme` attribute on `<html>`.

### Rationale
Color mode is a runtime user preference, not a layout configuration option. It should remain as a navbar widget, not an `<c-app>` attribute.

---

## 8. Context Processor Future

### Decision
The existing `mvp_config` context processor provides brand defaults and layout fallbacks. It should remain as a convenience for `base.html` (title, favicon, brand defaults) but must NOT be the primary configuration pathway. The demo app may use view-based context for its dynamic demos.

### Rationale
Keeping the context processor provides backward compatibility and sensible defaults without conflicting with the Cotton-attribute-only configuration mandate. It populates `{{ mvp.brand.text }}` for the page title, etc., but layout classes are determined solely by `<c-app>` attributes.
