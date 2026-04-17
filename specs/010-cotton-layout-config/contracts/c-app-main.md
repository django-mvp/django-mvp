# Contract: Application Main Component (`<c-app.main>`)

**Version**: 1.0 | **Feature**: 010-cotton-layout-config

## Purpose

Main content area between header and footer. Renders as `<main class="app-main ...">`.

## Attribute Contract

| Attribute | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| (none currently exposed) | — | — | — | — |

## Slot Contract

| Slot | Required | Content |
|------|----------|---------|
| (default) | Yes | Page content — typically a `<c-page>` component or raw HTML |

## Rendered Output

```html
<main class="app-main pb-0">
  {slot content}
</main>
```

## Invariants

- `.app-main` and `.pb-0` are always present.
- No attributes modify the element currently (future extension point).
