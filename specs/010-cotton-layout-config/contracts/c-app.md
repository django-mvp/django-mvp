# Contract: Application Shell Component (`<c-app>`)

**Version**: 1.0 | **Feature**: 010-cotton-layout-config

## Purpose

Root application wrapper that renders the `<body>` element. All AdminLTE 4 layout
behaviour is controlled by attributes on this component. Child components
(`<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>`) are placed
in the default slot.

User-facing template attributes are kebab-case; django-cotton normalizes them to
snake_case inside the component template.

## Attribute Contract

| Attribute | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `fixed-sidebar` | boolean | (absent) | No | Adds `.layout-fixed` to `<body>` |
| `fixed-header` | boolean | (absent) | No | Adds `.fixed-header` to `<body>` |
| `fixed-footer` | boolean | (absent) | No | Adds `.fixed-footer` to `<body>` |
| `sidebar-collapsible` | boolean | (absent) | No | Adds `.sidebar-mini` to `<body>` |
| `collapsed` | boolean | (absent) | No | Adds `.sidebar-collapse` (requires `sidebar-collapsible`) |
| `sidebar-expand` | string | `"lg"` | No | Breakpoint class `.sidebar-expand-{value}` |
| `fill` | boolean | (absent) | No | Adds `.fill` to `.app-wrapper` |
| `class` | string | `""` | No | Extra CSS classes on `<body>` |

## Slot Contract

| Slot | Required | Content |
|------|----------|---------|
| (default) | Yes | `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>` |

## Rendered Output

```html
<body class="bg-body-tertiary [layout-fixed] [fixed-header] [fixed-footer] [sidebar-mini] [sidebar-collapse] sidebar-expand-{bp} [extra-class]">
  <div class="app-wrapper [fill]">
    {slot content}
  </div>
</body>
```

## Invariants

- `.bg-body-tertiary` is always present on `<body>`.
- `.sidebar-expand-{bp}` is always present (defaults to `lg`).
- `.sidebar-collapse` only appears when `sidebar-collapsible` is also set.
- No validation is performed on attribute values.
