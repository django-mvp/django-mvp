# Configuration

Everything django-mvp reads from Django settings lives in one dict,
`settings.MVP_CONFIG`. This page lists every key it accepts, its default, and
what it does.

## How a value resolves

The package ships its own defaults in `mvp/config.py`. At import time it deep-merges
`settings.MVP_CONFIG` over them (`mergedeep.merge`, default *replace* strategy):

- Nested dicts recurse. Set only the keys you are changing and every sibling keeps
  its default.
- A list or a scalar replaces the default outright. Setting
  `layout.navbar.desktop.end` replaces the whole list rather than extending it.

Register the context processor, or nothing settings-driven reaches a template:

```python
# settings.py
TEMPLATES = [{"OPTIONS": {"context_processors": [
    "django.template.context_processors.request",   # the shell needs it
    "mvp.context_processors.mvp_config",             # exposes the merged dict as `mvp_config`
]}}]
```

Read the merged result in Python with `from mvp.config import MVP_CONFIG`, and in a
template as `{{ mvp_config.layout.sidebar.breakpoint }}`.

Resolution order is the same everywhere in the package: **component attribute
(per-page) → `MVP_CONFIG` (project) → package default.** A Cotton component
declares the config value as its own default, so an attribute passed at a call
site overrides the project setting for that one tag only.

## Every key

| Key | Accepts | Default | What it does |
| --- | --- | --- | --- |
| `view_names.list` | URL-name template string | `"{model_name}-list"` | Name the CRUD views reverse for the list page |
| `view_names.detail` | URL-name template string | `"{model_name}-detail"` | Same, for the detail page |
| `view_names.create` | URL-name template string | `"{model_name}-create"` | Same, for the create page |
| `view_names.update` | URL-name template string | `"{model_name}-update"` | Same, for the update page |
| `view_names.delete` | URL-name template string | `"{model_name}-delete"` | Same, for the delete page |
| `brand.avatar_resolver` | dotted import path | `"mvp.utils.avatar_url"` | Callable that returns a user's avatar URL |
| `brand.logo_resolver` | dotted import path | `"mvp.utils.logo_url"` | Callable that returns the brand logo URL |
| `brand.icon_resolver` | dotted import path | `"mvp.utils.icon_url"` | Callable that returns the brand mark URL |
| `theme.default` | theme name | `"light"` | Theme applied when the visitor has expressed no preference |
| `theme.dark` | theme name | `"dark"` | The other half of the two-theme toggle |
| `theme.choices` | list of theme names | `[]` | Non-empty turns the theme control into a menu of these |
| `layout.sidebar.breakpoint` | `sm` \| `md` \| `lg` \| `xl` \| `2xl` \| `never` \| `none` | `"lg"` | Viewport width at which the sidebar becomes persistent |
| `layout.sidebar.collapse` | `"offcanvas"` \| `"icons"` | `"offcanvas"` | How the sidebar collapses when toggled at or above that width |
| `layout.sidebar.title` | string or falsey | `None` | Text beside the brand mark in the sidebar header |
| `layout.sidebar.boost` | bool | `False` | Navigate sidebar links without a full page load |
| `layout.navbar.mobile.end` | list of component names | `[]` | Widgets at the trailing edge of the navbar below the sidebar breakpoint |
| `layout.navbar.desktop.end` | list of component names | `["actions.theme-controller", "actions.login"]` | Same, at and above the breakpoint |
| `layout.navbar.sticky` | bool | `True` | Whether the header stays pinned as the page scrolls |
| `table.wrap` | bool | `False` | Project-wide default for whether table cell text wraps |
| `pwa.enabled` | bool | `False` | Make the project installable as an app; needs the root include described in [Installable app](installable-app.md) |
| `pwa.name` | string or `None` | `None` | The app's name; `None` takes the current site's name |
| `pwa.short_name` | string or `None` | `None` | The label under the icon; `None` takes the name |
| `pwa.start_url` | URL path or `None` | `None` | Where the app opens; `None` takes the site root |
| `pwa.display` | manifest display mode | `"standalone"` | How the installed app's window looks |
| `pwa.theme_color` | CSS hex colour or `None` | `None` | Browser toolbar colour; `None` takes the default theme's colour when the package ships it |
| `pwa.background_color` | CSS hex colour or `None` | `None` | Launch background; resolved like `theme_color` |

