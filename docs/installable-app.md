# Installable app

A project built on django-mvp can be installed from the browser as an app: it gets its own
window and an icon on the home screen or desktop, and stays out of the tab strip. One setting
turns it on, and the Account Center's URLs, which your project already mounts, then serve the two
files a browser needs and a page telling visitors how to install it.

With the setting off, nothing changes. Pages render exactly as they did before.

## Turning it on

```python
# settings.py
MVP_CONFIG = {
    "pwa": {"theme_color": "#f8f6f2"},
}
```

`theme_color` is required. It is the colour of the launch screen, and of the browser toolbar
until the page has loaded, so match it to the header of your default theme. Any other value that is on, such as `True`, fails when the
manifest is built.

The manifest and the worker are served by `mvp.urls`, the same URLconf that serves the Account
Center. Those two routes exist only while `MVP_CONFIG["pwa"]` is set: with it off, reversing
their names raises `NoReverseMatch`, and the page head carries no install tags. If your project
doesn't mount `mvp.urls` yet:

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("", include("mvp.urls")),
    ...
]
```

The manifest is then at `/manifest.webmanifest` and the worker at `/sw.js`. Every shell page then links a web app manifest, sets the browser's theme
colour and registers a service worker. The manifest and the tags are built from three things:

| Value | Where it comes from |
| --- | --- |
| Name | `MVP_CONFIG["site_name"]` when set, otherwise the current site's name (`Site.name`). Without `django.contrib.sites`, or when no `Site` matches or its name is empty, the request's host. Set `MVP_CONFIG["site_name"]` if the styled error page has to survive a database outage: reading the site name can need the database, and an error page that can't render falls back to the server's bare one. |
| Colour | `MVP_CONFIG["pwa"]["theme_color"]`, used for the manifest's theme and background colours, the `theme-color` tag as the page is served and the background of the padded images. |
| Images | Four PNG files under `brand/pwa/` in your static files (see [The images](#the-images)). |

`MVP_CONFIG["short_name"]` sets the label under the icon, and takes the name when unset. The
application name and short name are top-level settings, listed in [Configuration](configuration.md).
Every other value is fixed: the app opens at the site root (the script prefix included) and
uses the `standalone` display mode.

## The install page

Not every browser offers to install a site, and the ones that do put the option in different
places. `mvp.urls` also serves a page that tells a visitor how to install yours, at `/install/`
under the URL name `mvp-pwa-install`. Like the manifest and the worker, it exists only while
`MVP_CONFIG["pwa"]` is set.

The page's title names the app by its short name (`MVP_CONFIG["short_name"]`, falling back to
the name as in the table above), the label the visitor will find under the icon. The page
carries the steps for every platform: iPhone and iPad, Android, Chrome and Edge on a computer,
Safari on a Mac, and a note that Firefox on a computer can't install apps. Without the bundled
script the page shows all of them. With it:

- An **On this device** card shows the steps for the device and browser the page is open on.
  On a phone, that phone's section is left out of **Other devices** below the card.
- In Chrome and Edge, when the browser offers to install the site, the card shows the app's icon,
  name and host with an **Install** button that opens the browser's own install dialog. If the
  visitor dismisses it, the card falls back to the written steps, because a browser offers the
  dialog only once per page load.
- Once the app is installed while the page is open, the card is replaced by a line saying so.
- Opened inside the installed app, the page shows only a line saying the visitor is using it now.

The page holds back the browser's own install offer only while it is open. On every other page
the browser behaves as it would without django-mvp.

### Linking to it

django-mvp adds no menu entry for the page, so link to it wherever suits your project. A menu
item, for example:

```python
from flex_menu import MenuItem

from mvp.menus import AppMenu

AppMenu.append(
    MenuItem(
        name="install-app",
        view_name="mvp-pwa-install",
        extra_context={"label": "Install this app", "icon": "install"},
    )
)
```

With `MVP_CONFIG["pwa"]` off the name doesn't reverse, and the menu leaves the item out. The
`install` icon is in the packaged icon set (see [Icons](icons.md)).

To change the page, add `mvp/pwa/install.html` to your own templates. Each platform's steps are a
template of their own under `mvp/pwa/install/` (`ios.html`, `android.html`, `chromium.html`,
`safari.html` and `firefox.html`), so one can be replaced without the rest.

## The toolbar colour follows the theme

A browser colours the toolbar around the page from the `theme-color` tag, and an installed app
colours its title bar the same way. The page is served with `pwa.theme_color` in that tag. Once
it has loaded, the bundled script sets the tag to the colour of the application header, which is
what the toolbar sits against, and sets it again whenever the visitor changes theme. A visitor on
your dark theme gets a toolbar that matches the dark header.

The colour is read from the page as it is drawn, so a theme you wrote yourself and a header you
recoloured (see [Theming](theming.md)) are followed without any setting. A header with no
background of its own gives the colour of the page behind it, and so does a page that has no
header, such as the sign-in page.

The manifest and the launch screen can only hold one colour, so they keep `pwa.theme_color` in
every theme. So does the tag where the script does not run.

## Why the worker controls the whole site

A service worker controls only pages at or below the path it is served from, which is why
`mvp.urls` serves the worker at the site root, `/sw.js`. The view also sends a
`Service-Worker-Allowed` header naming the site root (the script prefix, when there is one), and
the page registers the worker with that scope, so it still covers every page if a project mounts
`mvp.urls` somewhere other than the root.

A site served under a script prefix (for example `/app/`) has `/app/` as the manifest's
`start_url` and `scope`, and as the worker's scope.

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
pip install resvg-py        # or: uv add --dev resvg-py
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
| Maskable and Apple icons | 512 px and 180 px, the mark in the central 80% on an opaque background. The background is `pwa.theme_color`. The command stops with an error when `MVP_CONFIG["pwa"]` is not set. |

Run it again whenever the mark changes.

## Python reference

You only need these if you build something of your own on the same values.

- `mvp.utils.reverse_or_none(name)` reverses a URL name, and returns `None` instead of
  raising when the name isn't registered.
- `mvp.pwa.views.manifest`, `mvp.pwa.views.service_worker` and `mvp.pwa.views.InstallView` are
  the three views `mvp.urls` serves, at `manifest.webmanifest`, `sw.js` and `install/`.
- `mvp.utils.site_name(request)` returns the current site's name. When no `Site` matches, or the name is empty, it returns the request's host instead. This is the default application name.
