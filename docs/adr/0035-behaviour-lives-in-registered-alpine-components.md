# ADR 0035 — Behaviour lives in registered Alpine components

**Status:** accepted

## Decision

An Alpine component with real behaviour lives in its own module under `assets/js/`. It is registered with `Alpine.data()` from `assets/js/index.js` before `Alpine.start()`, and it is bundled into `mvp/static/js/django-mvp.js` by `invoke build-js`. A template passes configuration only, for example `x-data="mvpPageSide({ id: 'filters', breakpointRem: 80 })"`.

"Real behaviour" means anything beyond binding a value or toggling a flag: focus management, event listeners on `window` or `document`, media queries, `inert`, timers, or cleanup in `destroy()`.

This applies to the whole package from FS-042 on. `layout.js` and `dropdown.js` already follow it, and `page_side.js` is the first component written to it.

## Why

Behaviour written inline in `x-data` is a string inside a template attribute. No linter or type checker reads it, and it is copied into the page once per use. It can't be imported by a test or shared between components, and a template override can quietly drop half of it. A registered component is ordinary JavaScript in one place, built and shipped once. The template keeps only what differs per use.

## Revisit if

The package stops bundling Alpine, or a project needs to replace one component's behaviour without rebuilding the bundle.
