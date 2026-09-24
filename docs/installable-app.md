# Installable app

A project built on django-mvp can be installed from the browser as an app: it gets its own
window and an icon on the home screen or desktop, and stays out of the tab strip. One setting
turns it on, and the Account Center's URLs, which your project already mounts, serve the two files
a browser needs.

With the setting off, nothing changes. Pages render exactly as they did before.

## Turning it on

```python
# settings.py
MVP_CONFIG = {
    "pwa": {"theme_color": "#f8f6f2"},
}
```

`theme_color` is the colour of the browser toolbar and the launch screen. Match it to your
theme's page colour. Without it the manifest and the `theme-color` tag carry no colour, and the
padded images use white. `"pwa": True` turns the feature on with no colour.

The manifest and the worker are served by `mvp.urls`, the same URLconf that serves the Account
Center. If your project doesn't mount it yet:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("account/", include("mvp.urls")),
    ...
]
```

Mount it at any prefix. Every shell page then links a web app manifest, sets the browser's theme
colour and registers a service worker. The manifest and the tags are built from three things:

| Value | Where it comes from |
| --- | --- |
| Name | `MVP_CONFIG["site_name"]` when set, otherwise the current site's name (`Site.name`). Without `django.contrib.sites`, or when no `Site` matches or its name is empty, the request's host. Set `MVP_CONFIG["site_name"]` if the styled error page has to survive a database outage: reading the site name can need the database, and an error page that can't render falls back to the server's bare one. |
| Colour | `MVP_CONFIG["pwa"]["theme_color"]`, used for the manifest's theme and background colours, the `theme-color` tag and the background of the padded images. |
| Images | Four PNG files under `brand/pwa/` in your static files (see [The images](#the-images)). |

`MVP_CONFIG["short_name"]` sets the label under the icon, and takes the name when unset. The
application name and short name are top-level settings, listed in [Configuration](configuration.md).
Every other value is fixed: the app opens at the site root (the script prefix included) and
uses the `standalone` display mode.

## Why the worker controls the whole site

A service worker normally controls only pages at or below the path it is served from, and the
worker here is served from wherever you mounted `mvp.urls`, for example `/account/sw.js`. The
view sends a `Service-Worker-Allowed` header naming the site root (the script prefix, when there
is one), and the page registers the worker with that scope, so it covers every page of the site.

A site served under a script prefix (for example `/app/`) has `/app/` as the manifest's
`start_url` and `scope`, and as the worker's scope.

Mounting `mvp.urls` is your project's own act, so the two URLs answer whether or not
`MVP_CONFIG["pwa"]` is on.

## What the packaged worker does

The packaged worker (`mvp/pwa/sw.js`) has an `install` listener and an `activate` listener, and
nothing else. It has no `fetch` listener, so the browser sends every request to the network
exactly as it would without a worker. It stores nothing, so it can never show one visitor a
response meant for another.

It does not make the site work offline. Because it is a template, a project can replace it by
adding `mvp/pwa/sw.js` to its own templates.

## Replacing the worker or the head

The worker and the head are templates, so a project replaces them by path. Add `mvp/pwa/sw.js`
to your own templates to replace the packaged worker, or `mvp/pwa/head.html` to replace the
manifest link, theme colour, touch icon and registration script in the head. Keep the
`Service-Worker-Allowed` scope in mind: a replacement head has to register the worker with the
scope you want it to control.

After changing `theme_color`, run `mvp_pwa_icons` again so the padded backgrounds of the images
match (see [Generating the images](#generating-the-images)).

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
| Maskable and Apple icons | 512 px and 180 px, the mark in the central 80% on an opaque background. The background is `pwa.theme_color`, else white. |

Run it again whenever the mark changes.

## The startup warning

When `MVP_CONFIG["pwa"]` is on, Django's system checks report a missing include. The check doesn't run with the feature off. Missing images aren't reported,
because generating them is a deployment step and development doesn't need them.

| Id | Meaning | Fix |
| --- | --- | --- |
| `mvp.W001` | `mvp.urls` is not included, so the manifest and the worker have no URL. | Add `path("account/", include("mvp.urls"))` to the root URLconf. |

A page keeps rendering when the include is missing. The head then carries no manifest link,
and `mvp.W001` tells you why. It also carries no registration script.

## Python reference

You only need these if you build something of your own on the same values.

- `mvp.pwa.resolver.resolve(request)` returns a dictionary with every value the manifest uses.
  The keys are:
  - `name`, `short_name`, `start_url` and `scope`
  - `theme_color`, which is `None` when none is configured
  - `icon_192`, `icon_512`, `icon_maskable_512` and `apple_touch_icon`, the static URLs of the
    four images
- `mvp.utils.reverse_or_none(name)` reverses a URL name, and returns `None` instead of
  raising when the name isn't registered. The startup warning uses it to find out whether
  `mvp.urls` is mounted.
- `mvp.pwa.views.manifest` and `mvp.pwa.views.service_worker` are the two views `mvp.urls`
  serves, at `manifest.webmanifest` and `sw.js`.
- `mvp.utils.site_name(request)` returns the current site's name. When no `Site` matches, or the name is empty, it returns the request's host instead. This is the default application name.
- `mvp.pwa.resolver.InstallableApp` reads `MVP_CONFIG["pwa"]`. `InstallableApp.enabled()` is true
  when the setting is truthy. `InstallableApp.theme_color()` returns the configured
  `theme_color`, or `None`.
