# Django MVP — Domain Model

## Core Concepts

### Component

A reusable, override-able UI building block implemented as a Cotton template. Components define the **public API** of django-mvp. They are named after their domain role, not their implementation or any external design system.

**Examples:** `c-app`, `c-page`, `c-card`, `c-grid`

### Component Attribute

A configurable property declared via `<c-vars>` that controls a component's appearance or behavior. Attributes are the **only** way to customize components — raw CSS classes must not appear in templates that demonstrate components.

**Valid attributes:** `title`, `icon`, `variant`, `size`, `gap`, `cols` (on `c-grid`)
**Invalid:** `class="flex grid-cols-3"` — use component attributes instead.

### Override

The mechanism by which a consumer replaces a package component with their own implementation. Drop a template at the same path in your project's template directory and it replaces the package version. This is the **primary extension point**.

### Mixin

A Python class that provides cross-cutting behavior for Django views. Consumers compose their own view from exported mixins rather than using factory functions or pre-built concrete classes. This follows Django's standard pattern.

**Exported mixins:** `PageMixin`, `BaseTemplateNameMixin`, `SearchMixin`, `OrderMixin`, `CRUDDirectoryMixin`
**Concrete views:** `MVPListView`, `MVPCreateView`, `MVPDetailView`, `MVPUpdateView`, `MVPDeleteView`

### Integration

A guarded Python module under `mvp.integrations` that builds on exactly one optional third-party package (e.g. `mvp.integrations.django_tables.views`). Integrations are **never** imported by the core package and are **not** packaging extras — the third-party dependency is only required when a project explicitly imports the integration. Importing without the dependency raises `ImproperlyConfigured` with install instructions.

**Existing integrations:** `django_tables` (django-tables2), `django_filters` (django-filter)

### Config

A single merged dictionary, built at module import time by deep-merging package defaults with user overrides from ``settings.MVP_CONFIG``. Consumers import it directly::

    from mvp.config import MVP_CONFIG

**Structure:**

```python
# settings.py — optional overrides
MVP_CONFIG = {
    "view_names": {"list": "{model_name}_list"},
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm | md | lg | xl | 2xl — when the sidebar becomes persistent
            "collapse": "offcanvas",  # "offcanvas" (slides away) | "icons" (icon rail)
        },
        "navbar": {
            # Cotton component NAMES (not template paths), rendered in order at the
            # navbar end via <c-component :is="...">
            "end": ["actions.theme-controller", "actions.language-switcher"],
        },
    },
}
```

The context processor ``mvp.context_processors.mvp_config`` exposes the merged dict
to all templates as ``mvp_config``. Layout config resolution order: component
attribute (per-page override, e.g. ``<c-app breakpoint="xl">`` or
``<c-app.sidebar collapse="icons">``) → ``MVP_CONFIG`` → package default.

## Component Library

The complete component library is declared below. Components are organized by their namespace (directory). Root-level components have no namespace prefix beyond `c-`. Nested components use dot notation: `c-app.header` means the `header.html` template inside the `app/` directory.

### App

App components make django-mvp a **MVP framework**. They are pre-configured, highly opinionated, and provide the default application chrome. Unless a consumer redefines their own app structure (which they can do via override), they will never touch these directly. They have no configurable attributes — they just work.

```
c-app
  c-app.header          — application header bar
    c-app.header.navbar — top navbar (sidebar toggle, brand, configured widgets)
  c-app.sidebar         — application sidebar (provides default slot content: main application menu)
    c-app.sidebar.header
    c-app.sidebar.footer
  c-app.main            — main content area
  c-app.footer          — application footer bar
  c-app.dock            — application mobile navigation
```

### Layout

Layout components are **empty, configurable building blocks** — the opposite of app components. They provide structure without opinion. Consumers must fill their slots with their own content.

```
c-container             — content width constraint wrapper
c-toolbar               — horizontal action toolbar
c-group                 — flex group for inline items
c-divider               — visual separator
c-section               — titled content section (wraps any content with optional title/icon toolbar)
c-backdrop              — absolutely-positioned backdrop (e.g., over hero images to improve text readability)
c-grid                  — responsive CSS grid layout
c-layout.sidebar        — drawer shell (checkbox toggle + sidebar/content slots); c-app delegates to this
```

### Page

Page components define the structure and content areas within a layout.

