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
        },
        "navbar": {
            "end": ["actions.theme-controller"],
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

Per-page override:

```html
{% block app %}
  <c-app breakpoint="xl">...</c-app>
{% endblock %}
```

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

Per-page override (the sidebar consumes this attribute, not `c-app`):

```html
{% block app.sidebar %}
  <c-app.sidebar collapse="icons" />
{% endblock %}
```

The open/closed state persists across page loads (localStorage, key
`mvp-app-drawer-open`). On first visit it defaults to open at/above the breakpoint and
closed below it.

## Navbar widgets

`layout.navbar.end` is a list of **Cotton component names** rendered in order at the
right end of the navbar via `<c-component :is="...">`:

```python
MVP_CONFIG = {
    "layout": {
        "navbar": {
            "end": [
                "actions.theme-controller",     # light/dark toggle
                "actions.language-switcher",    # i18n language menu
                "myapp.notifications-bell",     # your own component
            ],
        },
    },
}
```

A name maps to a Cotton template: `"myapp.notifications-bell"` →
`templates/cotton/myapp/notifications_bell.html`. Any component in your project's
cotton directory works, so app-specific widgets need no configuration beyond the name.

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
