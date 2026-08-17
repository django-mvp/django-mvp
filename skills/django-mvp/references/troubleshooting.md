# Troubleshooting — reference

Symptom, cause, fix for the failure modes django-mvp actually produces: menus, icons,
layout config, styling, views and integrations. Scan the bold lines first.

## Menus and navigation

**Menu items do not appear at all.**
The module defining them was never imported. `flex_menu`'s app config runs Django's
`autodiscover_modules("menus")`, which only ignores an app that *has no* `menus.py` — an
error raised inside an existing one bubbles up at startup rather than vanishing, so a
silent no-show is not a swallowed traceback.
Check that the app is in `INSTALLED_APPS`, that the file is named `menus.py`, and that
`AppMenu.extend([...])` runs at module level. Importing it from `AppConfig.ready()` also
works.

**The sidebar renders but the menu inside it is empty.**
`FLEX_MENUS["renderers"]["sidebar"]` is unset, so the shell has no renderer to call.
Set `"sidebar": "mvp.renderers.SidebarRenderer"` and `"dock":
"mvp.renderers.MobileFooterNavRenderer"`.

**The menu is empty even with the renderer set.**
An item whose `view_name` cannot be reversed is hidden when it has no children, so a
whole menu of unresolvable names renders as nothing.
Set `FLEX_MENUS["log_url_failures"] = True` to get a warning per failure, then fix the
URL names.

**An item never highlights as active.**
Matching is exact string equality between the item's resolved URL and `request.path`.
A detail page will not light up its list item, because the paths differ — only an
ancestor of a selected item inherits the highlight. An item declared with `params` gets a
querystring appended to its URL, which `request.path` never carries, so it can never
match.
Add a dedicated item for the path, or accept the ancestor highlight from nesting.

## Icons

**Icons render as empty boxes — cause one: the name is not registered.**
`<c-icon name="…">` calls easy-icons' default renderer, which resolves nothing for an
unknown name. Devtools shows an element with no icon class on it.
Include `mvp.utils.BS5_ICONS` in `EASY_ICONS["default"]["packs"]` and register your own
names under `"icons"`.

**Icons render as empty boxes — cause two: the webfont is unreachable.**
`mvp/base.html` links the Bootstrap Icons webfont from a CDN inside `{% block head %}`.
Offline development, a restrictive content-security policy or an air-gapped deployment
means no glyphs, even though every name resolves. The tell is the opposite of cause one:
devtools shows the correct icon class, and the box is the missing-glyph fallback.
Self-host the font and override the `head` block to point at your copy.

## Layout and configuration

**Layout config appears to do nothing.**
Either you are setting `settings.MVP`, which was removed, or
`mvp.context_processors.mvp_config` is missing from `TEMPLATES["OPTIONS"]
["context_processors"]`, so `mvp_config` never reaches a template.
Use `settings.MVP_CONFIG` and register the context processor. The shell also needs
`django.template.context_processors.request`.

**Widgets configured for the navbar do not appear.**
The widget lists are split by screen size: `layout.navbar.mobile.end` and
`layout.navbar.desktop.end`. Setting only one leaves the other on the package default.
A flat `layout.navbar.end` is the legacy pre-split shape — it still works and is
normalized onto both lists, but only when written as exactly that key.
Set both keys, or use the flat `end` key when the widgets suit every width.

**A per-page `breakpoint` or `collapse` override does not move the navbar toggle.**
The sidebar drawer, the collapsed rail and the navbar toggle all read the values resolved
once at the top of `{% block app %}`. Setting the attributes on `<c-app>` or
`<c-app.sidebar>` styles those components and leaves the toggle on the project default.
Resolve them in the block instead: `{% block app %}{% with breakpoint="xl"
collapse="icons" %}{{ block.super }}{% endwith %}{% endblock %}`, or supply them from view
context.

## Templates and styling

**Hand-composing the app shell in a page.**
Re-writing `<c-app>…</c-app>` in a template is the removed API and drops whatever the
shell does today.
Extend `mvp/base.html` and fill `{% block content %}`. The sidebar, header, footer and
mobile dock render on their own.

**Overriding `{% block head %}` loses the stylesheet, the icon font or the scripts.**
That block holds the icon webfont link, the nested `styles` block that loads
`django-mvp.css`, and the bundled front-end runtime — Alpine, htmx and the theme
switcher. Replacing it drops all three.
Add your own stylesheet by overriding the inner `styles` block, or call `{{ block.super }}`
inside your `head` override.

