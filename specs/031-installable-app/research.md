# Research — 031 Installable app

Each entry records a question the plan had to answer before it could be written, what was
chosen, and the evidence behind it.

## R1 — Where the settings live

**Chosen**: three keys in `mvp/config.py`, all off or empty by default.

```python
"site_name": None,   # the application's name; None → the current site's name, else the host
"short_name": None,  # the label under the icon; None → the resolved name
"pwa": False,        # falsey → off; True → on; {"theme_color": "#…"} → on, with that colour
```

The name and short name sit at the top level because they name the application everywhere: the
page title uses `site_name` too. The feature itself is turned on by `MVP_CONFIG["pwa"]` being
truthy, with no separate switch. The one colour it carries covers the manifest's theme and
background colours, the page's colour tag and the padded image backgrounds. It is required: the
package derives no colour of its own (R4). The start address is always the site root, and the display is always
standalone. A different worker or different head tags come from overriding
`mvp/pwa/sw.js` or `mvp/pwa/head.html`, not from a setting. This was decided with the
maintainer at the walkthrough, after an earlier draft carried eight keys.

**Why "pwa"**: it is the word the request uses and the word the web platform documentation uses
for the whole set (manifest, worker, install). The glossary entry defines *installable app* as
what a project gets when the block is on.

## R2 — Where the manifest and the worker are served from

**Chosen**: from `mvp/urls.py`, the Account Center's URL configuration, which every project
already mounts. There is no second include.

- `manifest.webmanifest`, name `mvp-pwa-manifest`, content type `application/manifest+json`.
- `sw.js`, name `mvp-pwa-service-worker`, content type `text/javascript`, `Cache-Control: no-cache`
  so browsers pick up an updated worker promptly.

A service worker normally controls only the pages at or below the path it is served from, so a
worker at `/account/sw.js` would control only `/account/`. The standard `Service-Worker-Allowed`
response header lifts that limit: the worker view sends `Service-Worker-Allowed: <script prefix>`,
and the page registers the worker with that scope. The worker then controls the whole site
wherever `mvp.urls` is mounted.

