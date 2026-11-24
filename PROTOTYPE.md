# Prototype: the shell, cards and dialogs on django-mvp-layout

Issue: https://github.com/django-mvp/django-mvp/issues/719

django-mvp depends on django-mvp-layout (module `mvp_layout`), and three things are drawn with it:

- the application shell, arranged by one code in `MVP_CONFIG["layout"]["view"]`
- `<c-mvp.card>`, which takes sidebars and its own code
- `<c-mvp.modal>`, which takes sidebars and its own code

A card or dialog with no sidebar and no code is drawn exactly as before.

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
- The dock's Menu item is a button with `data-mvpl-toggle="left" data-mvpl-layout="mvp-app"`.
- Full-height pages (`<c-mvp.page fill>`) fill the window inside the layout's grid.

Screens: every page. http://devserver:8002/layout/code/ fills the right sidebar,
http://devserver:8002/products/ has none, http://devserver:8002/layout/full-page/ is a filled page.

### 2. A card with a layout (feature)

A developer sets `view` on a card and places django-mvp-layout's own `<c-layout.sidebar>` and
`<c-layout.page>` inside it, exactly as in the shell. Every sidebar option the package has is
available, measured against the card's own width.

- `view` turns layout mode on. It has no default: a card without it is drawn as before.
- `height` is optional. Unset, the card is as tall as its content (django-mvp-layout 0.1.1). Set,
  the body scrolls inside it.
- The title row (title, icon, badges, actions) is the layout's header, with a `<c-layout.toggle>`
  for each side that hides itself when that sidebar is absent or never closes. The footer slots are
  the layout's footer.
- `href`, `tight` and `body_class` are not used with a view: pad the `<c-layout.page>` instead.

Depends on 1 only for the shared box styles. Screens:
http://devserver:8002/components/card/#sidebars, #icon-rail, #another-layout-code,
#a-drawer-at-every-width, #in-a-narrow-card.

### 3. A dialog with a layout (feature)

The same for `<c-mvp.modal>`: sections in a sidebar, a details pane, options in a drawer.

- `view` turns layout mode on. The children are `<c-layout.sidebar>` and `<c-layout.page>`.
- The box stays daisyUI's `.modal-box`, capped at the screen's height, as a flex column. The
  layout grows with its content up to that cap, then scrolls inside it with the heading and
  actions rows in view.
- The heading row carries the toggles, the actions slot and the close button. The actions row is
  the footer.
