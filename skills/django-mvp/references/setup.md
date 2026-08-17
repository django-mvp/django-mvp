# Setup — reference

Getting django-mvp working in a fresh Django project: install, settings, error handlers,
first page, verification. It does not cover layout configuration, views, menus or the
Tailwind build. Each of those has its own reference.

## Install

```bash
pip install django-mvp
```

The package pulls in django-cotton, django-flex-menus, django-easy-icons, mergedeep,
django-crispy-forms and crispy-tailwind. All six are plain runtime dependencies, none
optional and none detected at runtime. Form rendering needs crispy on every install.

## INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "your_app",         # your own apps, above "mvp"
    "django_cotton",
    "easy_icons",
    "flex_menu",
    "mvp",
    "crispy_forms",
    "crispy_tailwind",  # must stay below "mvp"
]

SITE_ID = 1
```

Order is load-bearing in two directions. Django's app template loader takes the first copy
of a template name it finds, so your own apps go **above** `mvp`. That is what lets you
replace any packaged template, from `base.html` down to a single component, with a file of
the same name. And `mvp` goes **above** `crispy_tailwind`, because the package ships an
override of crispy-tailwind's help-text template that only wins if it is found first.
Templates in a `TEMPLATES` `DIRS` directory sidestep the question: that loader runs first
regardless. `django.contrib.staticfiles` is required too, because the shell resolves its
stylesheet, its JavaScript bundle and the brand SVGs through `{% static %}`. The auth,
contenttypes, sessions and messages apps back the two contrib context processors below:
the shell renders auth-aware widgets and the message toasts on every page.

## Sites and the site name

The shell prints `request.site.name` in the `<title>` and in the navbar. That attribute is
set by `CurrentSiteMiddleware`, not by the sites app alone, so all three pieces are needed:

```python
# settings.py
MIDDLEWARE = [
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    # ... the rest of your middleware
]
```

Without the middleware nothing raises. The site name renders empty.

## Context processors

```python
# settings.py
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "mvp.context_processors.mvp_config",
            ],
        },
    },
]
```

| Processor | What it provides | What breaks without it |
| --- | --- | --- |
| `django.template.context_processors.request` | `request` in every template | Menu rendering raises `KeyError: 'request'` — flex-menus reads `context["request"]` directly. Site name, active-item highlighting and the auth-aware widgets also go dead. |
| `mvp.context_processors.mvp_config` | `mvp_config`, the merged package config | Every settings-driven knob resolves to nothing: no theme is applied on first paint, the sidebar gets no breakpoint or collapse mode, and the configured navbar/sidebar widget lists render empty. |

`mvp_config` is package defaults deep-merged with your `settings.MVP_CONFIG`, so keys you
do not set keep their defaults. The setting is `MVP_CONFIG`, not `MVP`.

## Form rendering

```python
# settings.py
CRISPY_TEMPLATE_PACK = "tailwind"
CRISPY_ALLOWED_TEMPLATE_PACKS = ["tailwind"]
```

Both settings, plus the `crispy_forms` and `crispy_tailwind` entries in `INSTALLED_APPS`.
Having the distributions installed is not enough: Django resolves `{% load %}`
tag libraries only from registered apps, so without the app entries the packaged form
templates raise `TemplateSyntaxError` on `{% load crispy_forms_tags %}`.

## Menu renderers

```python
# settings.py
FLEX_MENUS = {
    "renderers": {
        "sidebar": "mvp.renderers.SidebarRenderer",
        "dock": "mvp.renderers.MobileFooterNavRenderer",
    },
}
```

Both keys are needed, but nothing reads them at startup. `manage.py check` passes without
them and the failure lands at first render. The sidebar renders its menu with
`renderer="sidebar"` and the mobile dock with `renderer="dock"`, and an unregistered name
raises `ValueError` from flex-menus, so every page that renders the shell fails.
Populating the menus themselves is a separate topic with its own reference.

## Icons

```python
# settings.py
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],
        "icons": {"dashboard": "bi bi-speedometer2"},  # your own names
    },
}
```

A `default` renderer must exist. With `EASY_ICONS` unset, the first icon on the page
raises `ImproperlyConfigured`. Registration, the pack's contents and the webfont have
their own reference.

## Error handlers

Django reads `handler400`, `handler403`, `handler404` and `handler500` **only** from the
module named by `ROOT_URLCONF`. Setting them in an included app's `urls.py` does nothing.

```python
# urls.py — the module named by ROOT_URLCONF
handler400 = "mvp.views.bad_request"
handler403 = "mvp.views.permission_denied"
handler404 = "mvp.views.not_found"
handler500 = "mvp.views.server_error"
```

Each handler renders an unqualified template name — `400.html`, `403.html`, `404.html`,
`500.html`. The packaged copies extend `mvp/error_base.html`, which overrides the whole
`app` block: error pages have **no shell**, no sidebar, no navbar, no dock. To restyle
one, put a template of that name in an app listed above `mvp` and extend the same base:

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

The blocks the shell defines outside `app` — `head`, `styles`, `announcement`, `extra_js` —
are still available on error pages. The `content` and `app.*` blocks are not, because `app`
itself has been replaced.

**500 specifics.** The handler puts `support_email` in the context, taken from
`settings.DEFAULT_FROM_EMAIL`, and the packaged page adds a `mailto:` contact button
whenever that value is truthy. Leaving the setting untouched does not suppress the button:
Django's own global default for `DEFAULT_FROM_EMAIL` is `webmaster@localhost`, so an
untouched project ships a 500 page inviting visitors to mail `webmaster@localhost`. Set it
to your real support address, or to `""` to drop the button. This handler runs while the
request that crashed is already broken, so it must never touch the database. Keep any
override free of queries, including anything that would lazily load a user, a site record
or a menu.

## Your first page

```html
<!-- your_app/templates/dashboard.html -->
{% extends "mvp/base.html" %}

{% block content %}
  <c-container>
    <h1>Hello</h1>
  </c-container>
{% endblock content %}
```

Do not re-compose `<c-app>` in your own page. The sidebar, header, main region, footer and
dock are assembled by the shell, and hand-composing them means every layout setting stops
reaching the page.

The packaged page templates (`page_view.html` and the list, detail, form, delete and table
pages built on it) extend the unqualified `base.html` instead. That name is yours: write
your own and every packaged page renders through it. Write none and the package's default
forwards to `mvp/base.html` and defines nothing else.

## Verify

```bash
python manage.py check
```

Then load a page and walk the list:

- [ ] The shell renders: sidebar, header, content area, footer.
- [ ] The `<title>` and navbar show your site's name (sites app, `SITE_ID`, middleware).
- [ ] Sidebar items appear, each links to a resolving URL, and the current one is highlighted.
- [ ] Every icon draws a glyph, not an empty box.
- [ ] A page with a form renders styled fields rather than raising `TemplateSyntaxError`.
- [ ] Below the `md` breakpoint the dock appears. Below `layout.sidebar.breakpoint`
      (default `lg`) the sidebar becomes an overlay drawer and the header toggle opens it.
- [ ] With `layout.sidebar.collapse` set to `"icons"`, toggling collapses the sidebar to an
      icon rail instead of sliding it away.
- [ ] With `DEBUG = False`, an unknown URL returns the styled 404 rather than Django's
      plain one. With `DEBUG = True` Django serves its own pages for 404 and 500 instead,
      but `handler403` still runs, so a `PermissionDenied` shows the styled 403 either way.

---

Back to [SKILL.md](../SKILL.md).