**Path prefix edge case**: a site served under `/app/` gets `Service-Worker-Allowed: /app/`, a
registration scope of `/app/` (the request's `SCRIPT_NAME` plus a slash), and a manifest whose
`start_url` and `scope` are `/app/`. The tests cover it with `set_script_prefix`.

## R3 — What the application is called

`django.contrib.sites.shortcuts.get_current_site(request).name`. With the sites framework
installed that is the `Site.name`, which is what `base.html`'s `<title>` already reads. Without
it, Django returns a `RequestSite` whose name is the request's host, which is never empty. That
satisfies FR-005's non-empty fallback without a packaged string.

## R4 — Where the theme colour comes from

**Chosen**: from `MVP_CONFIG["pwa"]["theme_color"]`, and nowhere else. Without it, the colour
entries are omitted and the padded images use white.

A theme is CSS the server never reads. An earlier draft parsed each shipped theme's colour out of
the package's committed stylesheet. It was dropped at the walkthrough: it only worked for a
theme exactly as daisyUI ships it, and returned a wrong colour the moment a project recoloured
that theme in its own CSS. A colour the project states is always right.

## R5 — Rendering the images

**Chosen**: `resvg-py` (0.5.0, Python ≥ 3.10, abi3 wheels for Linux, macOS, Windows and
musl, with no system library needed). It renders an SVG string to PNG bytes in one call:
`resvg_py.svg_to_bytes(svg_string=..., width=..., height=..., background=...)`. Smoke-tested on
this machine during planning: a 10×20 SVG rendered to a valid 64×64 PNG.

Rejected: `cairosvg`, which needs the system Cairo library. That would break "one command in
CI" on Windows and on slim containers.

**Keeping proportions and padding**: the mark is embedded in a square wrapper SVG as a
`data:image/svg+xml;base64` `<image>` with `preserveAspectRatio="xMidYMid meet"`, so a
non-square mark is centred rather than stretched. The wrapper also carries the padding:

| File (under `brand/pwa/`) | Size | Mark occupies | Background |
|---|---|---|---|
| `icon-192.png` | 192 | full square | transparent |
| `icon-512.png` | 512 | full square | transparent |
| `icon-maskable-512.png` | 512 | central 80% (the W3C maskable safe zone) | opaque |
| `apple-touch-icon.png` | 180 | central 80% | opaque (iOS fills transparency with black) |

The opaque background is the resolved `background_color`. If none can be resolved, it is
white.

**Optional dependency**: imported lazily inside the command. Its absence raises `CommandError`
naming `resvg-py`. It goes in the **test** group, plus the `DEP001` ignore list in
`[tool.deptry.per_rule_ignores]` with a one-line reason, following the entries already there.
The runtime dependency set does not change (Article VII).

## R6 — Which brand mark is rendered, and where the images go

- **Source**: `staticfiles.finders.find("brand/icon.svg")`, the same file `mvp.utils.icon_url`
  serves. If the path it returns is inside the package's own static directory, the command says
  it is rendering the package's mark (FR-015).
- **Destination**: `<output-dir>/brand/pwa/`. `<output-dir>` is `--output-dir` when given,
  otherwise the first entry of `STATICFILES_DIRS`. If neither exists, the command raises
  `CommandError` saying to pass `--output-dir`. It never guesses.

## R7 — Startup warning

One Django system check, registered from `MvpConfig.ready()`, and run only when
`MVP_CONFIG["pwa"]` is truthy:

- `mvp.W001`: `reverse("mvp-pwa-service-worker")` fails, so `mvp.urls` is not mounted.

Missing images are deliberately not checked. They are generated at deployment, so a development
checkout never has them, and a warning on every development start would be noise. This was
decided with the maintainer at the walkthrough.

This is the package's first system check, so there is nothing existing to renumber.

## R8 — The head tags, and leaving projects that don't turn it on untouched

The tags live in one template, `mvp/pwa/head.html`, which a project can override by path
(FR-012). It is not a Cotton component and not an underscore partial, because projects are
expected to override it (ADR 0026). `base.html` includes it from inside `{% block head %}`,
after the favicon links, **on the same line as the existing dark favicon `<link>`**:

```django
            href="{% icon_url "16px" "dark" %}" />{% if mvp_config.pwa %}{% include "mvp/pwa/head.html" %}{% endif %}
```

A tag on a line of its own leaves a newline and indentation in the output even when the
condition is false. That would break SC-002, which requires the page head to be byte-identical
for a project that doesn't turn the feature on. A golden-file test pins the off-state render
against a copy captured from `main`.

The template is plain template code, with no custom tag:

- `{% url 'mvp-pwa-manifest' as manifest_url %}` and the same for the worker. The `as` form
  yields nothing rather than raising when `mvp.urls` isn't mounted, so pages keep rendering and
  `mvp.W001` is how the developer finds out.
- The manifest link, only when `manifest_url` resolved.
- `<meta name="theme-color">` from `mvp_config.pwa.theme_color`, only when set.
- The Apple home-screen icon through `{% static %}`.
- `apple-mobile-web-app-title` from
  `{% firstof mvp_config.short_name mvp_config.site_name request.site.name request.get_host %}`,
  the label shown under the icon.
- `mobile-web-app-capable`.
- An inline registration script, only when `worker_url` resolved. The URL and the scope are
  passed through `json_script`.

The manifest view computes the same values in Python (`mvp.pwa.resolver.resolve`), because it
builds JSON rather than rendering a template.

## R9 — The packaged worker

A template, `mvp/pwa/sw.js`, rendered by the worker view:

```js
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
```

It has no `fetch` listener. With none registered, the browser sends every request to the network
exactly as it would without the worker (FR-009, SC-003). Current Chromium no longer needs a fetch
handler before it offers installation. Offline support will add a `fetch` listener to this file
later. It is a template, so a project can override it by path, like every other packaged
template.
