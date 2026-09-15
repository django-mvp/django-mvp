# Layout

django-mvp renders a complete application shell around your content:

```
{% block announcement %}      empty by default, outside the shell (scrolls away)
<c-app>                        DaisyUI drawer (sidebar + content)
├── <c-app.sidebar>            brand header, AppMenu, fixed footer
├── <c-app.header>             sticky header
│   └── <c-app.header.navbar>  sidebar toggle, site icon, breadcrumbs, widgets
├── <c-app.main>               your {% block content %} + flash messages
├── <c-app.footer>
└── <c-app.dock>               mobile bottom navigation
```

Everything is configured from `settings.MVP_CONFIG` — similar in spirit to
pydata-sphinx-theme's layout options. Its `layout` section is what this page covers,
and the package defaults are:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm | md | lg | xl | 2xl
            "collapse": "offcanvas",  # "offcanvas" | "icons"
            "title": None,            # text beside the brand icon (falsey = none)
            "boost": False,           # navigate sidebar links with htmx
        },
        "navbar": {
            "mobile": {"end": []},    # widgets below the sidebar breakpoint
            "desktop": {"end": ["actions.theme-controller", "actions.login"]},
            "sticky": True,           # True: pinned | False: scrolls away
        },
    },
}
```

`layout` is one of five top-level sections. `theme` is covered in
[Theming](theming.md), `table` in [Styling](styling.md) and `view_names` in
[Views](views.md). The fifth, `brand`, holds three dotted paths —
`avatar_resolver`, `logo_resolver` and `icon_resolver` — that the brand and avatar
components call to find their images. Their defaults serve `brand/logo.svg` and
`brand/icon.svg` from your static files, preferring a `_dark` sibling under a dark
theme where one exists, and resolve no avatar at all until you point
`avatar_resolver` at your own function.

Configuration resolves in this order everywhere:
**component attribute (per-page) → `MVP_CONFIG` (project) → package default.**

## Sidebar breakpoint

`layout.sidebar.breakpoint` sets the viewport width at which the sidebar becomes a
persistent panel. Below the breakpoint it is a mobile overlay drawer (opened by the
navbar hamburger or the dock, closed by tapping the overlay).

| Value | Persistent from |
| --- | --- |
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px (default) |
| `xl` | 1280px |
| `2xl` | 1536px |

Per-page override — see [Overriding the layout per page](#overriding-the-layout-per-page).

## Sidebar collapse mode

At or above the breakpoint, the navbar toggle collapses the sidebar.
`layout.sidebar.collapse` picks the behavior:

- **`"offcanvas"`** (default) — the sidebar slides fully away and content takes the
  full width.
- **`"icons"`** — the sidebar collapses to a 4rem icon rail: menu labels, badges and
  section titles hide, icons center, and hovering an item shows its label as a tooltip.
  The brand logo swaps for the brand icon.

In your own sidebar content, control rail visibility with two utility classes:

- `.mvp-rail-hide` — hidden while the rail is collapsed
- `.mvp-rail-only` — shown *only* while the rail is collapsed

Per-page override — see [Overriding the layout per page](#overriding-the-layout-per-page).

The open/closed state persists across page loads (localStorage, key
`mvp-app-drawer-open`). On first visit it defaults to open at/above the breakpoint and
closed below it.

## Sidebar title

`layout.sidebar.title` renders a short text label beside the brand icon in the sidebar
header. Falsey (the default `None`) renders no title. In the `"icons"` collapse mode the
title hides along with the rail's other labels, leaving just the icon.

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "title": "Acme Admin",
        },
    },
}
```

Per-page override:

```html
{% block app.sidebar %}
  <c-app.sidebar title="Acme Admin" />
{% endblock %}
```

## Sidebar footer

The sidebar footer is a fixed composition, not a configured widget list: it always
renders the signed-in user's menu (or a log-in button for a visitor), a theme control
and a language control, in a single row that fills the sidebar's width.

To change what the footer shows, override the component template in your project:

