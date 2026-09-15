# Icons

django-mvp renders icons by name, not by raw CSS class, through
[django-easy-icons](https://github.com/SamuelJennings/django-easy-icons):

```html
<c-icon name="search" />
```

This page covers how a name resolves to a glyph, the settings that control it, what
the packaged icon set defines, and how to point the package at a different icon
library.

## How a name resolves

`<c-icon name="search" />` renders `{% icon name defaults=attrs.dict %}` with no
renderer hint. Resolution then runs like this:

1. At startup, easy-icons builds one registry of every icon name across every
   configured renderer. The `default` renderer is processed first, then the rest in
   settings order, so `default` wins any name defined in two places.
2. A name with no hint is looked up in that registry and rendered by whichever
   renderer claimed it.
3. With `EASY_ICONS` unset, the registry is empty and the lookup falls back to
   `default`, which then raises `ImproperlyConfigured` because no such renderer is
   configured.

Put everything under `default`. Every name the package's own components use has to
resolve, and `default` is the only renderer guaranteed to be consulted first.

A name that resolves nowhere is governed by `EASY_ICONS_FAIL_SILENTLY`, which
**defaults to `settings.DEBUG`**. In development the icon renders as an empty
string. In production, with `DEBUG = False`, the same name raises
`IconNotFoundError` and takes the page down with it. Set the flag explicitly if you
want one behaviour in both.

Attributes on the tag are forwarded. `<c-icon name="x" class="text-lg" aria-hidden="true" />`
renders `<i class="bi bi-x-lg text-lg" aria-hidden="true"></i>` — `class` is
appended to the resolved icon classes, and anything else lands on the element.

## Settings

```python
# settings.py
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],   # the packaged Bootstrap Icons pack
        "icons": {
            "dashboard": "bi bi-speedometer2",   # your own names
        },
    },
}
```

Packs merge in list order, last wins. The `icons` block is applied on top of every
pack, so your own entry always overrides a pack's version of the same name.

A key containing commas declares several aliases for one glyph. Surrounding
whitespace is stripped, so format for readability. A logical name therefore cannot
itself contain a comma.

```python
# settings.py
"icons": {
    "dashboard, overview, stats": "bi bi-speedometer2",
}
```

## What the pack defines

`mvp.utils.BS5_ICONS` is the packaged Bootstrap Icons set. Groups are the source's
own ordering; comma-separated names are aliases for one glyph.

| Name(s) | Class |
| --- | --- |
| `add`, `plus`, `create` | `bi bi-plus` |
| `minus`, `dash` | `bi bi-dash` |
| `delete`, `remove`, `trash` | `bi bi-trash` |
| `edit`, `pencil` | `bi bi-pencil` |
| `copy`, `duplicate`, `clone` | `bi bi-copy` |
| `search`, `find` | `bi bi-search` |
| `filter` | `bi bi-funnel` |
| `check`, `tick`, `confirm` | `bi bi-check-lg` |
| `x`, `close`, `cancel` | `bi bi-x-lg` |
| `share` | `bi bi-share` |
| `copy-link`, `link` | `bi bi-link-45deg` |
| `login` | `bi bi-box-arrow-in-right` |
| `logout` | `bi bi-box-arrow-right` |
| `save` | `bi bi-save2` |
| `print` | `bi bi-printer` |
| `view`, `preview`, `eye` | `bi bi-eye` |
| `hide`, `eye-slash` | `bi bi-eye-slash` |
| `import`, `upload` | `bi bi-upload` |
| `export`, `download` | `bi bi-download` |
| `refresh`, `reload`, `sync` | `bi bi-arrow-clockwise` |
| `undo` | `bi bi-arrow-counterclockwise` |
| `archive` | `bi bi-archive` |
| `drag`, `move`, `grip` | `bi bi-grip-vertical` |
| `home`, `house` | `bi bi-house` |
| `menu` | `bi bi-list` |
| `account_center` | `bi bi-person-gear` |
| `overview` | `bi bi-grid` |
| `navbar` | `bi bi-window` |
| `table` | `bi bi-table` |
| `sidebar-left` | `bi bi-layout-sidebar` |
| `sidebar-right` | `bi bi-layout-sidebar-reverse` |
| `maximize` | `bi bi-arrows-fullscreen` |
| `minimize` | `bi bi-arrows-angle-contract` |
| `arrow-right` | `bi bi-arrow-right` |
| `arrow-left` | `bi bi-arrow-left` |
| `chevron-up` | `bi bi-chevron-up` |
| `chevron-down` | `bi bi-chevron-down` |
| `chevron-left` | `bi bi-chevron-left` |
| `chevron-right` | `bi bi-chevron-right` |
| `expand`, `chevron-expand` | `bi bi-chevron-expand` |
| `collapse`, `chevron-contract` | `bi bi-chevron-contract` |
| `grid-view`, `grid` | `bi bi-grid-3x3-gap` |
| `list-view` | `bi bi-view-list` |
| `more`, `options`, `kebab` | `bi bi-three-dots-vertical` |
| `external-link` | `bi bi-box-arrow-up-right` |
| `sort` | `bi bi-sort-down` |
| `sort-asc` | `bi bi-arrow-up-short` |
| `sort-desc` | `bi bi-arrow-down-short` |
| `person`, `user`, `account` | `bi bi-person` |
| `people`, `users` | `bi bi-people` |
| `settings`, `gear`, `cog`, `gears` | `bi bi-gear` |
| `theme.auto` | `bi bi-circle-half` |
| `theme.dark` | `bi bi-moon-stars-fill` |
| `theme.light` | `bi bi-sun` |
| `email`, `envelope` | `bi bi-envelope` |
| `phone`, `telephone` | `bi bi-telephone` |
| `chat`, `message`, `comment` | `bi bi-chat-dots` |
| `notification`, `bell` | `bi bi-bell` |
| `attachment`, `paperclip` | `bi bi-paperclip` |
| `calendar`, `date` | `bi bi-calendar` |
| `clock`, `time` | `bi bi-clock` |
| `location`, `map`, `map-pin` | `bi bi-geo-alt` |
| `document`, `file` | `bi bi-file-earmark` |
| `folder` | `bi bi-folder` |
| `image`, `photo` | `bi bi-image` |
| `video` | `bi bi-camera-video` |
| `audio`, `music` | `bi bi-music-note-beamed` |
| `pdf` | `bi bi-file-earmark-pdf` |
| `database` | `bi bi-database` |
| `cloud` | `bi bi-cloud` |
| `lock`, `locked` | `bi bi-lock` |
| `unlock`, `unlocked` | `bi bi-unlock` |
| `key`, `password` | `bi bi-key` |
| `github` | `bi bi-github` |
| `facebook` | `bi bi-facebook` |
| `twitter` | `bi bi-twitter-x` |
| `reddit` | `bi bi-reddit` |
| `pinterest` | `bi bi-pinterest` |
| `linkedin` | `bi bi-linkedin` |
| `youtube` | `bi bi-youtube` |
| `instagram` | `bi bi-instagram` |
| `whatsapp` | `bi bi-whatsapp` |
| `telegram` | `bi bi-telegram` |
| `mastodon` | `bi bi-mastodon` |
| `bluesky` | `bi bi-bluesky` |
| `discord` | `bi bi-discord` |
| `slack` | `bi bi-slack` |
| `circle` | `bi bi-circle` |
| `globe` | `bi bi-globe` |
| `life-preserver` | `bi bi-life-preserver` |
| `help`, `question` | `bi bi-question-circle` |
| `star`, `favorite` | `bi bi-star` |
| `bookmark` | `bi bi-bookmark` |
| `info` | `bi bi-info-circle-fill` |
| `success`, `dropdown_check` | `bi bi-check-circle-fill` |
| `warning` | `bi bi-exclamation-triangle-fill` |
| `error` | `bi bi-x-circle-fill` |

The last four are keyed to the alert and badge variant names, so a component can
pass its variant straight through to `<c-icon>` — `<c-alert variant="warning">`
renders the `warning` icon with no `icon` attribute needed.

Browse <https://icons.getbootstrap.com/> for more glyphs. The class is `bi bi-<slug>`.

## Where names are consumed

| Site | Form |
| --- | --- |
| Menu items | `MenuItem(..., extra_context={"icon": "dashboard"})` |
| Component attribute | `<c-button icon="add" />`, `<c-menu.item icon="logout" />` |
| Direct render | `<c-icon name="search" />` |

Anything reaching any of these has to be a registered name, not a raw `bi bi-…`
class.

## An icon isn't showing up

Three different causes produce three different symptoms:

| Symptom | Cause | Fix |
| --- | --- | --- |
| Page crashes with `ImproperlyConfigured` on any icon | `EASY_ICONS` is unset, or has no `default` key | Add the `default` renderer block from [Settings](#settings) above |
| Nothing renders in development; `IconNotFoundError` in production | The name isn't in the registry — check it against the [pack table](#what-the-pack-defines) and your own `icons` block | Register the name, or use one already defined |
| The `<i>` tag is there (inspect the element) but shows an empty box | The webfont didn't load | See [The webfont comes from a CDN](#the-webfont-comes-from-a-cdn) below |

## The webfont comes from a CDN

`mvp/base.html` links the Bootstrap Icons stylesheet from jsDelivr
(`bootstrap-icons@1.13.1`). Offline, air-gapped, or behind a network that blocks the
CDN, **every icon renders as an empty box** even when the name is registered
correctly. The `<i>` element and its classes are correct; the font backing them
never arrives.

That `<link>` sits directly in `{% block head %}`, *outside* `{% block styles %}`.
Two ways to serve the font yourself, with different trade-offs:

```html
<!-- your_app/templates/base.html — additive; the CDN link stays and simply fails offline -->
{% extends "mvp/base.html" %}
{% load static %}

{% block styles %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'vendor/bootstrap-icons.min.css' %}" />
{% endblock styles %}
```

Your copy loads after the CDN link, so it wins whether or not the CDN answers. The
cost is one failed request per page load. Keep `{{ block.super }}` — without it you
also drop the packaged stylesheet and the whole shell loses its styling.

To remove the CDN link outright, override `head` **without** `{{ block.super }}` and
re-declare its contents. `block.super` re-emits the CDN link, so it cannot be used
here, and overriding `head` blindly drops the `<title>`, the viewport and charset
meta tags, the favicon links, `{% block styles %}` and the packaged stylesheet with
it, and the JavaScript bundle. Copy them across from `mvp/base.html` first.

## A different icon set

The `renderer` key names the class and `config` is passed to its constructor. Three
ship with easy-icons:

| Renderer | `config` | `icons` values are |
| --- | --- | --- |
| `easy_icons.renderers.ProviderRenderer` | `tag` (default `"i"`) | Full class strings, e.g. `"bi bi-plus"` |
| `easy_icons.renderers.SvgRenderer` | `svg_dir` (default `"icons"`) | Template filenames under that directory |
| `easy_icons.renderers.SpritesRenderer` | `sprite_url` (required) | Symbol ids in the sprite sheet |

`mvp.utils.BS5_ICONS` holds Bootstrap Icons class strings, so it is only meaningful
under `ProviderRenderer`. If you make something else your `default`, drop the pack
and map every name in the [pack table](#what-the-pack-defines) to your own set —
those are the names the packaged components ask for, and each one has to resolve.

You can also register a second renderer alongside `default`. Because `default` is
consulted first and other renderers only claim names it does not define, a project
can run its own set as `default` and keep the pack under a secondary renderer to
cover the leftovers.
