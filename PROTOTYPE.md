# Prototype: the shell, cards and dialogs on django-mvp-layout

Issue: https://github.com/django-mvp/django-mvp/issues/719

django-mvp depends on django-mvp-layout 0.2.0 (module `mvp_layout`), and three things are drawn with it:

- the application shell, arranged by one code in `MVP_CONFIG["layout"]["view"]`
- `<c-card>`, built from header, body and footer parts, which takes sidebars and its own code
- `<c-modal>`, built the same way

Both override daisy-cotton's components of the same name, recorded in
`docs/adr/0047-the-card-and-the-modal-override-daisy-cottons.md`, which supersedes ADR 0030 for
these two. A card or dialog with no `view` is drawn
as the package's card and dialog always looked.

## The features

Build order is top to bottom.

### 1. The shell on a layout code (feature)

A project arranges its whole shell with one code and configures both sidebars from settings. A page
gets a right sidebar by filling a template block.

- `MVP_CONFIG["layout"]["view"]`, default `"lHh LpR lff"`. A view or template can set
  `layout_view` in the context to draw one page with another code.
- `MVP_CONFIG["layout"]["sidebar"]` gains `behavior` (`auto`, `docked`, `overlay`) and `width`,
  next to the existing `collapse`, `breakpoint`, `title` and `boost`.
- `MVP_CONFIG["layout"]["secondary_sidebar"]`: `collapse`, `breakpoint` (default `xl`),
  `behavior`, `width` (default `18rem`), `label`.
- `{% block app.secondary_sidebar %}` in `mvp/base.html` fills the right sidebar. A page that
  leaves it empty has no right sidebar and no navbar button for it.
- The navbar's sidebar button is a `<c-layout.toggle>` that shows only while the left sidebar is
  closed, and the brand shows beside it only then (`data-mvpl-when="left-closed"`). The sidebar's
  own header carries the close button. The right-sidebar button sits at the end of the navbar.
- The left sidebar remembers open or closed in the cookie `mvpl-mvp-sidebar`, the right in
  `mvpl-mvp-secondary-sidebar`.
- The left sidebar's content (`cotton/app/sidebar/`) is stacked by django-mvp-layout's `HbF`: the
  brand row and the footer stay in place while the menu scrolls between them.
- The dock's Menu item is a button with `data-mvpl-toggle="left" data-mvpl-layout="mvp-app"`.
- Full-height pages (`<c-mvp.page fill>`) fill the window inside the layout's grid.

Screens: every page. http://devserver:8002/components/card/ has sidebars in a box,
http://devserver:8002/products/ has none, http://devserver:8002/layout/full-page/ is a filled page.

### 2. A card built from parts, with a layout (feature)

`<c-card>` overrides daisy-cotton's card. The caller writes the parts it wants: `<c-card.header>`
(`title`, `icon`, `href`, slots `badges` and `actions`, and a default slot for heading markup),
`<c-card.body>` (`tight`) and `<c-card.footer>` (a start group and an `end` slot), stacked by
django-mvp-layout's `hbf`: the parts are `.mvpl-header`, `.mvpl-body` and `.mvpl-footer`, and a
card without a figure carries `hbf`. With no parts the content sits straight on the surface. It keeps daisy-cotton's `size`, `border`, `dash`, `side`,
`image-full` and `figure`. `<c-mvp.card>` and `<c-mvp.card.wrapper>` are gone, with no alias.

A developer sets `view` on a card and places django-mvp-layout's own `<c-layout.sidebar>` and
`<c-layout.page>` between the header and the footer, exactly as in the shell. Every sidebar option
the package has is available, measured against the card's own width.

- `view` turns layout mode on. It has no default.
- `height` is optional. Unset, the card is as tall as its content (django-mvp-layout 0.1.1 and later). Set,
  the body scrolls inside it.
- The header part is the layout's header, with a `<c-layout.toggle>` for each side that hides
  itself when that sidebar is absent or never closes. The footer part is the layout's footer.