- Escape closes an open drawer before the dialog (the layout package's script).

Depends on 2 for the shared component (see below). Screens:
http://devserver:8002/components/modal/#sections-in-a-sidebar, #two-sidebars,
#options-in-a-drawer.

### 4. Demo pages (resolve)

The Layout code page (`/layout/code/`: the current code, a diagram of it, a form to try another,
five presets, a table of the letters, the right sidebar filled) and the new card and modal
examples. Nobody gets a new way of working from them, so this is resolve work that comes with
features 1 to 3.

## Shared pieces

| Piece | Where it occurs | Becomes | Built by |
|---|---|---|---|
| A box with a layout: header row with a toggle each side, the caller's sidebars and page, footer row | `mvp/templates/cotton/mvp/card/index.html` (the `{% if view %}` branch), `mvp/templates/cotton/mvp/modal.html` (the same) | One Cotton component, e.g. `<c-mvp.box.layout>`, that both the card and the dialog call | 2, reused by 3 |
| Box colours (`--mvpl-sidebar-bg`, `--mvpl-line`, `.mvp-box-header`, `.mvp-box-footer`) | `mvp/tailwind/base.css`, end of file | Kept, keyed to the shared component's class instead of `:is(.mvp-card-layout, .mvp-modal-layout)` | 2 |
| Rail-aware variants `is-drawer-open` / `is-drawer-close` | `mvp/tailwind/base.css` (`@custom-variant`) | Kept, keyed to `.mvpl-sidebar[data-mvpl-rail]` | 1 |
| Rail labels | `mvp-sidebar--icons` rules in `mvp/tailwind/base.css` and the package's `.mvpl-rail-hide` / `.mvpl-rail-only` | One mechanism: the package's classes, used by django-mvp's menu | 1 |
| Parsing the code | `demo/views.py` (`LayoutCodeView`) and the package's `LayoutView.parse` | The package's parser, also called by a django-mvp system check on `layout.view` | 1 |

## Duplication to remove

- The card and the dialog each carry the same header-and-footer layout markup. One component.
- `mvp/tailwind/base.css` still holds the `.drawer[data-mvp-breakpoint…]` rules for
  `mvp-sidebar-hidden-only` and `mvp-sidebar-toggle`. They match nothing now.
- `mvp/layout.py` (`LayoutConfig`) resolves breakpoint, collapse and sticky for a shell that no
  longer exists.

## The look

| File | Ported by | Lands in |
|---|---|---|
| `mvp/templates/mvp/base.html` (the `app` block) | 1 | Same path |
| `mvp/templates/cotton/app/header.html, navbar.html, sidebar/header.html, sidebar/index.html` | 1 | Same paths |
| `mvp/templates/menus/dock/item.html` | 1 | Same path |
| `mvp/config.py` (`layout.view`, `sidebar`, `secondary_sidebar`) | 1 | Same path |
| `mvp/tailwind/base.css` (variants, rail, full-page rules, box colours) | 1, 2 | Same path |
| `mvp/templates/cotton/mvp/card/index.html` | 2 | The shared component plus the card |
| `mvp/templates/cotton/mvp/modal.html` | 3 | The shared component plus the modal |
| `demo/templates/demo/layout/code.html`, `demo/views.py` (`LayoutCodeView`), `demo/urls.py`, `demo/menus.py` | 4 | Same paths |
| `demo/templates/demo/components/card.html`, `modal.html` (new sections at the end) | 4 | Same paths |

Screens for the parity check, each at 390 and 1440 wide, signed out and as `regular.user`:

- http://devserver:8002/layout/code/, with each sidebar open and closed
- http://devserver:8002/layout/code/?view=hHh+LpR+fFf
- http://devserver:8002/products/ (no right sidebar)
- http://devserver:8002/layout/full-page/
- http://devserver:8002/components/card/ (the five new sections, each sidebar opened and closed)
- http://devserver:8002/components/modal/ (each new dialog open, and on the phone the sections
  drawer open)

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

## Decided on my own

- **The shell's default code is `lHh LpR lff`**, as the current shell looks: the left sidebar runs
  the full height, the header and both sidebars stay in place.
- **The right sidebar is a block, `app.secondary_sidebar`**, drawn only when filled. Beside the
  page from `xl`, a drawer below.
- **The toggles in a box's title row take the package's default names**, "Left sidebar" and "Right
  sidebar", not the sidebar's own label.
- **`href`, `tight` and `body_class` are ignored on a card with a view.**
- **`behavior: "overlay"` replaces `breakpoint: "never"`.**
- **`page.side` stays as it is.** Whether `app.secondary_sidebar` replaces it is for the rebuild.

## Faked or skipped

- **No tests.** Features 1 to 3.
- **No docs.** `layout.md`, `configuration.md` and `components.md` are rewritten. Features 1 to 3.
- **A wrong `layout.view` fails at render**, not at startup. Feature 1 adds a system check.
- **The old shell is still in the tree**: `mvp/layout.py`, `cotton/app/index.html`,
  `cotton/mvp/layout/sidebar/index.html`, the Alpine `$store.mvp` layout store
  (`assets/js/layout.js`), and the demo pages `/layout/sidebar/` and `/layout/store/` that show it.
  Feature 1 removes them.
- **`MVP_CONFIG["layout"]["navbar"]["sticky"]` is no longer read.** Feature 1 removes it.
- **The card and dialog duplicate the layout markup.** Feature 2 makes the shared component.
- **A drawer with `behavior="overlay"` on a fixed side stops short of the box's bottom** by the
  header's height. A django-mvp-layout defect, being fixed as 0.1.2; the prototype upgrades when
  it is out.
- **A toggle's name doesn't follow its sidebar's label.** The package's script could copy it
  across. Feature 1 of django-mvp-layout's own roadmap, not django-mvp's.
- **`assets/tailwind.css` scans the demo's component and layout templates** so their example
  classes build. Feature 4 moves this to the demo.
- **Icons come from the Bootstrap Icons CDN**, like the rest of the demo.

## What it replaces

- The daisyUI drawer the shell was built on, the `mvp-app-toggle` checkbox and the Alpine layout
  store with its localStorage key.
- `mvp/layout.py` and the sticky navbar setting.
- `breakpoint: "never"` on the sidebar.

Nothing is stored, so nothing needs migrating. A project that set the old sidebar settings changes
its settings.
