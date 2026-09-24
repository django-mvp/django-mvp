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
truthy, with no separate switch. The one colour it can carry covers the manifest's theme and
background colours, the page's colour tag and the padded image backgrounds. It is only needed
when the default theme is the project's own, or a shipped theme it has recoloured, because the
package cannot read either. The start address is always the site root, and the display is always
standalone. A different worker or different head tags come from overriding
`mvp/pwa/sw.js` or `mvp/pwa/head.html`, not from a setting. This was decided with the
maintainer at the walkthrough, after an earlier draft carried eight keys.

**Why "pwa"**: it is the word the request uses and the word the web platform documentation uses
for the whole set (manifest, worker, install). The glossary entry defines *installable app* as
what a project gets when the block is on.

## R2 — Where the manifest and the worker are served from

A service worker controls only the pages at or below the path it is served from. Serving it from
`/static/…` would limit it to static files. So both are views, in a URLconf the project mounts at
the root of its own URLconf:

```python
urlpatterns = [
    path("", include("mvp.pwa.urls")),
    ...
]
```

- `manifest.webmanifest`, name `mvp-pwa-manifest`, content type `application/manifest+json`.
- `sw.js`, name `mvp-pwa-service-worker`, content type `text/javascript`, `Cache-Control: no-cache`
  so browsers pick up an updated worker promptly.

**Path prefix edge case**: Django's `reverse()` already includes the script prefix, so a site
served under `/app/` serves the worker at `/app/sw.js` and the manifest's `start_url` and `scope`
default to `/app/`. Nothing prefix-specific needs writing. The tests cover it with
`set_script_prefix`.

## R3 — What the application is called

`django.contrib.sites.shortcuts.get_current_site(request).name`. With the sites framework
installed that is the `Site.name`, which is what `base.html`'s `<title>` already reads. Without
it, Django returns a `RequestSite` whose name is the request's host, which is never empty. That
satisfies FR-005's non-empty fallback without a packaged string.

## R4 — Where the theme colours come from

DaisyUI 5 declares each theme's colours as `oklch()` custom properties. A project's own theme is
CSS the server never parses, so the package can only offer a colour for the themes it ships.

**Chosen**: read them from the package's own committed stylesheet,
`mvp/static/css/django-mvp.css`, by package path rather than through staticfiles. Every prebuilt
theme has a `[data-theme=<name>]{…}` block there carrying `--color-base-100:oklch(…)`. All 35
parse with one regular expression; this was checked on the base commit during planning. The
value is converted OKLCH → OKLab → linear sRGB → gamma-encoded sRGB, clamped to the gamut, and
returned as `#rrggbb`. The parse and the conversion live on one class in `mvp/pwa/`
(Article XVII). The parsed table is cached once per process.

- **No new build artifact.** An earlier draft generated a JSON file from `node_modules`. The
  design review showed it duplicated data the committed stylesheet already carries, and it could
  go stale after a daisyUI bump without any test noticing. Reading the stylesheet means the
  colours can never disagree with the CSS the page actually uses.
- **Hex, not oklch**: browsers parse manifest colours differently, and older engines, Apple's
  `theme-color` handling among them, do not understand `oklch`. Hex is safe everywhere.
- **base-100 for both colours**: the header and the page body both sit on `base-100` in the
  shell. The installed window's title bar then matches the header and the launch background
  matches the page.
- **Reference values** (computed independently of the implementation with the published
  OKLab matrices, and matching daisyUI's long-standing hex values for these themes):
  `light` → `#ffffff`, `dark` (`oklch(25.33% .016 252.42)`) → `#1d232a`, `cupcake`
  (`oklch(97.788% .004 56.375)`) → `#faf7f5`.

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

## R7 — Startup warnings

Django system checks, registered from `MvpConfig.ready()`, and run only when
`MVP_CONFIG["pwa"]["enabled"]` is true:

- `mvp.W001`: `reverse("mvp-pwa-service-worker")` fails, or does not resolve to
  `<script prefix>sw.js`. The root include is missing or mounted under a sub-path.
- `mvp.W002`: any of the four images in R5 is missing from the static files finders. The hint
  names `python manage.py mvp_pwa_icons`.

These are the package's first system checks, so there is nothing existing to renumber.

## R8 — The head tags, and leaving projects that don't turn it on untouched

The tags live in one template, `mvp/pwa/head.html`, which a project can override by path
(FR-012). It is not a Cotton component and not an underscore partial, because projects are
expected to override it (ADR 0026). `base.html` includes it from inside `{% block head %}`,
after the favicon links, **on the same line as the existing dark favicon `<link>`**:

```django
            href="{% icon_url "16px" "dark" %}" />{% if mvp_config.pwa.enabled %}{% include "mvp/pwa/head.html" %}{% endif %}
```

A tag on a line of its own leaves a newline and indentation in the output even when the
condition is false. That would break SC-002, which requires the page head to be byte-identical
for a project that doesn't turn the feature on. A golden-file test pins the off-state render
against a copy captured from `main`.

Contents when on:

- `<link rel="manifest" href="{% url 'mvp-pwa-manifest' %}">`
- `<meta name="theme-color" content="…">`, only when a colour resolves
- `<link rel="apple-touch-icon" href="{% static 'brand/pwa/apple-touch-icon.png' %}">`
- `<meta name="apple-mobile-web-app-title" content="…">`
- `<meta name="mobile-web-app-capable" content="yes">`
- a small inline `<script>` that registers the worker when `'serviceWorker' in navigator`. The
  URL is the configured `service_worker` or the reverse of `mvp-pwa-service-worker`, passed
  through `json_script` or `escapejs`.

The resolved values (name, colours, worker URL) come from one function, `mvp.pwa.resolver.resolve(request)`,
which both the manifest view and the head template call, so the two can never disagree. The
template reaches it through a new simple tag in the existing `mvp` template-tag library
(`{% mvp_pwa as pwa %}`). `base.html` already loads that library. The context processor is not
touched, so nothing runs on renders with the feature off.

**When the root include isn't mounted**, `resolve()` catches `NoReverseMatch` and returns no
manifest or worker URL, and `head.html` then omits the manifest link and the registration
script. Pages keep rendering, and `mvp.W001` is how the developer finds out. A setting turned on
without its include must not take every page down.

`apple-mobile-web-app-title` carries the resolved **short name**, the label shown under the
icon.

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
