# Decisions — 031 Installable app

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without
escalation. Every question raised while specifying was answered in the spec's own
Clarifications section and integrated into the requirement it affects, so this file starts
empty. Planning adds to it.

## D1 — Pages keep rendering when the addresses can't be found

**Ambiguous because** the head needs the manifest and worker URLs, and a reverse that fails
raises. Turning the feature on in a project that doesn't mount `mvp.urls` would then break every
page.

**Chosen**: the head uses `{% url … as … %}`, which yields nothing instead of raising, and omits
the manifest link and the registration script. Nothing warns about it.

**Why**: a raising reverse would take a live site down over a missing line of URL
configuration. A startup check was built for this and removed at the walkthrough as noise.

**ADR:** none — a local failure mode of this feature, recorded in its docs and tests.

## D2 — The theme colour comes from configuration only

**Chosen**: `MVP_CONFIG["pwa"]["theme_color"]`. No colour is derived from any theme. See
research R4.

**Why**: the server never reads a theme's CSS. The package's own copy of a shipped theme is
wrong as soon as a project recolours it, so a derived colour is right only for projects that
never touched their theme. A stated colour is always right. Decided with the maintainer at the
walkthrough.

**ADR:** none — local to this feature.

## D3 — The head template is plain template code

**Chosen**: no custom template tag. The URLs, the name, the colour and the icon are all
expressible with `{% url … as %}`, `{% firstof %}`, `mvp_config` and `{% static %}`. See
research R8.

**Why**: once the colour stopped being derived, nothing in the head needed Python. A tag would
be one more public name to document and keep.

**ADR:** none — local to this feature.

## D6 — The installable-app addresses are part of `mvp.urls`

**Chosen**: `manifest.webmanifest` and `sw.js` are registered in `mvp/urls.py`, and the worker
sends `Service-Worker-Allowed` so it controls the whole site from under that prefix. See research
R2.

**Why**: every project already mounts `mvp.urls` for the Account Center. A second include that
had to sit at the site root was setup a project could get wrong, and the header is the web
platform's own mechanism for exactly this case. Decided with the maintainer at the walkthrough.

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

## D7 — The routes exist only while the feature is on

**Chosen**: `mvp/urls.py` adds `manifest.webmanifest` and `sw.js` only when `MVP_CONFIG["pwa"]`
is set, the same way it adds the sign-in pages only when allauth is absent. The setting is a
colour or nothing, and it is read directly, with no wrapper.

**Why**: a project that hasn't turned the feature on should not serve its files. Decided with the
maintainer at the walkthrough.

**ADR:** none — local to this feature.
