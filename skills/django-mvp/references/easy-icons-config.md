# EASY_ICONS Full Configuration Reference

Copy this into `settings/common.py` (or equivalent settings file).

The `"default"` renderer must have Bootstrap Icons because django-mvp's `<c-icon name="..." />`
calls `{% icon name %}` with no renderer hint, so it falls back to the default renderer.

## Full Block

```python
EASY_ICONS = {
    "default": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "icons": {
            # ── django-mvp internal icons (REQUIRED — do not remove) ──────────
            "chevron_right": "bi bi-chevron-right",
            "chevron_down": "bi bi-chevron-down",
            "theme_light": "bi bi-sun",
            "theme_dark": "bi bi-moon",
            "theme_auto": "bi bi-circle-half",
            "dropdown_check": "bi bi-check2",
            "search": "bi bi-search",
            "check": "bi bi-check",
            "circle": "bi bi-circle",
            "person": "bi bi-person",
            # ── App navigation icons (Bootstrap Icons) ────────────────────────
            # Add your sidebar/navbar icons here using Bootstrap Icons names.
            # Icon name → CSS class (bi bi-<name>)
            #
            # Examples:
            "speedometer2": "bi bi-speedometer2",   # dashboard
            "plus-circle": "bi bi-plus-circle",     # add/create
            "journal-text": "bi bi-journal-text",   # log/entries
            "exclamation-circle": "bi bi-exclamation-circle",
            "arrow-repeat": "bi bi-arrow-repeat",
            "list-ol": "bi bi-list-ol",
            "graph-up": "bi bi-graph-up",           # analytics
            "house": "bi bi-house",
            "gear": "bi bi-gear",                   # settings
            "pencil": "bi bi-pencil",               # edit
            "trash": "bi bi-trash",                 # delete
            "eye": "bi bi-eye",
            "lock": "bi bi-lock",
            "envelope": "bi bi-envelope",
        },
    },
    # Optional: preserve Font Awesome for app-specific icons
    "fontawesome": {
        "renderer": "easy_icons.renderers.ProviderRenderer",
        "config": {"tag": "i"},
        "icons": {
            "github": "fab fa-github",
            "google": "fab fa-google",
        },
    },
}
```

## Finding Bootstrap Icon Names

Browse <https://icons.getbootstrap.com/> — the icon name to use is the part after `bi-`
in the CSS class. Example: class `bi-speedometer2` → name `"speedometer2"`.

## Declaring Aliases (Comma-Separated Keys)

A single entry can register several names for one icon by separating them with commas.
Surrounding whitespace is stripped, so format for readability:

```python
"icons": {
    "add, plus, create": "bi bi-plus",
    "delete, remove, trash": "bi bi-trash",
    "person, user, account": "bi bi-person",
}
```

Every alias resolves to the same class, which keeps a pack flexible for callers while
grouping synonyms onto single, manageable lines. The bundled `mvp.utils.BS5_ICONS` pack
uses this throughout. (A logical icon name therefore cannot itself contain a comma.)

## Using a Non-Default Renderer in Templates

When you have multiple renderers configured, pass a renderer hint to the template tag:

```django
{% icon "github" renderer="fontawesome" %}
```

Without a renderer hint, the default renderer is used. This is why django-mvp's
`<c-icon>` always resolves to the default renderer.
