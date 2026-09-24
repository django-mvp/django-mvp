# Installable app

A project built on django-mvp can be installed from the browser as an app: it gets its own
window and an icon on the home screen or desktop, and stays out of the tab strip. One setting
turns it on, and one line in the root URLconf serves the two files a browser needs.

With the setting off, nothing changes. Pages render exactly as they did before.

## Turning it on

```python
# settings.py
MVP_CONFIG = {
    "pwa": {"enabled": True},
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
| Name | The current site's name (`Site.name`). Without `django.contrib.sites`, the request's host. |
| Colour | The `base-100` colour of the default theme (`MVP_CONFIG["theme"]["default"]`), for a theme the package ships. A theme your project writes has no colour the package can read, so no colour is set. |
| Images | Four PNG files under `brand/pwa/` in your static files (see [The images](#the-images)). |

The other keys in the `pwa` block, `short_name`, `start_url`, `display`, `theme_color`,
`background_color` and `service_worker`, are listed in [Configuration](configuration.md).

## Why the include is at the root

A service worker only controls pages at or below the path it is served from. Served from
`/static/`, it would control nothing but static files. So the worker is a view, and it has to
answer at `/sw.js` for every page of the site to be covered.

A site served under a script prefix (for example `/app/`) serves the worker at `/app/sw.js`, and
the manifest's `start_url` and `scope` default to `/app/`.

Mounting the include is your project's own act, so the two URLs answer whether or not
`pwa.enabled` is on.

## What the packaged worker does

The packaged worker (`mvp/pwa/sw.js`) has an `install` listener and an `activate` listener, and
nothing else. It has no `fetch` listener, so the browser sends every request to the network
exactly as it would without a worker. It stores nothing, so it can never show one visitor a
response meant for another.

It does not make the site work offline. Because it is a template, a project can replace it by
adding `mvp/pwa/sw.js` to its own templates.

## The images

The manifest and the page head name four files, looked up through Django's static files finders:

| File | Used for |
| --- | --- |
| `brand/pwa/icon-192.png` | The manifest's 192 px icon |
| `brand/pwa/icon-512.png` | The manifest's 512 px icon |
| `brand/pwa/icon-maskable-512.png` | The manifest's maskable icon |
| `brand/pwa/apple-touch-icon.png` | The `apple-touch-icon` link in the page head |

Put them in a directory listed in `STATICFILES_DIRS`, or in an app's `static/` directory.

## The two warnings

When `pwa.enabled` is on, Django's system checks report a setup that is not finished. Neither
runs with the feature off.

| Id | Meaning | Fix |
| --- | --- | --- |
| `mvp.W001` | `mvp.pwa.urls` is not included, or is included somewhere other than the root. | Add `path("", include("mvp.pwa.urls"))` to the root URLconf. |
| `mvp.W002` | One or more of the four images is missing from the static files. Each missing file is named. | Add the files. `python manage.py mvp_pwa_icons` is the command the hint points at for generating them. |

A page keeps rendering when the include is missing: the head then carries no manifest link and no
registration script, and `mvp.W001` tells you why.
