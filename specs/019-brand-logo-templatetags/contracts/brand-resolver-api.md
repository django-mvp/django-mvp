# Public API Contract: Brand Resolver Callable

**Feature**: 019 — Brand Logo & Icon Templatetags
**Type**: Python callable interface contract
**Stability**: Alpha

---

## Contract: Brand Resolver Callable

Any function registered as `MVP_LOGO_RESOLVER` or `MVP_ICON_RESOLVER` MUST conform to this contract.

### Signature

```python
def my_brand_resolver(
    request: HttpRequest | None,
    height: int | None,  # int from template calls; None when invoked outside template context (e.g. management commands)
    theme: str,
) -> str | None:
    ...
```

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `request` | `HttpRequest \| None` | Yes | The current request. `None` if no request context is available (e.g., management commands, offline rendering). |
| `height` | `int \| None` | Yes | Advisory max image height in pixels. `None` means no hint. Use for thumbnailer integration. |
| `theme` | `str` | Yes | Theme identifier. Typically `"light"` or `"dark"`. Any string is valid; resolver decides how to handle unknown values. |

### Return Values

| Value | Meaning |
|-------|---------|
| Non-empty `str` | URL to the brand asset. Rendered inline by the templatetag. |
| `""` or `None` | No asset available. Templatetag renders as empty string. |

### Constraints

- The function MUST accept all three arguments. Missing arguments will cause a `TypeError` at call time (not caught by `ImproperlyConfigured` checks).
- The function MUST NOT raise exceptions that could break page rendering. If the function may fail, it SHOULD handle exceptions internally.
- The function MUST return a plain `str`, `None`, or `""`. Returning `mark_safe()` is not needed and will result in double-escaping if Django auto-escaping is active.

---

## Contract: Template Tag Usage

### `logo_url`

```django
{% load mvp %}

{# height is required #}
<img src="{% logo_url height=40 %}">

{# With theme override #}
<img src="{% logo_url height=40 theme="dark" %}">

{# Sidebar logo (small) #}
<img src="{% logo_url height=32 %}">
```

### `icon_url`

```django
{% load mvp %}

{# height is required #}
<img src="{% icon_url height=32 %}">

{# With theme override #}
<img src="{% icon_url height=32 theme="dark" %}">
```

### Tag Argument Contract

| Argument | Position | Type | Default | Description |
|----------|----------|------|---------|-------------|
| `height` | keyword | `int` | **required** | Max image height in pixels. Always supply this; passed to the resolver as a sizing hint. |
| `theme` | keyword | `str` | `"light"` | Theme identifier passed to resolver |

> **Note**: The `request` object is extracted automatically from the Django template context (`takes_context=True`). Template authors do not pass it explicitly.

### Output

Both tags render the resolver's return value as a plain string directly into the template. Django auto-escaping applies normally.

---

## Contract: Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `MVP_LOGO_RESOLVER` | `str` | `"mvp.utils.logo_url"` | Dotted Python import path to logo resolver callable |
| `MVP_ICON_RESOLVER` | `str` | `"mvp.utils.icon_url"` | Dotted Python import path to icon resolver callable |

**Error behaviour**:

| Scenario | Behaviour |
|----------|-----------|
| Setting absent | Default resolver used silently |
| Setting present, import fails | `django.core.exceptions.ImproperlyConfigured` raised on first tag call |
| Resolver returns `None` | Tag outputs empty string |
| Resolver raises exception | Tag outputs empty string silently |

---

## Example: Minimal Custom Resolver

```python
# myapp/branding.py
from django.templatetags.static import static

def get_logo_url(request, height, theme):
    if theme == "dark":
        return static("myapp/brand/logo_dark.svg")
    return static("myapp/brand/logo_light.svg")
```

```python
# settings.py
MVP_LOGO_RESOLVER = "myapp.branding.get_logo_url"
```

## Example: Per-Tenant Multi-Brand Resolver

```python
# myapp/branding.py

def get_logo_url(request, height, theme):
    if request is None:
        return None
    tenant = getattr(request, "tenant", None)
    if tenant and tenant.logo_url:
        return tenant.logo_url
    from django.templatetags.static import static
    return static("myapp/brand/logo_default.svg")
```
