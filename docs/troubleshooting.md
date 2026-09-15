# Troubleshooting

Symptom first, then the likely cause and the fix. Each row points at the page that
explains the setting or component in full.

## Menus and navigation

| Symptom | Cause | Fix |
| --- | --- | --- |
| A menu item doesn't show up at all. | The app's `menus.py` was never imported, or the item was built with no `parent` and attached to flex-menus' own root instead of `AppMenu`. | Confirm the app is in `INSTALLED_APPS` and the file is named `menus.py` — its own app config already autodiscovers it — or import it yourself from `AppConfig.ready()`. Run `python manage.py render_menu --name AppMenu` to see the registered tree. |
| The sidebar renders, but the menu inside it is empty. | `FLEX_MENUS["renderers"]["sidebar"]` is unset, so nothing turns the tree into markup. | Register `"sidebar": "mvp.renderers.SidebarRenderer"` and `"dock": "mvp.renderers.MobileFooterNavRenderer"`. |
| The renderer is registered and the menu is *still* empty. | An item whose `view_name` won't reverse is dropped, and a container left with no visible children hides itself too — so one bad URL name can blank a whole section. | Set `FLEX_MENUS["log_url_failures"] = True` to log each reversal failure, then fix the URL names. |
| A page's sidebar item never highlights, even on that page. | Active-state matching is exact string equality between the item's resolved URL and `request.path` — no prefix matching. A detail page's URL differs from its list item's, and an item built with `params` carries a querystring `request.path` never has. | Add a dedicated item for the path, or rely on the parent highlighting instead. |

See [Navigation](navigation.md) for menu classes, `extra_context` keys, and the mobile dock.

## Icons

