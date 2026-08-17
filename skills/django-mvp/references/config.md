# Configuration — reference

Everything django-mvp reads from Django settings lives in one dict, `MVP_CONFIG`.
This file lists every key it accepts today, the values each one takes, and how a
value is resolved at render time.

## How a value resolves

The package ships defaults in `mvp/config.py`. At import time it deep-merges
`settings.MVP_CONFIG` over them using `mergedeep.merge` on its default *replace*
strategy:

- Nested dicts recurse. Set only the keys you are changing and every sibling keeps
  its default.
- A list or a scalar replaces the default outright. Setting `layout.sidebar.footer`
  replaces the whole list, it does not extend it.

Register the context processor, or nothing settings-driven reaches a template:

```python
# settings.py
TEMPLATES = [{"OPTIONS": {"context_processors": [
    "django.template.context_processors.request",   # the shell needs it
    "mvp.context_processors.mvp_config",            # exposes the merged dict as `mvp_config`
]}}]
```

Read the merged result in Python with `from mvp.config import MVP_CONFIG`, and in a
template as `{{ mvp_config.layout.sidebar.breakpoint }}`. **Resolution order,
everywhere: component attribute → `MVP_CONFIG` → package default.** Components
declare the config value as their own default, so a value passed at a call site
overrides the project setting for that one tag only.

## Every key

| Key | Accepts | Default | What it does |
|---|---|---|---|
| `view_names.list` | URL-name template string | `"{model_name}-list"` | Name the CRUD views reverse for the list page |
| `view_names.detail` | URL-name template string | `"{model_name}-detail"` | Same, for the detail page |
| `view_names.create` | URL-name template string | `"{model_name}-create"` | Same, for the create page |
| `view_names.update` | URL-name template string | `"{model_name}-update"` | Same, for the update page |
| `view_names.delete` | URL-name template string | `"{model_name}-delete"` | Same, for the delete page |
| `brand.avatar_resolver` | dotted import path | `"mvp.utils.avatar_url"` | Callable that returns a user's avatar URL |
| `brand.logo_resolver` | dotted import path | `"mvp.utils.logo_url"` | Callable that returns the brand logo URL |
| `brand.icon_resolver` | dotted import path | `"mvp.utils.icon_url"` | Callable that returns the brand mark URL |
| `theme.default` | theme name | `"mvp"` | Theme applied when the visitor has expressed no preference |
| `theme.dark` | theme name | `"mvp-dark"` | The other half of the two-theme toggle |
| `theme.choices` | list of theme names | `[]` | Non-empty turns the theme control into a menu of these |
| `layout.sidebar.breakpoint` | `sm`&#124;`md`&#124;`lg`&#124;`xl`&#124;`2xl`&#124;`never`&#124;`none` | `"lg"` | Viewport width at which the sidebar becomes persistent |
| `layout.sidebar.collapse` | `"offcanvas"` &#124; `"icons"` | `"offcanvas"` | How the sidebar collapses when toggled at or above that width |
| `layout.sidebar.title` | string or falsey | `None` | Text beside the brand mark in the sidebar header |
| `layout.sidebar.footer` | list of component names | `[]` | Widgets in the sidebar footer, in order |
| `layout.sidebar.boost` | bool | `False` | Navigate sidebar links without a full page load |
| `layout.navbar.mobile.end` | list of component names | `["actions.theme-controller", "actions.login"]` | Widgets at the trailing edge of the navbar below the wide breakpoint |
| `layout.navbar.desktop.end` | list of component names | same as `mobile.end` | Same, at wide widths |
| `layout.navbar.sticky` | bool | `True` | Whether the header stays pinned as the page scrolls |
| `table.wrap` | bool | `False` | Project-wide default for whether table cell text wraps |

A worked override, changing four things and inheriting the rest:

```python
# settings.py
MVP_CONFIG = {
    "theme": {"choices": ["mvp", "mvp-dark", "dracula"]},
    "layout": {
        "sidebar": {"title": "Acme", "footer": ["actions.theme-controller"]},
        "navbar": {"desktop": {"end": ["actions.search", "actions.login"]}},
    },
}
```

## `view_names`

