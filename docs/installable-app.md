# Installable app

A project built on django-mvp can be installed from the browser as an app: it gets its own
window and an icon on the home screen or desktop, and stays out of the tab strip. One setting
turns it on, and one line in the root URLconf serves the two files a browser needs.

With the setting off, nothing changes. Pages render exactly as they did before.

## Turning it on

```python
# settings.py
MVP_CONFIG = {
    "pwa": True,
}
```

Then mount the package's URLs at the **root** of your URLconf:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("", include("mvp.pwa.urls")),
    ...
]
```

Every shell page then links a web app manifest, sets the browser's theme colour and registers a
service worker. The manifest and the tags are built from three things:

| Value | Where it comes from |
| --- | --- |
| Name | `MVP_CONFIG["site_name"]` when set, otherwise the current site's name (`Site.name`). Without `django.contrib.sites`, or when no `Site` matches or its name is empty, the request's host. Set `MVP_CONFIG["site_name"]` if the styled error page has to survive a database outage: reading the site name can need the database, and an error page that can't render falls back to the server's bare one. |
| Colour | The `base-100` colour of the default theme (`MVP_CONFIG["theme"]["default"]`), for a theme the package ships. A theme your project writes has no colour the package can read, so no colour is set. |
| Images | Four PNG files under `brand/pwa/` in your static files (see [The images](#the-images)). |

`MVP_CONFIG["short_name"]` sets the label under the icon, and takes the name when unset. The
application name and short name are top-level settings, listed in [Configuration](configuration.md).
Every other value is fixed: the app opens at the site root (the script prefix included) and
uses the `standalone` display mode.

## Why the include is at the root

A service worker only controls pages at or below the path it is served from. Served from
`/static/`, it would control nothing but static files. So the worker is a view, and it has to
answer at `/sw.js` for every page of the site to be covered.

A site served under a script prefix (for example `/app/`) serves the worker at `/app/sw.js`, and
the manifest's `start_url` and `scope` are `/app/`.

Mounting the include is your project's own act, so the two URLs answer whether or not
`MVP_CONFIG["pwa"]` is on.

## What the packaged worker does

The packaged worker (`mvp/pwa/sw.js`) has an `install` listener and an `activate` listener, and
nothing else. It has no `fetch` listener, so the browser sends every request to the network
exactly as it would without a worker. It stores nothing, so it can never show one visitor a
response meant for another.

It does not make the site work offline. Because it is a template, a project can replace it by
adding `mvp/pwa/sw.js` to its own templates.

## Colours for a theme of your own

The package reads the browser toolbar and launch colours from the default theme, but only for
themes it ships. A theme of your own has no colour the package can read, so the manifest and the
`theme-color` tag carry none until you set one. Give `pwa` a dict with its one key:

```python
MVP_CONFIG = {
    "pwa": {"theme_color": "#f8f6f2"},
}
```

That colour is the manifest's theme and background colour, the `theme-color` tag's content and
the background of the padded images. Match it to your theme's page colour. After changing it, run
`mvp_pwa_icons` again so the padded backgrounds of the images match (see
[Generating the images](#generating-the-images)).

## Replacing the worker or the head

The worker and the head are templates, so a project replaces them by path. Add `mvp/pwa/sw.js`
to your own templates to replace the packaged worker, or `mvp/pwa/head.html` to replace the
manifest link, theme colour, touch icon and registration script in the head. A worker still has to
be served from the site root, for the reason given in
[Why the include is at the root](#why-the-include-is-at-the-root): a worker only controls pages at
or below its own path, so one served from `/static/` would control nothing but static files.

## The images

The manifest and the page head name four files, looked up through Django's static files finders:

| File | Used for |
| --- | --- |
| `brand/pwa/icon-192.png` | The manifest's 192 px icon |
| `brand/pwa/icon-512.png` | The manifest's 512 px icon |
| `brand/pwa/icon-maskable-512.png` | The manifest's maskable icon |
| `brand/pwa/apple-touch-icon.png` | The `apple-touch-icon` link in the page head |

Put them in a directory listed in `STATICFILES_DIRS`, or in an app's `static/` directory, or
generate them from your brand mark as described next.

## Generating the images

`mvp_pwa_icons` renders all four images from your brand mark:

```bash
pip install resvg-py        # or: poetry add --group dev resvg-py
python manage.py mvp_pwa_icons
```

The renderer is optional. django-mvp does not depend on `resvg-py`, so install it wherever you run
the command. Without it the command stops and names the package.

The command asks nothing, so it runs in a build pipeline:

```bash
python manage.py mvp_pwa_icons
python manage.py collectstatic --noinput
```

**Run it before `collectstatic`.** `collectstatic` copies what exists at that moment, so images
generated afterwards are not served. With a manifest static files storage (for example
`ManifestStaticFilesStorage`) the consequence is worse than a missing icon: the page head names
the images through the static tag, and a file that is not in the manifest makes that tag raise, so
pages fail to render.

| Detail | Behaviour |
| --- | --- |
| Source | `brand/icon.svg`, found through the static files finders. The command reads this file whatever the configured icon resolver is. `brand/icon_dark.svg` is never used. |
| Package mark | When the file found is the one shipped inside django-mvp, the command says so. Put your own `brand/icon.svg` in your static files to use it instead. |
| Destination | `--output-dir` if given, otherwise the first entry of `STATICFILES_DIRS` that has no prefix. A `(prefix, path)` entry is skipped, because its files are served under the prefix, where the manifest doesn't look. With no usable entry, the command stops and asks for `--output-dir`. Files go in `<directory>/brand/pwa/`, which is created if missing. Existing images are overwritten. |
| Proportions | A mark that is not square is centred, never stretched. |
| Plain icons | 192 px and 512 px, the mark filling the square on a transparent background. |
| Maskable and Apple icons | 512 px and 180 px, the mark in the central 80% on an opaque background. The background is `pwa.theme_color`, else the default theme's colour, else white. |

Run it again whenever the mark changes.

## The startup warning

When `MVP_CONFIG["pwa"]` is on, Django's system checks report an include that is missing or in
the wrong place. The check doesn't run with the feature off. Missing images aren't reported,
because generating them is a deployment step and development doesn't need them.

| Id | Meaning | Fix |
| --- | --- | --- |
| `mvp.W001` | `mvp.pwa.urls` is not included, or is included somewhere other than the root. | Add `path("", include("mvp.pwa.urls"))` to the root URLconf. |

A page keeps rendering when the include is missing. The head then carries no manifest link,
and `mvp.W001` tells you why. It also carries no registration script.

## Python reference

You only need these if you override `mvp/pwa/head.html` or build something of your own on the
same values.

- `mvp.pwa.resolver.resolve(request)` returns a dictionary with every value the manifest and the
  page head use. The keys are:
  - `name`, `short_name`, `start_url` and `scope`
  - `theme_color`, which is `None` when no colour can be resolved
  - `manifest_url`, which is `None` when `mvp.pwa.urls` is not mounted
  - `worker_url`, which is `None` when `mvp.pwa.urls` is not mounted
  - `icon_192`, `icon_512`, `icon_maskable_512` and `apple_touch_icon`, the static URLs of the
    four images

  In a template, `{% mvp_pwa as pwa %}` from the `mvp` tag library gives you the same
  dictionary.
- `mvp.utils.reverse_or_none(name)` reverses a URL name, and returns `None` instead of
  raising when the name isn't registered. The page head and the startup warning both use it
  to find out whether the root include is mounted.
- `mvp.pwa.colors.ThemeColors.for_theme(name)` returns the `#rrggbb` background colour of one of
  the daisyUI themes that ship with the package, or `None` for any other name. It reads the
  colour from the package's own stylesheet, so a shipped theme you have recoloured in your own
  CSS still returns daisyUI's original. Set `theme_color` for that case.
- `mvp.pwa.views.manifest` and `mvp.pwa.views.service_worker` are the two views `mvp.pwa.urls`
  mounts, at `manifest.webmanifest` and `sw.js`.
- `mvp.utils.site_name(request)` returns the current site's name. When no `Site` matches, or the name is empty, it returns the request's host instead. This is the default application name.
- `mvp.pwa.resolver.InstallableApp` reads `MVP_CONFIG["pwa"]`. `InstallableApp.enabled()` is true
  when the setting is truthy. `InstallableApp.theme_color()` returns the configured
  `theme_color`, or the default theme's colour when the package ships that theme, or `None`.
