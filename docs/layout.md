# Layout

django-mvp renders a complete application shell around your content:

```
<c-app>                        DaisyUI drawer (sidebar + content)
├── <c-app.sidebar>            brand header, AppMenu, user footer
├── <c-app.header>             sticky header
│   └── <c-app.header.navbar>  sidebar toggle, brand, configured widgets
├── <c-app.main>               your {% block content %} + flash messages
├── <c-app.footer>
└── <c-app.dock>               mobile bottom navigation
```

Everything is configured from `settings.MVP_CONFIG` — similar in spirit to
pydata-sphinx-theme's layout options. Package defaults:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm | md | lg | xl | 2xl
            "collapse": "offcanvas",  # "offcanvas" | "icons"
            "title": None,            # text beside the brand icon (falsey = none)
            "footer": [],             # Cotton components in the sidebar footer
            "boost": False,           # navigate sidebar links with htmx
        },
        "navbar": {
            "mobile": {"end": ["actions.theme-controller"]},
            "desktop": {"end": ["actions.theme-controller"]},
            "sticky": True,           # True: pinned | False: scrolls away
        },
    },
}
```

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

## Sidebar footer widgets

`layout.sidebar.footer` is a list of **Cotton component names** rendered in the sidebar
footer, above the user menu. They are laid out as a **horizontally centered, wrapping
flex row**, so they reflow gracefully as the sidebar narrows:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "footer": [
                "actions.theme-controller",     # light/dark toggle
                "actions.language-switcher",    # i18n language menu
                "myapp.support-link",           # your own component
            ],
        },
    },
}
```

Names map to Cotton templates the same way as [navbar widgets](#navbar-widgets):
`"myapp.support-link"` → `templates/cotton/myapp/support_link.html`. The default is an
empty list (no footer actions).

For deeper control of the footer, override the component template itself by dropping your
own `templates/cotton/app/sidebar/footer.html`.

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

## Navbar widgets

`layout.navbar.mobile.end` and `layout.navbar.desktop.end` are each a list of
**Cotton component names** rendered in order at the right end of the navbar via
`<c-component :is="...">`. They're configured separately because a widget can be
right for one screen size and noise on the other — a language switcher that's fine
in a spacious desktop bar may not be worth the tap target on a phone, and for a
third-party widget you often can't rely on it making that call itself:

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
with Tailwind's responsive display utilities (the mobile region is `flex lg:hidden`,
the desktop region `hidden lg:flex`) — a config-driven widget list can't be resolved
from the request alone, so there's no way to render only one without a live layout.
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
  [sidebar footer](#sidebar-footer-widgets), where a dropdown would be cramped.

Both post to Django's `set_language` view and preserve the current path, so they are
interchangeable:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "footer": ["actions.language-switcher-modal"],
        },
    },
}
```

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

> Setting `breakpoint`/`collapse` as attributes on `<c-app>` or `<c-app.sidebar>`
> directly still styles *that* component, but it does **not** reach the navbar toggle
> (a sibling region) — resolve them in the `app` block as above so all three stay in
> sync.

## Template blocks

`mvp/base.html` exposes blocks for coarse-grained control:

| Block | Replaces |
| --- | --- |
| `head`, `title`, `extra_js` | document head / scripts |
| `app` | the entire app shell |
| `app.sidebar` | the sidebar (default: `<c-app.sidebar />`) |
| `app.header` | the header |
| `app.header.widgets` | extra navbar-end content |
| `app.header.tray` | a row below the navbar |
| `app.main` / `content` | the main area / page content |
| `app.footer` | the footer |

For anything deeper, override the component template itself (e.g. drop your own
`templates/cotton/app/sidebar/footer.html`) — that is the intended extension path.
