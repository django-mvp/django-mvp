# Data Model: Mobile Footer Navigation

**Branch**: `017-mobile-footer-nav` | **Date**: 2026-05-26

---

## Overview

This feature introduces no new database models. All entities are in-memory Python
objects and Django templates that extend the existing django-flex-menus menu system.

---

## Entity 1: `MobileFooterMenu`

**Kind**: In-memory singleton (`flex_menu.Menu` instance)
**Module**: `mvp/menus.py`
**Exported**: Yes — `from mvp.menus import MobileFooterMenu`

```python
from flex_menu import Menu, MenuItem

MobileFooterMenu = Menu("MobileFooterMenu", children=[
    MenuItem(
        name="sidebar_toggle",
        extra_context={
            "label": "Menu",
            "icon": "list",        # django-easy-icons Bootstrap Icons key
            "url": "#",
            "sidebar_toggle": True,  # renderer flag → <button data-lte-toggle="sidebar">
        }
    )
])
```

**Attributes** (inherited from `flex_menu.Menu`):

| Attribute  | Type          | Description                                   |
|------------|---------------|-----------------------------------------------|
| `name`     | `str`         | Registry name — `"MobileFooterMenu"`           |
| `children` | `list[MenuItem]` | Ordered list of nav items                  |

**Lifecycle**: Instantiated at module import time (same pattern as `AppMenu`). Items
can be appended after import using `MobileFooterMenu.children.append(...)` or
`MobileFooterMenu.children.extend([...])`.

**Relationships**: Independent of `AppMenu`. Shares the `MenuItem` class from
django-flex-menus but maintains a separate children list.

**Visibility / Permissions**: Items support the same `visible_to` / permission
mechanism as `AppMenu` items (inherited from `BaseRenderer.get_context_data` in
django-flex-menus). No additional permission infrastructure is required.

---

## Entity 2: `MobileFooterNavRenderer`

**Kind**: Python class (django-flex-menus `BaseRenderer` subclass)
**Module**: `mvp/renderers.py`
**Registry key**: `"mobile-footer-nav"` (in Django's `FLEX_MENUS["renderers"]` setting)

```python
from flex_menu.renderers import BaseRenderer

class MobileFooterNavRenderer(BaseRenderer):
    """Renderer for the mobile footer navigation bar.

    Produces flat BS5 .nav-item > .nav-link HTML for each registered MenuItem.
    Sidebar toggle items are rendered as <button data-lte-toggle="sidebar">
    rather than anchor links.

    Config:
        FLEX_MENUS["renderers"]["mobile-footer-nav"] = "mvp.renderers.MobileFooterNavRenderer"
    """

    templates = {
        0: {"default": "menus/mobile-footer-nav/wrapper.html"},
        "default": {
            "parent": "menus/mobile-footer-nav/item.html",
            "leaf":   "menus/mobile-footer-nav/item.html",
        },
    }
```

**Template resolution**:

| Depth | Kind   | Template                                       |
|-------|--------|------------------------------------------------|
| 0     | root   | `menus/mobile-footer-nav/wrapper.html`         |
| 1+    | leaf   | `menus/mobile-footer-nav/item.html`            |
| 1+    | parent | `menus/mobile-footer-nav/item.html` (flat nav) |

---

## Entity 3: `menus/mobile-footer-nav/wrapper.html`

**Kind**: Django template (depth-0 renderer output)
**Path**: `mvp/templates/menus/mobile-footer-nav/wrapper.html`

Responsibility: Renders the `<ul class="nav">` list and iterates children.

```html
{% load flex_menu %}
<ul class="nav w-100">
  {% for child in children %}
    {% render_item child renderer=renderer %}
  {% endfor %}
</ul>
```

---

## Entity 4: `menus/mobile-footer-nav/item.html`

**Kind**: Django template (depth-1+ renderer output)
**Path**: `mvp/templates/menus/mobile-footer-nav/item.html`

Responsibility: Renders one BS5 `.nav-item`. Sidebar toggle items render as
`<button data-lte-toggle="sidebar">`; all other items render as `<a>` links.

```html
{% load easy_icons %}
<li class="nav-item flex-grow-1 text-center">
  {% if sidebar_toggle %}
    <button type="button"
            class="nav-link w-100{% if selected %} active{% endif %}"
            data-lte-toggle="sidebar">
      {% icon icon %}
      <span class="d-block" style="font-size: 0.7rem">{{ label }}</span>
    </button>
  {% else %}
    <a class="nav-link{% if selected %} active{% endif %}"
       href="{{ url }}">
      {% icon icon %}
      <span class="d-block" style="font-size: 0.7rem">{{ label }}</span>
    </a>
  {% endif %}
</li>
```

---

## Entity 5: `c-app.mobile-footer-nav` Cotton Component

**Kind**: Django Cotton component
**Path**: `mvp/templates/cotton/app/mobile-footer-nav.html`

Responsibility: Wraps the rendered menu in a `<nav>` element with `show-on-mobile`
for responsive hiding and `aria-label` for accessibility.

```html
{% load flex_menu i18n %}
<c-vars class />
<nav class="mobile-footer-nav show-on-mobile{% if class %} {{ class }}{% endif %}"
     aria-label="{% trans 'Mobile navigation' %}">
  {% render_menu "MobileFooterMenu" renderer="mobile-footer-nav" %}
</nav>
```

**Attributes**:

| Attribute | Type  | Default | Description                           |
|-----------|-------|---------|---------------------------------------|
| `class`   | `str` | `""`    | Extra CSS classes appended to `<nav>` |

---

## Entity 6: SCSS Partial `_mobile-footer-nav.scss`

**Kind**: SCSS partial
**Path**: `mvp/static/scss/_mobile-footer-nav.scss`
**Imported by**: `mvp/static/scss/mvp.scss`

Responsibility: Sticky positioning, z-index, visual treatment, and nav-link vertical layout.

```scss
.mobile-footer-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: $zindex-fixed;
  background-color: var(--bs-body-bg);
  border-top: 1px solid var(--bs-border-color);

  // Pad bottom for devices with a home indicator (iOS safe area)
  padding-bottom: env(safe-area-inset-bottom, 0);

  .nav-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0.25rem;
  }
}
```

---

## Entity 7: Base Template Block

**Kind**: Django template block
**File**: `mvp/templates/mvp/base.html`
**Block name**: `app.mobile_footer_nav`

```html
{% block app.mobile_footer_nav %}
  <c-app.mobile-footer-nav />
{% endblock app.mobile_footer_nav %}
```

Inserted inside `<c-app>`, after `{% block app.footer %}`.

---

## State Transitions

No state transitions. The component is stateless server-side rendered output.
Active state on `.nav-link` is determined at render time by comparing the current
request URL against each item's `url` field (handled by `BaseRenderer`).

---

## Validation Rules

| Rule                                    | Enforcement                         |
|-----------------------------------------|-------------------------------------|
| `MobileFooterMenu` name must be unique  | django-flex-menus registry (runtime)|
| Items must be `MenuItem` instances      | Type — duck typed at render time    |
| `icon` in `extra_context` is optional   | Template: `{% icon icon %}` is safe when `icon` is empty |
| `url` defaults to `"#"` for toggle item | Hard-coded in pre-populated item    |
