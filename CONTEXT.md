# Django MVP — Domain Model

## Core Concepts

### Component

A reusable, override-able UI building block implemented as a Cotton template. Components define the **public API** of django-mvp. They are named after their domain role, not their implementation or any external design system. Those the package owns are reached under the `mvp.` prefix.

**Examples:** `c-mvp.app`, `c-mvp.page`, `c-mvp.card`, `c-mvp.grid`

### Component Attribute

A configurable property declared via `<c-vars>` that controls a component's appearance or behavior. Attributes are the **only** way to customize components — raw utility classes must not appear in templates that demonstrate this package's own components. A daisy-cotton component is configured the way daisy-cotton documents, which for a few options is a class.

**Valid attributes:** `title`, `icon`, `variant`, `size`, `gap`, `cols` (on `c-mvp.grid`)
**Invalid:** `class="flex grid-cols-3"` — use component attributes instead.

### Override

The mechanism by which a consumer replaces a package component with their own implementation. Drop a template at the same path in your project's template directory and it replaces the package version: `templates/cotton/mvp/card/index.html` replaces `c-mvp.card`. This is the **primary extension point**.

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
            "end": ["mvp.actions.theme-controller", "mvp.actions.language-switcher"],
        },
    },
}
```

The context processor ``mvp.context_processors.mvp_config`` exposes the merged dict
to all templates as ``mvp_config``. Layout config resolution order: component
attribute (per-page override, e.g. ``<c-mvp.app breakpoint="xl">`` or
``<c-mvp.app.sidebar collapse="icons">``) → ``MVP_CONFIG`` → package default.

### Theme

A named set of CSS custom properties (colors, corner radii, border width, base sizing, and
the depth/noise surface effects) applied to the whole document at once through
`[data-theme="<name>"]`. A theme carries no structure or layout, which is why changing one
never requires a template change. Themes come from two sources: those shipped with the
package (every prebuilt daisyUI theme) and those a project writes for itself as a plain CSS
file. Selected through `MVP_CONFIG["theme"]`. See [Theming](docs/theming.md) for the full
variable reference and how to write one.

### Installable app

A project that a browser offers to install: it opens in its own window and has its own icon.
A project gets one by setting `MVP_CONFIG["pwa"]` to `True` (or a dict with a `theme_color`) and mounting `mvp.pwa.urls` at the
root of its URLconf. Every shell page then links a web app manifest and registers a
[service worker](#service-worker). See [Installable app](docs/installable-app.md).

### Service worker

A script the browser runs in the background for a site, served from `/sw.js` so it covers every
page. The one django-mvp packages listens for `install` and `activate` only and has no `fetch`
listener, so every request still goes to the network. A project replaces it by overriding the
template `mvp/pwa/sw.js`.

### Mounted app

A package built on django-mvp that can run inside another django-mvp project without changing
its code. It declares itself once, as a `MountedApp` subclass with a name, an icon, its own `flex_menu`
`Menu`, its URLs, a landing URL name and an optional check, and ships an instance of it. The
[host project](#host-project) mounts that instance with `mount("literature/", literature)` in
its own `urls.py`, and may adjust it by keyword argument or by subclassing. On the app's pages the
sidebar draws the app's menu under a "Back to *site name*" link and the browser title names the
app. Everywhere else nothing changes. See [Mounted apps](docs/mounted-apps.md).

### Host project

The django-mvp project that mounts a [mounted app](#mounted-app). It owns the URL prefix, adds its
own menu entry for the app, and keeps its own `AppMenu` on every page outside the app: a mounted
app never writes into the host's menus.

### Layout store

An Alpine store (`Alpine.store("mvp", ...)`, read as `$store.mvp`) that every shell page
registers, grouped by component (`sidebar`, `header`) plus a top-level `isWide`: the sidebar's
open state, the remembered desktop-width state, the resolved
[`LayoutConfig`](docs/layout.md#reading-the-resolved-layout-in-python) values behind the sidebar
and header, and whether the viewport is currently at the sidebar breakpoint. The drawer's own
checkbox stays the source of truth for whether the sidebar is open; the store mirrors it rather
than the reverse. See [The layout store](docs/layout.md#the-layout-store).

### Related row

One record belonging to a parent — a line item, a question. Rows are created, edited and
removed on the parent's page and are only persisted when that page is submitted.

### Row set

The collection of related rows shown on a page, together with the bookkeeping that lets a
submission be read back and tells the page how many rows may exist. Rendered by
`c-mvp.form.formset`, one row set per formset.

### Row set declaration

One related model's configuration for a page, written once as an `InlineFormSet` subclass and
reusable across views. Carries which fields its rows edit, how many blank rows to offer, and
the heading and help text shown above the row set. Listed on a view's `inlines`, one
declaration per row set.

## Component Library

The complete component library is declared below: 67 components under the `mvp.` prefix and 17 that keep a bare name. Components are organized by their namespace (directory). A component this package owns is written `c-mvp.` followed by its path: `c-mvp.app.header` means the `header.html` template inside the `app/` directory of `mvp/templates/cotton/mvp/`. The 17 bare names are `c-icon`, which is permanent, and the basic components that wait for #435; the Component Naming Rules say why.

### App

App components make django-mvp a **MVP framework**. They are pre-configured, highly opinionated, and provide the default application chrome. Unless a consumer redefines their own app structure (which they can do via override), they will never touch these directly. They have no configurable attributes — they just work.

```
c-mvp.app
  c-mvp.app.header          — application header bar
    c-mvp.app.header.navbar — top navbar (sidebar toggle, brand, configured widgets)
  c-mvp.app.sidebar         — application sidebar (provides default slot content: main application menu)
    c-mvp.app.sidebar.header
    c-mvp.app.sidebar.back  — link back to the host project, opening a mounted app's sidebar
    c-mvp.app.sidebar.footer — fixed row: user menu or log-in, theme, language
  c-mvp.app.main            — main content area
  c-mvp.app.footer          — application footer bar
  c-mvp.app.dock            — application mobile navigation
