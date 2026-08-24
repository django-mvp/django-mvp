# Component Reference

All UI in django-mvp is built from [django-cotton](https://github.com/wrabit/django-cotton)
components. Components expose a deliberately small attribute API; when the attributes
aren't enough, **override the component's template** by placing a file at the same path
in your project (e.g. `templates/cotton/card.html` replaces `<c-card>`).

Conventions:

- Directory = namespace: `cotton/page/list/empty.html` → `<c-page.list.empty>`.
- `class` adds CSS classes to the root element; other unrecognized attributes pass
  through to the root element (`href`, `id`, Alpine directives, ...).
- Icon attributes take [easy-icons](getting-started.md#configure-icons) names.

## App chrome

The application shell. Pre-configured and opinionated — configure via
[`MVP_CONFIG["layout"]`](layout.md) or replace via template override; these have almost
no attributes by design.

| Component | Notes |
| --- | --- |
| `c-app` | drawer wrapper; attr: `breakpoint` |
| `c-app.sidebar` | brand + AppMenu + user footer; attrs: `collapse`, `bg`, `brand-url`, `menu`, `title`, `boost` |
| `c-app.header` / `c-app.header.navbar` | sticky header; slots: `above`, `below`, `right`, `tray` |
| `c-app.main`, `c-app.footer`, `c-app.dock` | content area, footer, mobile bottom nav |

## Layout primitives

Empty, unopinionated building blocks — you provide the content.

| Component | Attributes |
| --- | --- |
| `c-container` | `fluid`, `fill` — width constraint wrapper |
| `c-grid` | `cols`, `sm`, `md`, `lg`, `xl`, `xxl` (column counts 1–6, 12), `gap` |
| `c-group` | `row`, `collapse`, `wrap`, `gap` — flex group |
| `c-toolbar` | `row` (True or breakpoint), `gap`; slots: default (left), `actions` (right) |
| `c-divider` | `vertical` (True or a breakpoint), `variant`, `position`, `class` — a section break, with room for a label |
| `c-rule` | `class` — a hairline between items in one list, where a divider would be too loud |
| `c-backdrop` | `opacity` — absolute overlay (e.g. over hero images) |
| `c-layout.sidebar` | `id`, `breakpoint` — reusable drawer shell (what `c-app` uses) |

## Page structure

| Component | Attributes / notes |
| --- | --- |
| `c-page` | page wrapper |
| `c-page.title` | title/subtitle block (fed by `PageMixin` context) |
| `c-page.content`, `c-page.toolbar` | body / page-level toolbar |
| `c-page.list` | list-view wrapper used by `MVPListView` templates |
| `c-page.list.empty` | `icon`, `heading`, `message` — empty state |
| `c-page.list.actions` | `actions` — renders the action components below, default `['search','sort','filter','create']`; each one draws itself only when the view configures what it drives |
| `c-page.list.actions.{search,sort,create,filter,share}` | individual list actions |
| `c-page.list.actions.search` | `placeholder`, `label` — the search box and its submit button's text |
| `c-section` | `title`, `icon`, `level` (heading level 1–4); slot `actions` |
| `c-section.hero` | `bg-image`, `title`, `subtitle`, `opacity`, `height`, `class`; slots `top`, `actions`, `bottom` — daisyUI hero |
| `c-entrance` | `size` (`sm`/`md`/`lg`/`xl`/`2xl`/`3xl`/`4xl`/`full`, default `2xl`), `full-height` — the centered card for anonymous-facing pages; `small` is its deprecated predecessor |
| `c-entrance.background` | full-screen background the card sits on |

## Data display

| Component | Attributes |
| --- | --- |
| `c-card` | `title`, `icon` |
| `c-button` | `text`, `icon`, `variant` (DaisyUI color names), `size` (`sm`/`md`/`lg`), `outline`, `ghost`, `full` (full width), `reverse`, `align` (default `center`), `condition` (render at all, default True), `class` |
| `c-link` | `href`, `text`, `variant` (DaisyUI color names), `hover` (underline on hover only) — a styled inline text link, for prose rather than actions |
| `c-badge` | `text`, `size` (`sm`/`lg`) |
| `c-icon` | `name` (required) |
| `c-text` | `text`, `size` (default `base`), `align` (`left`/`center`/`right`), `muted`, `tight`, `bold`, `upper`, `class` |
| `c-alert` | `variant` (DaisyUI color names), `icon`, `soft`, `outline`, `dash`, `dismissible`, `delay` (auto-dismiss milliseconds), `class` — see the content rule below |
| `c-data-field` | key–value display |
| `c-messages` | Django messages list; `dismissible`, `delay` (auto-dismiss milliseconds, default 2000) |
| `c-modal` | modal dialog |
| `c-dropdown` | `valign` (`top/bottom/left/right`), `halign` (`start/center/end`); slot `button` = trigger |
| `c-avatar` / `c-avatar.group` | user avatar(s) |
| `c-brand.logo` / `c-brand.icon` | brand images via the configured resolvers |

### Alert content goes in one element

An alert lays its direct children out side by side — that is what puts the status icon
beside the message, and what lets a trailing button sit at the end of the row. So each
thing the alert says needs to be a single element:

```html
<c-alert variant="warning">
  <span>This cannot be undone.</span>
</c-alert>

<c-alert variant="info">
  <span>We use cookies to improve your experience.</span>
  <c-button text="Accept" variant="primary" size="sm" />
</c-alert>
```

Passing bare text works until the message contains markup. A sentence with a `<strong>`
in the middle of it is three children, so it is laid out as three columns and reads as
fragments spread across the alert's width:

```html
<!-- Don't: three columns, not one sentence -->
<c-alert variant="warning">
  You are about to <strong>permanently</strong> delete this.
</c-alert>
```

Anything richer than a sentence — a heading, a paragraph and a list — goes in a `<div>`
for the same reason.

## Navigation

| Component | Notes |
| --- | --- |
| `c-menu` | `label`, `horizontal`, `responsive` (breakpoint at which a vertical menu turns horizontal), `paged` (DaisyUI paged mode), `grow` (stretch to fill a flex parent, off by default — the sidebar nav passes it explicitly) — DaisyUI menu `<ul>` |
| `c-menu.item` | `label`, `icon`, `href`, `active`, `badge`, `tip` (rail tooltip) |
| `c-menu.group` | `label`, `collapse`, `icon`, `badge` — section header or `<details>` group |
| `c-menu.collapse`, `c-menu.divider` | collapsible wrapper / separator |
| `c-breadcrumbs` / `c-breadcrumbs.item` | breadcrumb trail |
| `c-pagination` | `page_obj`, `page_window`, `use_icons`, `show_first_and_last` |
| `c-dock` / `c-dock.item` | `size`; bottom dock navigation |

Menus are normally rendered from Python via django-flex-menus — see
[Navigation](navigation.md). Use these components directly only for hand-built menus.

## Actions, user, misc

| Component | Notes |
| --- | --- |
| `c-actions.theme-controller` | light/dark theme toggle (`size`) |
| `c-actions.language-switcher` | i18n language dropdown (needs `set_language` URL) |
| `c-actions.language-switcher-modal` | the same switcher as a modal, for the sidebar footer where a dropdown would be cramped |
| `c-actions.search` | navbar search input |
| `c-actions.login` | navbar log-in button (needs `login` URL); renders only when anonymous |
| `c-user.sidebar-menu` | account dropdown for the sidebar footer |
| `c-user.display.compact` | avatar + name row |
| `c-form`, `c-form.render` | form wrapper / renderer dispatch |
| `c-form.field` | single presentational field: `type` (text-like, `textarea`, `select`, `file`, `checkbox`, `radio`, `toggle`), `label`, `hide-label`, `help-text`, `errors`, `prelabel`, `postlabel`, `wrapper-class`; `label`/`help_text`/`errors` also accept named slots |
| `c-form.formset` | whole Django formset: `formset` (required), `title` (defaults to the model in plural), `description`, `add-label`, `remove-label`, `class` — see [Formsets](formsets.md) |
| `c-form.formset.row` | one row of a formset: `form` (required), `label` (defaults to the object), `first`, `can-delete`, `remove-label`, `class` |
| `c-placeholder.card` | `message`, `icon`, `height` — coming-soon card |
| `c-mockup.browser`, `c-mockup.window`, `c-mockup.phone`, `c-mockup.code` | visual mockups |
| `c-addons.share-dropdown` | social share menu (`url`, `title`, `size`) |
| `c-addons.django-table` | scrollable region around a django-tables2 table, with its heading and footer rows pinned (`table`, `class`, `label`, `role`) |

## Extending with your own components

Put templates under `templates/cotton/` in your own app — they're immediately usable as
`<c-your-component>` and can be referenced by name in
[`MVP_CONFIG["layout"]["navbar"]["end"]`](layout.md#navbar-widgets). If your components
use Tailwind classes the packaged stylesheet doesn't include, follow the
[Tier 2 build in the styling guide](styling.md#tier-2-build-your-own-stylesheet).
