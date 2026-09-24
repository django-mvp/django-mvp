# Decisions — 031 Installable app

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without
escalation. Every question raised while specifying was answered in the spec's own
Clarifications section and integrated into the requirement it affects, so this file starts
empty. Planning adds to it.

## D1 — A missing root include leaves pages rendering, and a warning reports it

**Ambiguous because** the head template reverses the manifest and worker URLs, and a reverse
that fails raises, which would turn every page into an error the moment a project enables the
setting without mounting the include.

**Chosen**: the resolver catches `NoReverseMatch` and the head omits the manifest link and the
registration script. The `mvp.W001` system check is how the developer finds out.

**Why**: the spec's first edge case describes exactly this state as one the developer learns
about at startup, which presumes the pages still work. A warning cannot stop a deploy, so a
raising reverse would take a live site down over a missing line of URL configuration.

**ADR:** none — a local failure mode of this feature, recorded in its docs and tests.

## D2 — Theme colours are read from the committed stylesheet, not a generated file

**Chosen**: parse `--color-base-100` per `[data-theme=…]` block from
`mvp/static/css/django-mvp.css` at first use and cache it per process. See research R4.

**Why**: the stylesheet already carries every shipped theme's colours, so a second generated
file would duplicate it and could drift after a daisyUI upgrade with every test still passing.
Reading the stylesheet keeps one source.

**ADR:** none — an implementation choice inside this feature, reversible without touching any
public surface.

## D3 — The head template gets its values from a template tag, not the context processor

**Chosen**: a `{% mvp_pwa as pwa %}` simple tag in the existing `mvp` library.

**Why**: the context processor runs on every render, including htmx partials and projects with
the feature off. A tag runs only where `head.html` is rendered, which is only when the feature is
on. A project that overrides `head.html` can use the same tag.

**ADR:** none — local to this feature.

## D4 — The packaged worker has no fetch listener

**Chosen**: install and activate listeners only. See research R9.

**Why**: with no fetch listener, the browser sends every request to the network untouched, which
is what FR-009 asks for. Chromium's install criteria no longer require a fetch handler. This
could not be checked against a live browser while planning.

**Revisit if**: a supported browser declines to offer installation because there is no fetch
handler. Then add a listener that returns without calling `respondWith`. That still leaves every
response to the network, so FR-009 holds.

**ADR:** none — the worker is a template a project can override, and this choice is expected to
change when offline support arrives.

## D5 — `resvg_py` is listed under DEP004, not DEP001

**Decision**: the deptry allowance for `resvg_py` sits in `DEP004`, with its reason beside the
existing entries. `DEP001` does not list it.

**Why**: the package is installed (test group), so deptry does not call it missing (DEP001). It
reports the lazy import inside the packaged command as a development dependency imported from
package code (DEP004), the same case as `markdown_it`. The brief named DEP001; that entry made
`poetry run deptry .` fail with DEP004, so the entry went where the rule fires.

**Revisit if**: `resvg-py` becomes a declared optional extra, which would drop the need for an
allowance.

**ADR:** none — local to this feature.

## The `pwa` setting is read through one class

**Decision**: `InstallableApp` in `mvp/pwa/resolver.py` holds `enabled()` and `theme_color()`, and every reader of `MVP_CONFIG["pwa"]` (the resolver, the checks, the icon command) goes through it. Templates test `mvp_config.pwa` directly for truthiness.

**Why**: the setting is a bool or a dict, so reading a key off it directly fails for `True`. One reader keeps the falsey, `True` and dict cases in one place.

**Revisit if**: the block regains a second key.

**ADR:** none — local to this feature.
