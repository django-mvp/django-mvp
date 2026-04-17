# Contract: Application Footer Component (`<c-app.footer>`)

**Version**: 1.0 | **Feature**: 010-cotton-layout-config

## Purpose

Site-level footer. Renders as `<footer class="app-footer ...">` with default
copyright text and optional right-aligned content.

## Attribute Contract

| Attribute | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `text` | string | `"Copyright © 2026"` | No | Default copyright text when no slot content |
| `class` | string | `""` | No | Extra CSS classes on `<footer>` |

## Slot Contract

| Slot | Required | Content |
|------|----------|---------|
| (default) | No | Override default text with custom footer content |
| `right` | No | Right-aligned footer content |

## Rendered Output

```html
<footer class="app-footer [class]">
  {slot content OR text}
  <div class="float-end">
    {right slot content}
  </div>
</footer>
```

## Invariants

- `.app-footer` is always present.
- When no slot content is provided, the `text` attribute value is rendered.
- Right slot content is always wrapped in `.float-end`.
