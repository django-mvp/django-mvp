# Public API Contract: Mobile Footer Navigation

**Branch**: `017-mobile-footer-nav` | **Date**: 2026-05-26

---

## Python API

### `mvp.menus.MobileFooterMenu`

**Type**: `flex_menu.Menu` singleton instance

**Import path**: `from mvp.menus import MobileFooterMenu`

**Contract**:
- Always present after `import mvp.menus`
- `MobileFooterMenu.children` is a mutable list of `MenuItem` instances
- Starts with one pre-populated `MenuItem` named `"sidebar_toggle"`
- Developers MUST NOT reassign `MobileFooterMenu` itself; they MAY mutate `.children`
- Name `"MobileFooterMenu"` is stable across minor releases

---

### `mvp.renderers.MobileFooterNavRenderer`

**Type**: Class (subclass of `flex_menu.renderers.BaseRenderer`)

**Import path**: `from mvp.renderers import MobileFooterNavRenderer`

**Contract**:
- Registered as `"mobile-footer-nav"` in `FLEX_MENUS["renderers"]`
- Renders depth-0 output via `menus/mobile-footer-nav/wrapper.html`
- Renders depth-1+ output via `menus/mobile-footer-nav/item.html`
- Items with `extra_context["sidebar_toggle"] == True` render as
  `<button data-lte-toggle="sidebar">` not `<a>` links
- `active` class applied to `.nav-link` when item URL matches `request.path`
- Class is stable and subclassable

---

## Template Block API

### `{% block app.mobile_footer_nav %}`

**File**: `mvp/templates/mvp/base.html`

**Contract**:
- Block is always present inside `<c-app>`, after `{% block app.footer %}`
- Default content: `<c-app.mobile-footer-nav />`
- Developers MAY override to customise, replace, or remove the footer nav
- Block name `app.mobile_footer_nav` is stable across minor releases

---

## Cotton Component API

### `<c-app.mobile-footer-nav>`

**Path**: `mvp/templates/cotton/app/mobile-footer-nav.html`

**Attributes**:

| Attribute | Type    | Required | Default | Description                              |
|-----------|---------|----------|---------|------------------------------------------|
| `class`   | `str`   | No       | `""`    | Additional CSS classes on the `<nav>` element |

**Contract**:
- Always renders a `<nav aria-label="Mobile navigation">` element
- Always applies `show-on-mobile` CSS class (responsive visibility)
- Always renders `MobileFooterMenu` via the `"mobile-footer-nav"` renderer
- Visible below the app's sidebar-expand breakpoint; hidden at or above it
- Component name `c-app.mobile-footer-nav` is stable across minor releases

---

## Settings Contract

```python
FLEX_MENUS = {
    "renderers": {
        "mobile-footer-nav": "mvp.renderers.MobileFooterNavRenderer",
    }
}
```

**Contract**:
- Key `"mobile-footer-nav"` MUST be present for the component to render
- Missing key produces a django-flex-menus `RendererNotFound` error at render time
- Value MUST be the full dotted Python path to `MobileFooterNavRenderer` or a subclass

---

## Stability Guarantees

| Symbol                         | Stability |
|-------------------------------|-----------|
| `mvp.menus.MobileFooterMenu`  | Stable    |
| `MobileFooterMenu.children`   | Stable    |
| `mvp.renderers.MobileFooterNavRenderer` | Stable |
| `c-app.mobile-footer-nav`     | Stable    |
| `c-app.mobile-footer-nav` `class` attribute | Stable |
| `{% block app.mobile_footer_nav %}` | Stable |
| `"mobile-footer-nav"` renderer key | Stable |
| Template paths (`menus/mobile-footer-nav/*.html`) | Internal — may change |
