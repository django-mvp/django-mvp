# Getting Started

## Installation

```bash
pip install django-mvp
```

Add the required apps to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "your_app",        # your own apps, above "mvp"
    "django.contrib.sites",
    "django_cotton",   # Cotton template components
    "easy_icons",      # Icon system
    "flex_menu",       # Menu system
    "mvp",             # django-mvp
    "crispy_forms",    # Form rendering
    "crispy_tailwind", # Tailwind template pack for crispy forms
    ...
]
```

### Why the order matters

Django's app template loader walks `INSTALLED_APPS` top to bottom and uses the first
copy of a template name it finds. Two consequences, pulling in opposite directions:

- **Your own apps go above `mvp`.** An app listed earlier wins, so this is what lets you
  replace any template django-mvp ships, from `base.html` down to a single Cotton
  component, by putting a file of the same name in your own app. It is the same rule
  projects already use to override the Django admin's templates.
- **`mvp` goes above `crispy_tailwind`.** django-mvp ships an override of
  crispy-tailwind's help text template, and it only takes effect if `mvp` is found
  first.

So place your apps above `mvp` rather than pushing `mvp` towards the bottom of the list.
Templates in a directory listed under `TEMPLATES` `DIRS` sidestep the question entirely:
that loader runs before any app is consulted, whatever the order.

Add the context processor so layout configuration reaches every template:

```python
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "mvp.context_processors.mvp_config",
            ],
        },
    },
]
```

Without `django.template.context_processors.request`, menu rendering raises `KeyError:
'request'` — the sidebar and dock read `request` from the template context directly.
Without `mvp.context_processors.mvp_config`, every settings-driven option resolves to
nothing: no theme applied on first paint, no sidebar breakpoint, empty navbar widget
lists.

## Sites and the site name

The shell prints `request.site.name` in the page `<title>` and the navbar. That
attribute is set by `CurrentSiteMiddleware`, not by `django.contrib.sites` alone, so add
the middleware and the site ID too:

```python
MIDDLEWARE = [
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    # ... the rest of your middleware
]

SITE_ID = 1
```

Skip either piece and nothing raises — the site name in the title and navbar just
renders empty.

## Configure icons

django-mvp resolves icon names through
[django-easy-icons](https://github.com/SamuelJennings/django-easy-icons). The package
ships a Bootstrap Icons pack (`mvp.utils.BS5_ICONS`) covering every icon its own
components use — include it and add your own names on top:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],
        "icons": {
            # your app's icons
            "dashboard": "bi bi-speedometer2",
            "invoices": "bi bi-receipt",
        },
    },
}
```

`EASY_ICONS` needs a `default` renderer entry — leave the setting unset and the first
icon on the page raises `ImproperlyConfigured`.

The bundled pack registers common icons under several synonyms — `add`, `plus` and
`create` all resolve to the same glyph, as do `delete`/`remove`/`trash`,
`person`/`user`/`account`, `settings`/`gear`/`cog`, and more — so callers can reach for
whichever name reads best. You can do the same in your own `"icons"` block by declaring
comma-separated keys (whitespace is ignored):

```python
"icons": {
    "dashboard, home, overview": "bi bi-speedometer2",
}
```

`mvp/base.html` loads the Bootstrap Icons webfont from a CDN by default; override the
`head` block to self-host it.

## Configure menu renderers

