# Components — reference

The full catalogue of Cotton components django-mvp ships today: what each tag is for,
what attributes it accepts, and what named slots it fills. Attributes are the supported
customisation surface.

## Naming

A component's tag name is its path under `templates/cotton/`, with two rules:

- **Directory levels become dots.** `cotton/page/list/empty.html` is `<c-page.list.empty>`.
- **Hyphens in a tag become underscores in the filename.** `<c-data-field>` resolves to
  `cotton/data_field.html`, `<c-actions.theme-controller>` to
  `cotton/actions/theme_controller.html`. Cotton rewrites `.` to `/` and then `-` to `_`
  before looking the template up, so a tag can never contain an underscore.
- **`index.html` is the namespace root.** `cotton/menu/index.html` is `<c-menu>`, and the
  files beside it are `<c-menu.item>`, `<c-menu.group>` and so on. Cotton tries
  `<name>.html` first and falls back to `<name>/index.html`.

This matters beyond authoring templates: the widget lists in `MVP_CONFIG`
(`layout.navbar.mobile.end`, `layout.navbar.desktop.end`, `layout.sidebar.footer`) are
lists of **component names**, not template paths. `"actions.theme-controller"` in settings
renders `<c-actions.theme-controller />`.

## Extending a component

1. **Pass attributes.** Everything a component supports on purpose is in the tables below.
2. **Add classes.** Every component that takes a `class` attribute appends it to its root
   element rather than replacing what is already there.
3. **Pass anything else.** Attributes a component does not declare are collected and, on
   the components whose root spreads them, emitted verbatim on that root element — so
   `id`, `hx-*`, `x-data`, `aria-*` and event handlers reach the DOM without the component
   declaring them. Components that render fixed markup with no spread (for example
   `<c-section.hero>`, `<c-badge>`, `<c-placeholder.card>`) deliberately accept only their
   declared attributes.
4. **Override the template.** For anything the attributes do not reach, put a template at
   the same path in your own project's `templates/cotton/` directory. Yours wins. This is
   the primary extension point — read the packaged template first so you know what you are
   replacing.

```html
<c-card title="Recent samples" icon="flask" id="samples" x-data="{ open: true }">
  <c-slot name="actions"><c-button size="sm" icon="add" text="New" href="{% url 'sample-create' %}" /></c-slot>
  <c-data-field label="Collected" value="{{ object.collected_on }}" />
</c-card>
```

## Shared attribute vocabulary

A handful of attribute names mean the same thing everywhere they appear.

| Attribute | Meaning |
|---|---|
| `variant` | Semantic colour role: `primary`, `secondary`, `accent`, `neutral`, `info`, `success`, `warning`, `error`. Unset means the neutral default. |
| `size` | A step on the component's own scale. The scales differ — a button runs `sm`–`lg`, an avatar `xs`–`xxl`, a modal `sm`–`full` — so each is spelled out in the tables below. |
| `icon` | An icon name resolved through the configured icon packs, the same names `<c-icon name="…">` takes. |
| `class` | Extra classes appended to the component's root element. |
| Breakpoint values | `sm`, `md`, `lg`, `xl`, `2xl` — except on `<c-grid>`, which spells the largest `xxl`. `row` on `<c-toolbar>` and `vertical` on `<c-divider>` also accept `True`, meaning "at every width". `responsive` on `<c-menu>` wants a breakpoint name and nothing else. |

Boolean attributes are set by presence: `<c-alert dismissible>`, not `dismissible="True"`.

## Page structure

| Tag | Purpose | Attributes (default) | Slots |
|---|---|---|---|
| `<c-page>` | Root wrapper for a page's content, stacking its children with a consistent gap | `fluid`, `fill`, `gap` (`6`), `class` | default |
| `<c-page.content>` | A flexible region inside a page that absorbs leftover height | `gap` (`4`), `class` | default |
| `<c-page.title>` | Page heading with optional subtitle and a right-aligned action row | `title`, `subtitle`, `class` (declared, currently unused) | default, `actions` |
| `<c-page.toolbar>` | A row of controls that renders nothing at all when given no children | `class` | default |
| `<c-container>` | Centred, width-constrained content band | `fluid`, `fill`, `class` | default |
| `<c-section>` | A titled block of a page, with an optional heading icon and actions | `title`, `icon`, `level` (`2`) | default, `actions` |
| `<c-section.hero>` | Full-width banner with a large heading over an optional background image | `bg-image`, `title`, `subtitle`, `opacity` (`0.5`), `height`, `class` | `top`, `actions`, `bottom` |
| `<c-entrance>` | The centred card that anonymous-facing pages (log in, sign up, reset) render into | `size` (`2xl`; `sm`–`4xl` or `full`), `full-height` | default |
| `<c-entrance.background>` | The full-height, centred backdrop `<c-entrance>` sits on. Use directly for a custom entrance card | — | default |