Depends on 1 only for the shared box styles. Screens: every section of
http://devserver:8002/components/card/, and http://devserver:8002/components/card/#sidebars, #icon-rail, #another-layout-code,
#a-drawer-at-every-width, #in-a-narrow-card.

### 3. A dialog built from parts, with a layout (feature)

`<c-modal>` overrides daisy-cotton's modal, built from `<c-modal.header>` (`title`, `icon`, slot
`actions`), `<c-modal.body>` and `<c-modal.footer>` (a start group and an `end` slot). It keeps
`placement`, `closable`, `open`, `content_class` and `class`, and the package's `size`, and writes
its own `<dialog>`, box, close button and backdrop. The header's title names the dialog.
`<c-mvp.modal>` is gone, with no alias. The sheet and the search dialog call it.

The layout works as on the card: sections in a sidebar, a details pane, options in a drawer.

- `view` turns layout mode on. The children are the header part, `<c-layout.sidebar>`,
  `<c-layout.page>` and the footer part.
- Built from parts, the box stays daisyUI's `.modal-box`, capped at the screen's height, and
  carries django-mvp-layout's `hbf`. The body (`.mvpl-body`) scrolls inside the cap, with the
  heading row, the actions row and the close button in view.
- With a view the layout grows with its content up to that cap, then scrolls inside it with the
  heading and actions rows in view.
- The header part carries the toggles and the actions slot. The close button sits in the box's
  top corner and the header leaves room for it. The footer part is the layout's footer.