**A Tailwind class silently does nothing.**
The prebuilt stylesheet carries a curated utility list, not all of Tailwind, so anything
outside it has no rule. Four recurring cases:

- Shadow utilities. `shadow-md` has no rule, and neither does any prefixed form
  (`md:shadow-lg`, `hover:shadow-xl`). A few unprefixed names — `shadow-sm`, `shadow-lg`,
  `shadow-xl`, `shadow-none` — do exist as a by-product of the component scan, so one may
  appear to work while its neighbour does not. Do not build on that.
- Physical inline-axis utilities — `pl-*`, `pr-*`, `ml-*`, `mr-*`, `text-left`,
  `text-right`, `left-*`, `right-*`, `border-l`, `border-r`, `rounded-l-*`/`rounded-r-*`.
  Replaced by their logical counterparts.
- Arbitrary values like `w-[37px]`. No prebuilt file can contain them.
- Classes assembled at render time from string fragments. No scanner ever sees these,
  not even in your own build.

Switch to the logical name (`ps-4`, `text-start`), pick something from the shipped list,
or move to your own build with `python manage.py mvp_tailwind`. Write class names out in
full either way.

**A `{# … #}` comment renders into the page as visible text.**
Django's lexer matches that form without `re.DOTALL`, so a comment written across two
lines is not a comment.
Use `{% comment %}…{% endcomment %}` for anything longer than one line.

## Views

**A form view on a plain, non-model `Form` raises `ImproperlyConfigured` when the page renders.**
It fails at render, not at redirect. `MVPFormView` carries the model-aware page-class and
breadcrumb machinery, and building that context resolves a model. A plain `django.forms.Form`
offers none, so `get_model_class()` runs out of places to look and raises before any HTML
is produced. The message names `model`, `queryset`, a `ModelForm` `form_class` and
`get_model_class()`.
Give the view a `ModelForm`, or override `get_model_class()` to return whichever model the
page belongs to.

**A form view raises `ImproperlyConfigured` after a valid POST.**
Nothing produced a redirect target: no validated `?next=`, and no `success_url`.
Set `success_url`. On `MVPFormView` it must be a literal path or a `reverse_lazy()` — the
CRUD shorthands `list`, `detail`, `create`, `update` and `delete` are resolved for
`success_url` only on the model form views, and a shorthand set here is used verbatim as a
relative path.

**A CRUD link raises `NoReverseMatch`.**
`show_<action>_action` draws the link and the directory then reverses
`{model_name}-<action>` from `MVP_CONFIG["view_names"]`. A shown action whose route is not
registered raises rather than quietly dropping the link, so the misconfiguration surfaces.
Register the route under the configured name, drop the action from `directory`, leave its
flag off, or return `None` from `get_url_kwargs()` for it.

## Integrations

**Importing an integration raises `ImproperlyConfigured` naming a package.**
The third-party dependency is not installed. Integrations are guarded modules, not extras,
so nothing pulls it in for you.
Run the `pip install` command in the message.

**Importing `mvp.views.htmx` raises `ImportError`.**
The htmx mixins are not guarded — they import `django_htmx` directly.
`pip install django-htmx`, and add `django_htmx.middleware.HtmxMiddleware` to
`MIDDLEWARE`. `HtmxFormMixin` reads `request.htmx`, which only that middleware sets.
`HtmxMixin` does not, so it works without the middleware.

**A table view raises `ImproperlyConfigured` at construction.**
It declares `order_by`, which a table view must not — the table already sorts through its
own column headers.
Move the ordering to the table class, as its own `order_by` or `Meta.order_by`.

**`min_height` on `<c-addons.django-table>` has no effect.**
The attribute was removed. The component is now the scroll region of the full-screen
layout and takes its height from the page.
Drop the attribute and mark the page `fill`.

**A list of action names prints next to the breadcrumbs.**
A context key called `actions` was added by a view. `<c-toolbar>` and `<c-page.title>`
expose a slot of that name, and a Cotton slot falls through to the context variable when
the caller fills no slot, so the list renders its own repr.
Name the context key something else — the table view uses `table_actions` for exactly
this reason.

**A width class on a table column looks like it did nothing.**
Tables lay out with the browser's default automatic algorithm, which negotiates a column's
width across every cell including the heading. A long heading wins over a `td`-only class.
Name the class on the `th` as well as the `td`.

---

Back to [SKILL.md](../SKILL.md).