`<c-page fill>` marks a page that wants the shell's height instead of its content's. The
shell keys off it. `<c-entrance>` still accepts a deprecated `small` attribute that
predates `size` — pass one or the other, never both.

## Layout primitives

| Tag | Purpose | Attributes (default) | Slots |
|---|---|---|---|
| `<c-grid>` | Responsive column grid | `cols` (`1`), `gap` (`4`), `sm`, `md`, `lg`, `xl`, `xxl`, `class` | default |
| `<c-group>` | A stack of children that can turn into a row | `row` (`False`), `collapse` (`False`), `wrap` (`False`), `gap` (`2`), `class` | default |
| `<c-toolbar>` | Content on one side, actions on the other, stacking on narrow screens | `row` (`md`; `True` or a breakpoint name), `gap` (`2`), `class` | default, `actions` |
| `<c-divider>` | A labelled break between sections of a page | `vertical` (`True` or a breakpoint, to separate side-by-side content), `variant`, `position`, `class` | default, `label` |
| `<c-rule>` | A hairline between items that belong to the same set: an `<hr>` with one border-width of `base-300` and no margin or label | `class` | — |
| `<c-backdrop>` | A dimming layer filling its positioned parent | `opacity` (`0.5`) | — |

`row` on `<c-group>` is a boolean (always a row). `collapse` becomes a row only on wide
screens. `row` on `<c-toolbar>` takes either `True` or a breakpoint name.

## Data display

| Tag | Purpose | Attributes (default) | Slots |
|---|---|---|---|
| `<c-card>` | The standard card layout: heading row, body, footer row — every part optional | `title`, `icon`, `tight`, `class`, `body_class` | default, `badges`, `actions`, `footer`, `footer_end` |
| `<c-card.wrapper>` | The bare card surface, for a fully custom interior | `class` | default |
| `<c-button>` | Button, or a link styled as one when given `href` | `text`, `icon`, `variant`, `size`, `outline`, `ghost`, `full`, `reverse`, `align` (`center`), `condition` (`True`), `class` | default |
| `<c-link>` | Inline text link | `href` (`#`), `text`, `variant`, `hover`, `class` | default |
| `<c-badge>` | Small count or status marker | `text`, `variant`, `size` (`sm` or `lg`), `outline`, `class` | default |
| `<c-icon>` | Renders a named icon from the configured icon packs | `name`, `class` | — |
| `<c-text>` | A paragraph with the standard prose treatments | `text`, `size` (`base`), `align`, `muted`, `tight`, `bold`, `upper`, `class` | default |
| `<c-alert>` | A standing message, optionally dismissible on a timer | `variant`, `icon`, `soft`, `outline`, `dash`, `dismissible`, `delay`, `class` | default |
| `<c-data-field>` | One label-and-value pair for a detail page; links the value when it has a URL | `label`, `value`, `help_text`, `missing` (`–`) | default |
| `<c-messages>` | Renders Django's flash messages as stacked, self-dismissing alerts | `dismissible`, `delay` (`2000`) | — |
| `<c-modal>` | A dialog laid out as a card. Open and close it by its `id` | `id`, `size` (`md`; `sm`–`xl` or `full`), `position`, `closable`, `class` | default, `actions`, `footer`, `footer_end` |
| `<c-dropdown>` | A trigger plus a floating panel | `halign` (`start`), `valign` (`bottom`), `full`, `hover`, `class`, `content_class` | default, `button` |
| `<c-avatar>` | A user's picture, initials, or a silhouette fallback | `for` (`request.user`), `src`, `alt` (`User avatar`), `size` (`md`; `xs`–`xxl` or a width class), `shape` (`rounded-full`), `variant` (`primary`), `status`, `placeholder`, `class` | — |
| `<c-avatar.group>` | Overlapping row of avatars | `size` (`md`) | default |
| `<c-brand.icon>` | The site's square mark, resolved through the brand config | `max-height`, `class` | — |
| `<c-brand.logo>` | The site's full logo, resolved through the brand config | `max-height`, `class` | — |
| `<c-placeholder.card>` | A card-shaped stand-in for a region that is not built yet | `message` (`Coming soon...`), `icon`, `height`, `class` | — |
| `<c-mockup.browser>` | Content framed as a browser window with an address bar | `url`, `class` | default |
| `<c-mockup.window>` | Content framed as a plain application window | — | default |
| `<c-mockup.phone>` | Content framed as a phone screen | — | default |
| `<c-mockup.code>` | A terminal or code block frame | — | default |
| `<c-mockup.code.line>` | One line inside `<c-mockup.code>` | `text` | default |

