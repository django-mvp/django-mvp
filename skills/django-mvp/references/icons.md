# Icons — reference

How icon names resolve, what the packaged Bootstrap Icons pack contains, and how to
register your own or swap the icon set entirely. It does not cover menus, layout config or
the Tailwind build.

## How a name resolves

`<c-icon name="search" />` renders `{% icon name defaults=attrs.dict %}` from
django-easy-icons, with **no renderer hint**. Resolution then runs like this:

1. At startup, easy-icons builds one registry of every icon name across every configured
   renderer. The `default` renderer is processed first, then the rest in settings order, so
   `default` wins any name defined in two places.
2. A name with no hint is looked up in that registry and rendered by whichever renderer
   claimed it.
3. With `EASY_ICONS` unset the registry is empty and the lookup falls back to `default`,
   which then raises `ImproperlyConfigured` because no such renderer is configured.

In practice: put everything under `default`. Every name the package's own components use
has to resolve, and `default` is the only renderer guaranteed to be consulted first.

A name that resolves nowhere is governed by `EASY_ICONS_FAIL_SILENTLY`, which **defaults to
`settings.DEBUG`**. In development the icon renders as an empty string. In production,
with `DEBUG = False`, the same name raises `IconNotFoundError` and takes the page down
with it. Set the flag explicitly if you want one behaviour in both.

Attributes on the tag are forwarded. `<c-icon name="x" class="text-lg" aria-hidden="true" />`
renders `<i class="bi bi-x-lg text-lg" aria-hidden="true"></i>` — `class` is appended to the
resolved icon classes and anything else lands on the element.

## Settings

```python
# settings.py
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],   # the packaged Bootstrap Icons pack
        "icons": {
            "account_center": "bi bi-person-gear",   # see below — not in the pack
            "dashboard": "bi bi-speedometer2",       # your own names
        },
    },
}
```

Packs merge in list order, last wins. The `icons` block is applied on top of every pack, so
your own entry always overrides a pack's version of the same name.

A key containing commas declares several aliases for one glyph. Surrounding whitespace is
stripped, so format for readability. A logical name therefore cannot itself contain a comma.

```python
# settings.py
"icons": {
    "dashboard, overview, stats": "bi bi-speedometer2",
}
```

## `account_center` is not in the pack

`mvp.utils.BS5_ICONS` covers the names the package's own components use **with one
exception**. `<c-user.sidebar-menu>` renders an "Account Center" row with
`icon="account_center"`, and that name is defined nowhere in the pack or the package.

The row is guarded by `{% url "account-center" %}`, so it only renders in a project that
has a URL of that name. If yours does, and you put `<c-user.sidebar-menu>` in the sidebar,
register the name yourself:

```python
# settings.py
EASY_ICONS = {
    "default": {
        # ...
        "packs": ["mvp.utils.BS5_ICONS"],
        "icons": {"account_center": "bi bi-person-gear"},   # any glyph you like
    },
}
```

Skip it and the consequence depends on `DEBUG`: an invisible gap in development, an
`IconNotFoundError` in production. Neither reaches a project that has not opted in. The
component is not in the packaged sidebar, so the row only renders once you have placed
`<c-user.sidebar-menu>` yourself, the visitor is authenticated, and `account-center`
resolves.

## What the pack defines

Groups are the source's own ordering. Comma-separated names are aliases for one glyph.

