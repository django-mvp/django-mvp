# Component Reference

All UI in django-mvp is built from [django-cotton](https://github.com/wrabit/django-cotton)
components. The shell, pages, forms and menus are this package's own. The basic
components, such as the button and the alert, come from
[daisy-cotton](https://github.com/django-mvp/daisy-cotton) (see
[Basic components from daisy-cotton](#basic-components-from-daisy-cotton)). Components
expose a deliberately small attribute API; when the attributes aren't enough,
**override the component's template** by placing a file at the same path in your project
(e.g. `templates/cotton/mvp/card/index.html` replaces `<c-mvp.card>`).

## Names and the `mvp.` prefix

The components this package owns live under `mvp/templates/cotton/mvp/`, so their tags
start with `mvp.`: `<c-mvp.card>`, `<c-mvp.page.list.empty>`, `<c-mvp.app.sidebar>`.
No component this package keeps shares a name with one from
[daisy-cotton](https://github.com/django-mvp/daisy-cotton), the icon excepted.

- **`<c-icon>` keeps its bare name for good.** daisy-cotton ships a plain icon and
  expects a project to replace it when it wants icons looked up by name. This package's
  icon is that replacement, so it has to sit at the same name to reach every caller,
  daisy-cotton's own components included.
- **The basic components use daisy-cotton's bare names.** `<c-button>`, `<c-alert>` and
  the rest of [the sixteen](#basic-components-from-daisy-cotton) are daisy-cotton's. This
  package ships no template for any of them.
- **A project overrides a component at the same prefixed path** under its own
  templates: `templates/cotton/mvp/card/index.html` for `<c-mvp.card>`.

Conventions:

- Directory = namespace: `cotton/mvp/page/list/empty.html` → `<c-mvp.page.list.empty>`.
- Hyphens in a tag become underscores in the filename: `<c-mvp.data-field>` resolves to
  `cotton/mvp/data_field.html`, `<c-mvp.actions.theme-controller>` to
  `cotton/mvp/actions/theme_controller.html`. A tag can never contain an underscore.
- `index.html` is the namespace root: `cotton/mvp/card/index.html` is `<c-mvp.card>`,
  and the file beside it (`wrapper.html`) is `<c-mvp.card.wrapper>`. Cotton tries
  `<name>.html` first and falls back to `<name>/index.html`.
- `class` adds CSS classes to the root element; other unrecognized attributes pass
  through to the root element (`href`, `id`, Alpine directives, ...) on components whose
  root spreads them. A few components that render fixed markup — `<c-mvp.section.hero>`,
  `<c-mvp.placeholder.card>` — deliberately accept only their declared attributes.
- Icon attributes take [easy-icons](getting-started.md#configure-icons) names.
- The widget lists in [`MVP_CONFIG`](layout.md) (`layout.navbar.mobile.end`,
  `layout.navbar.desktop.end`) are lists of component names, not template paths:
  `"mvp.actions.theme-controller"` renders `<c-mvp.actions.theme-controller />`.

## Basic components from daisy-cotton

Sixteen basic components come from [daisy-cotton](https://github.com/django-mvp/daisy-cotton),
which is installed with django-mvp. This package ships no template for any of them, and its
own pages call them the way your pages do. daisy-cotton's README and its component gallery
(`python manage.py runserver` from a checkout) document each one, and every template in
daisy-cotton starts with a description of the attributes it takes.

| Tag | What it is | Documentation |
| --- | --- | --- |
| `<c-button>` | a button, or a link drawn as one | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-alert>` | a message banner; `variant` is `info`, `success`, `warning` or `error` | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-badge>` | a small label or count | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-avatar.group>` | a row of avatars; pass the overlap in `class`, for example `class="-space-x-6"` | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-breadcrumbs>` | a breadcrumb trail | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-breadcrumbs.item>` | one step of a trail | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-divider>` | a section break with an optional label | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-link>` | a styled link | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-dock>` | a bottom navigation bar | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-dock.item>` | one item of a dock | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-mockup.browser>` | a browser frame | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-mockup.code>` | a terminal-style code block | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-mockup.code.line>` | one line of a code block | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-mockup.phone>` | a phone frame | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-mockup.window>` | an application window frame | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |
| `<c-menu>` | a menu list | [daisy-cotton](https://github.com/django-mvp/daisy-cotton) |

This package's own `<c-mvp.menu.item>`, `<c-mvp.avatar>` and the other `mvp.` components
sit inside these and are described below.

### Isolating a call with `only`

Cotton fills an attribute you did not pass from the template the tag sits in, when the
component declares that attribute with no default. A template whose context holds a
variable named `text`, `icon`, `variant`, `items`, `class`, `href`, `size` or `label` can
therefore change what a component draws. Nothing raises; the value just renders somewhere
it doesn't belong. `only` on the tag stops this: the component sees nothing but what you
pass it. Content between the tags still sees the page's context.

This package's own templates pass `only` on every call to a daisy-cotton component. The
pages and examples in this documentation do not, because a page rarely holds a variable
with one of those names. You need `only` when a template's context may hold one, most
often inside a component of your own that declares `text` or `class` and draws a tag from
the sixteen, or one of this package's components such as `<c-mvp.modal>`, which has an
`actions` slot:

```html
<c-vars text actions />
<c-button icon="info" aria-label="{% trans "About this page" %}" only />
<c-mvp.modal id="helpModal" title="{{ title }}" only>
  <div>{{ text }}</div>
</c-mvp.modal>
```

### Overriding one of these tags

A project template at `cotton/button.html`, or at the path of any of the sixteen, still
wins over daisy-cotton's, as it did over this package's. It now answers more than your own
calls: it also answers when one of daisy-cotton's components draws that tag inside itself.
The dismiss button in an alert, the close button in daisy-cotton's modal, and the trigger
of its dropdown and floating action button are all `<c-button>` calls, and a trail draws
each of its steps as `<c-breadcrumbs.item>`. An override that declares fewer attributes
than daisy-cotton's template can break those components. Start from a copy of
daisy-cotton's template and keep every attribute it declares.

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
   the same path in your own project's `templates/cotton/` directory, which for a
   packaged component means under `templates/cotton/mvp/`. Yours wins. Read
   the packaged template first so you know what you're replacing.

Components read props they weren't given from the surrounding template context. See
[Isolating a call with `only`](#isolating-a-call-with-only) for when that matters and how to
stop it.

## Shared attribute vocabulary

A handful of attribute names mean the same thing everywhere they appear.

| Attribute | Meaning |
| --- | --- |
| `variant` | Semantic colour role: `primary`, `secondary`, `accent`, `neutral`, `info`, `success`, `warning`, `error`. Unset means the neutral default. An alert takes only `info`, `success`, `warning` and `error`. |
| `size` | A step on the component's own scale. The scales differ — a button runs `xs`–`xl`, an avatar `xs`–`xxl`, a modal `sm`–`full` — each is spelled out in the tables below or in daisy-cotton's documentation. |
| `icon` | An icon name resolved through the configured icon packs, the same names `<c-icon name="…">` takes. |
| `class` | Extra classes appended to the component's root element. |
| Breakpoint values | `sm`, `md`, `lg`, `xl`, `2xl` — except on `<c-mvp.grid>`, which spells the largest `xxl`. `row` on `<c-mvp.toolbar>` also accepts `True`, meaning "at every width". |

Boolean attributes are set by presence: `<c-alert dismissible>`, not `dismissible="True"`.

## App chrome

The application shell. Pre-configured and opinionated — configure via
[`MVP_CONFIG["layout"]`](layout.md) or replace via template override; these have almost
no attributes by design. The shell places them; a page never writes them by hand.

| Component | Notes |
| --- | --- |
| `c-mvp.app` | drawer wrapper; attr: `breakpoint` |
| `c-mvp.layout.sidebar` | the drawer mechanism `c-mvp.app` is built on: toggle, overlay, desktop open-state persistence, and the resolved layout it publishes to the browser; attrs: `id`, `breakpoint`, `collapse`, `sticky`, `boost` (all from config), `class` |
| `c-mvp.app.header` / `c-mvp.app.header.navbar` | sticky header — site icon and [breadcrumb trail](layout.md#breadcrumbs) leading, actions trailing; slots: `above`, `below`, `right`, `tray`. `c-mvp.app.header` takes `sticky` and `class`, its background (both from config); `c-mvp.app.header.navbar` takes no attributes — which navbar widget list shows at which width is a stylesheet rule keyed off the drawer breakpoint, and the `right` slot shares the desktop list's visibility rule |
| `c-mvp.app.sidebar` | brand header + `AppMenu` + fixed footer; attrs: `collapse`, `bg`, `brand-url`, `menu`, `title`, `boost`. `boost` sets `hx-boost` on the sidebar root, so every link inside it — menu items, the brand link, the footer actions — navigates with htmx instead of a full page load; off by default, because it changes how the page's own scripts see navigation |
| `c-mvp.app.sidebar.header` | the sidebar's top strip: brand icon, optional title, collapse toggle; attrs: `link` (`/`), `bg`, `title` (from config) |
| `c-mvp.app.sidebar.footer` | the pinned strip at the sidebar's foot: user menu (or log-in button), theme control, language control; attr: `bg` (from the sidebar). Override the template to change it |
| `c-mvp.app.main`, `c-mvp.app.footer`, `c-mvp.app.dock` | content area, and the containing block for [absolutely positioned page content](layout.md#positioning-inside-the-main-area); footer (`class`), mobile bottom nav rendered from `MobileFooterMenu` |

`c-mvp.app.sidebar` and `c-mvp.app.dock` render menus by name through django-flex-menus, so
changing what's in them is a menu change, not a template change.

## Layout primitives

Empty, unopinionated building blocks — you provide the content.

| Component | Attributes |
| --- | --- |
| `c-mvp.container` | `fluid`, `fill`, `class` — width constraint wrapper |
| `c-mvp.grid` | `cols`, `sm`, `md`, `lg`, `xl`, `xxl` (column counts 1–6, 12), `gap` |
| `c-mvp.group` | `row`, `collapse`, `wrap`, `gap` — flex group |
| `c-mvp.toolbar` | `row` (True or breakpoint), `gap`; slots: default (left), `actions` (right) |
| `c-mvp.rule` | `class` — a hairline between items in one list, where a divider would be too loud |
| `c-mvp.backdrop` | `opacity` — absolute overlay (e.g. over hero images) |
| `c-mvp.layout.sidebar` | `id`, `breakpoint`, `collapse`, `sticky`, `boost` — reusable drawer shell (what `c-mvp.app` uses). The last four default to their `MVP_CONFIG` values and are the resolved layout it publishes to the browser |

`row` on `c-mvp.group` is a boolean (always a row); `collapse` turns into a row only at the
`lg` breakpoint. `row` on `c-mvp.toolbar` takes either `True` or a breakpoint name and
defaults to `md`.

## Page structure

| Component | Attributes / notes |
| --- | --- |
| `c-mvp.page` | `fluid`, `fill`, `gap` (`6`), `class` — page wrapper |
| `c-mvp.page.title` | title/subtitle block (fed by `PageMixin` context); attrs `title`, `subtitle`, `info`, `info_actions`, `class` — any other attribute lands on the block's root element |
| `c-mvp.page.info` | `text`, `title`, `actions` — info icon beside the title, opening a dialog that explains the page; drawn by `c-mvp.page.title` from `page_info`, and nothing renders without `text`. A plain `text` string is escaped; a safe string is written out as markup |
| `c-mvp.page.content` | `gap` (`4`), `class` — flexible body region that absorbs leftover height |
| `c-mvp.page.toolbar` | `class` — page-level toolbar; renders nothing at all when given no children |
| `c-mvp.page.list` | list-view wrapper used by `MVPListView` templates — see [below](#list-components-driven-by-view-context) |
| `c-mvp.page.list.empty` | `icon`, `heading`, `message` — empty state |
| `c-mvp.page.list.actions` | `actions` — renders the action components below, default `['search','sort','filter','create']`; each one draws itself only when the view configures what it drives |
| `c-mvp.page.list.actions.{search,sort,create,filter,share}` | individual list actions — see [below](#list-components-driven-by-view-context) for the context each one needs |
| `c-mvp.page.list.actions.search` | `placeholder`, `label` — the search box and its submit button's text |
| `c-mvp.section` | `title`, `icon`, `level` (heading level 1–4); slot `actions` |
| `c-mvp.section.hero` | `bg-image`, `title`, `subtitle`, `opacity`, `height`, `class`; slots `top`, `actions`, `bottom` — daisyUI hero |
| `c-mvp.entrance` | `size` (`sm`/`md`/`lg`/`xl`/`2xl`/`3xl`/`4xl`/`full`, default `2xl`), `full-height` — the centered card for anonymous-facing pages; `small` is its deprecated predecessor |
| `c-mvp.entrance.background` | full-screen background the card sits on |

`<c-mvp.page fill>` marks a page that wants the shell's height instead of its
content's. The shell keys off it. `<c-mvp.entrance>` still accepts a deprecated
`small` attribute that predates `size` — pass one or the other, never both.

## Data display

| Component | Attributes |
| --- | --- |
| `c-mvp.card` | `title`, `icon`, `tight` (remove body padding), `class`, `body_class`; slots: default, `badges`, `actions`, `footer`, `footer_end` |
| `c-mvp.card.wrapper` | `class` — the bare card surface (background, rounded corners, shadow), for a fully custom interior |
| `c-icon` | `name` (required); every other attribute reaches the rendered icon element, so `class`, `height` and the rest are set on the tag |
| `c-mvp.text` | `text`, `size` (default `base`), `align` (`left`/`center`/`right`), `muted`, `tight`, `bold`, `upper`, `class` |
| `c-mvp.data-field` | `label`, `value`, `help_text`, `missing` (default `–`) — key–value display; links the value when it has a URL |
| `c-mvp.messages` | Django messages list; `dismissible`, `delay` (auto-dismiss milliseconds, default 2000) |
| `c-mvp.modal` | `id` (for `showModal()`/`close()`), `size` (`sm`/`md`/`lg`/`xl`/`full`, default `md`), `position` (`top`/`bottom`/`start`/`end`), `closable` (show a close button), `class` — a dialog laid out as a card; `title`, `icon` and the `actions`/`footer`/`footer_end` slots forward to the inner `c-mvp.card` |
| `c-mvp.dropdown` | `valign` (`top/bottom/left/right`), `halign` (`start/center/end`), `full` (panel matches the trigger's width), `hover` (open on hover), `class`, `content_class`; slot `button` = trigger — see the placement note below |
| `c-mvp.avatar` | `for` (default `request.user`), `src`, `alt` (default `User avatar`), `size` (`xs`/`sm`/`md`/`lg`/`xl`/`xxl` or a Tailwind width class, default `md`), `shape` (default `rounded-full`), `variant` (initials background colour, default `primary`), `status` (`online`/`offline`), `placeholder` (initials shown when there's no image), `class` |
| `c-mvp.brand.logo` / `c-mvp.brand.icon` | `max-height`, `class` — brand images via the configured resolvers |
| `c-mvp.placeholder.card` | `message` (default `Coming soon...`), `icon`, `height`, `class` — a card-shaped stand-in for a region that isn't built yet |

Without a `button` slot, `<c-mvp.dropdown>` forwards its undeclared attributes to an inner
`<c-button>` that becomes the trigger, so `text`, `icon`, `variant` and `size` configure
it directly. Supply the `button` slot instead and those attributes fall through to the
dropdown wrapper — then you own the trigger's focus behaviour.

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
<c-mvp.dropdown valign="bottom" halign="end" text="Options">
  <c-menu>
    <c-mvp.menu.item label="Edit" href="#" />
  </c-menu>
</c-mvp.dropdown>
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
| `c-mvp.menu.item` | `label`, `icon`, `href`, `active`, `badge`, `tip` (rail tooltip) — a link when given `href`, otherwise a button |
| `c-mvp.menu.group` | `label`, `collapse`, `icon`, `icon_class`, `badge`, `badge_class` — section header or `<details>` group |
| `c-mvp.menu.collapse` | a thin pass-through to `c-mvp.menu.item` that also takes children — every attribute is forwarded |
| `c-mvp.menu.divider` | separator between menu entries |
| `c-mvp.pagination` | `page_obj`, `page_window` (default `5`), `use_icons`, `show_first_and_last`, `label` (the `<nav>`'s accessible name, default `Navigation page results`) — renders nothing when there's only one page; `show_first_and_last` swaps the First/Last text controls for the first and last page numbers |
| `c-mvp.pagination.link` / `c-mvp.pagination.wrapper` | building blocks for a hand-built pager: `page`, `text`, `active`, `disabled`, `size`, `class` on the link; `label`, `class` on the labelled wrapper it sits in |

Menus are normally rendered from Python via django-flex-menus — see
[Navigation](navigation.md). Use these components directly only for hand-built menus.

`<c-menu>`, `<c-breadcrumbs>` and `<c-dock>` are daisy-cotton's. A `<c-menu>` has no
accessible name of its own, so give one you write by hand an `aria-label`, or put it inside
a `<nav>`. `<c-breadcrumbs>` takes either `items`, a list of dictionaries holding the
attributes of one `<c-breadcrumbs.item>` each, or hand-written items as its content; the
shell already draws a trail in the header from `page.breadcrumbs`. `<c-dock>` has no default
class, so the dock the shell draws passes it `layout.dock.class`, and a dock you write
yourself takes the class you pass.

## Widgets you place by name

These are designed to be listed in `MVP_CONFIG` — `layout.navbar.mobile.end`,
`layout.navbar.desktop.end` — rather than written into a page. The sidebar footer is a
fixed composition rather than a configured list (see `c-mvp.app.sidebar.footer` above), but
several of the same components are what it's built from, and you'll still reach for them
by name if you override that template. Each renders nothing when its precondition is
unmet.

| Component | Notes |
| --- | --- |
| `c-mvp.actions.theme-controller` | light/dark theme toggle (`size`, `valign`, `halign`, `compact`). `compact` renders the two-theme switcher as one square icon button instead of the icon/checkbox/icon row, for narrow slots like the sidebar footer — it has no effect when `theme.choices` is configured, since that branch is already a square icon button |
| `c-mvp.actions.language-switcher` | i18n language dropdown (needs `set_language` URL); renders only when `LocaleMiddleware` is installed **and** `set_language` reverses |
| `c-mvp.actions.language-switcher-modal` | the same switcher as a modal, better for narrow slots like the sidebar footer where a dropdown would be cramped — the variant the fixed sidebar footer uses (`id`, `size`); same preconditions as the dropdown switcher |
| `c-mvp.actions.search` | navbar search input; renders an input that is not wired to a form or a view — it submits nothing on its own |
| `c-mvp.actions.login` | log-in button (needs `login` URL); renders only when anonymous and `account_login` or `login` reverses — used in the navbar and in the fixed sidebar footer (`variant`, `full`) |
| `c-mvp.user.sidebar-menu` | account dropdown; part of the fixed sidebar footer. Its default slot lands between the account-centre entry and log out, so extra `c-mvp.menu.item` children land in the middle of the menu |
| `c-mvp.user.display.compact` | avatar + name row |

## Forms

| Component | Attributes |
| --- | --- |
| `c-mvp.form` | the `<form>` element: CSRF token (only when `method` is `post`), multipart detection, and an optional rendered form. `form-obj` renders through `c-mvp.form.render`; `formset` and `inlines` only detect that a multipart encoding is needed and are not rendered by `c-mvp.form` itself. `method`, `action`, `id` and anything else pass straight to the `<form>` element |
| `c-mvp.form.render` | `form` — renders a Django form's fields, honouring its helper when it has one |
| `c-mvp.form.field` | single presentational field: `type` (text-like, `textarea`, `select`, `file`, `checkbox`, `radio`, `toggle`), `label`, `hide-label`, `help-text`, `errors`, `prelabel`, `postlabel`, `wrapper-class`; `label`/`help_text`/`errors` also accept named slots. `errors` takes a string or a list and switches the control to its error state. `name`, `id`, `value`, `placeholder`, `required`, `disabled`, `checked` and `rows` pass straight through to the control |
| `c-mvp.form.formset` | whole Django formset: `formset` (required), `title` (defaults to the model in plural), `description`, `add-label`, `remove-label`, `class` — see [Formsets](formsets.md) |
| `c-mvp.form.formset.row` | one row of a formset: `form` (required), `label` (defaults to the object), `first`, `can-delete`, `remove-label`, `class` — placed by `c-mvp.form.formset`, which supplies `first` and `can-delete` from the set; write it by hand only for a custom set layout |

## Add-ons

Components that sit alongside the core set rather than inside it. One of them needs a
third-party package installed and its integration wired up before you use it.

| Component | Attributes | Needs |
| --- | --- | --- |
| `c-mvp.addons.share-dropdown` | `url` (default: current page URL), `title` (default: `page.title`), `size`, `class` — social share menu (social networks, email, copy link) | nothing |
| `c-mvp.addons.django-table` | `table`, `class`, `label`, `role` (default `region`) — scrollable region around a django-tables2 table, with its heading and footer rows pinned | django-tables2 |

`c-mvp.addons.share-dropdown` is plain markup over hard-coded social URLs, so it renders
anywhere — `c-mvp.page.list.actions.share` puts it on a list page unconditionally.

Give `c-mvp.addons.django-table` a distinct `label` on any page with more than one table.
The default accessible name is shared.

## List components driven by view context

These render from context a list view supplies. Each one is a no-op without its key, so
they are meant to sit on a page served by an MVP list view (or a view mixing in the same
mixins), not dropped into an arbitrary template.

| Component | Context key it needs | Attributes |
| --- | --- | --- |
| `c-mvp.page.list` | `list` | `card` names the template each row is rendered with; undeclared attributes pass to the grid it renders, so column counts and gaps are set on the tag itself; `empty_state` takes a dict of attributes forwarded to `c-mvp.page.list.empty` when the result set is empty |
| `c-mvp.page.list.empty` | — (`directory.create_url` gates the add button) | `icon` (default `search`), `heading`, `message`, `class` |
| `c-mvp.page.list.actions` | — (each action needs its own key) | `actions` (default `['search','sort','filter','create']`) |
| `c-mvp.page.list.actions.search` | `is_searchable` (from `SearchMixin`) | `placeholder` (default `Search`), `label` (default `Search`, the submit button's text) |
| `c-mvp.page.list.actions.sort` | `order_by_choices` (from `OrderMixin`) | — |
| `c-mvp.page.list.actions.filter` | `filter` (from the django-filter integration) | `label` (default `Filter`), `icon` (default `filter`) |
| `c-mvp.page.list.actions.create` | `directory.create_url`, optionally `create_form` and `create_modal_title` | `label` (default `Add`, the button's text), `icon` (default `add`) |
| `c-mvp.page.list.actions.share` | — (always renders) | — |

The search, sort and filter actions all write into a single form with the id
`filterForm`. The filter action renders it when a `FilterSet` is configured, and
`c-mvp.page.list.actions` renders an empty hidden one otherwise, so search and sort work in
any combination.

Each action draws itself only when the view configures what it drives —
`search_fields`, `order_by`, a `FilterSet`, `show_create_action`. Naming all four is
therefore the safe default, and a view drops a control by not configuring it rather than
by shortening this list. `share` is the exception: it takes no context and always
renders, so it appears only where a caller asks for it.

```html
<c-mvp.page>
  <c-mvp.page.title title="{{ page.title }}">
    <c-slot name="actions"><c-mvp.page.list.actions /></c-slot>
  </c-mvp.page.title>
  <c-mvp.page.list :list="object_list" :card="list_item_template" md="2" lg="3" />
  {% if page_obj %}<c-mvp.pagination :page_obj="page_obj" />{% endif %}
</c-mvp.page>
```

## Extending with your own components

Put templates under `templates/cotton/` in your own app — they're immediately usable as
`<c-your-component>` and can be referenced by name in
[`MVP_CONFIG["layout"]["navbar"]["end"]`](layout.md#navbar-widgets). If your components
use Tailwind classes the packaged stylesheet doesn't include, follow the
[Tier 2 build in the styling guide](styling.md#tier-2-build-your-own-stylesheet).