Without a `button` slot, `<c-dropdown>` forwards its undeclared attributes to an inner
`<c-button>` that becomes the trigger, so `text`, `icon`, `variant` and `size` configure it
directly. Supply the `button` slot instead and those attributes fall through to the
dropdown wrapper — then you own the trigger's focus behaviour.

`<c-modal>` forwards `title`, `icon` and its `actions` / `footer` / `footer_end` slots to
an inner `<c-card>`, so a modal is laid out exactly like a card.

`<c-button condition="{{ perms.app.add_thing }}">` renders nothing when the condition is
falsy, which keeps permission checks out of the surrounding template.

## Navigation

| Tag | Purpose | Attributes (default) | Slots |
|---|---|---|---|
| `<c-menu>` | A list of navigation items | `label`, `horizontal`, `responsive`, `paged`, `grow` (`False`), `class` | default |
| `<c-menu.item>` | One entry — a link with `href`, otherwise a button | `label`, `icon`, `href`, `active`, `badge`, `tip`, `class` | default |
| `<c-menu.group>` | A named group of entries, either a heading or an expandable section | `label`, `collapse`, `icon`, `icon_class`, `badge`, `badge_class` | default |
| `<c-menu.collapse>` | A thin pass-through to `<c-menu.item>` that also takes children. Every attribute is forwarded | (all forwarded) | default |
| `<c-menu.divider>` | A separator between menu entries | — | — |
| `<c-breadcrumbs>` | Trail of ancestor links | `items`, `class` | default |
| `<c-breadcrumbs.item>` | One crumb; a link when given `href` | `text`, `href`, `class` | default |
| `<c-pagination>` | Full pager built from a Django `page_obj` | `page_obj`, `page_window` (`5`), `use_icons`, `show_first_and_last` | — |
| `<c-pagination.link>` | One page control, for a hand-built pager | `page`, `text`, `active`, `disabled`, `size`, `class` | default |
| `<c-pagination.wrapper>` | The labelled container a hand-built pager goes in | `label`, `class` | default |
| `<c-dock>` | Bottom bar of primary destinations on small screens | `size` (`xs`–`xl`) | default |
| `<c-dock.item>` | One dock entry — a drawer toggle with `toggle`, a link with `href`, otherwise a button | `label`, `icon`, `href`, `toggle`, `active`, `class` | — |

`<c-breadcrumbs>` takes either an `items` list of attribute dicts or hand-written
`<c-breadcrumbs.item>` children. `items` wins when both are given. `<c-pagination>` renders
nothing when there is only one page. `show_first_and_last` swaps the First/Last text
controls for the first and last page numbers.

## Forms

| Tag | Purpose | Attributes (default) | Slots |
|---|---|---|---|
| `<c-form>` | The `<form>` element: CSRF token, multipart detection, and an optional rendered form | `form-obj`, `formset`, `inlines` | default |
| `<c-form.render>` | Renders a Django form's fields, honouring its helper when it has one | `form` | — |
| `<c-form.field>` | One presentational control with optional label, help text and errors | `type` (`text`), `label`, `hide-label`, `help-text`, `errors`, `prelabel`, `postlabel`, `class`, `wrapper-class` | default, `label`, `help_text`, `errors`, `prelabel`, `postlabel` |
| `<c-form.formset>` | A whole Django formset: heading, management form, rows, and an add-row control | `formset`, `title`, `description`, `add-label`, `remove-label`, `class` | — |
| `<c-form.formset.row>` | One row of a formset, with its label and remove control | `form`, `label`, `first` (`False`), `can-delete` (`False`), `remove-label`, `class` | — |