The sidebar and mobile dock render menus through
[django-flex-menus](https://github.com/SamuelJennings/django-flex-menus) — register
django-mvp's renderers in settings:

```python
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
}
```

Neither key is checked at startup — `manage.py check` passes without them, and a page
fails only when it tries to render a menu through an unregistered renderer name.

## Configure form rendering

django-mvp's form pages render through
[django-crispy-forms](https://github.com/django-crispy-forms/django-crispy-forms) with
the Tailwind template pack. Add both settings:

```python
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
CRISPY_TEMPLATE_PACK = "tailwind"
```

Installing the two distributions is necessary but not sufficient on its own: Django
resolves `{% load %}` tag libraries only from apps registered in `INSTALLED_APPS`, so
without the `crispy_forms` and `crispy_tailwind` entries above, `{% load
crispy_forms_tags %}` still raises `TemplateSyntaxError`.

## Your first page

Templates extend `mvp/base.html`, which renders the full app shell (sidebar, navbar,
content area, footer, mobile dock):

```html
{% extends "mvp/base.html" %}

{% block content %}
  <c-container>
    <h1>Hello!</h1>
  </c-container>
{% endblock %}
```

Fill `block content`; don't recompose `<c-app>` in your own template. The sidebar,
header, main region, footer and dock are assembled by the shell, and hand-composing them
means every layout setting stops reaching the page.

The packaged page templates — `page_view.html` and the list, detail, form, delete and
table pages that build on it — extend the unqualified `base.html` instead. That name is
yours to own: write your own `base.html` and every packaged page renders through it.
Write none and django-mvp's default takes over, forwarding to `mvp/base.html` and
defining nothing of its own. Either way the pages render, which also means a reusable
app can extend `page_view.html` without requiring a template from the project
installing it.

For a complete page with title, breadcrumbs and consistent structure, use an MVP view
instead of a bare `TemplateView` — see [Views](views.md):

```python
from mvp.views import MVPTemplateView


class DashboardView(MVPTemplateView):
    template_name = "dashboard.html"
    page_title = "Dashboard"
```

## Add menu items

Create `menus.py` in your app and register it in `AppConfig.ready()` — the sidebar
renders the `AppMenu` automatically. See [Navigation](navigation.md).

```python
# myapp/menus.py
from flex_menu import MenuItem
from mvp.menus import AppMenu

AppMenu.extend([
    MenuItem(name="dashboard", view_name="dashboard",
             extra_context={"label": "Dashboard", "icon": "dashboard"}),
])
```

## Configure the layout

Layout behavior is controlled from settings — no template edits required:

```python
MVP_CONFIG = {
    "layout": {
        "sidebar": {"breakpoint": "lg", "collapse": "offcanvas"},
        "navbar": {"end": ["actions.theme-controller"]},
    },
}
```

See [Layout](layout.md) for every option.

## Error pages

Wire django-mvp's styled error handlers in your root `urls.py` — Django reads
`handler400`, `handler403`, `handler404` and `handler500` only from the module named by
`ROOT_URLCONF`, so setting them in an included app's `urls.py` has no effect:

```python
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

Each handler renders an unqualified template name (`400.html`, `403.html`, `404.html`,
`500.html`). The packaged copies extend `mvp/error_base.html`, which replaces the entire
shell — an error page has no sidebar, navbar or dock. Restyle one by putting a template
of the same name in an app listed above `mvp` and extending the same base:

```html
<!-- your_app/templates/404.html -->
{% extends "mvp/error_base.html" %}
{% block error_code %}404{% endblock %}
{% block heading %}Nothing here.{% endblock %}
{% block description %}That page has moved or never existed.{% endblock %}
```

| Block | Default | Notes |
| --- | --- | --- |
| `title` | `"Error"` in the base, per-code in each page | Rendered inside the shared `<title>`. |
| `error_code` | empty | The large numeral. |
| `heading` | empty | The `<h1>`. |
| `description` | empty | Body text under the heading. |
| `actions` | a "Return to site" button to `/` | Use `{{ block.super }}` to keep it and add your own. |

The 500 page adds a `mailto:` support button whenever `settings.DEFAULT_FROM_EMAIL` is
truthy. Django's own global default for that setting is `webmaster@localhost`, so an
unconfigured project ships a 500 page inviting visitors to mail `webmaster@localhost` —
set it to a real address, or to `""` to drop the button. If you override the 500
template, keep it free of database queries: the handler runs while the request that
crashed is already broken.

With `DEBUG = True`, Django serves its own 404 and 500 pages instead of the ones above;
`handler403` still runs in debug, so a `PermissionDenied` always shows the styled 403.

## Verify

```bash
python manage.py check
```

Then load a page and confirm:

- The shell renders: sidebar, header, content area, footer.
- The `<title>` and navbar show your site's name.
- Sidebar items appear, each links to a resolving URL, and the current one is highlighted.
- Every icon draws a glyph, not an empty box.
- A page with a form renders styled fields rather than raising `TemplateSyntaxError`.
- With `DEBUG = False`, an unknown URL returns the styled 404 rather than Django's own.
