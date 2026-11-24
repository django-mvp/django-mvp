# Prototype: the layout code

Issue: https://github.com/django-mvp/django-mvp/issues/717

The application shell is arranged by a nine-letter layout code, such as `lHh LpR lff`, read the way
Quasar's `QLayout` reads its `view` property and the way sphinx-daisyui reads its `layout` option.
The layout is a set of Cotton components in a new package, `daisy_cotton_layout`, that any Django
project running django-cotton and daisyUI can use. django-mvp's shell is rebuilt on it.

The package lives at the root of this branch for the prototype. In the real build it is its own
repository and distribution, with its own browser tests, and django-mvp depends on it.

## The features

Build order is top to bottom.

### 1. The layout package (new package, feature)

A developer arranges a page, or a box inside a page, with `<c-layout view="…">` and its areas, and
gets sidebars that open, close, collapse to an icon rail and turn into drawers by themselves.

- `<c-layout view container id class style>`: reads the code, refuses a wrong one with the rules,
  and arranges the areas on a CSS grid. `container` makes it fill the box it is placed in and
  scroll inside it, so it nests in a card, a dialog or another layout.
- `<c-layout.header>`, `<c-layout.page tag>`, `<c-layout.footer>`.
- `<c-layout.sidebar side collapse breakpoint behavior width rail-width closed persist label>`:
  drawn only when it has content. `collapse` is `offcanvas`, `icons` or `none`. `behavior` is
  `auto` (a drawer below `breakpoint`), `docked` or `overlay`. `persist` remembers its state in a
  cookie that the server reads, so the page is drawn in the remembered state.
- `<c-layout.toggle side when label>`: opens and closes its own layout's sidebar, hides itself
  when there is nothing to toggle, reports `aria-expanded` and `aria-controls`. Any element with
  `data-dcl-toggle` and `data-dcl-layout="<id>"` toggles a layout from outside it (django-mvp's
  dock does).
- Breakpoints are measured against the layout's own width with container queries, never the
  window's.
- A drawer is a modal dialog: focus moves in and returns to the toggle, Escape closes the top
  drawer only (not a dialog around it), the rest of its layout is inert, the page behind a
  page-mode drawer doesn't scroll, the backdrop and following a link close it.
- Script API: `DaisyCottonLayout.mount/sync/state/toggle/open/close`, and a `dcl:change` event.

Screens: http://devserver:8002/layout/code/ and http://devserver:8002/layout/nested/

### 2. The shell on the layout (django-mvp, feature)

A project sets `MVP_CONFIG["layout"]["view"]` and configures both sidebars. A page fills the right
sidebar through `{% block app.secondary_sidebar %}` and a page that doesn't has none.

- `MVP_CONFIG["layout"]["view"]`, default `"lHh LpR lff"`.
- `MVP_CONFIG["layout"]["sidebar"]`: `collapse`, `breakpoint`, `behavior`, `width`, plus the
  existing `title` and `boost`.
- `MVP_CONFIG["layout"]["secondary_sidebar"]`: `collapse`, `breakpoint`, `behavior`, `width`,
  `label`.
- The navbar's sidebar button shows only while the left sidebar is closed, the sidebar's own
  header carries the close button, and a right-sidebar button appears when a page has one.
- The dock's Menu item toggles the left sidebar.
- Full-height pages (`<c-mvp.page fill>`) fill the window inside the new grid.

Depends on 1. Screens: every page; http://devserver:8002/layout/code/ fills the right sidebar,
http://devserver:8002/layout/full-page/ is a filled page.

### 3. The demo pages (django-mvp demo, resolve)

The playground and the nested examples. No new way for a developer to work with the package beyond
features 1 and 2, so this is resolve work that comes with feature 2 or straight after it. In the
real build the playground's live preview belongs in the package's own docs or demo rather than in
django-mvp.

## Shared pieces

| Piece | Where it occurs | Becomes | Built by |
|---|---|---|---|
| The layout's markup | `daisy_cotton_layout/templates/cotton/layout/*.html` | The package's Cotton components | 1 |
| Reading the code | `daisy_cotton_layout/view.py` (`LayoutView.parse`) | The package's parser, used by the component and by django-mvp's settings check | 1 |
| Sidebar options and the cookie | `daisy_cotton_layout/templatetags/daisy_cotton_layout.py` (`layout_sidebar`) | A template tag in the package | 1 |
| Drawer rules per breakpoint | `daisy_cotton_layout/build_css.py` writes `static/daisy_cotton_layout/layout.css` | The package's stylesheet, generated at release | 1 |
| Behaviour | `daisy_cotton_layout/static/daisy_cotton_layout/layout.js` | The package's script | 1 |
| Rail-aware Tailwind variants | `mvp/tailwind/base.css`, `@custom-variant is-drawer-open/close` | Kept in django-mvp, keyed to `.dcl-sidebar[data-dcl-rail]` | 2 |
| Rail labels | `.dcl-rail-hide` / `.dcl-rail-only` in layout.css, `mvp-sidebar--icons` in django-mvp | One mechanism. The package's classes, with django-mvp's menu using them | 1, reused by 2 |
| A layout in a card | `demo/layouts/templates/layouts/nested.html` (inbox, project, filters) and `_preview_layout.html` | Docs examples. No component: a card holding a layout is two lines | 3 |

## Duplication to remove

- `describe()` in `demo/layouts/views.py` and `LayoutView.explain()` both put a layout into
  sentences. One function in the package.