`<c-form>` passes `method`, `action`, `id` and anything else through to the `<form>`
element, and only emits a CSRF token when `method` is `post`. `formset` and `inlines` on
`<c-form>` exist so the form can detect that it needs a multipart encoding — they are not
rendered by it.

`<c-form.field>` accepts every text-like input type plus `textarea`, `select`, `file`,
`checkbox`, `radio` and `toggle`. `name`, `id`, `value`, `placeholder`, `required`,
`disabled`, `checked` and `rows` pass straight to the control. `errors` takes a string or a
list and switches the control to its error state. Each of `label`, `help-text`, `errors`,
`prelabel` and `postlabel` can be an attribute or a same-named slot when you need rich
content. Reach for `<c-form.render>` when you have a whole Django form.

`<c-form.formset.row>` is placed by `<c-form.formset>`, which supplies `first` and
`can-delete` from the set. You would only write it by hand for a custom set layout.

## Widgets you place by name

These are designed to be listed in `MVP_CONFIG` — `layout.navbar.mobile.end`,
`layout.navbar.desktop.end`, `layout.sidebar.footer` — rather than written into a page.
Each renders nothing when its precondition is unmet.

| Tag | Purpose | Attributes (default) | Renders when |
|---|---|---|---|
| `<c-actions.theme-controller>` | Theme menu when `theme.choices` is configured, otherwise a two-theme toggle | `size` (`sm`) | always |
| `<c-actions.language-switcher>` | Language chooser as a dropdown list | — | `LocaleMiddleware` is installed **and** `set_language` is routed |
| `<c-actions.language-switcher-modal>` | Language chooser as a dialog with a tappable grid — the phone-friendly alternative | `id` (`languageModal`) | `LocaleMiddleware` is installed **and** `set_language` is routed |
| `<c-actions.login>` | Log-in button, preferring allauth's URL over Django's | — | visitor is anonymous **and** `account_login` or `login` reverses |
| `<c-actions.search>` | A standalone search box | — | always |
| `<c-user.sidebar-menu>` | The signed-in user's menu: account centre, your own extra entries, log out | — | user is authenticated |
| `<c-user.display.compact>` | Avatar plus name and email, for use inside a user menu or panel | — | always |

`<c-actions.search>` renders an input that is not wired to a form or a view — it submits
nothing on its own. Treat it as markup to build on, not a working search.

`<c-user.sidebar-menu>` puts its default slot between the account-centre entry and log out,
so extra `<c-menu.item>` children land in the middle of the menu.

## Add-ons

Components that sit alongside the core set rather than inside it. One of them needs a
third-party package installed and its integration wired up before you use it.

| Tag | Purpose | Attributes (default) | Slots | Needs |
|---|---|---|---|---|
| `<c-addons.share-dropdown>` | Share menu for the current page: social networks, email, copy link | `url` (current URL), `title` (`page.title`), `size`, `class` | — | nothing |
| `<c-addons.django-table>` | Scroll region around a rendered django-tables2 table, owning both axes | `table`, `label`, `role` (`region`), `class` | — | django-tables2 |

`<c-addons.share-dropdown>` is plain markup over hard-coded social URLs, so it renders
anywhere — `<c-page.list.actions.share>` puts it on a list page unconditionally.

Give `<c-addons.django-table>` a distinct `label` on any page with more than one table.
The default accessible name is shared.

## List components driven by view context

These render from context a list view supplies. Each one is a no-op without its key, so
they are meant to sit on a page served by an MVP list view (or a view mixing in the same
mixins), not dropped into an arbitrary template.