```html
{# templates/cotton/app/sidebar/footer.html #}
<div class="bg-base-200 w-full sticky bottom-0 mt-auto z-20 flex items-center gap-2 px-4 py-2">
  <c-user.sidebar-menu />
  <c-actions.login />
  <c-actions.theme-controller valign="top" />
  <myapp.support-link />
</div>
```

`<c-user.sidebar-menu>` and `<c-actions.login>` each guard on
`request.user.is_authenticated` internally, so drop both in unguarded — exactly one
renders per request. See [docs/adr/0023](adr/0023-the-sidebar-footer-is-a-fixed-composition.md)
for why this moved from a setting to a template override.

## Boosted sidebar navigation

`layout.sidebar.boost` adds htmx's `hx-boost` to the sidebar. Clicking a menu item then
fetches the next page and swaps it into the document you are already on, instead of
loading a new one. Pages stop flashing white between clicks and the back button still
works, because htmx updates the URL as it goes. htmx already ships with the package, so
the attribute is the whole change.

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "boost": True,
        },
    },
}
```

It is off by default, because a swapped page is not quite a loaded one:

- Scripts in `{% block extra_js %}` do not re-run, and anything that binds listeners
  once at startup finds its elements gone. The controls django-mvp ships deal with this
  themselves. Your own, and any third-party widget, may not.
- `<head>` is not swapped, so a stylesheet or meta tag a page adds in `{% block head %}`
  never arrives when that page is reached by a boosted link.
- Only sidebar links are boosted. Links elsewhere on the page, and form submissions,
  navigate normally. To boost the rest of the app, put `hx-boost` on your own `<body>`
  in your base template.

Below the sidebar breakpoint, a boosted link closes the mobile drawer on its way out,
so the sidebar never sits over the page it just opened. At desktop widths the sidebar
is persistent and stays exactly as you left it.

Per-page override:

```html
{% block app.sidebar %}
  <c-app.sidebar boost />
{% endblock %}
```

## Breadcrumbs

The breadcrumb trail is drawn in the header, beside the site icon, at the leading
edge of the row. It reads the `breadcrumbs` list an [MVP view](views.md) puts in the
page context, so a view declares its trail the same way it always has:

```python
class ProductDetailView(MVPDetailView):
    model = Product

    def get_breadcrumbs(self):
        return [{"text": "Products", "href": "/products/"}, {"text": str(self.object)}]