Each value is a `str.format` template given two names: `model_name` and
`app_name`. `"{app_name}:{model_name}-list"` works for namespaced URLconfs. The
CRUD views read this to build the edit, delete and back links they render, and a
single view class can override the whole mapping by setting `crud_views` on
itself. Asking for an action outside these five keys raises `ValueError`.

## `brand.*` resolvers

Each value is a dotted path to a callable. The signatures differ:

| Setting | Signature | Returns | Called by |
|---|---|---|---|
| `avatar_resolver` | `(user, size)` | URL string or `None` | `{% avatar_url user size %}`, used by the avatar component |
| `logo_resolver` | `(request, height, theme)` | URL string or `None` | `{% logo_url height theme %}`, used by the logo component |
| `icon_resolver` | `(request, height, theme)` | URL string or `None` | `{% icon_url height theme %}`, used by the brand-mark component and the favicon links |

`size` is the token the avatar was asked for, such as `"md"`. `height` is advisory
and the packaged resolvers ignore it. `theme` is the literal string `"light"` or
`"dark"` (not one of your configured theme names) and defaults to `"light"` when
the caller passes none, which is what the in-page brand components do. Only the
favicon links request both variants.

Failure behaviour differs between the three:

- `logo_resolver` and `icon_resolver` are defensive. An import path that does not
  resolve raises `ImproperlyConfigured` naming the setting and the path. A
  resolver that raises at runtime is swallowed and the tag returns `""`, which
  renders an image element with an empty source rather than a 500. Returning
  `None` also becomes `""`.
- `avatar_resolver` is not. The import error propagates as-is, and an exception
  inside your callable propagates too. Returning `None` is the supported "no
  avatar" answer and makes the avatar component fall back to initials, or to a
  silhouette when it has none.

## `theme.*`

`default` is applied on a first visit and whenever the visitor has stored no
choice. A blocking script in the document head sets it before first paint, so
there is no flash of the wrong theme.

`dark` drives the theme control **only while `choices` is empty**. With no choices
set, the packaged control is a two-state toggle that moves between `default` and
`dark`, and swapping one usually means swapping both. The moment `choices` is
non-empty the same control becomes a dropdown listing exactly those names in
order, and `dark` stops being read by it. The shell reads `dark` regardless: the
document head emits a `[data-theme="<dark>"] .hide-on-dark-theme` rule from it, so
the value still decides which theme hides `.hide-on-dark-theme` content even when
the control has stopped consulting it.

`choices` also gates what a returning visitor may keep. A stored selection that is
no longer offered is rewritten to `default` on the next load.

Theme names are **not validated**. An ADR records this as a deliberate decision,
since the package cannot see a theme a project defines in its own stylesheet. A
typo is therefore silent: the name is written to the document as given, nothing
matches it, and the page renders in the default theme. If a theme "does nothing",
check the spelling before you check your CSS. Two themes ship under the names
`mvp` and `mvp-dark`, and every prebuilt theme ships alongside them, so a name
like `dracula` needs nothing installed.

## Widget lists take component names, not template paths

`layout.navbar.mobile.end`, `layout.navbar.desktop.end` and
`layout.sidebar.footer` are lists of **Cotton component names**. Each is rendered
dynamically, so the string is exactly what you would write between `<c-` and `>`.
The mapping to a file is Cotton's own:

