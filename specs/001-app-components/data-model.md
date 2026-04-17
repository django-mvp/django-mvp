# Data Model: Cotton App Layout Configuration

**Branch**: `001-app-components` | **Date**: 2026-04-17

> This feature has **no Django models** — all state is declarative via Cotton component
> attributes and rendered as CSS classes. This document describes the conceptual data
> model that maps component attributes to rendered output.
>
> User-facing template attributes are documented in kebab-case; django-cotton
> normalizes them to snake_case inside component templates.

---

## Entity 1: Application Shell (`<c-app>`)

The top-level layout wrapper. Renders the `<body>` tag and `.app-wrapper` div.
All layout behaviour is controlled by attributes on this component.

### Attributes

| Attribute | Type | Default | Rendered As |
|-----------|------|---------|-------------|
| `fixed-sidebar` | boolean | `False` | `.layout-fixed` on `<body>` |
| `fixed-header` | boolean | `False` | `.fixed-header` on `<body>` |
| `fixed-footer` | boolean | `False` | `.fixed-footer` on `<body>` |
| `sidebar-collapsible` | boolean | `False` | `.sidebar-mini` on `<body>` |
| `collapsed` | boolean | `False` | `.sidebar-collapse` on `<body>` (requires `sidebar-collapsible`) |
| `sidebar-expand` | string | `"lg"` | `.sidebar-expand-{value}` on `<body>` |
| `fill` | boolean | `False` | `.fill` on `.app-wrapper` |
| `class` | string | `""` | Appended to `<body>` class list |

### Rules

- `collapsed` has no visible effect unless `sidebar-collapsible` is also set.
- `sidebar-expand` must be a valid Bootstrap 5 breakpoint: `sm`, `md`, `lg`, `xl`, `xxl`.
- `fill` constrains `.app-wrapper` to `100vh` so only the content area scrolls.
- The class `.bg-body-tertiary` is always applied to `<body>`.

### Composition (child slots)

| Slot | Component | Required |
|------|-----------|----------|
| (default) | Any — typically `<c-app.header>`, `<c-app.sidebar>`, `<c-app.main>`, `<c-app.footer>` in order | Yes |

---

## Entity 2: Application Header (`<c-app.header>`)

The top navigation bar. Renders as `<nav class="app-header navbar ...">`.

### Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `class` | string | `"bg-body"` | CSS classes on `<nav>` |
| `border` | boolean | `True` | When `False`, adds `border-0` |
| `container-class` | string | `"container-fluid"` | Width constraint class |

### Slots

| Slot | Purpose |
|------|---------|
| (default) | Content in left nav (after hamburger toggle) |
| `left` | Explicit left nav items |
| `right` | Right-aligned nav items (search, widgets, avatar) |
| `tray` | Second row below main navbar |

### Child Components

- `<c-app.sidebar.toggle>` — Hamburger sidebar toggle button (rendered in header nav; file lives at `sidebar/toggle.html`)

---

## Entity 3: Application Sidebar (`<c-app.sidebar>`)

The main navigation sidebar. Renders as `<aside class="app-sidebar shadow ...">`.

### Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `brand-text` | string | `"Django MVP"` | Text next to brand logo |
| `brand-logo` | string | `""` | Full-size logo image path |
| `brand-icon` | string | `""` | Icon-size logo (for collapsed state) |
| `brand-url` | string | `"/"` | Brand link href |
| `class` | string | `""` | Extra classes on `<aside>` |

### Slots

| Slot | Purpose |
|------|---------|
| (default) | Override auto-rendered `AppMenu` with custom navigation |

### Default Behaviour

When no slot content is provided, renders `{% render_menu "AppMenu" renderer="adminlte" %}` automatically.

### Child Components

- `<c-app.sidebar.header>` — Branding/logo block (file: `sidebar/header.html`)
- `<c-app.sidebar.toggle>` — Hamburger toggle button (file: `sidebar/toggle.html`; rendered inside `<c-app.header>` nav)
- `<c-app.sidebar.menu>` — Navigation menu container (rendered by flex_menu)