```
c-page
  c-page.content        — page body content
  c-page.title          — page title/subtitle block
  c-page.toolbar        — page-level toolbar
  c-page.list           — list view wrapper
    c-page.list.empty   — empty state display
    c-page.list.footer  — list view footer
    c-page.list.actions
      c-page.list.actions.create
      c-page.list.actions.filter
      c-page.list.actions.search
      c-page.list.actions.sort
      c-page.list.actions.share
c-entrance              — entrance animation wrapper
  c-entrance.background — entrance background layer
```

**App vs. Layout:** `c-app.sidebar` already occupies the default slot with the main application menu. If you use `c-layout.sidebar` directly, you must provide your own slot content. Use `c-app.*` for the default chrome; use `c-layout.*` when you need a reusable sidebar primitive inside `c-page.content`, `c-card`, or anywhere else.

### Section

The basic building blocks of a page. Sections are **not** full-page layouts — they are meant to be composed inside a page or card.

```
c-section

c-section.hero          — full-width hero banner with background image, parallax support, and centered text layout

```

### Actions

Actions directories hold prebuilt, non-customizable components that work out of the box without attribute configuration.

```
c-actions.theme-controller
c-actions.language-switcher
c-actions.search
c-actions.login          — navbar log-in button, renders only when anonymous
```

### Data Display

```
c-card                  — container for grouped content
c-avatar
  c-avatar.group        — group of avatars
c-badge                 — status/count badge
c-icon                  — icon glyph (iconify)
c-text                  — styled text element
c-data-field            — key-value display field
c-messages              — Django messages flash list
c-alert                 — contextual alert banner
c-modal                 — modal dialog overlay
c-dropdown              — dropdown menu trigger
c-button                — action button
c-brand.logo            — brand logo image
c-brand.icon            — brand icon glyph
```

### Navigation

```
c-breadcrumbs
  c-breadcrumbs.item
c-pagination
  c-pagination.link
  c-pagination.wrapper  — join wrapper around pagination links
c-dock                  — bottom dock navigation
  c-dock.item
c-menu                  — menu container
  c-menu.group          — collapsible menu group
  c-menu.item           — single menu entry
  c-menu.collapse       — collapsible menu toggle
  c-menu.divider        — menu separator line
```

### Placeholders & Mockups

Loading states, placeholders, and visual mockup components.

```
c-placeholder.card      — coming-soon placeholder
c-mockup.browser        — browser window mockup
c-mockup.code           — code block mockup
  c-mockup.code.line    — code line with prefix
c-mockup.phone          — phone frame mockup
c-mockup.window         — OS window mockup
```

### User

```
c-user.sidebar-menu     — user-specific sidebar menu entry
c-user.display.compact  — compact user display card
```

### Forms

```
c-form                  — form wrapper
c-form.render           — controls how a form is rendererd
c-form.field            — single presentational field (control + label, help text, errors)
```

### Addons

Components that require additional packages to be installed. They are only available when the corresponding dependency is present.

```
c-addons.share-dropdown   — social share dropdown (no extra dependencies)
c-addons.django-table     — requires django-tables2
```

### Component Naming Rules

1. **Root components** use the `c-` prefix followed by a single descriptive word: `c-button`, `c-grid`, `c-card`.
2. **Nested components** use dot notation: `c-app.header`, `c-page.list.empty`.
3. **Directory = namespace**: A component's directory determines its namespace. `mvp/templates/cotton/card/index.html` → `c-card`. `mvp/templates/cotton/card/header.html` → `c-card.header`.
4. **No implementation leakage**: Component names must not reference DaisyUI, Tailwind, or any external design system. They describe *what they are*, not *how they look*.

## Terminology

### Cotton Component vs. DaisyUI Component

Django MVP's components are **not** DaisyUI components. They borrow DaisyUI classes as an implementation detail today, but their names and API are independent of any external design system. The component vocabulary belongs to django-mvp.

### Layout vs. Page

- **Layout** (`c-app`): The outermost wrapper that defines the application chrome (sidebar, header, footer). One per page.
- **Page** (`c-page`): The content container within a layout. Defines the page structure (header, body, footer sections).

### View vs. Template

- **View**: A Python class (usually a Django CBV composed from mixins) that handles request/response logic.
- **Template**: A Cotton component or HTML template that renders the visual output. Views and templates are separate concerns.

## Constraints

1. Demo templates must never use raw Tailwind classes — only Cotton component attributes.
2. Components must not declare ghost attributes (declared in `<c-vars>` but never used).
3. Mixin composition is the extension path — no factory functions, no pre-built concrete views for consumers.
4. Config uses deep merge — consumers override individual keys, not the entire dict.
