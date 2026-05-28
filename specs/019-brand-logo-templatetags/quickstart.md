# Quickstart: Brand Logo & Icon Templatetags

**Feature**: 019 — Brand Logo & Icon Templatetags
**Package**: `django-mvp`

---

## Overview

`django-mvp` provides two template tags — `logo_url` and `icon_url` — that resolve your application's brand assets (logo and icon) for a given theme. Both tags call a configurable resolver function, making it easy to swap in per-tenant, thumbnail-aware, or CDN-backed asset resolution without touching your templates.

By default the tags use built-in resolver functions that return bundled SVG files. This is ready to use with zero configuration.

---

## Step 1: Load the Tag Library

```django
{% load mvp %}
```

Add this to any template that uses `logo_url` or `icon_url`.

---

## Step 2: Use the Tags

### Display the logo

```django
{# height is always required #}
<img src="{% logo_url height=40 %}" alt="Logo" style="max-height: 40px; width: auto;">
```

### Display the icon

```django
<img src="{% icon_url height=32 %}" alt="Icon" style="max-height: 32px; width: auto;">
```

### With a theme override

```django
{# Explicit dark theme #}
<img src="{% logo_url height=40 theme="dark" %}" alt="Dark Logo" style="max-height: 40px; width: auto;">

{# Explicit light theme #}
<img src="{% icon_url height=32 theme="light" %}" alt="Light Icon" style="max-height: 32px; width: auto;">
```

The `height` argument is **required** and is passed to your resolver function as a sizing hint. The default resolver ignores it (SVG files scale freely), but custom resolvers — especially thumbnailer-backed ones — use it to return the appropriate image variant.

---

## Step 3: Configure Your Brand Assets (Optional)

If you want to serve your own brand assets, point the settings to a resolver function:

```python
# settings.py
MVP_LOGO_RESOLVER = "myapp.branding.get_logo_url"
MVP_ICON_RESOLVER = "myapp.branding.get_icon_url"
```

### Writing a Resolver Function

A resolver function must accept exactly three arguments: `request`, `height`, and `theme`.

```python
# myapp/branding.py
from django.templatetags.static import static

def get_logo_url(request, height, theme):
    """Return the URL to the application logo for the given theme."""
    if theme == "dark":
        return static("myapp/brand/logo_dark.svg")
    return static("myapp/brand/logo_light.svg")  # default / light fallback

def get_icon_url(request, height, theme):
    """Return the URL to the application icon for the given theme."""
    if theme == "dark":
        return static("myapp/brand/icon_dark.svg")
    return static("myapp/brand/icon_light.svg")
```

---

## Advanced: Per-Tenant / Multi-Brand Resolver

For apps with multiple tenants or white-label branding, use the `request` argument to look up the current tenant's assets:

```python
# myapp/branding.py
from django.templatetags.static import static

def get_logo_url(request, height, theme):
    tenant = getattr(request, "tenant", None) if request else None
    if tenant and tenant.logo_url:
        return tenant.logo_url
    # Fall back to default brand asset
    return static("myapp/brand/logo.svg")
```

Templates remain unchanged — just swap in your resolver via settings.

---

## Advanced: Thumbnailing / Raster Images

For non-SVG images where you need to serve size-optimised variants, use the `height` argument:

```python
# myapp/branding.py

def get_logo_url(request, height, theme):
    base_url = "https://cdn.example.com/brand/logo.png"
    if height:
        return f"{base_url}?h={height}"
    return base_url
```

---

## Behaviour Reference

| Scenario | Result |
|----------|--------|
| `MVP_LOGO_RESOLVER` not set | Built-in default (`mvp.utils.logo_url`) used |
| `MVP_LOGO_RESOLVER` set, import fails | `ImproperlyConfigured` raised on first tag call |
| Resolver returns `None` or `""` | Tag renders as empty string |
| Resolver raises an exception | Tag renders as empty string silently |
| `theme` not supplied | Defaults to `"light"` |
| `height` omitted | Template error — `height` is required; always supply a value |
| Only a light asset exists | Resolver returns light asset for all themes |

---

## Default Asset Locations

The default resolver returns bundled placeholder assets:

| Tag | Asset |
|-----|-------|
| `{% logo_url height=40 %}` | `mvp/static/brand/logo.svg` (all themes) |
| `{% icon_url height=32 theme="light" %}` | `mvp/static/brand/icon_light.svg` |
| `{% icon_url height=32 theme="dark" %}` | `mvp/static/brand/icon_dark.svg` |
| `{% icon_url height=32 %}` (no theme) | `mvp/static/brand/icon_light.svg` |

Replace with your own brand assets by configuring `MVP_LOGO_RESOLVER` / `MVP_ICON_RESOLVER`.