---

## Entity 4: Application Main Content (`<c-app.main>`)

Content area between header and footer. Renders as `<main class="app-main ...">`.

### Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `fill` | boolean | `False` | Reserved for future use |

### Slots

| Slot | Purpose |
|------|---------|
| (default) | Page content — typically a `<c-page>` component or raw content |

---

## Entity 5: Application Footer (`<c-app.footer>`)

The site-level footer. Renders as `<footer class="app-footer ...">`.

### Attributes

| Attribute | Type | Default | Effect |
|-----------|------|---------|--------|
| `text` | string | `"Copyright © 2026"` | Default copyright text (used when no slot content) |
| `class` | string | `""` | Extra classes on `<footer>` |

### Slots

| Slot | Purpose |
|------|---------|
| (default) | Override default text with custom footer content |
| `right` | Right-aligned footer content |

---

## Entity 6: Navigation Node (Menu System)

Menu items are defined in Python via `django-flex-menus` and rendered by the `AdminLTERenderer`.

### Menu Item Types

| Type | Python Class | Rendered As |
|------|-------------|-------------|
| Leaf item | `MenuItem` | `<c-app.sidebar.menu.item>` — Link with icon, label, optional badge |
| Section header | `MenuGroup` | `<c-app.sidebar.menu.group>` — Nav header divider |
| Collapsible parent | `MenuCollapse` | `<c-app.sidebar.menu.collapse>` — Expandable group with children |

### Registration Pattern

```python
# myapp/menus.py
from mvp.menus import AppMenu, MenuGroup, MenuCollapse
from flex_menu import MenuItem

AppMenu.extend([
    MenuItem("Dashboard", url="/", icon="speedometer2"),
    MenuGroup("Management"),
    MenuCollapse("Users", icon="people", children=[
        MenuItem("All Users", url="/users/"),
        MenuItem("Add User", url="/users/add/"),
    ]),
])
```

### Renderer

The `AdminLTERenderer` (registered as `"adminlte"` in `FLEX_MENUS` settings) selects template based on item type and nesting depth:
- Depth 0: Container template
- Depth 1+: Parent (collapsible/group) or leaf item template

---

## Relationship Diagram

```
<c-app>                           ← Body classes (layout-fixed, fixed-header, etc.)
├── <c-app.header>                ← Top navbar (header.html)
│   ├── <c-app.sidebar.toggle>   ← Hamburger button (sidebar/toggle.html, rendered here)
│   ├── [left slot]               ← Left nav items
│   ├── [right slot]              ← Right nav items (widgets)
│   └── [tray slot]               ← Optional second row
├── <c-app.sidebar>               ← Navigation sidebar (sidebar/index.html)
│   ├── <c-app.sidebar.header>   ← Branding/logo block (sidebar/header.html)
│   └── <c-app.sidebar.menu>     ← AppMenu (via flex_menu)
│       ├── menu.item             ← Leaf nav link
│       ├── menu.group            ← Section header
│       └── menu.collapse         ← Collapsible group
│           └── menu.item         ← Nested leaf links
├── <c-app.main>                  ← Content area (main.html)
│   └── [slot: page content]      ← Typically <c-page> or raw content
├── <c-app.footer>                ← Site footer (footer.html)
│   ├── [default slot]            ← Copyright/custom text
│   └── [right slot]              ← Right-aligned content
└── <c-app.menu>                  ← Standalone app menu (menu.html)
    └── renders "Site Navigation" via sidebar renderer (independent of sidebar)
```

---

## Configuration Precedence

There is a single configuration source: **Cotton component attributes**.

1. Attribute explicitly set on the component tag → used
2. Attribute not set → `<c-vars>` default from component template → used
3. No default defined → attribute is absent from rendered output

No settings.py, no view context, no `:attrs` dict indirection. Declare attributes as kebab-case on component tags; django-cotton maps them to snake_case internally. Attribute values map 1:1 to CSS classes and HTML output.
