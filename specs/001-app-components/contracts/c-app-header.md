# Contract: Application Header Component (`<c-app.header>`)

**Version**: 1.0 | **Feature**: 001-app-components

## Purpose

Top navigation bar. Renders as `<nav class="app-header navbar ...">` with support
for left/right navigation zones, an optional tray, and a sidebar toggle button.

User-facing template attributes are kebab-case; django-cotton normalizes them to
snake_case inside the component template.

## Attribute Contract

| Attribute | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `class` | string | `"bg-body"` | No | CSS classes on the `<nav>` element |
| `border` | boolean | `True` | No | When `False`, adds `border-0` to remove bottom border |
| `container-class` | string | `"container-fluid"` | No | Inner container width constraint |

## Slot Contract

| Slot | Required | Content |
|------|----------|---------|
| (default) | No | Content placed in left navigation area (after toggle) |
| `left` | No | Explicit left navigation items |
| `right` | No | Right-aligned navigation items (search, widgets, avatar) |
| `tray` | No | Second row below the main navbar |

## Child Components

| Component | Purpose | Auto-included |
|-----------|---------|---------------|
| `<c-app.sidebar.toggle>` | Hamburger sidebar toggle button (file: `sidebar/toggle.html`) | Yes — rendered as first left nav item |

## Rendered Output

```html
<nav class="app-header navbar navbar-expand {class} [border-0]">
  <div class="[container-class value]">
    <ul class="navbar-nav">
      <c-app.sidebar.toggle />
      {left slot or default slot content}
    </ul>
    <ul class="navbar-nav ms-auto">
      {right slot content}
    </ul>
  </div>
  {tray slot if provided}
</nav>
```

## Invariants

- `.app-header`, `.navbar`, `.navbar-expand` are always present.
- `<c-app.sidebar.toggle>` is always rendered as the first left nav item (file: `sidebar/toggle.html`).
- Default `class` is `bg-body` (not empty string).
