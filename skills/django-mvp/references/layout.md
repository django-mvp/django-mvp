# Layout (`MVP_CONFIG` reference)

The shell wraps every page:

```
<c-app>                        DaisyUI drawer (sidebar + content)
├── <c-app.sidebar>            brand header, AppMenu, footer widgets, user menu
├── <c-app.header>             header
│   └── <c-app.header.navbar>  sidebar toggle, brand, configured widgets
├── <c-app.main>               your {% block content %} + flash messages
├── <c-app.footer>
└── <c-app.dock>               mobile bottom navigation
```

Configured from `settings.MVP_CONFIG` (deep-merged over `mvp/config.py` defaults). The
context processor `mvp.context_processors.mvp_config` exposes the merged dict to templates
as `mvp_config`. **Resolution order: component attribute (per-page) → `MVP_CONFIG` →
package default.**

## Package defaults

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {
            "breakpoint": "lg",       # sm | md | lg | xl | 2xl | never
            "collapse": "offcanvas",  # "offcanvas" | "icons"
            "title": None,            # text beside the brand icon (falsey = none)
            "footer": [],             # Cotton component NAMES in the sidebar footer
        },
        "navbar": {
            "end": ["actions.theme-controller", "actions.login"],  # Cotton NAMES, right side
            "sticky": True,           # True: pinned | False: scrolls away
        },
    },
}
```

## `sidebar.breakpoint`

Viewport width at which the sidebar becomes a persistent panel; below it, the sidebar is a
mobile overlay drawer (opened by the navbar hamburger or the dock).

| Value | Persistent from |
|---|---|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px (default) |
| `xl` | 1280px |
| `2xl` | 1536px |
| `never` | never — stays an off-canvas overlay at every width |

## `sidebar.collapse`

Behavior when the navbar toggle collapses the sidebar at/above the breakpoint:

- **`"offcanvas"`** (default) — the sidebar slides fully away; content takes full width.
- **`"icons"`** — collapses to a 4rem icon rail: labels, badges and section titles hide,
  icons center, hovering an item shows its label as a tooltip, and the brand logo swaps
  for the brand icon. In your own sidebar content, use `.mvp-rail-hide` (hidden while
  collapsed) and `.mvp-rail-only` (shown only while collapsed) to control rail visibility.

Open/closed state persists across loads (localStorage key `mvp-app-drawer-open`); first
visit defaults to open at/above the breakpoint, closed below.

## `sidebar.title`

Short text beside the brand icon in the sidebar header. Falsey (`None`, default) = no
title. Hidden in `"icons"` collapse mode.

## `sidebar.footer` and `navbar.end` — Cotton component NAMES

Both are lists of **Cotton component names**, not template paths, rendered via
`<c-component :is="…">`:

- `"actions.theme-controller"` → `<c-actions.theme-controller />`
- `"myapp.notifications-bell"` → `templates/cotton/myapp/notifications_bell.html`

Any component in your project's cotton directory works with no extra config.
`sidebar.footer` widgets lay out as a horizontally centered, wrapping flex row (above the
user menu); `navbar.end` widgets render in order at the right of the navbar.

Bundled widgets: `actions.theme-controller`, `actions.language-switcher` (dropdown),
`actions.language-switcher-modal` (globe button → modal grid; better for touch/narrow
slots), `actions.search`, `actions.login` (renders only when anonymous).

A `MVP_CONFIG` name takes no attributes. To pass one (e.g. a distinct modal id when the
same widget appears twice), wrap it in your own component and reference that name instead.

## `navbar.sticky`

- **`True`** (default) — header pinned to the top on scroll (gains a subtle shadow once
  scrolled).
- **`False`** — header scrolls away with the page (no scroll shadow).

Per-page override (keep it a real boolean with the `:` form):

```django
{% block app.header %}<c-app.header :sticky="False" />{% endblock %}
```

## Overriding `breakpoint` / `collapse` per page

These drive three regions that must agree — the sidebar drawer, the collapsed sidebar, and
the **navbar toggle**. `mvp/base.html` resolves both once at the top of `{% block app %}`
from `breakpoint`/`collapse` context vars and threads them everywhere. Override for one
page by setting those vars — the tidiest way is wrapping `{{ block.super }}`:

```django
{% block app %}
  {% with breakpoint="xl" collapse="icons" %}{{ block.super }}{% endwith %}
{% endblock %}
```

Either knob may be set alone; the other keeps its `MVP_CONFIG` value. The same vars can
come from the view context (e.g. `{"breakpoint": "xl"}`).

> Setting `breakpoint`/`collapse` as attributes directly on `<c-app>` / `<c-app.sidebar>`
> styles *that* component but does **not** reach the navbar toggle (a sibling). Resolve
> them in the `app` block (or view context) so all three stay in sync.

## Template blocks

| Block | Replaces |
|---|---|
| `head`, `title`, `styles`, `extra_js` | document head / stylesheet links / scripts |
| `app` | the entire shell |
| `app.sidebar` | the sidebar (default `<c-app.sidebar />`) |
| `app.header` | the header |
| `app.header.widgets` | extra navbar-end content (renders before the configured list) |
| `app.header.tray` | a row below the navbar |
| `app.main` / `content` | the main area / page content |
| `app.footer` | the footer |

For anything deeper, override the component template itself (e.g. drop your own
`templates/cotton/app/sidebar/footer.html`).