**Icons render as empty boxes, and devtools shows no icon class at all.** The name isn't
registered — [easy-icons](https://github.com/SamuelJennings/django-easy-icons) resolves
nothing for an unknown name. Include `mvp.utils.BS5_ICONS` in `EASY_ICONS["default"]["packs"]`
and add your own names under `"icons"`. See [Configure icons](getting-started.md#configure-icons).

**Icons render as empty boxes, but devtools shows the correct icon class.** The name
resolved fine; the webfont just isn't reachable. `mvp/base.html` links the Bootstrap Icons
webfont from a CDN inside `{% block head %}`, so offline development, a restrictive
content-security policy, or an air-gapped deployment leaves every glyph missing even though
the class is right. Self-host the font and override the `head` block to point at your copy.

## Layout and configuration

**A layout setting in `MVP_CONFIG` appears to do nothing.** Either it's written under
`settings.MVP`, a key the package doesn't read, or `mvp.context_processors.mvp_config` is
missing from `TEMPLATES["OPTIONS"]["context_processors"]`, so the merged config never
reaches a template. Use `settings.MVP_CONFIG` and register the context processor — the shell
also needs `django.template.context_processors.request`. See [Configuration](configuration.md).

**Widgets configured for the navbar only show up on one screen size.** `layout.navbar.mobile.end`
and `layout.navbar.desktop.end` are separate lists; setting only one leaves the other on the
package default. Set both, or use the flat `layout.navbar.end` key, which the package still
normalizes onto both. See [Navbar widgets](layout.md#navbar-widgets).

**A per-page `breakpoint` or `collapse` override doesn't move the navbar toggle.** The
sidebar drawer, the collapsed rail, and the toggle all read values resolved once at the top
of `{% block app %}`. Setting the attributes on `<c-app>` or `<c-app.sidebar>` styles those
components alone and leaves the toggle on the project default. Resolve them in the block
instead: `{% block app %}{% with breakpoint="xl" collapse="icons" %}{{ block.super }}{% endwith %}{% endblock %}`,
or supply them from view context. See [Overriding the layout per page](layout.md#overriding-the-layout-per-page).

## Templates and styling

**Rewriting `<c-app>…</c-app>` inside a page template.** That composition is the shell's
own job. Extend `mvp/base.html` and fill `{% block content %}` — the sidebar, header,
footer and mobile dock render themselves. See [Your first page](getting-started.md#your-first-page).

**Overriding `{% block head %}` drops the stylesheet, the icon font, or the scripts.** That
block holds the icon webfont link, the nested `styles` block that loads `django-mvp.css`,
and the bundled front-end runtime (Alpine, htmx, the theme switcher) together. Add your own
stylesheet by overriding the inner `styles` block on its own, or call `{{ block.super }}`
inside a `head` override that needs the rest. See [Styling](styling.md).

**A Tailwind class you wrote doesn't apply, and nothing errors.** The prebuilt stylesheet
carries a curated utility list, not all of Tailwind — anything outside it has no rule and
fails silently. The usual causes: a shadow utility beyond the handful that ship as a
by-product (`shadow-sm`, `shadow-lg`, `shadow-xl`, `shadow-none`), a physical inline-axis
class like `pl-4` or `text-left` where only the logical form (`ps-4`, `text-start`) ships, an
arbitrary value such as `w-[37px]`, or a class assembled at render time from string
fragments. Switch to the logical name, pick something from the
[shipped list](utility-classes.md), or build your own stylesheet with
`python manage.py mvp_tailwind` — see [Tier 2](styling.md#tier-2-build-your-own-stylesheet).

**A `{# … #}` comment written across two lines shows up as visible text.** Django's template
lexer matches that form on one line at a time, so a comment spanning a line break isn't
recognised as one. Use `{% comment %}…{% endcomment %}` for anything longer than a line.

## Views

**A form view raises `ImproperlyConfigured` as soon as the page renders.** It's failing at
render, not at redirect. `MVPFormView` builds model-aware page chrome — title, breadcrumbs —
and a plain `django.forms.Form` gives `get_model_class()` nothing to resolve a model from.
The message names `model`, `queryset`, a `ModelForm` `form_class`, and `get_model_class()`.
Give the view a `ModelForm`, or override `get_model_class()` to return whichever model the
page belongs to. See [Plain form pages](views.md#plain-form-pages).

**A form view raises `ImproperlyConfigured` after a valid POST.** Nothing produced a
redirect target: no validated `?next=`, and no `success_url`. Set `success_url` — on
`MVPFormView` it must be a literal path or a `reverse_lazy()`, since the CRUD shorthands
(`list`, `detail`, `create`, `update`, `delete`) only resolve on the model form views. See
[Forms: create / update / generic](views.md#forms-create--update--generic).

**An edit or delete link raises `NoReverseMatch`.** `show_<action>_action` draws the link,
then the view reverses `{model_name}-<action>` from `MVP_CONFIG["view_names"]` — a shown
action whose route isn't registered raises rather than quietly dropping the link, so the
misconfiguration surfaces instead of vanishing. Register the route under the configured
name, drop the action from `directory`, turn its flag off, or return `None` from
`get_url_kwargs()` for that action. See [Detail pages and CRUD URLs](views.md#detail-pages-and-crud-urls).

## Integrations

**Importing an integration raises `ImproperlyConfigured` naming a package.** The third-party
dependency isn't installed — integrations under `mvp.integrations` are guarded modules, not
packaging extras, so nothing pulls the dependency in for you. Run the `pip install` command
the message gives.

**Importing `mvp.views.htmx` raises a plain `ImportError` instead.** The htmx mixins live
outside `mvp.integrations` and aren't guarded — they import `django_htmx` directly. Install
`django-htmx` and add `django_htmx.middleware.HtmxMiddleware` to `MIDDLEWARE`.
`HtmxFormMixin` reads `request.htmx`, which only that middleware sets; `HtmxMixin` doesn't,
so it works without it. See [htmx](integrations.md#htmx).

**A table view raises `ImproperlyConfigured` as soon as its module imports.** It declares
`order_by`, which a table view must not — a table already sorts through its own column
headers, and an ordering on the view too would be a second, competing source. Move the
ordering onto the table class, as its own `order_by` or `Meta.order_by`. See
[django-tables2](integrations.md#django-tables2).

**`min_height` on `<c-addons.django-table>` has no effect.** The attribute was removed; the
component is now the scroll region of the full-screen table layout and takes its height from
the page. Drop the attribute and mark the page `fill` instead. See
[Full-page content](layout.md#full-page-content).

**A list of action names prints next to the breadcrumbs or above a table.** A view put a
context key called `actions` there. `<c-toolbar>` and `<c-page.title>` both expose a slot of
that name, and a Cotton slot falls through to the context variable of the same name when the
caller fills no slot — so the list renders its own repr instead of nothing. Name the context
key something else; nothing this package ships puts one there.

**A width class on a table column looks like it did nothing.** Tables lay out with the
browser's default automatic algorithm, which negotiates a column's width across every cell,
heading included — a long heading wins over a class named only on the `td`. Name the class
on the `th` as well. See [Column behaviour classes](styling.md#column-behaviour-classes).