1. Dots become directory separators.
2. Hyphens become underscores (Cotton's default naming, `COTTON_SNAKE_CASED_NAMES`).
3. The result is looked up under your Cotton directory, `templates/cotton/` by
   default, with `<name>/index.html` tried as a fallback.

So `"actions.theme-controller"` is `<c-actions.theme-controller />` and resolves to
`templates/cotton/actions/theme_controller.html`. Any component in your own project
resolves the same way with no registration: `"billing.credit-meter"` finds
`templates/cotton/billing/credit_meter.html`.

A name in `MVP_CONFIG` carries no attributes. If you need to pass one — a distinct
element id when the same widget appears twice, say — wrap it in a component of your
own and list that name instead.

Bundled widgets:

| Name | Renders |
|---|---|
| `actions.theme-controller` | Toggle, or a dropdown when `theme.choices` is set |
| `actions.language-switcher` | Language dropdown; renders nothing without i18n and a `set_language` URL |
| `actions.language-switcher-modal` | Same choices in a modal grid, better for touch and narrow slots |
| `actions.login` | Log-in button; renders nothing for an authenticated visitor |
| `actions.search` | Presentation only: a search icon styled as a button beside an input with no name, no form and no handler. It submits nothing. Wire up your own |

Sidebar footer widgets lay out as a centred, wrapping row. Navbar widgets render
in order at the trailing edge.

## `layout.navbar` — mobile and desktop are separate

The current shape splits the widget list in two:

```python
"navbar": {
    "mobile": {"end": [...]},   # rendered below 1024px
    "desktop": {"end": [...]},  # rendered at 1024px and above
    "sticky": True,
}
```

Both regions are always emitted and one is hidden by viewport width, so a widget
that only makes sense on a phone can be listed in `mobile` alone without its author
having to make it responsive.

**The split is hard-coded at `lg` (1024px)** and does not follow
`layout.sidebar.breakpoint`. The navbar template emits the two regions with literal
`flex lg:hidden` and `hidden lg:flex` classes, so setting `breakpoint: "md"` moves
the sidebar to persistent at 768px while the navbar keeps showing the mobile widget
list up to 1024px. Override `cotton/app/header/navbar.html` in your own project if
you need the two to line up.

**A flat `navbar.end` is still accepted.** Older projects set a single list at
`layout.navbar.end`, and the deep merge would leave that sitting beside the new
keys as a third, unread entry. So the package normalises it after merging: if a
flat `end` is present it is popped and copied into both `mobile.end` and
`desktop.end`, which is exactly what it used to do.

The consequence: **`MVP_CONFIG["layout"]["navbar"]["end"]` does not exist after
import.** You may write it in settings, but reading it back finds nothing,
because the key has been removed and folded into the two split keys. Templates
only ever read `navbar.mobile.end` and `navbar.desktop.end`. Assert against those.

`sticky` applies at every width. `True` pins the header to the top of the viewport
as the page scrolls. `False` lets it scroll away with the page.

## `layout.sidebar.breakpoint`

The width at which the sidebar stops being an overlay drawer and becomes a
persistent column.

| Value | Persistent from |
|---|---|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px (default) |
| `xl` | 1280px |
| `2xl` | 1536px |
| `never` or `none` | never — an overlay at every width |

`never` and `none` are equivalent and matching is case-insensitive, so `"Never"`
and `"NONE"` both work. Any other unrecognised value falls back to `lg` silently
rather than raising, so a typo shows up as a sidebar that behaves normally at the
wrong width.

With the sidebar an overlay at every width, the navbar's sidebar toggle is always
visible, because an open overlay covers the navbar behind it.

## `layout.sidebar.collapse`

- `"offcanvas"` (default) — the sidebar slides fully away and the content takes the
  full width.
- `"icons"` — the sidebar narrows to a rail that keeps item icons and hides labels,
  badges and section headings. Collapsible groups become hover fly-outs instead of
  inline lists. In your own sidebar content, mark an element `mvp-rail-hide` to hide
  it in the rail and `mvp-rail-only` to show it only there. `sidebar.title` is
  hidden in the rail.

## `layout.sidebar.boost`

Enabling it makes every link inside the sidebar — menu items, the brand link and
the footer widgets — navigate by fetching the next page and swapping the document
body, rather than doing a full page load. The mobile overlay closes on its own as a
result, since the swapped-in markup carries its server-rendered closed state.

It defaults off deliberately. Swapping the body in place suits an app shell, but it
changes how your own scripts and any third-party widgets see the page. They are not
re-run on navigation the way a full load would re-run them. Opt in once your pages
tolerate being swapped rather than reloaded.

## `table.wrap`

Whether a table column's cell text may run onto more than one line. Resolution
order for any one column:

1. A wrap class the column names in its own `attrs` wins.
2. Otherwise `MVP_CONFIG["table"]["wrap"]` decides.
3. The package default is off, so a dense table keeps one row per record until you
   say otherwise.

Heading cells are always held to one line regardless of this setting, so a column
is never widened by its own title.

---

Back to [SKILL.md](../SKILL.md).