| Tag | Purpose | Context key it needs | Attributes (default) |
|---|---|---|---|
| `<c-page.list>` | The result grid: one item template per object, or the empty state when there are none | `list` (plus `list_item_template`) | `list`, `empty_state` |
| `<c-page.list.empty>` | The "nothing here" panel, with an add button when the view offers a create URL | — (`directory.create_url` gates the button) | `icon` (`search`), `heading`, `message`, `icon_class`, `class` |
| `<c-page.list.footer>` | Result count and pager beneath a list | `page_obj` | — |
| `<c-page.list.actions>` | Renders the action components in order | — (each action needs its own key) | `actions` (`['search','sort','filter','create']`) |
| `<c-page.list.actions.search>` | Search box bound to the filter form | `is_searchable` (from `SearchMixin`) | `placeholder` (`Search`), `label` (`Search`, the submit button's text) |
| `<c-page.list.actions.sort>` | Sort menu that resubmits the filter form on choice | `order_by_choices` (from `OrderMixin`) | — |
| `<c-page.list.actions.filter>` | Filter button and dialog, with a badge counting applied filters | `filter` (from the django-filter integration) | `label` (`Filter`), `icon` (`filter`) |
| `<c-page.list.actions.create>` | Add button — a dialog when the view supplies an inline create form, a link otherwise | `directory.create_url`, optionally `create_form` | `label` (`Add`), `icon` (`add`, declared but the button hard-codes `add`) |
| `<c-page.list.actions.share>` | Share menu for the list page | — (always renders) | — |

The search, sort and filter actions all write into a single form with the id `filterForm`.
The filter action renders it when a `FilterSet` is configured, and `<c-page.list.actions>`
renders an empty hidden one otherwise, so search and sort work in any combination.

Each action draws itself only when the view configures what it drives — `search_fields`,
`order_by`, a `FilterSet`, `show_create_action`. Naming all four is therefore the safe
default, and a view drops a control by not configuring it rather than by shortening this
list. `share` is the exception: it takes no context and always renders, so it appears only
where a caller asks for it.

```html
<c-page>
  <c-page.title title="{{ page.title }}">
    <c-slot name="actions"><c-page.list.actions /></c-slot>
  </c-page.title>
  <c-page.list :list="object_list" md="2" lg="3" />
  <c-page.list.footer />
</c-page>
```

`<c-page.list>` passes its undeclared attributes to the grid it renders, so column counts
and gaps are set on the tag itself. `empty_state` takes a dict of attributes forwarded to
`<c-page.list.empty>` when the result set is empty.

## App shell internals

The shell places these. **A page never writes them by hand.** They are documented so you
know what you are looking at when you override one. Configure the shell through
`MVP_CONFIG` first — most of what these read comes from there.

| Tag | What it is | Attributes (default) | Slots |
|---|---|---|---|
| `<c-app>` | The whole shell: a drawer holding the sidebar beside the page content | `breakpoint` (from config) | default |
| `<c-layout.sidebar>` | The drawer mechanism `<c-app>` is built on: the toggle, the overlay, and desktop open-state persistence | `id`, `breakpoint` (from config), `class` | default, `sidebar` |
| `<c-app.header>` | The header band, optionally pinned to the top on scroll | `sticky`, `breakpoint`, `collapse` (all from config) | `above`, `right`, `tray`, `below` |
| `<c-app.header.navbar>` | Inside the header: sidebar toggle, site name, then the configured navbar widgets — separate mobile and desktop lists | `breakpoint`, `collapse` (from config) | `right` |
| `<c-app.sidebar>` | The sidebar itself: brand header, `AppMenu`, footer widgets | `menu` (`AppMenu`), `brand-url` (`/`), `bg`, `collapse`, `title`, `boost` (from config), `class` | — |
| `<c-app.sidebar.header>` | The sidebar's top strip: brand icon, optional title, collapse toggle | `link` (`/`), `bg`, `title` (from config) | — |
| `<c-app.sidebar.footer>` | The pinned strip at the sidebar's foot, holding the configured footer widgets | — | — |
| `<c-app.main>` | The main content region the page's `{% block content %}` renders into | — | default |
| `<c-app.footer>` | The site footer under the content | `class` | default |
| `<c-app.dock>` | The bottom navigation bar on small screens, rendered from `MobileFooterMenu` | — | — |

`<c-app.sidebar>` and `<c-app.dock>` render menus by name through django-flex-menus, so
changing what is in them is a menu change, not a template change. The sidebar's `boost`
setting makes its links navigate with htmx instead of a full page load — off by default,
because it changes how the page's own scripts see navigation.

---

Back to [SKILL.md](../SKILL.md).