There is no `layout.sidebar.footer` key. The sidebar footer is a fixed
composition rather than a configured widget list — see
[Sidebar footer](layout.md#sidebar-footer) and
[ADR 0023](adr/0023-the-sidebar-footer-is-a-fixed-composition.md). A project
that still sets it gets an `MVPDeprecationWarning` and the key is popped.

A worked override, changing four things and inheriting the rest:

```python
# settings.py
MVP_CONFIG = {
    "theme": {"choices": ["light", "dark", "dracula"]},
    "layout": {
        "sidebar": {"title": "Acme"},
        "navbar": {"desktop": {"end": ["actions.search", "actions.login"]}},
    },
}
```

## `view_names`

Each value is a `str.format` template given two names: `model_name` and
`app_name`. `"{app_name}:{model_name}-list"` works for a namespaced URLconf. The
CRUD views read this to build the edit, delete and back links they render, and a
single view class can override the whole mapping by setting `crud_views` on
itself. Asking for an action outside these five keys raises `ValueError`.

## `brand.*` resolvers

Each value is a dotted path to a callable. The signatures differ:

| Setting | Signature | Returns | Called by |
| --- | --- | --- | --- |
| `avatar_resolver` | `(user, size)` | URL string or `None` | the avatar component |
| `logo_resolver` | `(request, height, theme)` | URL string or `None` | the logo component |
| `icon_resolver` | `(request, height, theme)` | URL string or `None` | the brand-mark component and the favicon links |

`size` is the token the avatar was asked for, such as `"md"`. `height` is
advisory and the packaged resolvers ignore it. `theme` is the literal string
`"light"` or `"dark"` (not one of your configured theme names) and defaults to
`"light"` when the caller passes none, which is what the in-page brand
components do. Only the favicon links request both variants.

Failure behavior differs between the three:

- `logo_resolver` and `icon_resolver` are defensive. An import path that does
  not resolve raises `ImproperlyConfigured` naming the setting and the path. A
  resolver that raises at runtime is swallowed and the tag returns `""`, which
  renders an image element with an empty source rather than a 500. Returning
  `None` also becomes `""`.
- `avatar_resolver` is not. The import error propagates as-is, and an
  exception inside your callable propagates too. Returning `None` is the
  supported "no avatar" answer and makes the avatar component fall back to
  initials, or to a silhouette when it has none.

The packaged `logo_resolver` and `icon_resolver` serve `brand/logo.svg` and
`brand/icon.svg` from your static files, preferring a `_dark.svg` sibling
under the dark theme where one exists and falling back to the light asset
otherwise. The packaged `avatar_resolver` returns `None` unconditionally —
point it at your own function to serve real avatars:

```python
# myproject/avatars.py
SIZES = {"sm": 32, "md": 48, "lg": 96}


def avatar_url(user, size):
    if not user.is_authenticated:
        return None
    return f"https://avatars.example.com/{user.pk}?px={SIZES.get(size, 48)}"
```

```python
MVP_CONFIG = {"brand": {"avatar_resolver": "myproject.avatars.avatar_url"}}
```

The second argument is a size token, never a number — `"sm"`, `"md"` and the
like, whatever the avatar component asked for. Map it to pixels yourself if
your source needs a dimension, as above.

## `theme.*`

`default` is applied on a first visit and whenever the visitor has stored no
choice. A blocking script in the document head sets it before first paint, so
there is no flash of the wrong theme.

`dark` drives the theme control **only while `choices` is empty**. With no
choices set, the packaged control is a two-state toggle that moves between
`default` and `dark`, and changing one usually means changing both. The
moment `choices` is non-empty the same control becomes a dropdown listing
exactly those names in order, and `dark` stops being read by it.

`choices` also gates what a returning visitor may keep. A stored selection
that is no longer offered is rewritten to `default` on the next load.

Theme names are **not validated**. An ADR records this as a deliberate
decision, since the package cannot see a theme a project defines in its own
stylesheet. A typo is therefore silent: the name is written to the document
as given, nothing matches it, and the page renders in the default theme. Every
prebuilt DaisyUI theme ships, so a name like `dracula` needs nothing
installed — see [ADR 0011](adr/0011-theme-names-are-not-validated.md) and
[Theming](theming.md) for the full picture, including the variable table and
a worked example of writing your own theme.

## Widget lists take component names, not template paths

`layout.navbar.mobile.end` and `layout.navbar.desktop.end` are lists of
**Cotton component names**. Each is rendered dynamically, so the string is
exactly what you would write between `<c-` and `>`. The mapping to a file is
Cotton's own:

1. Dots become directory separators.
2. Hyphens become underscores (Cotton's default naming,
   `COTTON_SNAKE_CASED_NAMES`).
3. The result is looked up under your Cotton directory, `templates/cotton/`
   by default, with `<name>/index.html` tried as a fallback.

So `"actions.theme-controller"` is `<c-actions.theme-controller />` and
resolves to `templates/cotton/actions/theme_controller.html`. A component of
your own resolves the same way with no registration: `"billing.credit-meter"`
finds `templates/cotton/billing/credit_meter.html`.

A name in `MVP_CONFIG` carries no attributes. If you need to pass one — a
distinct element id when the same widget appears twice, say — wrap it in a
component of your own and list that name instead.

Bundled widgets:

| Name | Renders |
| --- | --- |
| `actions.theme-controller` | Toggle, or a dropdown when `theme.choices` is set |
| `actions.language-switcher` | Language dropdown; renders nothing without i18n and a `set_language` URL |
| `actions.language-switcher-modal` | Same choices in a modal grid, better for touch and narrow slots |
| `actions.login` | Log-in button; renders nothing for an authenticated visitor |
| `actions.search` | Presentation only: a search icon styled as a button beside an input with no name, no form and no handler. It submits nothing — wire up your own |

## `layout.navbar` — mobile and desktop are separate

```python
"navbar": {
    "mobile": {"end": [...]},   # rendered below the sidebar breakpoint
    "desktop": {"end": [...]},  # rendered at the breakpoint and above
    "sticky": True,
}
```

Both regions are always emitted and one is hidden by viewport width, so a
widget that only makes sense on a phone can be listed in `mobile` alone
without its author having to make it responsive.

**The split is hard-coded at `lg` (1024px)** and does not follow
`layout.sidebar.breakpoint`. The navbar template emits the two regions with
literal `flex lg:hidden` and `hidden lg:flex` classes, so setting
`breakpoint: "md"` moves the sidebar to persistent at 768px while the navbar
keeps showing the mobile widget list up to 1024px. Override
`cotton/app/header/navbar.html` in your own project if you need the two to
line up.

**A flat `navbar.end` is still accepted.** Older projects set a single list at
`layout.navbar.end`, and the deep merge would leave that sitting beside the
new keys as a third, unread entry. So the package normalizes it after
merging: if a flat `end` is present it is popped and copied into both
`mobile.end` and `desktop.end`, which is exactly what it used to do.

The consequence: **`MVP_CONFIG["layout"]["navbar"]["end"]` does not exist
after import.** You may write it in settings, but reading it back finds
nothing, because the key has been removed and folded into the two split
keys. Templates only ever read `navbar.mobile.end` and `navbar.desktop.end`.
Assert against those.

`sticky` applies at every width. `True` pins the header to the top of the
viewport as the page scrolls. `False` lets it scroll away with the page.

## `layout.sidebar.breakpoint`

The width at which the sidebar stops being an overlay drawer and becomes a
persistent column.

| Value | Persistent from |
| --- | --- |
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px (default) |
| `xl` | 1280px |
| `2xl` | 1536px |
| `never` or `none` | never — an overlay at every width |

`never` and `none` are equivalent and matching is case-insensitive, so
`"Never"` and `"NONE"` both work. Any other unrecognised value falls back to
`lg` silently rather than raising, so a typo shows up as a sidebar that
behaves normally at the wrong width.

With the sidebar an overlay at every width, the navbar's sidebar toggle is
always visible, because an open overlay covers the navbar behind it.

## `layout.sidebar.collapse`

- `"offcanvas"` (default) — the sidebar slides fully away and the content
  takes the full width.
- `"icons"` — the sidebar narrows to a rail that keeps item icons and hides
  labels, badges and section headings. Collapsible groups become hover
  fly-outs instead of inline lists. In your own sidebar content, mark an
  element `mvp-rail-hide` to hide it in the rail and `mvp-rail-only` to show
  it only there. `sidebar.title` is hidden in the rail.

See [Sidebar collapse mode](layout.md#sidebar-collapse-mode) for how this
looks and how the open/closed state persists.

## `layout.sidebar.boost`

Enabling it makes every link inside the sidebar — menu items, the brand link
and the footer widgets — navigate by fetching the next page and swapping the
document body, rather than doing a full page load. The mobile overlay closes
on its own as a result, since the swapped-in markup carries its
server-rendered closed state.

It defaults off deliberately. Swapping the body in place suits an app shell,
but it changes how your own scripts and any third-party widgets see the page:
they are not re-run on navigation the way a full load would re-run them. Opt
in once your pages tolerate being swapped rather than reloaded. See
[Boosted sidebar navigation](layout.md#boosted-sidebar-navigation) for the
full list of what a boosted swap does and does not carry across.

## `table.wrap`

Whether a table column's cell text may run onto more than one line.
Resolution order for any one column:

1. A wrap class the column names in its own `attrs` (`mvp-col-wrap` or
   `mvp-col-nowrap`) wins — see [Column behaviour classes](styling.md#column-behaviour-classes).
2. Otherwise `MVP_CONFIG["table"]["wrap"]` decides.
3. The package default is off, so a dense table keeps one row per record
   until you say otherwise.

Heading cells are always held to one line regardless of this setting, so a
column is never widened by its own title.