- Escape closes an open drawer before the dialog (the layout package's script).

Depends on 2 for the shared rows (see below). Screens: every dialog on
http://devserver:8002/components/modal/ and http://devserver:8002/components/sheet/, the search
dialog (Ctrl K), the page information and create dialogs on http://devserver:8002/products/, the
language dialog in the sidebar's footer, and
http://devserver:8002/components/modal/#sections-in-a-sidebar, #two-sidebars,
#options-in-a-drawer.

### 4. Demo pages (resolve)

The sidebar's Layout group and the two theme pages become one group, Look & Feel, with three pages:

- **App layout** (`/layout/`): the shell's own regions, the sidebar's and the header's, each with
  its diagram and its table of blocks, then a short section on how the page sits in the shell. It
  links to django-mvp-layout's documentation of the layout code
  (https://django-mvp.github.io/django-mvp-layout/developer/layout-code.html). The page itself has
  no right sidebar: the diagrams show the layout. The demo has no page of its own for the code.
- **Page layout** (`/layout/page/`): the page title and the side panel together, one form for the
  options of both, and an "On this page" panel listing both halves.
- **Theme** (`/theme/`): what was Theme Preview, with a short explanation at the top and a theme
  menu as the page title's action. That menu changes this page only and saves nothing, so the next
  page is in the site's theme. Theme Customization is gone.

The new card and modal examples go with these. Nobody gets a new way of working from them, so this
is resolve work that comes with features 1 to 3.

## Shared pieces

| Piece | Where it occurs | Becomes | Built by |
|---|---|---|---|
| The heading row and the footer row of a card or dialog, with a toggle each side in a layout | `mvp/templates/cotton/mvp/box/header.html`, `mvp/templates/cotton/mvp/box/footer.html`, called by `cotton/card/header.html`, `card/footer.html`, `modal/header.html`, `modal/footer.html` | Kept as built | 2, reused by 3 |
| Stacking a header, body and footer | The card and the dialog built from parts, the shell's left sidebar | django-mvp-layout's `hbf` and `HbF` classes, no stacking rules of django-mvp's own | 1, 2, 3 |
| Box styles (part spacing, `--mvpl-sidebar-bg`, `--mvpl-line`, header and footer rules) | `mvp/tailwind/base.css`, the block in `@layer utilities { @layer daisyui.l1.l2 }` | Kept, keyed to `.mvp-box-layout` and the parts' classes | 2 |
| Rail-aware variants `is-drawer-open` / `is-drawer-close` | `mvp/tailwind/base.css` (`@custom-variant`) | Kept, keyed to `.mvpl-sidebar[data-mvpl-rail]` | 1 |
| Rail labels | `mvp-sidebar--icons` rules in `mvp/tailwind/base.css` and the package's `.mvpl-rail-hide` / `.mvpl-rail-only` | One mechanism: the package's classes, used by django-mvp's menu | 1 |
| Parsing the code | The package's `LayoutView.parse` | The package's parser, also called by a django-mvp system check on `layout.view` | 1 |

## Duplication to remove

- `mvp/tailwind/base.css` still holds the `.drawer[data-mvp-breakpoint…]` rules for
  `mvp-sidebar-hidden-only` and `mvp-sidebar-toggle`. They match nothing now.
- `mvp/layout.py` (`LayoutConfig`) resolves breakpoint, collapse and sticky for a shell that no
  longer exists.

## The look

| File | Ported by | Lands in |
|---|---|---|
| `mvp/templates/mvp/base.html` (the `app` block) | 1 | Same path |
| `mvp/templates/cotton/app/header.html, navbar.html, sidebar/header.html, sidebar/index.html, sidebar/footer.html` | 1 | Same paths |
| `mvp/templates/menus/dock/item.html` | 1 | Same path |
| `mvp/config.py` (`layout.view`, `sidebar`, `secondary_sidebar`) | 1 | Same path |
| `mvp/tailwind/base.css` (variants, rail, full-page rules, box colours) | 1, 2 | Same path |
| `mvp/templates/cotton/card/index.html, header.html, body.html, footer.html` | 2 | Same paths |
| `pyproject.toml` (django-mvp-layout 0.2.0) | 1 | Same path |
| `mvp/templates/cotton/modal.html`, `cotton/modal/header.html, body.html, footer.html` | 3 | Same paths |
| `mvp/templates/cotton/mvp/box/header.html, footer.html` | 2 | Same paths |
| `mvp/templates/cotton/mvp/sheet/index.html`, `search/dialog.html`, `page/info.html`, `page/list/actions/create.html`, `actions/language_switcher_modal.html`, `mvp/templates/mvp/account/overview.html`, `mvp/pwa/install.html` | 2, 3 | Same paths |
| `docs/adr/0047-the-card-and-the-modal-override-daisy-cottons.md`, the status line of `docs/adr/0030-…` | 2, 3 | Same paths |
| `demo/templates/demo/layout/app.html`, `layout/page.html`, `layout/blocks.html`, `theme.html`, `cotton/demo/layout/shell.html` (the region links), `demo/views.py`, `demo/urls.py`, `demo/menus.py` | 4 | Same paths |
| `demo/templates/demo/components/card.html`, `modal.html` (every section) | 4 | Same paths |
| Every other demo template with a card or dialog: `landing.html`, `dashboard.html`, `theme.html`, `components/index.html`, `cards/product_card.html`, `account_showcase/…/overview.html` | 2, 3 | Same paths |

Screens for the parity check, each at 390 and 1440 wide, signed out and as `regular.user`:

- http://devserver:8002/layout/, with each sidebar open and closed
- http://devserver:8002/products/ (no right sidebar)
- http://devserver:8002/layout/full-page/
- http://devserver:8002/components/card/ (every section, each sidebar opened and closed)
- http://devserver:8002/components/modal/ (every dialog open, and on the phone the sections
  drawer open)
- http://devserver:8002/ (the landing cards), http://devserver:8002/theme/,
  http://devserver:8002/layout/page/, http://devserver:8002/components/sheet/
- As `regular.user`: http://devserver:8002/, http://devserver:8002/account/,
  http://devserver:8002/install/

Seed: `python manage.py migrate && python manage.py generate_dummy_data`.

## The data model

None. The only state is the sidebar cookies, `mvpl-<persist>=open|closed`.

## Decisions

- 2026-11-24: django-mvp depends on django-mvp-layout, and one code arranges the shell. (Sam)
- 2026-11-24: Cards and dialogs take the layout too. (Sam)
- 2026-11-24: A card or dialog with a layout takes django-mvp-layout's own `<c-layout.sidebar>` and
  `<c-layout.page>` as children, the same way the shell does, not slots and per-side props. `view`
  turns it on and has no default. (Sam)
- 2026-11-24: A layout grows with its content; a height is optional. Fixed in django-mvp-layout
  0.1.1, https://github.com/django-mvp/django-mvp-layout/pull/16. (Sam)
- 2026-11-24: A dialog with a layout scrolls the daisyUI way: the box is capped at the screen and
  its body scrolls inside it. (Sam)
- 2026-11-24: Breaking existing projects is not a concern. (Sam, on
  https://github.com/django-mvp/django-mvp/issues/717)
- 2026-11-25: The card is a header, body and footer, built from parts the caller declares, in
  place of most of its props and slots. Simple cards get longer, and a project that wants the old
  shorthand writes its own wrapper component. Existing cards break, and better now. (Sam)
- 2026-11-25: The card goes back to `<c-card>`, overriding daisy-cotton's card, the way daisy-cotton
  was meant to be customised. `<c-mvp.card>` goes, with no alias. (Sam)
- 2026-11-25: The dialog does the same: `<c-modal>` overrides daisy-cotton's modal, built from
  parts. `<c-mvp.modal>` goes, with no alias. (Sam)
- 2026-11-25: django-mvp uses django-mvp-layout 0.2.0's hbf classes for every header, body and
  footer stack. (Sam)
- 2026-11-27: The demo has no layout code page. django-mvp-layout documents the code, and the App
  page links to it. (Sam)
- 2026-11-27: The main sidebar shows no horizontal scrollbar. Its menu fills the layout's panel and
  sets no width of its own. (Sam)
- 2026-11-27: A docked sidebar's page keeps to the panel's edge while it opens and closes, with no
  empty strip behind the panel and no early jump of the page. Fixed in django-mvp-layout:
  https://github.com/django-mvp/django-mvp-layout/issues/23,
  https://github.com/django-mvp/django-mvp-layout/pull/24. The prototype installs that branch until
  it is released. (Sam)
- 2026-11-27: django-mvp-layout takes a time for a sidebar's open and close: one for the whole
  site, and one per sidebar on `<c-layout.sidebar>`. Same pull request. (Sam)
- 2026-11-27: The demo's Layout group and its theme pages become one group, Look & Feel: App layout
  (app, sidebar and header, and a short section on the page), Page layout (page title and side
  panel) and Theme (the preview, with a theme menu as the title's action). Theme Customization is
  removed. (Sam)
- 2026-11-27: App layout has no right sidebar. It shows the layout in its diagrams, not in its own
  page. (Sam)
- 2026-11-27: The theme menu on the Theme page changes that page only. Leaving the page, by a link
  or a new load, shows the site's own theme again. (Sam)
- 2026-11-27: The main sidebar is 20rem wide as a drawer on a phone or tablet, and 16.25rem beside
  the page. django-mvp-layout gives a drawer a width of its own, `--mvpl-drawer-w`, 20rem by
  default, settable for every sidebar or on one with `drawer-width`:
  https://github.com/django-mvp/django-mvp-layout/issues/25, in
  https://github.com/django-mvp/django-mvp-layout/pull/24. (Sam)
- 2026-11-27: The main sidebar is django-mvp-layout's sidebar with `view="HbF"`, not a second box
  inside it. `<c-app.sidebar>` draws `<c-layout.sidebar side="left" view="HbF">`, its brand row,
  menu and footer sit straight inside the layout's panel, and the panel is the one thing that
  scrolls. (Sam)
- 2026-11-27: The sidebar's footer holds one full-width account button, with no theme or language
  control. The theme and the language are set from the header. (Sam)

## Decided on my own

- **The shell's default code is `lHh LpR lff`**, as the current shell looks: the left sidebar runs
  the full height, the header and both sidebars stay in place.
- **The right sidebar is a block, `app.secondary_sidebar`**, drawn only when filled. Beside the
  page from `xl`, a drawer below.
- **The toggles in a box's title row take the package's default names**, "Left sidebar" and "Right
  sidebar", not the sidebar's own label.
- **`href` is on the card's header part and `tight` on its body part.** `body_class` became the
  body part's own `class`.
- **The header part's default slot is heading markup**, drawn inside the heading after the title.
  The landing page's cards, which drew icons in daisy-cotton's title slot, use it. Their trailing
  tick moved to the header's `actions` slot.
- **The footer part has a start group and an `end` slot**, in place of the `footer` and
  `footer_end` slots.
- **A card keeps the package's raised look** (`bg-base-100 shadow-sm`) unless it has `border` or
  `dash`, which draw it flat as daisyUI does.
- **A card with no parts is the bare surface.** `<c-mvp.card.wrapper>` went with `<c-mvp.card>`.
- **The header part always draws its sidebar toggles**, and a stylesheet rule shows them only
  where the header sits in its own card's or dialog's layout. A part cannot see the `view` on the
  card around it, and a toggle outside that layout would reach the shell's sidebar.
- **The dialog keeps `size`**, which the agreed list did not name, because eleven dialogs use the
  widths. An empty `size` leaves the width to `content_class`, which the sheet and the search dialog
  use. `position` became daisy-cotton's `placement`.
- **The close button sits in the box's top corner**, daisyUI's place for it, in both kinds of
  dialog. The header leaves room for it.
- **The dialog takes its name from the header's title** through a short script after the
  `<dialog>`, since the part cannot reach the dialog's id. A caller's `aria-label` or
  `aria-labelledby` wins, as the sheet's and the search dialog's do.
- **The sheet and the search dialog keep their own inner markup** and call the new `<c-modal>`
  with an empty `size`. Their heads and bodies have their own styles and scripts.
- **`class:merge` is used where a part's default classes are fixed** (`card.body`, `modal.body`).
  Cotton resolves a merged default before the component's other variables, so classes that depend
  on them are written in the markup.
- **The card and dialog styles sit in daisyUI's own layer**, one level above its component rules,
  so they beat daisyUI's padding and a caller's utility classes still beat them.
- **The dialog's stack is `hbf`, nothing sticky.** The body scrolls inside the box, not the box
  itself, so the header, the footer and the close button stay in view without sticking, as before.
  A scrolling box would carry the close button away with it.
- **The shell's left sidebar is `HbF`**, sticky header and footer, as its brand row and footer
  were. `<c-app.sidebar>` is the layout's sidebar itself, so `boost`, `class` and `bg` land on its
  `aside`, and `{% block app.sidebar %}` holds the whole sidebar.
- **django-mvp-layout's stylesheet loads before django-mvp's**, as the package documents, so its
  layer sits below Tailwind's components and utilities and a `bg` class on the sidebar beats the
  layout's own background. As a drawer the panel takes the `aside`'s colour.
- **`boost` off writes `hx-boost="false"`** on the sidebar rather than leaving the attribute out.
  Cotton can't leave an attribute out of a component's tag, and false says what the setting says.
- **The rail's scroll styles and its tooltip script follow the panel**, which is now what scrolls.
- **The account button follows the common sidebar account row** (shadcn/ui's sidebar user block,
  Vercel, Linear, Supabase): avatar, name over email, and an up-down chevron that marks it as a menu.
  A faint fill and border at rest make it read as a button before it is pointed at, and pointing
  at it lifts it to the page's surface. The name is the full name, else the username, and the
  email line is left out when there is none. In the icon rail it is the avatar alone.
- **A visitor gets a full-width primary Log in button** at the normal button size, so the footer
  keeps its weight. `<c-mvp.actions.login>` takes a `size`, `sm` by default as before.
- **The account menu keeps its rows** (Account Center, Admin Site, Log out) and opens upward over
  the menu, as wide as the button.
- **A card with a figure is not stacked.** daisyUI places the figure above or beside the parts,
  which the three areas have no room for.
- **The dialog is stacked only when it has a part.** The sheet and the search dialog call
  `<c-modal>` with their own markup, a grab handle and a description beside a head, body and foot,
  and keep their own styles.
- **The right sidebar has no stack.** A page fills it with whatever it likes.
- **`behavior: "overlay"` replaces `breakpoint: "never"`.**
- **`page.side` stays as it is.** Whether `app.secondary_sidebar` replaces it is for the rebuild.
- **The three Look & Feel pages have only their own title as a breadcrumb.** The group has no page
  to link to, and a crumb without a link is drawn as the current page.
- **App layout, Page layout and Theme keep the URLs `/layout/`, `/layout/page/` and `/theme/`.**
  `/layout/sidebar/`, `/layout/header/`, `/layout/title/`, `/layout/side/` and `/theme/preview/`
  are gone, and the diagram's sidebar and header regions link to their sections on App layout.
- **The Theme page's menu is the demo's own**, built like the header's theme menu but with its own
  attribute and a short script, so theme-change never saves it. A boosted link keeps `<html>`, so
  the script puts the site's theme back once the page is gone.
- **Theme's explanation is the opening paragraph Theme Customization had**, without its list of the
  demo's themes, followed by the preview's own.
- **Page layout's sample title and eyebrow read "Page layout" and "Look & Feel"**, and its Contents
  button takes the small size of the title's other actions.

## Faked or skipped

- **No tests.** Features 1 to 3.
- **No docs.** `layout.md`, `configuration.md` and `components.md` are rewritten, and the naming
  rule in the constitution and the glossary follow ADR 0047. Features 1 to 3.
- **The tests still call `<c-mvp.card>` and `<c-mvp.modal>`**, and the test that keeps components
  under `cotton/mvp/` has no exception for the card and the modal. Features 2 and 3.
- **A dialog finds its parts by their class names in its content** (`cotton/modal.html`), since a
  part cannot tell the dialog around it that it is there. Feature 3 finds a cleaner way.
- **A wrong `layout.view` fails at render**, not at startup. Feature 1 adds a system check.
- **The old shell is still in the tree**: `mvp/layout.py`, `cotton/app/index.html`,
  `cotton/mvp/layout/sidebar/index.html`, the Alpine `$store.mvp` layout store
  (`assets/js/layout.js`), and the demo page `/layout/store/` that shows it.
  Feature 1 removes them.
- **`MVP_CONFIG["layout"]["navbar"]["sticky"]` is no longer read.** Feature 1 removes it.
- **django-mvp-accounts, compliance, community and payments break.** Nothing is changed in them.
- **A toggle's name doesn't follow its sidebar's label.** The package's script could copy it
  across. Feature 1 of django-mvp-layout's own roadmap, not django-mvp's.
- **`assets/tailwind.css` scans the demo's component and layout templates** so their example
  classes build. Feature 4 moves this to the demo.
- **Icons come from the Bootstrap Icons CDN**, like the rest of the demo.
- **The demo's tests still name the removed pages**: `test_page_title.py`, `test_theme_customization.py`,
  `test_pages.py`, `test_surfaces.py` and `test_surfaces_e2e.py` load `/layout/title/`,
  `/layout/side/`, `customization` or `/theme/preview/`. Feature 4 moves them to the new pages.
- **`--mvp-sidebar-width` and its touch sizing are no longer read.** The sidebar's drawer on a phone
  is the layout's width, 16.25rem, not the 20rem the old shell gave it. Feature 1 decides which.

## What it replaces

- The daisyUI drawer the shell was built on, the `mvp-app-toggle` checkbox and the Alpine layout
  store with its localStorage key.
- `mvp/layout.py` and the sticky navbar setting.
- `breakpoint: "never"` on the sidebar.

Nothing is stored, so nothing needs migrating. A project that set the old sidebar settings changes
its settings.
