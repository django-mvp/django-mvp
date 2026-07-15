# Icons (django-easy-icons + `BS5_ICONS`)

django-mvp resolves every icon name through
[django-easy-icons](https://github.com/SamuelJennings/django-easy-icons). `<c-icon>` and
component `icon=` attributes call `{% icon name %}` with **no renderer hint**, so the
`"default"` renderer must resolve every name — both mvp's internal names and yours.

## Minimum config

Include the bundled Bootstrap Icons pack — it registers every name mvp's own components
need — then add your app's icons:

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "packs": ["mvp.utils.BS5_ICONS"],   # ← covers all internal mvp icons
        "icons": {
            # your app icons — logical name → "bi bi-<glyph>"
            "dashboard": "bi bi-speedometer2",
            "invoices": "bi bi-receipt",
        },
    },
}
```

**Do not** hand-list "required mvp icons" — that was the old (pre-pack) approach.
`BS5_ICONS` is the single source; you only add names your own app references.

## Aliases (comma-separated keys)

One entry can register several names for the same glyph. Surrounding whitespace is
stripped, so format for readability:

```python
"icons": {
    "add, plus, create": "bi bi-plus-circle",
    "delete, remove, trash": "bi bi-trash",
    "person, user, account": "bi bi-person",
}
```

Every alias resolves to the same class. `BS5_ICONS` uses this throughout, so `add`/`plus`/
`create`, `delete`/`remove`/`trash`, `person`/`user`/`account`, `settings`/`gear`/`cog`
etc. all work — reach for whichever reads best. (A logical name therefore can't itself
contain a comma.)

## Where icon names are used

- Menu items: `extra_context={"icon": "dashboard"}` (see menu-patterns.md).
- Components: `<c-card icon="…">`, `<c-section icon="…">`, `<c-button icon="…">`,
  `<c-icon name="…">`, `<c-menu.item icon="…">`, etc.

Any name used in a template or menu must be registered (via `BS5_ICONS` or your `"icons"`
block), or it renders as an empty box.

## Finding Bootstrap Icon glyphs

Browse <https://icons.getbootstrap.com/>. The glyph class is `bi bi-<slug>`, e.g.
`bi bi-speedometer2`. Map a logical name to it: `"dashboard": "bi bi-speedometer2"`.

## Multiple renderers

Configure additional renderer keys (e.g. `"fontawesome"`) and pass a hint in templates:

```django
{% icon "github" renderer="fontawesome" %}
```

Without a hint the `"default"` renderer is used — which is why every name mvp resolves
must live under `"default"`.

## Webfont

`mvp/base.html` loads the Bootstrap Icons webfont from a CDN by default. To self-host,
override the `head` block and provide your own `<link>` to the font CSS.