| Name(s) | Class |
| --- | --- |
| `add`, `plus`, `create` | `bi bi-plus` |
| `minus`, `dash` | `bi bi-dash` |
| `delete`, `remove`, `trash` | `bi bi-trash` |
| `edit`, `pencil` | `bi bi-pencil` |
| `search`, `find` | `bi bi-search` |
| `filter` | `bi bi-funnel` |
| `check`, `tick` | `bi bi-check-lg` |
| `x`, `close` | `bi bi-x-lg` |
| `share` | `bi bi-share` |
| `copy-link`, `link` | `bi bi-link-45deg` |
| `login` | `bi bi-box-arrow-in-right` |
| `logout` | `bi bi-box-arrow-right` |
| `home`, `house` | `bi bi-house` |
| `menu` | `bi bi-list` |
| `navbar` | `bi bi-window` |
| `table` | `bi bi-table` |
| `sidebar-left` | `bi bi-layout-sidebar` |
| `sidebar-right` | `bi bi-layout-sidebar-reverse` |
| `maximize` | `bi bi-arrows-fullscreen` |
| `minimize` | `bi bi-arrows-angle-contract` |
| `arrow-right` | `bi bi-arrow-right` |
| `arrow-left` | `bi bi-arrow-left` |
| `sort` | `bi bi-sort-down` |
| `sort-asc` | `bi bi-arrow-up-short` |
| `sort-desc` | `bi bi-arrow-down-short` |
| `person`, `user`, `account` | `bi bi-person` |
| `people`, `users` | `bi bi-people` |
| `settings`, `gear`, `cog` | `bi bi-gear` |
| `theme.auto` | `bi bi-circle-half` |
| `theme.dark` | `bi bi-moon-stars-fill` |
| `theme.light` | `bi bi-sun` |
| `github` | `bi bi-github` |
| `facebook` | `bi bi-facebook` |
| `twitter` | `bi bi-twitter-x` |
| `reddit` | `bi bi-reddit` |
| `pinterest` | `bi bi-pinterest` |
| `email`, `envelope` | `bi bi-envelope` |
| `circle` | `bi bi-circle` |
| `globe` | `bi bi-globe` |
| `life-preserver` | `bi bi-life-preserver` |
| `exclamation-circle` | `bi bi-exclamation-circle` |
| `shield-x` | `bi bi-shield-x` |
| `bug` | `bi bi-bug` |
| `info` | `bi bi-info-circle-fill` |
| `success`, `dropdown_check` | `bi bi-check-circle-fill` |
| `warning` | `bi bi-exclamation-triangle-fill` |
| `error` | `bi bi-x-circle-fill` |

The last four are keyed to the alert and badge variant names, so a component can pass its
variant straight through to `<c-icon>`.

Browse <https://icons.getbootstrap.com/> for more glyphs. The class is `bi bi-<slug>`.

## Where names are consumed

| Site | Form |
| --- | --- |
| Menu items | `MenuItem(..., extra_context={"icon": "dashboard"})` |
| Component attribute | `<c-button icon="add" />`, `<c-menu.item icon="logout" />` |
| Direct render | `<c-icon name="search" />` |

Anything reaching any of these has to be a registered name, not a raw `bi bi-…` class.

## The webfont comes from a CDN

`mvp/base.html` links the Bootstrap Icons stylesheet from jsDelivr
(`bootstrap-icons@1.13.1`). Offline, air-gapped, or behind a network that blocks the CDN,
**every icon renders as an empty box** even when the name is registered correctly. The
`<i>` element and its classes are correct. The font backing them never arrives. This
failure looks nothing like an unregistered name, which produces no element at all in
development and an exception in production.

That `<link>` sits directly in `{% block head %}`, *outside* `{% block styles %}`. Two ways
to serve the font yourself, with different trade-offs:

```html
<!-- your_app/templates/base.html — additive; the CDN link stays and simply fails offline -->
{% extends "mvp/base.html" %}
{% load static %}

{% block styles %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'vendor/bootstrap-icons.min.css' %}" />
{% endblock styles %}
```

Your copy loads after the CDN link, so it wins whether or not the CDN answers. The cost is
one failed request per page load. Keep `{{ block.super }}`. Without it you also drop the
packaged stylesheet and the whole shell loses its styling.

To remove the CDN link outright, override `head` **without** `{{ block.super }}` and
re-declare its contents. `block.super` re-emits the CDN link, so it cannot be used here, and
overriding `head` blindly drops the `<title>`, the viewport and charset meta tags, the
favicon links, `{% block styles %}` and the packaged stylesheet with it, the JavaScript
bundle, and the theme-scoped `<style>` block. Copy them across from `mvp/base.html` first.

## A different icon set

The `renderer` key names the class and `config` is passed to its constructor. Three ship
with easy-icons:

| Renderer | `config` | `icons` values are |
| --- | --- | --- |
| `easy_icons.renderers.ProviderRenderer` | `tag` (default `"i"`) | Full class strings, e.g. `"bi bi-plus"` |
| `easy_icons.renderers.SvgRenderer` | `svg_dir` (default `"icons"`) | Template filenames under that directory |
| `easy_icons.renderers.SpritesRenderer` | `sprite_url` (required) | Symbol ids in the sprite sheet |

`mvp.utils.BS5_ICONS` holds Bootstrap Icons class strings, so it is only meaningful under
`ProviderRenderer`. If you make something else your `default`, drop the pack and map every
name in the table above to your own set. Those are the names the packaged components ask
for, and each one has to resolve.

You can also register a second renderer alongside `default`. Because `default` is consulted
first and other renderers only claim names it does not define, a project can run its own set
as `default` and keep the pack under a secondary renderer to cover the leftovers.

---

Back to [SKILL.md](../SKILL.md).
