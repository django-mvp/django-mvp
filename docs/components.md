# Component Reference

All UI in django-mvp is built from [django-cotton](https://github.com/wrabit/django-cotton)
components. Components expose a deliberately small attribute API; when the attributes
aren't enough, **override the component's template** by placing a file at the same path
in your project (e.g. `templates/cotton/card.html` replaces `<c-card>`).

Conventions:

- Directory = namespace: `cotton/page/list/empty.html` → `<c-page.list.empty>`.
- Hyphens in a tag become underscores in the filename: `<c-data-field>` resolves to
  `cotton/data_field.html`, `<c-actions.theme-controller>` to
  `cotton/actions/theme_controller.html`. A tag can never contain an underscore.
- `index.html` is the namespace root: `cotton/menu/index.html` is `<c-menu>`, and the
  files beside it (`item.html`, `group.html`, ...) are `<c-menu.item>`, `<c-menu.group>`.
  Cotton tries `<name>.html` first and falls back to `<name>/index.html`.
- `class` adds CSS classes to the root element; other unrecognized attributes pass
  through to the root element (`href`, `id`, Alpine directives, ...) on components whose
  root spreads them. A few components that render fixed markup — `<c-section.hero>`,
  `<c-badge>`, `<c-placeholder.card>` — deliberately accept only their declared
  attributes.
- Icon attributes take [easy-icons](getting-started.md#configure-icons) names.
- The widget lists in [`MVP_CONFIG`](layout.md) (`layout.navbar.mobile.end`,
  `layout.navbar.desktop.end`) are lists of component names, not template paths:
  `"actions.theme-controller"` renders `<c-actions.theme-controller />`.

## Extending a component

1. **Pass attributes.** Everything a component supports on purpose is in the tables
   below.
2. **Add classes.** Every component that takes a `class` attribute appends it to what's
   already there rather than replacing it.
3. **Pass anything else.** Attributes a component doesn't declare are collected and, on
   components whose root spreads them, emitted verbatim on that root element — so `id`,
   `hx-*`, `x-data`, `aria-*` and event handlers reach the DOM without the component
   declaring them.
4. **Override the template.** For anything the attributes don't reach, put a template at
   the same path in your own project's `templates/cotton/` directory. Yours wins. Read
   the packaged template first so you know what you're replacing.

A component reads props it wasn't given out of the surrounding template context, so a
component that wraps another one hands it everything in scope. Where names collide, the
inner one silently takes the wrapper's value — a wrapper with its own `text` gives
`<c-button>` a `text` it was never meant to have, and one with an `actions` prop fills
`<c-modal>`'s header slot with it. Neither raises; the value just renders somewhere it
doesn't belong. Add `only` to the nested tag and it sees nothing but what you pass it —
slot content still renders in the calling context:

```html
<c-vars text actions />
<c-button icon="info" aria-label="{% trans "About this page" %}" only />
<c-modal id="helpModal" title="{{ title }}" only>
  <div>{{ text }}</div>
</c-modal>
```

## Shared attribute vocabulary

A handful of attribute names mean the same thing everywhere they appear.

| Attribute | Meaning |
| --- | --- |
| `variant` | Semantic colour role: `primary`, `secondary`, `accent`, `neutral`, `info`, `success`, `warning`, `error`. Unset means the neutral default. |
| `size` | A step on the component's own scale. The scales differ — a button runs `sm`–`lg`, an avatar `xs`–`xxl`, a modal `sm`–`full` — each is spelled out in the tables below. |
| `icon` | An icon name resolved through the configured icon packs, the same names `<c-icon name="…">` takes. |
| `class` | Extra classes appended to the component's root element. |
| Breakpoint values | `sm`, `md`, `lg`, `xl`, `2xl` — except on `<c-grid>`, which spells the largest `xxl`. `row` on `<c-toolbar>` and `vertical` on `<c-divider>` also accept `True`, meaning "at every width". `responsive` on `<c-menu>` wants a breakpoint name and nothing else. |

Boolean attributes are set by presence: `<c-alert dismissible>`, not `dismissible="True"`.

## App chrome

The application shell. Pre-configured and opinionated — configure via
[`MVP_CONFIG["layout"]`](layout.md) or replace via template override; these have almost
no attributes by design. The shell places them; a page never writes them by hand.

| Component | Notes |
| --- | --- |
| `c-app` | drawer wrapper; attr: `breakpoint` |
| `c-layout.sidebar` | the drawer mechanism `c-app` is built on: toggle, overlay, desktop open-state persistence, and the resolved layout it publishes to the browser; attrs: `id`, `breakpoint`, `collapse`, `sticky`, `boost` (all from config), `class` |
| `c-app.header` / `c-app.header.navbar` | sticky header — site icon and [breadcrumb trail](layout.md#breadcrumbs) leading, actions trailing; slots: `above`, `below`, `right`, `tray`. `c-app.header` takes `sticky` (from config); `c-app.header.navbar` takes no attributes — which navbar widget list shows at which width is a stylesheet rule keyed off the drawer breakpoint, and the `right` slot shares the desktop list's visibility rule |
| `c-app.sidebar` | brand header + `AppMenu` + fixed footer; attrs: `collapse`, `bg`, `brand-url`, `menu`, `title`, `boost`. `boost` sets `hx-boost` on the sidebar root, so every link inside it — menu items, the brand link, the footer actions — navigates with htmx instead of a full page load; off by default, because it changes how the page's own scripts see navigation |
| `c-app.sidebar.header` | the sidebar's top strip: brand icon, optional title, collapse toggle; attrs: `link` (`/`), `bg`, `title` (from config) |
| `c-app.sidebar.footer` | the pinned strip at the sidebar's foot: user menu (or log-in button), theme control, language control; attr: `bg` (from the sidebar). Override the template to change it |
| `c-app.main`, `c-app.footer`, `c-app.dock` | content area, footer (`class`), mobile bottom nav rendered from `MobileFooterMenu` |

`c-app.sidebar` and `c-app.dock` render menus by name through django-flex-menus, so
changing what's in them is a menu change, not a template change.

## Layout primitives

Empty, unopinionated building blocks — you provide the content.

| Component | Attributes |
| --- | --- |
| `c-container` | `fluid`, `fill`, `class` — width constraint wrapper |
| `c-grid` | `cols`, `sm`, `md`, `lg`, `xl`, `xxl` (column counts 1–6, 12), `gap` |
| `c-group` | `row`, `collapse`, `wrap`, `gap` — flex group |
| `c-toolbar` | `row` (True or breakpoint), `gap`; slots: default (left), `actions` (right) |
| `c-divider` | `vertical` (True or a breakpoint), `variant`, `position`, `class` — a section break, with room for a label |
| `c-rule` | `class` — a hairline between items in one list, where a divider would be too loud |
| `c-backdrop` | `opacity` — absolute overlay (e.g. over hero images) |
| `c-layout.sidebar` | `id`, `breakpoint`, `collapse`, `sticky`, `boost` — reusable drawer shell (what `c-app` uses). The last four default to their `MVP_CONFIG` values and are the resolved layout it publishes to the browser |

`row` on `c-group` is a boolean (always a row); `collapse` turns into a row only at the
`lg` breakpoint. `row` on `c-toolbar` takes either `True` or a breakpoint name and
defaults to `md`.

## Page structure

| Component | Attributes / notes |
| --- | --- |
| `c-page` | `fluid`, `fill`, `gap` (`6`), `class` — page wrapper |
| `c-page.title` | title/subtitle block (fed by `PageMixin` context); attrs `title`, `subtitle`, `info`, `info_actions` — `class` is declared but currently has no effect |
| `c-page.info` | `text`, `title`, `actions` — info icon beside the title, opening a dialog that explains the page; drawn by `c-page.title` from `page_info`, and nothing renders without `text`. A plain `text` string is escaped; a safe string is written out as markup |
| `c-page.content` | `gap` (`4`), `class` — flexible body region that absorbs leftover height |
| `c-page.toolbar` | `class` — page-level toolbar; renders nothing at all when given no children |
| `c-page.list` | list-view wrapper used by `MVPListView` templates — see [below](#list-components-driven-by-view-context) |
| `c-page.list.empty` | `icon`, `heading`, `message` — empty state |
| `c-page.list.actions` | `actions` — renders the action components below, default `['search','sort','filter','create']`; each one draws itself only when the view configures what it drives |
| `c-page.list.actions.{search,sort,create,filter,share}` | individual list actions — see [below](#list-components-driven-by-view-context) for the context each one needs |
| `c-page.list.actions.search` | `placeholder`, `label` — the search box and its submit button's text |
| `c-section` | `title`, `icon`, `level` (heading level 1–4); slot `actions` |
| `c-section.hero` | `bg-image`, `title`, `subtitle`, `opacity`, `height`, `class`; slots `top`, `actions`, `bottom` — daisyUI hero |
| `c-entrance` | `size` (`sm`/`md`/`lg`/`xl`/`2xl`/`3xl`/`4xl`/`full`, default `2xl`), `full-height` — the centered card for anonymous-facing pages; `small` is its deprecated predecessor |
| `c-entrance.background` | full-screen background the card sits on |

`<c-page fill>` marks a page that wants the shell's height instead of its content's. The
shell keys off it. `<c-entrance>` still accepts a deprecated `small` attribute that
predates `size` — pass one or the other, never both.

## Data display

| Component | Attributes |
| --- | --- |
| `c-card` | `title`, `icon`, `tight` (remove body padding), `class`, `body_class`; slots: default, `badges`, `actions`, `footer`, `footer_end` |
| `c-card.wrapper` | `class` — the bare card surface (background, rounded corners, shadow), for a fully custom interior |
| `c-button` | `text`, `icon`, `variant` (DaisyUI color names), `size` (`sm`/`md`/`lg`), `outline`, `ghost`, `full` (full width), `reverse`, `align` (default `center`), `condition` (render at all, default True), `class` |
| `c-link` | `href`, `text`, `variant` (DaisyUI color names), `hover` (underline on hover only) — a styled inline text link, for prose rather than actions |
| `c-badge` | `text`, `variant` (DaisyUI color names), `size` (`sm`/`lg`), `outline`, `class` |
| `c-icon` | `name` (required) |
| `c-text` | `text`, `size` (default `base`), `align` (`left`/`center`/`right`), `muted`, `tight`, `bold`, `upper`, `class` |
| `c-alert` | `variant` (DaisyUI color names), `icon`, `soft`, `outline`, `dash`, `dismissible`, `delay` (auto-dismiss milliseconds), `class` — see the content rule below |
| `c-data-field` | `label`, `value`, `help_text`, `missing` (default `–`) — key–value display; links the value when it has a URL |
| `c-messages` | Django messages list; `dismissible`, `delay` (auto-dismiss milliseconds, default 2000) |
| `c-modal` | `id` (for `showModal()`/`close()`), `size` (`sm`/`md`/`lg`/`xl`/`full`, default `md`), `position` (`top`/`bottom`/`start`/`end`), `closable` (show a close button), `class` — a dialog laid out as a card; `title`, `icon` and the `actions`/`footer`/`footer_end` slots forward to the inner `c-card` |
| `c-dropdown` | `valign` (`top/bottom/left/right`), `halign` (`start/center/end`), `full` (panel matches the trigger's width), `hover` (open on hover), `class`, `content_class`; slot `button` = trigger — see the placement note below |
| `c-avatar` | `for` (default `request.user`), `src`, `alt` (default `User avatar`), `size` (`xs`/`sm`/`md`/`lg`/`xl`/`xxl` or a Tailwind width class, default `md`), `shape` (default `rounded-full`), `variant` (initials background colour, default `primary`), `status` (`online`/`offline`), `placeholder` (initials shown when there's no image), `class` |
| `c-avatar.group` | `size` (default `md`) — overlapping row of avatars |
| `c-brand.logo` / `c-brand.icon` | `max-height`, `class` — brand images via the configured resolvers |
| `c-placeholder.card` | `message` (default `Coming soon...`), `icon`, `height`, `class` — a card-shaped stand-in for a region that isn't built yet |
| `c-mockup.browser` / `c-mockup.window` / `c-mockup.phone` / `c-mockup.code` | visual mockups; `c-mockup.browser` takes `url`; `c-mockup.code` holds `c-mockup.code.line` children |

Without a `button` slot, `<c-dropdown>` forwards its undeclared attributes to an inner
`<c-button>` that becomes the trigger, so `text`, `icon`, `variant` and `size` configure
it directly. Supply the `button` slot instead and those attributes fall through to the
dropdown wrapper — then you own the trigger's focus behaviour.

`<c-button condition="{{ perms.app.add_thing }}">` renders nothing when the condition is
falsy, which keeps permission checks out of the surrounding template.

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

### A dropdown opens where it was told, unless it cannot

`valign` and `halign` say which side of the trigger the panel prefers, and that side is
used whenever there is room for it. When there is not, because the trigger is near the
foot of the window or hard against one edge, the panel takes the opposite side rather
than opening off-screen, and slides along the edge it is aligned to rather than
overhanging it. The panel is also drawn above the rest of the page, so a dropdown inside
a scrolling region or a card with clipped overflow is no longer cut off at the boundary:

```html
<!-- Prefers to open downwards, aligned to the trigger's end. Near the bottom
     of the window it opens upwards instead, with no change here. -->
<c-dropdown valign="bottom" halign="end" text="Options">
  <c-menu>
    <c-menu.item label="Edit" href="#" />
  </c-menu>
</c-dropdown>
```

The preference is honoured rather than second-guessed, so the same dropdown does not
swap sides while the page scrolls under it — it changes only when the side it asked for
genuinely will not fit.

The browser does the measuring, so this needs the package's JavaScript bundle, which
`mvp/base.html` already loads. Where the bundle never runs, a dropdown opens on the
declared side whether or not it fits, exactly as it always used to.

## Navigation

| Component | Notes |
| --- | --- |
| `c-menu` | `label`, `horizontal`, `responsive` (breakpoint at which a vertical menu turns horizontal), `paged` (DaisyUI paged mode), `grow` (stretch to fill a flex parent, off by default — the sidebar nav passes it explicitly) — DaisyUI menu `<ul>` |
| `c-menu.item` | `label`, `icon`, `href`, `active`, `badge`, `tip` (rail tooltip) — a link when given `href`, otherwise a button |
| `c-menu.group` | `label`, `collapse`, `icon`, `icon_class`, `badge`, `badge_class` — section header or `<details>` group |
| `c-menu.collapse` | a thin pass-through to `c-menu.item` that also takes children — every attribute is forwarded |
| `c-menu.divider` | separator between menu entries |
| `c-breadcrumbs` / `c-breadcrumbs.item` | breadcrumb trail — `items`, `class`; the shell already draws one in the header from `page.breadcrumbs`. Takes either an `items` list of attribute dicts or hand-written `c-breadcrumbs.item` children (`text`, `href`, `class`) — `items` wins when both are given |
| `c-pagination` | `page_obj`, `page_window` (default `5`), `use_icons`, `show_first_and_last` — renders nothing when there's only one page; `show_first_and_last` swaps the First/Last text controls for the first and last page numbers |
| `c-pagination.link` / `c-pagination.wrapper` | building blocks for a hand-built pager: `page`, `text`, `active`, `disabled`, `size`, `class` on the link; `label`, `class` on the labelled wrapper it sits in |
| `c-dock` / `c-dock.item` | `size` (`xs`–`xl`); bottom dock navigation. An item is a drawer toggle with `toggle`, a link with `href`, otherwise a button; attrs: `label`, `icon`, `href`, `toggle`, `active`, `class` |

Menus are normally rendered from Python via django-flex-menus — see
[Navigation](navigation.md). Use these components directly only for hand-built menus.

## Widgets you place by name

These are designed to be listed in `MVP_CONFIG` — `layout.navbar.mobile.end`,
`layout.navbar.desktop.end` — rather than written into a page. The sidebar footer is a
fixed composition rather than a configured list (see `c-app.sidebar.footer` above), but
several of the same components are what it's built from, and you'll still reach for them
by name if you override that template. Each renders nothing when its precondition is
unmet.

| Component | Notes |
| --- | --- |
| `c-actions.theme-controller` | light/dark theme toggle (`size`, `valign`, `halign`, `compact`). `compact` renders the two-theme switcher as one square icon button instead of the icon/checkbox/icon row, for narrow slots like the sidebar footer — it has no effect when `theme.choices` is configured, since that branch is already a square icon button |
| `c-actions.language-switcher` | i18n language dropdown (needs `set_language` URL); renders only when `LocaleMiddleware` is installed **and** `set_language` reverses |
| `c-actions.language-switcher-modal` | the same switcher as a modal, better for narrow slots like the sidebar footer where a dropdown would be cramped — the variant the fixed sidebar footer uses (`id`, `size`); same preconditions as the dropdown switcher |
| `c-actions.search` | navbar search input; renders an input that is not wired to a form or a view — it submits nothing on its own |
| `c-actions.login` | log-in button (needs `login` URL); renders only when anonymous and `account_login` or `login` reverses — used in the navbar and in the fixed sidebar footer (`variant`, `full`) |
| `c-user.sidebar-menu` | account dropdown; part of the fixed sidebar footer. Its default slot lands between the account-centre entry and log out, so extra `c-menu.item` children land in the middle of the menu |
| `c-user.display.compact` | avatar + name row |

## Forms

| Component | Attributes |
| --- | --- |
| `c-form` | the `<form>` element: CSRF token (only when `method` is `post`), multipart detection, and an optional rendered form. `form-obj` renders through `c-form.render`; `formset` and `inlines` only detect that a multipart encoding is needed and are not rendered by `c-form` itself. `method`, `action`, `id` and anything else pass straight to the `<form>` element |
| `c-form.render` | `form` — renders a Django form's fields, honouring its helper when it has one |
| `c-form.field` | single presentational field: `type` (text-like, `textarea`, `select`, `file`, `checkbox`, `radio`, `toggle`), `label`, `hide-label`, `help-text`, `errors`, `prelabel`, `postlabel`, `wrapper-class`; `label`/`help_text`/`errors` also accept named slots. `errors` takes a string or a list and switches the control to its error state. `name`, `id`, `value`, `placeholder`, `required`, `disabled`, `checked` and `rows` pass straight through to the control |
| `c-form.formset` | whole Django formset: `formset` (required), `title` (defaults to the model in plural), `description`, `add-label`, `remove-label`, `class` — see [Formsets](formsets.md) |
| `c-form.formset.row` | one row of a formset: `form` (required), `label` (defaults to the object), `first`, `can-delete`, `remove-label`, `class` — placed by `c-form.formset`, which supplies `first` and `can-delete` from the set; write it by hand only for a custom set layout |

## Add-ons

Components that sit alongside the core set rather than inside it. One of them needs a
third-party package installed and its integration wired up before you use it.

| Component | Attributes | Needs |
| --- | --- | --- |
| `c-addons.share-dropdown` | `url` (default: current page URL), `title` (default: `page.title`), `size`, `class` — social share menu (social networks, email, copy link) | nothing |
| `c-addons.django-table` | `table`, `class`, `label`, `role` (default `region`) — scrollable region around a django-tables2 table, with its heading and footer rows pinned | django-tables2 |

`c-addons.share-dropdown` is plain markup over hard-coded social URLs, so it renders
anywhere — `c-page.list.actions.share` puts it on a list page unconditionally.

Give `c-addons.django-table` a distinct `label` on any page with more than one table.
The default accessible name is shared.

## List components driven by view context

These render from context a list view supplies. Each one is a no-op without its key, so
they are meant to sit on a page served by an MVP list view (or a view mixing in the same
mixins), not dropped into an arbitrary template.

| Component | Context key it needs | Attributes |
| --- | --- | --- |
| `c-page.list` | `list` (plus `list_item_template`, read from the surrounding context rather than passed as an attribute) | undeclared attributes pass to the grid it renders, so column counts and gaps are set on the tag itself; `empty_state` takes a dict of attributes forwarded to `c-page.list.empty` when the result set is empty |
| `c-page.list.empty` | — (`directory.create_url` gates the add button) | `icon` (default `search`), `heading`, `message`, `class` |
| `c-page.list.actions` | — (each action needs its own key) | `actions` (default `['search','sort','filter','create']`) |
| `c-page.list.actions.search` | `is_searchable` (from `SearchMixin`) | `placeholder` (default `Search`), `label` (default `Search`, the submit button's text) |
| `c-page.list.actions.sort` | `order_by_choices` (from `OrderMixin`) | — |
| `c-page.list.actions.filter` | `filter` (from the django-filter integration) | `label` (default `Filter`), `icon` (default `filter`) |
| `c-page.list.actions.create` | `directory.create_url`, optionally `create_form` | `label` (default `Add`), `icon` — declared but the button hard-codes `add` |
| `c-page.list.actions.share` | — (always renders) | — |

The search, sort and filter actions all write into a single form with the id
`filterForm`. The filter action renders it when a `FilterSet` is configured, and
`c-page.list.actions` renders an empty hidden one otherwise, so search and sort work in
any combination.

Each action draws itself only when the view configures what it drives —
`search_fields`, `order_by`, a `FilterSet`, `show_create_action`. Naming all four is
therefore the safe default, and a view drops a control by not configuring it rather than
by shortening this list. `share` is the exception: it takes no context and always
renders, so it appears only where a caller asks for it.

```html
<c-page>
  <c-page.title title="{{ page.title }}">
    <c-slot name="actions"><c-page.list.actions /></c-slot>
  </c-page.title>
  <c-page.list :list="object_list" md="2" lg="3" />
  {% if page_obj %}<c-pagination :page_obj="page_obj" />{% endif %}
</c-page>
```

## Extending with your own components

Put templates under `templates/cotton/` in your own app — they're immediately usable as
`<c-your-component>` and can be referenced by name in
[`MVP_CONFIG["layout"]["navbar"]["end"]`](layout.md#navbar-widgets). If your components
use Tailwind classes the packaged stylesheet doesn't include, follow the
[Tier 2 build in the styling guide](styling.md#tier-2-build-your-own-stylesheet).
