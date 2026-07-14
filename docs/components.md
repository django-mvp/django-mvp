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
| `c-app.sidebar` | brand + AppMenu + user footer; attrs: `collapse`, `bg`, `brand-url`, `menu` |
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
| `c-divider` | `horizontal`, `variant`, `position` |
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
| `c-page.list.actions` | `actions` — renders the action components below, default `['search','sort','create','filter']` |
| `c-page.list.actions.{search,sort,create,filter,share}` | individual list actions |
| `c-section` | `title`, `icon`, `level` (heading level 1–4); slot `actions` |
| `c-section.hero` | `bg-image`, `title`, `subtitle`, `parallax`, `speed`, `opacity`, `height`; slots `top`, `actions`, `bottom` |
| `c-entrance` / `c-entrance.background` | entrance animation wrapper |

## Data display

| Component | Attributes |
| --- | --- |
| `c-card` | `title`, `icon` |
| `c-button` | `text`, `icon`, `variant` (DaisyUI color names), `size` (`sm`/`md`/`lg`), `outline`, `ghost`, `reverse`, `align`, `gap`, `condition` |
| `c-badge` | `text`, `size` (`sm`/`lg`) |
| `c-icon` | `name` (required) |
| `c-text` | `impact`, `muted`, `small`, `center`, `tight`, `bold`, `upper` |
| `c-alert` | `soft`, `outline`, `dash` |
| `c-data-field` | key–value display |
| `c-messages` | Django messages list; `dismissible`, `animate` |
| `c-modal` | modal dialog |
| `c-dropdown` | `valign` (`top/bottom/left/right`), `halign` (`start/center/end`); slot `button` = trigger |
| `c-avatar` / `c-avatar.group` | user avatar(s) |
| `c-brand.logo` / `c-brand.icon` | brand images via the configured resolvers |

## Navigation

| Component | Notes |
| --- | --- |
| `c-menu` | `label` — DaisyUI menu `<ul>` |
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
| `c-actions.search` | navbar search input |
| `c-actions.login` | navbar log-in button (needs `login` URL); renders only when anonymous |
| `c-user.sidebar-menu` | account dropdown for the sidebar footer |
| `c-user.display.compact` | avatar + name row |
| `c-form`, `c-form.render`, `c-form.field` | form wrapper / renderer dispatch / single field |
| `c-placeholder.card` | `message`, `icon`, `height` — coming-soon card |
| `c-mockup.browser`, `c-mockup.window`, `c-mockup.phone`, `c-mockup.code` | visual mockups |
| `c-addons.share-dropdown` | social share menu (`url`, `title`, `size`) |
| `c-addons.django-table` | renders a django-tables2 table (`table`, `min_height`) |

## Extending with your own components

Put templates under `templates/cotton/` in your own app — they're immediately usable as
`<c-your-component>` and can be referenced by name in
[`MVP_CONFIG["layout"]["navbar"]["end"]`](layout.md#navbar-widgets). If your components
use Tailwind classes the packaged stylesheet doesn't include, follow the
[Tier 2 build in the styling guide](styling.md#tier-2-build-your-own-stylesheet).
