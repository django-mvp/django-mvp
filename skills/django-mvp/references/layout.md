# Layout — reference

The app shell, the two layers of template blocks it exposes, and how to change a
region for one page.

## The shell

Extending the base template gets you the whole shell, already composed:

```
{% block announcement %}   empty, outside the shell, scrolls with the page
<c-app>                    the sidebar/header/content frame
├── <c-app.sidebar>        brand header, the AppMenu, configured footer widgets
├── <c-app.header>         header region: navbar, plus above/tray/below slots
│                          navbar: sidebar toggle, site icon, breadcrumbs, actions
│                          toggle and icon hide where the sidebar header shows them
├── <c-app.main>           your page content, then the message toasts
├── <c-app.footer>
└── <c-app.dock>           mobile bottom navigation (MobileFooterMenu)
```

**A page never re-composes `<c-app>`.** Writing the shell by hand in your own base
template is the old API and will drift from the package. Extend and override a
block instead.

The template chain matters when you decide where to put an override:

| Template | Extends | Role |
|---|---|---|
| `mvp/base.html` | — | The shell. Owns every `app.*` block. |
| `base.html` (packaged) | `mvp/base.html` | A forwarder that defines nothing. Write your own `templates/base.html` and it replaces this file entirely. |
| `page_view.html` | `base.html` | Standard page chrome. Owns every `page.*` block. |
| `list_view.html`, `detail_view.html`, `form_view.html`, `mvp/dashboard.html`, `mvp/landing.html`, `mvp/placeholder_view.html` | `page_view.html` | Fill some of those blocks |
| `table_view.html` | `list_view.html` | Re-declares the `page.*` blocks in its own markup |
| `delete_view.html` | `form_view.html` | Fills the form blocks |
| `mvp/entrance.html`, `mvp/error_base.html` | `mvp/base.html` | Replace the shell with a centred card |
| `mvp/account/base.html` | `base.html` | The [Account Center](../../../docs/account-center.md)'s layout. Owns `account.content`, and draws `AccountCenterMenu` beside it. |
| `mvp/account/overview.html` | `mvp/account/base.html` | The area's landing page. Fills `account.content`. |

Mounting `mvp.urls` gives the area an address, not a link: the sidebar footer ships empty.
`"actions.login"` and `"user.sidebar-menu"` in `MVP_CONFIG["layout"]["sidebar"]["footer"]`
are the complementary pair — the first renders for a visitor, the second for a signed-in
person and carries the Account Center row.

