# Research: Swipe and menu actions on list rows

The full investigation happens at planning. This file holds only what the specification assumes
already works, checked on `main` on 2026-11-22.

## Assumptions checked

| Assumption | Check | Result |
|---|---|---|
| `c-list.row` exists and holds a `c-mvp.dropdown` with a `c-menu` | Rendered `<c-list><c-list.row>…<c-mvp.dropdown>…<c-menu>…` through the test suite's component renderer | Holds: a `ul.list > li.list-row` containing `[data-mvp-dropdown]` and its menu |
| htmx is part of the shipped front end | `assets/js/index.js` imports `htmx.org` into the bundle built to `mvp/static/js/django-mvp.js` | Holds |
| Scripts ship with the package, not from a CDN | Same bundle, built by esbuild from `assets/js/` | Holds: a new gesture module joins that bundle |
| The default icon names include one for the ⋯ trigger | Rendered `c-mvp.dropdown icon="ellipsis"` | Fails: `IconNotFoundError`. FR-029 adds the name, resolved through the configured provider; the package ships no icon files (ADR 0038) |
| The sheet exists for the touch-screen menu | Searched `mvp/templates/cotton/` | Not yet: it is https://github.com/django-mvp/django-mvp/issues/687, a dependency of this feature |