```

### Layout

Layout components are **empty, configurable building blocks** — the opposite of app components. They provide structure without opinion. Consumers must fill their slots with their own content.

```
c-mvp.container         — content width constraint wrapper
c-mvp.toolbar           — horizontal action toolbar
c-mvp.group             — flex group for inline items
c-divider               — visual separator
c-mvp.rule              — hairline between items in one list
c-mvp.section           — titled content section (wraps any content with optional title/icon toolbar)
c-mvp.backdrop          — absolutely-positioned backdrop (e.g., over hero images to improve text readability)
c-mvp.grid              — responsive CSS grid layout
c-mvp.layout.sidebar    — drawer shell (checkbox toggle + sidebar/content slots); c-mvp.app delegates to this
```

### Page

Page components define the structure and content areas within a layout.

```
c-mvp.page
  c-mvp.page.content        — page body content
  c-mvp.page.title          — page title/subtitle block
  c-mvp.page.info           — info icon beside the title, opening a dialog about the page
  c-mvp.page.toolbar        — page-level toolbar
  c-mvp.page.list           — list view wrapper
    c-mvp.page.list.empty   — empty state display
    c-mvp.page.list.actions
      c-mvp.page.list.actions.create
      c-mvp.page.list.actions.filter
      c-mvp.page.list.actions.search
      c-mvp.page.list.actions.sort
      c-mvp.page.list.actions.share
c-mvp.entrance              — centered card for anonymous-facing pages (size, full-height)
  c-mvp.entrance.background — entrance background layer
```

**App vs. Layout:** `c-mvp.app.sidebar` already occupies the default slot with the main application menu. If you use `c-mvp.layout.sidebar` directly, you must provide your own slot content. Use `c-mvp.app.*` for the default chrome; use `c-mvp.layout.*` when you need a reusable sidebar primitive inside `c-mvp.page.content`, `c-mvp.card`, or anywhere else.

### Section

The basic building blocks of a page. Sections are **not** full-page layouts — they are meant to be composed inside a page or card.

```
c-mvp.section

c-mvp.section.hero      — full-width hero banner (daisyUI hero) with background image, dimming overlay and centered text

```

### Actions

Actions directories hold prebuilt, non-customizable components that work out of the box without attribute configuration.

```
c-mvp.actions.theme-controller
c-mvp.actions.language-switcher
c-mvp.actions.language-switcher-modal — the language choices in a dialog, for narrow slots
c-mvp.actions.search
c-mvp.actions.login     — navbar log-in button, renders only when anonymous
```

### Data Display

```
c-mvp.card              — container for grouped content
  c-mvp.card.wrapper    — the bare card surface, for a custom interior
c-mvp.avatar            — a user's avatar, with initials when there is no image
c-avatar.group          — group of avatars
c-badge                 — status/count badge
c-icon                  — icon glyph (iconify)
c-mvp.text              — styled text element
c-mvp.data-field        — key-value display field
c-mvp.messages          — Django messages flash list
c-alert                 — contextual alert banner
c-mvp.modal             — modal dialog overlay
c-mvp.dropdown          — dropdown menu trigger
c-button                — action button
c-link                  — styled inline text link
c-mvp.brand.logo        — brand logo image
c-mvp.brand.icon        — brand icon glyph
```

### Navigation

```
c-breadcrumbs
  c-breadcrumbs.item
