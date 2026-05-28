# Data Model: Brand Logo & Icon Templatetags

**Phase**: 1 — Design
**Branch**: `019-brand-logo-templatetags`
**Date**: 2026-05-28

---

## Overview

This feature has **no database entities**. All "data" is configuration (Django settings) and in-memory callables (resolver functions). The conceptual model covers three things: the configuration schema, the resolver callable contract, and the bundled static asset layout.

---

## Configuration Schema

Settings are read from the host project's Django settings module via `mvp/config.py` using `getattr(settings, name, default)`.

| Setting Key | Type | Default | Description |
|-------------|------|---------|-------------|
| `MVP_LOGO_RESOLVER` | `str` (dotted import path) | `"mvp.utils.logo_url"` | Dotted path to the logo resolver callable |
| `MVP_ICON_RESOLVER` | `str` (dotted import path) | `"mvp.utils.icon_url"` | Dotted path to the icon resolver callable |

**Renamed from**:
- `MVP_LOGO_URL_FUNC` → `MVP_LOGO_RESOLVER`
- `MVP_ICON_URL_FUNC` → `MVP_ICON_RESOLVER`

**Validation rules**:
- If a setting is absent: default resolver is used, no error.
- If a setting is present but the import path cannot be resolved: `ImproperlyConfigured` is raised on first tag use.
- Neither setting is required; both have safe defaults.

---

## Resolver Callable Contract

Both `MVP_LOGO_RESOLVER` and `MVP_ICON_RESOLVER` must point to a callable with this exact signature:

```python
def resolver(request, height, theme) -> str | None:
    ...
```

### Arguments (Template)

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `height` | `int` | **Yes** | — | Maximum image height in pixels. Always required; passed to the resolver as a sizing hint. |
| `theme` | `str` | No | `"light"` | Theme identifier string. Typically `"light"` or `"dark"`; any string is valid. |

> **Note**: The `request` object is extracted automatically from the template context via `takes_context=True`. It is NOT a template argument.

### Return Value

| Value | Description |
|-------|-------------|
| `str` | URL string to the brand asset. Rendered directly into the template. |
| `None` or `""` | No asset available; templatetag renders as empty string. |

### Invariants

- Resolver MUST accept all three arguments (positional or keyword).
- Resolver MUST NOT raise exceptions that affect page rendering (templatetag catches all and returns `""`).
- Resolver MUST return a plain string or `None`; `mark_safe()` objects are not expected.

---

## Default Resolver Behaviour

### `mvp.utils.logo_url` (default logo resolver)

| Input | Output |
|-------|--------|
| Any `theme` | `static("brand/logo.svg")` |

Falls back to `logo.svg` for all themes. No dark logo variant is bundled.

### `mvp.utils.icon_url` (default icon resolver)

| Input `theme` | Output |
|---------------|--------|
| `"light"` | `static("brand/icon_light.svg")` |
| `"dark"` | `static("brand/icon_dark.svg")` |
| Any other | `static("brand/icon.svg")` (generic fallback) |

---

## Bundled Static Asset Layout

```text
mvp/static/brand/
├── logo.svg          # Light logo (and dark fallback) — used by default logo resolver
├── icon_light.svg    # Light icon — used by default icon resolver
├── icon_dark.svg     # Dark icon — used by default icon resolver
├── icon.svg          # Generic icon fallback
└── icons.svg         # Icon sprite (unrelated to this feature)
```

No new static files are added by this feature.

---

## State Transitions

None — this feature is stateless. Each templatetag call is an independent URL resolution. No session state, no database reads, no caching.

---

## Validation Rules Summary

| Rule | Source |
|------|--------|
| Resolver path importable if set | FR-013 |
| Resolver accepts (request, height, theme) | FR-011 |
| Resolver returns str or None | Callable contract |
| Tag returns `""` on `None` or exception | FR-012 |
| Tag does not call `mark_safe()` | FR-017 |
| Theme defaults to `"light"` | FR-003, FR-010 |
| Height defaults to `None` | FR-004 |