```

A page that declares no trail — the entrance, the error pages, anything not built on
an MVP view — renders no navigation landmark at all, rather than an empty one for a
screen reader to announce. A long trail shrinks rather than pushing the widgets off
the row: each crumb gives up width and ellipsises its own text before the next one
does, so the whole path stays visible. Horizontal scrolling is the last resort, for a
width where even every crumb truncated still will not fit.

The site icon beside it stands down wherever the sidebar's own header is on screen
showing the same mark — at or above the breakpoint with the drawer open, or at any
width from the breakpoint up when `collapse` is `"icons"` and the rail keeps the icon.
So the brand appears once, and on a desktop page with the sidebar open the header's
leading edge is the trail alone. The sidebar toggle follows the same rule and always
has.

Putting the trail in the header rather than above the page body gives every page back
a row of vertical space, and puts "where am I" where a person already looks for it.
To draw a trail somewhere else instead, place `<c-breadcrumbs :items="page.breadcrumbs" />`
wherever you want it and override the `app.header` block with your own header.

## Navbar widgets

`layout.navbar.mobile.end` and `layout.navbar.desktop.end` are each a list of
**Cotton component names** rendered in order at the right end of the navbar via
`<c-component :is="...">`. They're configured separately because a widget can be
right for one screen size and noise on the other — a language switcher that's fine
in a spacious desktop bar may not be worth the tap target on a phone, and for a
third-party widget you often can't rely on it making that call itself:

`desktop.end` reaches the header from the [sidebar breakpoint](#sidebar-breakpoint)
up, `mobile.end` below it. **`mobile.end` ships empty.** Below the breakpoint the
header row is spent on the sidebar toggle, the site icon and the
[breadcrumb trail](#breadcrumbs), and a narrow header that keeps the trail readable
is worth more than one that keeps every control. A widget you list on `mobile.end`
is the deliberate exception that earns that width back — and a control your visitors
need on a phone belongs either there or in the [sidebar footer](#sidebar-footer),
whose theme and language controls the drawer already reaches at every width.

```python
MVP_CONFIG = {
    "layout": {
        "navbar": {
            "mobile": {
                "end": ["actions.theme-controller"],
            },
            "desktop": {
                "end": [
                    "actions.theme-controller",     # light/dark toggle
                    "actions.language-switcher",    # i18n language menu
                    "myapp.notifications-bell",     # your own component
                ],
            },
        },
    },
}
```

A name maps to a Cotton template: `"myapp.notifications-bell"` →
`templates/cotton/myapp/notifications_bell.html`. Any component in your project's
cotton directory works, so app-specific widgets need no configuration beyond the name.

**Backward compatibility:** a flat `layout.navbar.end` (the pre-split shape) still
works and applies the same list to both `mobile` and `desktop`:

```python
MVP_CONFIG = {
    "layout": {
        "navbar": {
            "end": ["actions.theme-controller"],  # applies to both mobile and desktop
        },
    },
}
```

**How it's rendered:** both lists render server-side, in two separate regions toggled
with Tailwind's responsive display utilities keyed off the sidebar breakpoint (at the
default `lg`, the mobile region is `flex lg:hidden` and the desktop region
`hidden lg:flex`) — a config-driven widget list can't be resolved from the request
alone, so there's no way to render only one without a live layout. The desktop region
also holds whatever you put in the [`app.header.widgets`](#template-blocks) block, so
your own header content gives way at the same width the configured widgets do. The
mobile region is not rendered at all while `mobile.end` is empty, since an empty flex
item still spends its parent's gap. With `breakpoint` set to `never` there is no width
to key off, so the desktop region is shown at every width and the mobile one at none.
The region hidden by `display:none` is dropped from the accessibility tree by every
evergreen browser, so screen-reader users only ever reach the visible one. The cost is
duplicate markup: any widget listed on both `mobile.end` and `desktop.end` renders
twice in the page (once per region). Most shipped widgets carry no DOM `id`, so this is
inert, but `actions.language-switcher-modal` does (its dialog `id`, default
`"languageModal"`) — list it on only one of `mobile.end`/`desktop.end`, or wrap it in
your own component that overrides the `id` (see
[Language switcher: dropdown or modal](#language-switcher-dropdown-or-modal)) before
placing it on both.

### Language switcher: dropdown or modal

Two i18n language pickers ship as widgets — use whichever fits the slot:

- **`actions.language-switcher`** — a compact dropdown menu. Best in the navbar, where
  it opens in place.
- **`actions.language-switcher-modal`** — a globe button that opens a centered modal with
  a responsive, tappable grid of languages (one column on phones, two from `sm` up), the
  active language highlighted. Better for touch and for narrow slots like the
  [sidebar footer](#sidebar-footer), where a dropdown would be cramped. It's the variant
  the sidebar footer ships with by default, for that reason.

Both post to Django's `set_language` view and preserve the current path, so they are
interchangeable. Placing either in the navbar is a `MVP_CONFIG` setting (above); placing
one in the sidebar footer instead of the packaged one means overriding
`templates/cotton/app/sidebar/footer.html` — see [Sidebar footer](#sidebar-footer).

If you place the modal switcher in more than one slot on the same page, give the extra
instances a distinct dialog id so they don't collide — this needs a wrapper component,
since `MVP_CONFIG` names take no attributes:

```html
{# templates/cotton/myapp/footer_language.html #}
<c-actions.language-switcher-modal id="footerLanguageModal" />
```

For one-off, page-specific widgets, the template block still works and renders before
the configured list:

```html
{% block app.header.widgets %}
  <c-my-page-widget />
{% endblock %}
```

## Navbar position

`layout.navbar.sticky` controls whether the header pins to the top of the viewport:

- **`True`** (default) — the header stays fixed at the top on scroll (app-style), gaining a
  subtle shadow once the page scrolls.
- **`False`** — the header scrolls away with the page (traditional-site behaviour). The
  scroll shadow is dropped along with the pinning.

```python
MVP_CONFIG = {
    "layout": {
        "navbar": {
            "sticky": False,
        },
    },
}
```

Per-page override (use the `:` expression form so the value stays a real boolean):

```html
{% block app.header %}
  <c-app.header :sticky="False" />
{% endblock %}
```

## Announcement banner

`{% block announcement %}` sits outside the app shell entirely — before the
sidebar/header/content grid, not inside it. Content placed there renders in
normal document flow above the shell, so it scrolls away with the page while
the header inside `app.header` keeps its own sticky behavior unaffected. It
ships empty: declaring the slot is the whole feature, and what goes in it —
a promotion, a release note, a one-time offer — is entirely your call, the
same way `app.header.tray` decides nothing on your behalf.

```html
{% block announcement %}
  <div class="alert alert-info rounded-none justify-center">
    New in this release: dark mode. <a href="/changelog/" class="link">See what's new</a>.
  </div>
{% endblock %}
```

## Full-page content

By default, page content scrolls with the window: `<c-app.main>` grows as tall as
its content and the browser handles scrolling. Some content — a full-bleed map, most
JavaScript-driven widgets — instead wants to fill the space the shell gives it and
handle its own scrolling.

Put `fill` on `<c-page>`. That is the whole opt-in:

```html
{% block content %}
  <c-page fill>
    <c-page.content>
      <div id="map" class="h-full w-full"></div>
    </c-page.content>
  </c-page>
{% endblock %}
```

There is nothing to configure above the page, and no setting for it. `fill` marks
the page, and the shell responds to the mark: `drawer-content` becomes a flex
column with a viewport-height floor, `<c-app.main>` is already `flex-1`, and
`<c-page.content>` is already `flex-1 min-h-0`. Your content can then take
`h-full` and scroll internally.

The demo runs a Leaflet map this way at `/layout/full-page/`.

Pages without `fill` are untouched. The shell's markup is identical either way —
the rule is scoped to pages carrying the mark, so on every other page it does not
apply at all.

The floor is stated rather than inherited because the sidebar only supplies a
height at some widths. At or above `layout.sidebar.breakpoint` the sidebar is a
persistent `100dvh` column in the same grid row, and the content area stretches
to match it. Below the breakpoint the sidebar is an overlay drawer, positioned
out of the document flow, and contributes no height at all. A page that relied on
inheriting one worked on a desktop and rendered into nothing on a phone.

The mobile dock moves into the flow on a filled page, so it sits below your
content instead of over it. Everywhere else the dock is fixed to the bottom of
the viewport, which works because the page scrolls underneath it and its last
inch is still reachable. A filled page does not scroll, so a fixed dock would
permanently cover the bottom 4rem — on the demo map, Leaflet's zoom controls and
attribution. Nothing to configure: `fill` carries this too.

### Dropping the footer

A page given over to one widget often has nothing for a footer to say, and every
row it takes is a row the content does not get. Override the block with nothing:

```html
{% block app.footer %}
{% endblock %}
```

The demo map page does exactly this. Leave the dock alone unless navigation is
genuinely unwanted on that page — it is the only navigation below the sidebar
breakpoint.

## Overriding the layout per page

`layout.sidebar.breakpoint` and `layout.sidebar.collapse` drive three regions that
have to agree: the sidebar drawer, the collapsed sidebar itself, and the **navbar
toggle** that shows/hides against them. `mvp/base.html` therefore resolves both knobs
*once* at the top of the `app` block and threads them to every region. To override them
for a single page, set `breakpoint` and/or `collapse` in the template context — the
whole shell, navbar toggle included, follows.

The tidiest way is to wrap `{{ block.super }}` so you reuse the shipped shell:

```html
{% block app %}
  {% with breakpoint="xl" collapse="icons" %}{{ block.super }}{% endwith %}
{% endblock %}
```

Either knob may be set on its own; the other keeps its `MVP_CONFIG` default. The same
variables can instead be supplied from the view context (e.g. `{"breakpoint": "xl"}`)
when the choice is view- rather than template-driven.

> Setting them on `<c-app>` works: it renders the resolved values onto the shell's
> drawer, and the navbar toggle reads them from there. Setting them on
> `<c-app.sidebar>` styles only that component and reaches nothing else. Resolving
> them in the `app` block as above is still the clearest form, because it is the one
> place every region reads.

## Reading the resolved layout in Python

By the time a page renders, the layout settings above have been through a resolution
step: a page-level override has replaced the project default where there is one, a
breakpoint name has become a pixel width, and `never` has become a flag rather than a
width. `LayoutConfig` is where that happens, and it is the only place it happens.

```python
from mvp.layout import LayoutConfig

config = LayoutConfig("xl", collapse="icons")
config.breakpoint      # "xl"
config.breakpoint_px   # 1280
config.persistent      # True
config.as_dict()       # every value above, as plain data
```

It normalises two cases you would otherwise have to handle yourself. `never` and `none`
in any capitalisation mean the sidebar is an overlay at every width, so `persistent` is
`False` and `breakpoint_px` is `None` — there is no width to report. A breakpoint name
the package does not recognise falls back to `lg` rather than raising, so a typo in
`MVP_CONFIG` costs you the default rather than the page.

`as_dict()` is what the shell hands to the browser: grouped by component and camelCase —
the same document [the layout store](#the-layout-store) reads, so the payload and the store
never have two shapes to keep in agreement.

## Responsive visibility

The drawer element — the one wrapping the sidebar, header and page content — carries
the resolved layout as two attributes: `data-mvp-breakpoint` (`sm`, `md`, `lg`, `xl`,
`2xl` or `never`, already normalised the same way `LayoutConfig.breakpoint` is above)
and `data-mvp-collapse` (`offcanvas` or `icons`). `mvp/tailwind/base.css` selects on
both to decide what shows at which width, and three classes are available for your own
markup to reuse the same rules instead of writing new media queries:

"Desktop" and "mobile" here mean what they mean everywhere else in this package: mobile is
where the sidebar is an off-canvas overlay, desktop is where it sits in the page's flow.
The configured breakpoint is the line between them.

| Class | Shown | Hidden |
| --- | --- | --- |
| `mvp-desktop-only` | desktop — at and above the configured breakpoint | on mobile. Under `breakpoint="never"` there is no desktop, so it is shown at every width rather than hidden at every width |
| `mvp-mobile-only` | mobile — below the configured breakpoint | on desktop, and at every width under `breakpoint="never"`, so it never doubles up with the unconditionally shown `mvp-desktop-only` region |
| `mvp-sidebar-hidden-only` | while the sidebar is not on screen | while it is: always in `icons` mode from the breakpoint up, since the rail is always there, and in `offcanvas` mode only while the drawer is open |

`mvp-sidebar-hidden-only` exists because the shell draws two controls twice. The sidebar's
own header carries the brand icon and a toggle button, and the navbar carries its own copy
of both — so that a page still has them when the sidebar is not on screen to provide them.
Put this class on a duplicate of something the sidebar already shows, and it will stand
down whenever the original is visible. The packaged navbar uses it for exactly those two.

**These two set `display: flex` when shown.** An element that needs a different display box should wrap one of them rather than combine it with a display utility: the package's rules sit outside Tailwind's utility layer and win against it whatever the specificity, so `class="mvp-mobile-only hidden"` resolves to `flex`.

Any descendant of the drawer element can carry one — the navbar's widget lists, the
account layout's collapsed/persistent navigation split, and the navbar's own copy of
the sidebar-toggle button and site icon are all built from these three.

## The layout store

Every shell page registers an Alpine store named `mvp`, so any element inside the shell can read
or react to the sidebar, header and viewport state through `$store.mvp`. Its shape, with
representative values:

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

- `sidebar.open` — whether the sidebar is open right now: the mobile overlay below the breakpoint, the persistent panel at/above it. Bound to the drawer's own checkbox; reading it never lags what is on screen.
- `sidebar.desktopOpen` — the remembered desktop-width open state (what `sidebar.open` is restored to on a later visit, at/above the breakpoint). Persisted to `localStorage`.
- `sidebar.breakpoint` — the normalised sidebar breakpoint for this page: `sm`, `md`, `lg`, `xl`, `2xl`, or `never`. An unrecognised name already fell back to `lg` server-side.
- `sidebar.breakpointPx` — the breakpoint's width in pixels (see the [breakpoint table](#sidebar-breakpoint)) — `null` when `breakpoint` is `never`, since there is no width to report. This is what `isWide`'s `matchMedia` listener watches.
- `sidebar.persistent` — whether the sidebar ever becomes a persistent panel at some width. `false` only when `breakpoint` is `never`; `isWide` then stays permanently `false` too, because no listener is attached.
- `sidebar.collapse` — `"offcanvas"` or `"icons"`, see [Sidebar collapse mode](#sidebar-collapse-mode).
- `sidebar.boost` — whether sidebar links use `hx-boost`, see [Boosted sidebar navigation](#boosted-sidebar-navigation).
- `header.stuck` — whether the sticky header has scrolled off its resting position (the same state that draws its shadow). Always `false` when `header.sticky` is `false`.
- `header.sticky` — whether the header pins to the top of the viewport, see [Navbar position](#navbar-position). Sourced from `MVP_CONFIG["layout"]["navbar"]["sticky"]`, unchanged by the store's own grouping.
- `isWide` — whether the viewport is currently at or above `sidebar.breakpointPx`. Permanently `false` when the sidebar is `never`/`none`. Reported at the top level rather than under `sidebar` because it describes the viewport, not the sidebar — the things that read it have nothing to do with the sidebar itself.

A page that renders no shell — the entrance page, the error pages — still gets a store reporting
the values above (`sidebar.open` and `header.stuck` both `false`), and nothing throws.

```html
<div x-data class="badge" :class="$store.mvp.sidebar.open ? 'badge-success' : 'badge-ghost'"
     x-text="$store.mvp.sidebar.open ? 'open' : 'closed'"></div>
```

The demo runs this, alongside the collapse mode and the header's stuck state, at
`/layout/store/` — pass `?breakpoint=` to exercise a per-page override or the `never` case,
e.g. `/layout/store/?breakpoint=xl` and `/layout/store/?breakpoint=never`.

The sidebar checkbox is the source of truth for whether it is open — the store mirrors it, rather
than the other way around — so write to `sidebar.open` only by driving that checkbox (the shipped
controls all do). Writing `sidebar.desktopOpen` directly works the same way `$persist` always has,
but the shell already keeps it in sync with `sidebar.open` above the breakpoint; there is normally
nothing to write yourself.

## Template blocks

`mvp/base.html` exposes blocks for coarse-grained control:

| Block | Replaces |
| --- | --- |
| `head`, `title`, `extra_js` | document head / scripts |
| `announcement` | a banner slot outside the app shell (empty by default) |
| `app` | the entire app shell |
| `app.sidebar` | the sidebar (default: `<c-app.sidebar />`) |
| `app.header` | the header |
| `app.header.widgets` | extra navbar-end content (hidden below the sidebar breakpoint, with the configured widgets) |
| `app.header.tray` | a row below the navbar |
| `app.main` / `content` | the main area / page content |
| `app.footer` | the footer |

For anything deeper, override the component template itself (e.g. drop your own
`templates/cotton/app/sidebar/footer.html`) — that is the intended extension path.