c-mvp.pagination
  c-mvp.pagination.link
  c-mvp.pagination.wrapper — join wrapper around pagination links
c-dock                  — bottom dock navigation
  c-dock.item
c-menu                  — menu container
  c-mvp.menu.group      — collapsible menu group
  c-mvp.menu.item       — single menu entry
  c-mvp.menu.collapse   — collapsible menu toggle
  c-mvp.menu.divider    — menu separator line
```

### Placeholders & Mockups

Loading states, placeholders, and visual mockup components.

```
c-mvp.placeholder.card  — coming-soon placeholder
c-mockup.browser        — browser window mockup
c-mockup.code           — code block mockup
  c-mockup.code.line    — code line with prefix
c-mockup.phone          — phone frame mockup
c-mockup.window         — OS window mockup
```

### User

```
c-mvp.user.sidebar-menu     — user-specific sidebar menu entry
c-mvp.user.display.compact  — compact user display card
```

### Forms

```
c-mvp.form                  — form wrapper
c-mvp.form.render           — controls how a form is rendered
c-mvp.form.field            — single presentational field (control + label, help text, errors)
c-mvp.form.formset          — a whole row set: management form, rows, add/remove controls
c-mvp.form.formset.row      — one row of a row set
```

### Addons

Components that require additional packages to be installed. They are only available when the corresponding dependency is present.

```
c-mvp.addons.share-dropdown   — social share dropdown (no extra dependencies)
c-mvp.addons.django-table     — requires django-tables2
```

### Documentation

```
c-mvp.documentation     — tabbed preview, source and output surface rendered by the show_code tag
```

### Component Naming Rules

1. **Root components** use the `c-mvp.` prefix followed by a single descriptive word: `c-mvp.grid`, `c-mvp.card`, `c-mvp.text`.
2. **Nested components** use dot notation after the prefix: `c-mvp.app.header`, `c-mvp.page.list.empty`.
3. **Directory = namespace**: A component's directory under `mvp/templates/cotton/mvp/` determines its namespace. `mvp/templates/cotton/mvp/card/index.html` → `c-mvp.card`. `mvp/templates/cotton/mvp/card/wrapper.html` → `c-mvp.card.wrapper`.
4. **No implementation leakage**: Component names must not reference DaisyUI, Tailwind, or any external design system. They describe *what they are*, not *how they look*.
5. **The `mvp.` prefix marks this package's components**, so none of them can share a name with a daisy-cotton component. The icon is the one exception: `c-icon` stays at `mvp/templates/cotton/icon.html` for good, because daisy-cotton ships a plain icon and expects a project to replace it, and this package's icon replaces it by sitting at the same name.
6. **The basic components are bare until #435.** `c-alert`, `c-avatar.group`, `c-badge`, `c-breadcrumbs`, `c-breadcrumbs.item`, `c-button`, `c-divider`, `c-dock`, `c-dock.item`, `c-link`, `c-menu` and `c-mockup.*` keep their bare names until #435 removes them in favour of daisy-cotton's. Until then a bare name can mean this package's component or daisy-cotton's.

## Terminology

### Cotton Component vs. DaisyUI Component

The components Django MVP owns are **not** DaisyUI components. They borrow DaisyUI classes as an implementation detail today, but their names and API are independent of any external design system. The component vocabulary belongs to django-mvp. Basic DaisyUI components (a button, an alert, a badge) come from daisy-cotton and are not written again in this package.

### Layout vs. Page

- **Layout** (`c-mvp.app`): The outermost wrapper that defines the application chrome (sidebar, header, footer). One per page.
- **Page** (`c-mvp.page`): The content container within a layout. Defines the page structure (header, body, footer sections).

### View vs. Template

- **View**: A Python class (usually a Django CBV composed from mixins) that handles request/response logic.
- **Template**: A Cotton component or HTML template that renders the visual output. Views and templates are separate concerns.

## Constraints

1. Demo templates that show one of this package's own components must never use raw Tailwind classes — only that component's attributes. A daisy-cotton component is configured the way daisy-cotton documents, which for a few options is a class.
2. Components must not declare ghost attributes (declared in `<c-vars>` but never used).
3. Mixin composition is the extension path — no factory functions, no pre-built concrete views for consumers.
4. Config uses deep merge — consumers override individual keys, not the entire dict.
