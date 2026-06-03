# Research: Mobile Footer Navigation

**Branch**: `017-dock` | **Date**: 2026-05-26

## 1. django-flex-menus Renderer Registration

**Decision**: Register `MobileFooterNavRenderer` as `"dock"` in the
`FLEX_MENUS["renderers"]` Django setting.

**Rationale**: Confirmed by reading `tests/settings.py` (lines 193-200). All existing
renderers (`adminlte`, `sidebar`, `navbar`, `dropdown`) follow this same pattern.
The renderer string key is passed directly to `{% render_menu menu renderer="key" %}`
in templates. This is the established project convention.

**Alternatives considered**: Class-based direct instantiation in templates — rejected
because the existing codebase exclusively uses the registry pattern, and a direct
import would couple templates to Python module paths.

---

## 2. `.show-on-mobile` CSS Visibility Mechanism

**Decision**: Apply `show-on-mobile` as the sole visibility class on the footer nav
container. No additional media query CSS is required in the new component.

**Rationale**: Confirmed by reading `mvp/static/scss/_utils.scss` (lines 1-26). The
`.show-on-mobile` class is defined inside the `.sidebar-expand` SCSS loop and maps
to every `sidebar-expand-{bp}` variant. When the parent `<body>` has
`sidebar-expand-lg` (the default), `.show-on-mobile` elements are hidden at `lg+`
and visible below `lg`. This is already the mechanism used by
`templates/cotton/app/header.html` (line 20) for the mobile logo.

**Alternatives considered**: Custom media query in the new SCSS file — rejected
because it would duplicate the breakpoint sync logic and break if the
`sidebar_expand` attribute on `c-app` is changed by the developer.

---

## 3. Sidebar Toggle Mechanism

**Decision**: The pre-populated sidebar toggle `MenuItem` will render as an element
with `data-lte-toggle="sidebar"`. No custom JS is required.

**Rationale**: Confirmed by reading `templates/cotton/app/header.html` (line 13) and
`templates/cotton/app/sidebar/toggle.html` (line 4). AdminLTE 4's JS intercepts
`data-lte-toggle="sidebar"` on any element and toggles the sidebar open/close state.
The `sidebar-toggle.js` script loaded in `base.html` (line 134) handles this.

**Alternatives considered**: Alpine.js `@click` dispatch — rejected because the
`data-lte-toggle` attribute is already the canonical mechanism across this codebase
and requires zero additional JavaScript.

**Implementation note**: The `MenuItem` for the sidebar toggle is stored with
`extra_context={"url": "#", "sidebar_toggle": True}`. The item template checks for
`sidebar_toggle` and renders a `<button type="button">` with `data-lte-toggle="sidebar"`
instead of an `<a href="#">` to avoid spurious URL navigation.

---

## 4. Cotton Component Placement Inside `c-app`

**Decision**: The `c-app.dock` component is inserted as a sibling of
`c-app.header`, `c-app.sidebar`, `c-app.main`, and `c-app.footer` within `c-app`'s
default slot in `base.html`.

**Rationale**: Confirmed by reading `templates/cotton/app/index.html`. The `c-app`
component renders a `<body>` containing `<div class="app-wrapper">{{ slot }}</div>`.
The slot accumulates all child elements from `base.html`. Because `position: fixed`
elements are positioned relative to the viewport (not their DOM parent), placing the
footer nav inside `.app-wrapper` has no adverse stacking context effect — AdminLTE 4
does not set `transform` or `overflow: hidden` on `.app-wrapper`.

**Alternatives considered**: New named slot on `c-app` — considered but rejected at
this stage to avoid a breaking change on `c-app`'s API. A `{% block app.mobile_footer_nav %}`
in `base.html` is sufficient for developer override.

---

## 5. Template Topology for `MobileFooterNavRenderer`

**Decision**: Two templates:

- `menus/dock/index.html` — depth-0 container; iterates children
- `menus/dock/item.html` — depth-1+ leaf; renders one BS5 `.nav-item`

**Rationale**: Mirrors the existing `NavRenderer` pattern (`menus/nav/wrapper.html` +
`menus/nav/link.html`). The mobile footer nav is intentionally flat (no nested menus),
so the parent template falls back to the same leaf template.

**Alternatives considered**: A single Cotton component for the whole nav — rejected
because django-flex-menus' rendering loop requires per-depth templates. The wrapper +
item split is the established pattern in this codebase.

---

## 6. Test Module Topology (Constitution Principle I + IX)

**Decision**: All new Cotton component tests go into the existing
`tests/test_components/test_c_app.py` module.

**Rationale**: The new component lives at `templates/cotton/app/dock.html`
— within the `cotton/app/` top-level directory. Constitution Principle IX mandates
one test module per top-level Cotton directory. `test_c_app.py` is the existing module
for `cotton/app/**` components. Adding dock tests there keeps the topology
consistent and avoids the prohibited one-module-per-component sprawl.

**Alternatives considered**: New `test_mobile_footer_nav.py` file — explicitly
prohibited by Constitution Principle IX unless justified. No justification exists here.

---

## 7. SCSS Sticky Positioning

**Decision**: A new `_dock.scss` partial handles sticky positioning and
z-index. It is `@use`d from `mvp.scss`.

**Rationale**: The `show-on-mobile` class handles responsive visibility. A small
dedicated SCSS partial is needed only for `position: fixed; bottom: 0; z-index` and
visual treatment (background, border-top). Bootstrap SCSS variables (`$zindex-fixed`,
`--bs-body-bg`, `--bs-border-color`) ensure theme compatibility.

**Alternatives considered**: Inline style on the Cotton component — rejected because
it cannot reference Bootstrap SCSS variables and would not respond to dark mode.

---

## 8. Pre-Populated Sidebar Toggle: Button vs. Link Rendering

**Decision**: The sidebar toggle item renders as `<button type="button">` with
`data-lte-toggle="sidebar"` rather than `<a href="#">`.

**Rationale**: Using `<a href="#">` causes a browser URL fragment change (`#`) and
can trigger unwanted scroll-to-top behaviour. A `<button>` with `type="button"` is
semantically correct for a non-navigation action, avoids href side effects, and is
keyboard-accessible by default.

**Alternatives considered**: `<a href="javascript:void(0)">` — rejected as an
anti-pattern; `<a href="#">` — rejected for scroll side effects.
