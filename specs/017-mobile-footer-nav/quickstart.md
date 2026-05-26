# Quickstart: Mobile Footer Navigation

**Branch**: `017-mobile-footer-nav` | **Date**: 2026-05-26

---

## Prerequisites

- `django-mvp` installed and wired up (see `skills/django-mvp/SKILL.md`)
- `FLEX_MENUS` already configured in your Django settings

---

## Step 1 — Register the Renderer

Add `"mobile-footer-nav"` to the `FLEX_MENUS["renderers"]` dictionary in your
Django settings alongside the existing `adminlte` renderer:

```python
# settings.py
FLEX_MENUS = {
    "renderers": {
        "adminlte": "mvp.renderers.AdminLTERenderer",
        "mobile-footer-nav": "mvp.renderers.MobileFooterNavRenderer",
        # ... other renderers
    },
}
```

---

## Step 2 — The Default Footer Nav

No additional configuration is required. The `MobileFooterMenu` singleton is
pre-populated with a sidebar toggle item. The `c-app.mobile-footer-nav` component
is included in `base.html` by default via:

```html
{% block app.mobile_footer_nav %}
  <c-app.mobile-footer-nav />
{% endblock app.mobile_footer_nav %}
```

On mobile screens (below the `sidebar_expand` breakpoint), users will see the
footer nav with the sidebar toggle button. On larger screens it is hidden
automatically via the `.show-on-mobile` CSS utility.

---

## Step 3 — Add Custom Items

Import `MobileFooterMenu` and append `MenuItem` instances in your app's `menus.py`
(or `apps.py` `ready()` method):

```python
# yourapp/menus.py
from flex_menu import MenuItem
from mvp.menus import MobileFooterMenu

MobileFooterMenu.children.append(
    MenuItem(
        name="home",
        view_name="yourapp:home",
        extra_context={
            "label": "Home",
            "icon": "house",          # Bootstrap Icons key (via django-easy-icons)
        }
    )
)
```

Items appear in the order they are registered, from left to right.

---

## Step 4 — Remove or Override the Default Footer Nav

To disable the footer nav entirely in a specific template, override the block:

```html
{% block app.mobile_footer_nav %}{% endblock %}
```

To replace the footer nav with a custom version, override the block and supply
your own component or markup.

---

## Step 5 — Removing the Pre-Populated Sidebar Toggle

If you want to remove the built-in sidebar toggle item:

```python
# yourapp/apps.py or menus.py
from mvp.menus import MobileFooterMenu

MobileFooterMenu.children = [
    item for item in MobileFooterMenu.children
    if item.name != "sidebar_toggle"
]
```

---

## Component Attributes

The `c-app.mobile-footer-nav` component accepts one optional attribute:

| Attribute | Type  | Default | Description                          |
|-----------|-------|---------|--------------------------------------|
| `class`   | `str` | `""`    | Extra CSS classes on the `<nav>` tag |

Example — add a custom background variant:

```html
{% block app.mobile_footer_nav %}
  <c-app.mobile-footer-nav class="bg-dark" />
{% endblock app.mobile_footer_nav %}
```