- The breakpoint widths are written in `build_css.py` (`BREAKPOINTS`), `demo/layouts/views.py`
  (`BREAKPOINT_WIDTHS`, `BREAKPOINTS`) and the template tag. One table in the package.
- `mvp/tailwind/base.css` still has the old `.drawer[data-mvp-breakpoint…]` rules for
  `mvp-sidebar-hidden-only` and `mvp-sidebar-toggle`. They match nothing now and go.

## The look

| File | Ported by | Lands in |
|---|---|---|
| `daisy_cotton_layout/templates/cotton/layout/index.html, header.html, page.html, footer.html, sidebar.html, toggle.html` | 1 | The package |
| `daisy_cotton_layout/static/daisy_cotton_layout/layout.css` (and `build_css.py`) | 1 | The package |
| `daisy_cotton_layout/static/daisy_cotton_layout/layout.js` | 1 | The package |
| `mvp/templates/mvp/base.html` (the `app` block) | 2 | Same path |
| `mvp/templates/cotton/app/header.html, navbar.html, sidebar/header.html, sidebar/index.html` | 2 | Same paths |
| `mvp/templates/menus/dock/item.html` | 2 | Same path |
| `mvp/tailwind/base.css` (variants, rail selectors, full-page rules) | 2 | Same path |
| `mvp/config.py` (`layout.view`, `sidebar`, `secondary_sidebar`) | 2 | Same path |
| `demo/layouts/` (views, templates) | 3 | The package's demo, or django-mvp's demo |

Screens for the parity check, each at 390 and 1440 wide, signed out and as `regular.user`:

- http://devserver:8002/layout/code/ with the sidebars open, then closed (the left closes to its
  rail in the preview)
- http://devserver:8002/layout/code/?view=hHh+LpR+fFf
- http://devserver:8002/layout/nested/, with the settings dialog open and the filters drawer open
- http://devserver:8002/products/ (no right sidebar)
- http://devserver:8002/layout/full-page/

No seeded data beyond `seed_accounts`.

## The data model

None. The only state is the sidebar cookie, `dcl-<persist>=open|closed`.

## Decisions

- 2026-11-24: The layout becomes a standalone package, not part of django-mvp. (Sam)
- 2026-11-24: Breaking existing projects is not a concern. (Sam)
- 2026-11-24: Both sidebars can open and close; the layout nests inside itself. (Sam)

## Decided on my own

- **Package name `daisy-cotton-layout`**, module `daisy_cotton_layout`, components under
  `c-layout`. It depends on Django and django-cotton only; daisyUI's theme variables come from the
  host.
- **The shell's default code is `lHh LpR lff`**: the left sidebar runs the full height beside the
  header and footer, as the current shell does, and the header and both sidebars stay in place.
- **Sidebar options are shadcn/ui's** (`offcanvas`, `icons`, `none`) and **Quasar's** (`behavior`,
  `breakpoint`). `behavior="overlay"` replaces django-mvp's old `breakpoint: "never"`, and
  `docked` keeps a sidebar beside the page at every width.
- **Default breakpoints**: left `lg`, right `xl`, measured against the layout's width.
- **The remembered state is a cookie, not localStorage**, so the server draws it and nothing snaps.
- **An empty area takes no space**: a sidebar renders nothing without content, and the grid's
  `auto` columns collapse.
- **The right sidebar is a block, `app.secondary_sidebar`**, replacing `page.side`.
- **Escape closes only the topmost drawer**, so a drawer inside a dialog closes before the dialog.
- **The dock stays outside the layout**, fixed at the bottom, and names the layout it toggles.

## Faked or skipped

- **No tests.** The package needs browser tests (toggles, drawers, focus, cookies, nesting,
  container queries) in its own repository. Feature 1.
- **Focus is not trapped** in a contained drawer: Tab can leave the drawer for content outside the
  layout. Only the layout's own areas are made inert. Feature 1.
- **Right-to-left** is wired through `--dcl-dir` but never tried. Feature 1.
- **The stylesheet is generated by a script** in the package and committed. The release needs a
  check that the committed file matches. Feature 1.
- **No docs.** The package's docs and django-mvp's `layout.md` and `configuration.md` are
  rewritten. Features 1 and 2.
- **Width transitions** on docked sidebars animate `width`, which reflows the page each frame. Fine
  in the demo, worth measuring on a heavy page. Feature 1.
- **The navbar's `sticky` setting** is still in `mvp/config.py` but no longer read: the code's
  upper-case `H` does it. Feature 2 removes it.
- **Icons** in the demo come from the Bootstrap Icons CDN like the rest of the demo.

## What it replaces

- `mvp/layout.py` (`LayoutConfig`) and the breakpoint, collapse and sticky settings it resolves.
- `mvp/templates/cotton/app/index.html` and `mvp/templates/cotton/mvp/layout/sidebar/index.html`:
  the daisyUI drawer the shell was built on.
- The Alpine `$store.mvp` layout store and the `mvp-app-drawer-open` localStorage key
  (`assets/js/layout.js`, `assets/js/index.js`), and the `mvp-app-toggle` checkbox the dock item
  pointed at (`mvp/menus.py`).
- `page.side` and `<c-mvp.page.side>`, replaced by `app.secondary_sidebar`, and their print and
  column rules in `mvp/tailwind/base.css`.
- `MVP_CONFIG["layout"]["navbar"]["sticky"]`.
- The demo pages `/layout/sidebar/`, `/layout/store/` and `/layout/side/`, which demonstrate the
  old settings.

Nothing is stored, so nothing needs migrating. A project that set the old sidebar settings or
filled `page.side` changes its settings and templates.