An installed app puts a card on the landing page by shipping its own copy of
`mvp/account/overview.html`, extending the same name, and adding to its
`{% block account.cards %}` through `{{ block.super }}` — no page or menu entry required.
Django resolves the same-name `{% extends %}` to the next template of that name in the
loader path, so several apps chain this way; list a contributing app before `mvp` in
`INSTALLED_APPS` or its override is never reached. A card renders as part of the same
template as the rest of the page — the page's context, not one of its own. See [Contributing
a card](../../../docs/account-center.md#contributing-a-card) for the full worked example.

Because the view templates extend the unqualified name `base.html`, a
`templates/base.html` of your own is picked up automatically by every MVP view.
That is the file to put project-wide `app.*` overrides in.

## Layer 1 — shell blocks, from `mvp/base.html`

| Block | The region it wraps |
|---|---|
| `head` | The entire document head: metadata, the title element, favicon links, the icon font, the `styles` block, the bundled front-end runtime, the theme-conditional style rules. Use `{{ block.super }}` to add rather than replace. |
| `title` | The text inside the title element. The site name is appended after it automatically. |
| `styles` | The packaged stylesheet link. Sits inside `head`. |
| `announcement` | Empty by default. Sits *outside* the shell, before the sidebar/header/content frame, in normal document flow — so it scrolls away while a pinned header keeps pinning. |
| `app` | The whole shell, from the opening frame to the dock. |
| `app.sidebar` | The sidebar component, inside the shell's sidebar slot. |
| `app.header` | The header component and its slot wiring. |
| `app.header.widgets` | Fills the header's `right` slot. Renders at the trailing edge of the navbar, *before* the widgets configured in settings, and shares their visibility: the whole trailing region is hidden below the sidebar breakpoint. |
| `app.header.tray` | Fills the header's `tray` slot — a full-width row under the navbar, still inside the header region. Empty by default. |
| `app.main` | The main region wrapper, including the message toasts inside it. |
| `content` | Page content inside the main region, above the toasts. |
| `app.footer` | The footer component. |
| `extra_js` | End of the document body, after the shell. |

## Layer 2 — `page.*` blocks, and why they are the ones you want

**If your page is backed by an MVP view, `{% block content %}` is already spent.**
`page_view.html` fills it with the page chrome — the container, the title bar, the
content region, the footer toolbar. Overriding
`content` in a template that extends an MVP view template throws all of that away
and leaves you with a bare region inside the shell.

Override a `page.*` block instead.

| Block | Declared in | Region |
|---|---|---|
| `page.header` | `page_view.html` | Above the title. Empty by default — the breadcrumb trail moved to the app header |
| `page.content-wrapper` | `page_view.html` | The content region, title bar included |
| `page.title` | `page_view.html` | The title bar: heading, subtitle and actions |
| `page.actions` | `page_view.html` | The action buttons in the title bar |
| `page.content` | `page_view.html` | **The page body. This is the usual override.** |
| `page.footer` | `page_view.html` | The toolbar below the content |
| `page.hero` | `mvp/landing.html` | A full-width band above the content region |
| `entrance` | `mvp/entrance.html` | The centred card itself, restated when you want a different width |
| `before_form` | `form_view.html` | Above the form, inside `page.content` |
| `formset` | `form_view.html` | The formset rows inside the form |
| `actions` | `form_view.html` | The form's submit and delete buttons |
| `after_form` | `form_view.html` | Below the form, inside `page.content` |

What the shipped views already put in these:

- `list_view.html` fills `page.content` with the result count, the list and the
  pagination, and `page.actions` with search, sort, filter and create.
- `detail_view.html` fills `page.actions` with edit and delete links and leaves
  `page.content` deliberately empty — that empty block is where your
  `<app>/<model>_detail.html` goes.
- `form_view.html` fills `page.content` with the form, and extends `head` and
  `extra_js` with the form's own media.
- `mvp/landing.html` overrides `content` wholesale, so it has `page.hero`,
  `page.content-wrapper`, `page.content` and `page.footer` but **not**
  `page.header`, `page.title` or `page.actions`.
- `mvp/error_base.html` replaces the `app` block with a centred card and exposes
  `error_code`, `heading`, `description` and `actions` instead of any `page.*`
  block.

## Table pages are laid out differently

`table_view.html` also overrides `content` wholesale rather than reusing
`page_view.html`'s markup, because the intermediate container breaks the chain the
full-height layout depends on. All six `page.*` names are re-declared, so an
override you wrote still applies. It lands in a different position, though, and
the defaults around it are different:

- `page.header` is empty, as it is on every other page. The heading is a plain
  `<h1>` in the title bar; the breadcrumb trail is drawn by the app header.
- `page.actions` does not call `{{ block.super }}`, and its default action set
  deliberately excludes sort.
- `page.footer` holds the row count and pagination, in a bar pinned below the rows.
- `app.footer` is blanked to an empty block. The shell footer does not render on a
  table page. Restore it in your own template if you want it back.

## The breadcrumb trail

The trail is drawn by the navbar, at the leading edge of the header row, beside the
site icon. It reads `page.breadcrumbs` straight out of the context an MVP view
already puts there, so a view declares its trail through `breadcrumbs` or
`get_breadcrumbs()` exactly as before and nothing is plumbed through the shell.

- A page that declares no trail renders no `<nav>` at all, not an empty one.
- No page template draws a trail of its own. `page.header` is empty everywhere.
- To move it, override `app.header` and place `<c-breadcrumbs :items="page.breadcrumbs" />`
  where you want it.
- A long trail shrinks rather than scrolling: each crumb ellipsises its own text
  before the next one gives up any width, so the whole path stays visible. Horizontal
  scrolling only takes over at a width where every crumb is already truncated and the
  trail still does not fit.

## What no block can suppress

Two things inside the shell have no enclosing block of their own:

- **The message toasts.** They are emitted inside `<c-app.main>`, after `content`.
  The nearest block is `app.main`, so removing or relocating them means overriding
  `app.main` and restating the main region and `{% block content %}` yourself.
- **The mobile dock.** It is emitted as the last child of `<c-app>`, outside every
  block. Suppressing it means overriding the whole `app` block.

Everything else in the shell is reachable through the layer-1 table above.

## Header slots versus header blocks

`<c-app.header>` has four slots and the base template only wires up two of them:

| Slot | Position | Reached by |
|---|---|---|
| `above` | Above the navbar, inside the header region | Restating `<c-app.header>` in the `app.header` block |
| `right` | Trailing edge of the navbar, before the configured widgets | `{% block app.header.widgets %}` |
| `tray` | Below the navbar, full width, inside the header region | `{% block app.header.tray %}` |
| `below` | Below the tray, same region | Restating `<c-app.header>` in the `app.header` block |

So `app.header.tray` feeds the `tray` slot specifically, not `below`. The two
render in the same region and differ only in order. To use `above` or `below`,
override `app.header` and write the component out with the slots you want, keeping
the `breakpoint` and `collapse` attributes described next.

## Changing `breakpoint` or `collapse` for one page

These two settings drive three regions that must agree: the sidebar drawer, the
collapsed sidebar rail, and the navbar's sidebar toggle. The base template resolves
both **once**, at the top of the `app` block, taking a context variable of the same
name if one is present and otherwise the configured value. It then threads the
result into all three.

Override for one page by putting those variables in scope around
`{{ block.super }}`:

```django
{# templates/reports/wide.html #}
{% extends "base.html" %}
{% block app %}
  {% with breakpoint="xl" collapse="icons" %}{{ block.super }}{% endwith %}
{% endblock %}
```

Either may be set alone and the other keeps its configured value. The same
variables can come from the view context instead, for example
`context["breakpoint"] = "xl"`.

Setting them on `<c-app>` works: it renders the resolved values onto the shell's
drawer element, and the navbar toggle takes its visibility from a stylesheet rule
that selects on them. Setting them on `<c-app.sidebar>` reaches only that component.
Resolving them in the `app` block or the view context is still the clearest form,
because it is the one place every region reads.

`sticky` is the header's own attribute. Use the dynamic form so it stays a real
boolean. Overriding `app.header` replaces the whole block, so restate the `right` and
`tray` slots that carry `app.header.widgets` and `app.header.tray`:

```django
{% block app.header %}
  <c-app.header :sticky="False">
    <c-slot name="right">
      {% block app.header.widgets %}{% endblock app.header.widgets %}
    </c-slot>
    <c-slot name="tray">
      {% block app.header.tray %}{% endblock app.header.tray %}
    </c-slot>
  </c-app.header>
{% endblock app.header %}
```

The one-line form `<c-app.header :sticky="False" />` drops both slots, so anything a
page put in `app.header.widgets` or `app.header.tray` stops being reachable.

## Responsive visibility classes

The drawer element (`<c-app>`'s root, wrapping sidebar + header + content) carries
`data-mvp-breakpoint` (`sm`/`md`/`lg`/`xl`/`2xl`/`never`, already normalised) and
`data-mvp-collapse` (`offcanvas`/`icons`). `mvp/tailwind/base.css` selects on both;
three classes are available for a descendant to reuse the pattern:

- `mvp-desktop-only` — shown at/above the breakpoint, hidden below it (and never under
  `never`, which has no width to key off).
- `mvp-mobile-only` — the inverse, and always hidden under `never` so it never
  doubles up with `mvp-desktop-only`'s unconditionally-shown copy.
- `mvp-sidebar-hidden-only` — shown only while the sidebar is not on screen. Hidden from
  the breakpoint up: always in `icons` mode, since the rail is always there, and in
  `offcanvas` mode only while the drawer is open. Put it on a duplicate of something the
  sidebar header already draws, and it stands down whenever the original is visible. The
  packaged navbar uses it for the brand icon and the sidebar toggle, both of which the
  sidebar header carries too.

"Desktop" and "mobile" mean what they mean everywhere in this package: mobile is where the
sidebar is an off-canvas overlay, desktop is where it sits in the page's flow. The
configured breakpoint is the line between them.

`mvp-desktop-only` and `mvp-mobile-only` set `display: flex` when shown, and the package's rules sit outside Tailwind's utility layer, so they beat a display utility whatever its specificity. Wrap them rather than combining them with one.

The navbar's widget lists, the account layout's collapsed/persistent navigation, and
the navbar's own sidebar-toggle/site-icon are all built from these three classes —
no template tag needed.

## Full-page content: `fill` on `<c-page>`

New in `[Unreleased]`. By default a page grows as tall as its content and the
window scrolls. Marking the page `fill` makes it take exactly the height the shell
has left instead, so the window stops scrolling and your content scrolls
internally:

```django
{# templates/fleet/map.html — fill is an attribute on <c-page>, so this is #}
{# one of the few cases where overriding `content` is the right move #}
{% block content %}
  <c-page fill>
    <c-page.content>
      <div id="map" class="h-full w-full"></div>
    </c-page.content>
  </c-page>
{% endblock %}
```

There is no setting for it and nothing to configure above the page. The mark on the
page is what the shell keys off, because the page renders long after the shell
around it. `page_view.html` renders `<c-page>` without the mark, so filling
`page.content` alone will not give you a full-height page. You have to state the
page element yourself, and the standard chrome goes with it.

- The content region gets a viewport height as a ceiling as well as a floor. Content
  taller than the viewport scrolls inside the region rather than pushing the shell
  past it and handing the scrollbar back to the window.
- **The mobile dock joins the flow** instead of floating fixed over the bottom of
  the viewport. On a page that does not scroll, a fixed dock would permanently cover
  the last strip of content with no way to reach it.

Reach for `fill` when the content owns its own scrolling: a full-bleed map, a
canvas or charting widget that needs a real container height, an embedded editor.
The packaged table views already do this for you. The rule is scoped, so pages
without the mark are untouched.

## Sidebar open state

At and above the sidebar breakpoint, open and collapsed state persists across page
loads in `localStorage` under the key `mvp-app-drawer-open` (the shell element's id
plus `-drawer-open`). A first visit defaults to open. The stored value is also read
by a small blocking script during parse, before first paint, so a sidebar restored
to collapsed does not animate shut after the page appears.

Below the breakpoint the sidebar is a transient overlay. It always starts closed,
and toggling it never writes back, so opening the mobile drawer cannot clobber the
saved desktop state. With `breakpoint` set to `never` or `none` the sidebar is an
overlay at every width and nothing is persisted at all.

## Layout store

Every shell page registers `Alpine.store("mvp", ...)`, read from any element as `$store.mvp`.
The drawer's checkbox stays the source of truth for whether the sidebar is open — the store
mirrors it, not the reverse — and a shell-less page still gets one, reporting defaults rather
than throwing. Its shape, with representative values:

```json
{
  "sidebar": {
    "open": true,
    "desktopOpen": true,
    "breakpoint": "lg",
    "breakpointPx": 1024,
    "persistent": true,
    "collapse": "offcanvas",
    "boost": false
  },
  "header": {
    "stuck": false,
    "sticky": true
  },
  "isWide": true
}
```

- `sidebar.open` — whether the sidebar is open right now: overlay below the breakpoint, persistent panel at/above it.
- `sidebar.desktopOpen` — the remembered desktop-width open state, persisted to `localStorage`.
- `sidebar.breakpoint` — the resolved sidebar breakpoint for this page: `sm`, `md`, `lg`, `xl`, `2xl`, or `never`.
- `sidebar.breakpointPx` — the breakpoint's pixel width, or `null` when `never` — there is no width to report.
- `sidebar.persistent` — whether the sidebar ever becomes a persistent panel at some width. `false` only when `breakpoint` is `never`.
- `sidebar.collapse` — `"offcanvas"` or `"icons"`.
- `sidebar.boost` — whether sidebar links use `hx-boost`.
- `header.stuck` — whether the sticky header has scrolled off its resting position.
- `header.sticky` — whether the header pins to the top of the viewport, from `MVP_CONFIG["layout"]["navbar"]["sticky"]`.
- `isWide` — whether the viewport is at/above `sidebar.breakpointPx`, via a `matchMedia` listener. Permanently `false` when `sidebar.breakpoint` is `never`. Stands at the top level, not under `sidebar`, because it reports the viewport rather than the sidebar itself.

Grouped by component rather than flattened, dropping the earlier `config` tier: whether a value
came from settings or from a click is not what a consumer of the store is asking — see
`specs/029-layout-state-store/decisions.md` D14. Full reference and a worked example:
[docs/layout.md#the-layout-store](../../../docs/layout.md#the-layout-store); the demo runs it at
`/layout/store/`, and accepts `?breakpoint=` for exercising a per-page override or the `never` case.

---

Back to [SKILL.md](../SKILL.md).
