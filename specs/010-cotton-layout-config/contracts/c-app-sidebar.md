# Contract: Application Sidebar Component (`<c-app.sidebar>`)

**Version**: 1.0 | **Feature**: 010-cotton-layout-config

## Purpose

Main navigation sidebar. Renders as `<aside class="app-sidebar shadow ...">`.
Includes branding block and navigation menu. When no custom slot content is provided,
renders `AppMenu` automatically via `django-flex-menus`.

User-facing template attributes are kebab-case; django-cotton normalizes them to
snake_case inside the component template.

## Attribute Contract

| Attribute | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `brand-text` | string | `"Django MVP"` | No | Text next to brand logo |
| `brand-logo` | string | `""` | No | Full-size logo image path |
| `brand-icon` | string | `""` | No | Icon-size logo (collapsed sidebar state) |
| `brand-url` | string | `"/"` | No | Brand link href |
| `class` | string | `""` | No | Extra CSS classes on `<aside>` |

## Slot Contract

| Slot | Required | Content |
|------|----------|---------|
| (default) | No | Custom navigation content. When absent, renders `{% render_menu "AppMenu" renderer="adminlte" %}` |

## Child Components

| Component | Purpose | Auto-included |
|-----------|---------|---------------|
| `<c-app.sidebar.header>` | Branding/logo block (file: `sidebar/header.html`) | Yes |
| `<c-app.sidebar.toggle>` | Hamburger toggle button (file: `sidebar/toggle.html`; rendered inside `<c-app.header>`) | Defined here; included by header |
| `<c-app.sidebar.menu>` | Navigation menu container | Yes (via default slot) |

## Rendered Output

```html
<aside class="app-sidebar shadow [class]" data-bs-theme="dark">
  <c-app.sidebar.header text brand-logo brand-icon link />
  </div>
  <div class="sidebar-wrapper">
    <nav class="mt-2">
      {slot content OR {% render_menu "AppMenu" renderer="adminlte" %}}
    </nav>
  </div>
</aside>
<div class="sidebar-overlay" data-lte-toggle="sidebar" data-lte-dismiss="sidebar-menu"></div>
```

## Invariants

- `.app-sidebar` and `.shadow` are always present on `<aside>`.
- `<c-app.sidebar.header>` branding block is always rendered (may have empty logo if not configured).
- `data-bs-theme="dark"` is set by default (dark sidebar).
- Sidebar overlay div is always rendered (for mobile drawer dismiss).
- `AppMenu` renders automatically when slot is empty.
