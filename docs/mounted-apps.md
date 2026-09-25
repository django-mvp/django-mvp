# Mounted apps

A package built on django-mvp can run inside another django-mvp project without changing its
code. The package declares itself once as a **mounted app**. The project that hosts it, the
**host project**, mounts it with one line in its own `urls.py` and adds its own menu entry for
it. On the app's pages the sidebar swaps to the app's own menu under a "Back to" link, and the
browser tab names the app. Every other page renders exactly as before.

The examples below use a small library app. The demo project ships the same thing in
`demo/library/`, mounted at `library/`: open `/library/` to see the sidebar, the back link and
the tab title, and look at the demo's own sidebar for the host's entry.

## Declaring an app

The package writes one `MountedApp` in a module of its own, usually `mounted.py`:

```python
# library/mounted.py
from django.utils.translation import gettext_lazy as _

from mvp.mounted import MountedApp

from .menus import LibraryMenu

library = MountedApp(
    name=_("Library"),
    icon="book",
    menu=LibraryMenu,
    urls="library.urls",
    landing="library:catalogue",
)
```

| Argument | What it is |
| --- | --- |
| `name` | What people call the app. Shown in the page title and on the host's menu entry. Use a lazy translation. |
| `icon` | An [icon name](icons.md) for the host's menu entry. |
| `menu` | The app's own [flex-menus](navigation.md) `Menu`. It is drawn in the sidebar on the app's pages. |
| `urls` | The app's URLs: a dotted module path or a list of patterns, exactly what `include()` takes. |
| `landing` | The URL name of the app's first page. The host's menu entry points here. |

The app's URL module sets `app_name`, so its pages reverse as `library:catalogue` wherever the
host mounts it:

```python
# library/urls.py
from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.CatalogueView.as_view(), name="catalogue"),
    path("reading-list/", views.ReadingListView.as_view(), name="reading-list"),
]
```

The app's menu is an ordinary menu, built the way [Navigation](navigation.md) describes:

```python
# library/menus.py
from flex_menu import Menu, MenuItem

LibraryMenu = Menu(
    "LibraryMenu",
    children=[
        MenuItem(
            name="library-catalogue",
            view_name="library:catalogue",
            extra_context={"label": "Catalogue", "icon": "book"},
        ),
        MenuItem(
            name="library-reading-list",
            view_name="library:reading-list",
            extra_context={"label": "Reading list", "icon": "list"},
        ),
    ],
)
```

Declaring an app changes nothing in the host. The package never writes into `AppMenu` or any
other menu of the project it runs in, so the same code is safe to install anywhere.

## Mounting it

The host mounts the app in its own `urls.py`, with `mount()` where it would otherwise write
`path(route, include(...))`:

```python
# host project's urls.py
from django.urls import include, path

from library.mounted import library
from mvp.mounted import mount

urlpatterns = [
    path("", include("mvp.urls")),
    mount("library/", library),
]
```

`mount()` takes the route the app's pages live under. Choose any route: the app's landing page
reverses correctly under whichever prefix the host picks, so `mount("shelf/library/", library)`
works as well.

Which app a page belongs to is decided in two steps, and neither compares the path with a
prefix. A language prefix, a project served under a sub-path, or an app mounted at `""` cannot
confuse them.

1. **A page belongs to the app whose mount served it**, decided from the URL patterns that
   matched the request. Pages of the host that sit beside the app's are not the app's.
2. **If no mount served the page, it belongs to the first mounted app whose menu marks it as
   current**, meaning one of the app's menu entries links to that page. The order is the order
   of the mounts in the URLconf. This is how a page an installed app adds to another app's
   menu, from its own URLs, ends up inside that app: the [Account Center](account-center.md)
   works this way. If two apps' menus both link one page, the first mount wins.

A host page that no mounted app's menu links to belongs to no app.

## Running an app as a site of its own

A package can also be the whole site. The project mounts it at the root with `main=True`:

```python
# host project's urls.py
urlpatterns = [
    path("", include("mvp.urls")),
    mount("", library, main=True),
]
```

The main app's menu is then the sidebar on every page that belongs to no other mounted app,
including the main app's own pages. Those pages draw no back link, and the page title does not
gain the app's name, because the app is the site. Other mounted apps, the Account Center among
them, still swap the sidebar to their own menu under a back link.

`AppMenu` is not drawn in a project with a main app, so the project adds its own entries to the
main app's menu instead. A project has one main app: mounting two with `main=True` is refused
when the project starts, with error `mvp.E001` naming both apps. `main` is an argument of
`mount()` only, so an app the project has not mounted cannot be named main. The same app mounted
without `main=True`, in another project, behaves as described above.

## The Account Center is a mounted app

django-mvp's own [Account Center](account-center.md) is the package's example of a mounted app.
It is declared in `mvp/views/account.py` as `account_center`, with `AccountCenterMenu` as its
menu and `account-center` as its landing, and `mvp.urls` mounts it at `account/`. On its pages
the sidebar draws the area's menu under "Back to *site name*", and the title reads
`Account Center | <site name>`. The landing's URL name stays `account-center`, with no
namespace, so `reverse("account-center")` still gives `/account/`.

Pages other installed apps add to the Account Center are served from those apps' own URLs. They
belong to the Account Center by the second rule above, because `AccountCenterMenu` has an entry
for each of them.

## Adding the entry to the host's menus

The host adds its own entry for the app from the declaration, in whichever menus it wants it:

```python
# host project's menus.py
from mvp.menus import AppMenu, MobileFooterMenu

from library.mounted import library

AppMenu.append(library.menu_item())
MobileFooterMenu.append(library.menu_item(name="library-dock"))
```

`menu_item()` returns an entry that points at the app's landing page, with the app's name as its
label and its icon. It is marked as the current page on **every** page of the app, not only the
landing page, so the dock keeps the app highlighted while a person moves around inside it. It is
not current on the host's own pages.

Pass `name=` to choose the entry's name in the menu, and any other keyword argument to add to its
display data, such as `badge="3"`. Each menu needs its own call, because a menu entry belongs to
one menu at a time.

## What changes inside an app

On a page served through the mount:

- **The sidebar draws the app's menu**, and none of `AppMenu`.
- **A back link opens the sidebar**, reading "Back to *site name*" and going to the same address
  as the sidebar's brand link, the host's home page. The site name is the one the page title
  ends with: `MVP_CONFIG["site_name"]`, then the current site's name. A project with no site name
  gets "Back". In the collapsed icon rail the link shows its icon, and the label is its
  accessible name. If the app's menu has nothing visible for the current person, the back link
  is all the sidebar shows.
- **The title names the app**: `Detail | Library | Example` for a page titled "Detail", and
  `Library | Example` for a page with no title of its own.
- **The mobile dock is unchanged.**
- **Error pages name no app.** A 404 raised inside the app renders the ordinary error page, with
  no app in the title and no sidebar.

A page that passes `menu=` to `<c-app.sidebar>` explicitly keeps that menu with no back link, even
inside an app. Overriding the `app.sidebar` block this way is how a page opts out.

Pages outside every mounted app, and every project that mounts none, render as they always have.

## What is refused

Three shapes are turned away when the project starts, because either would make the choice of
sidebar depend on the order of URL patterns:

- **The same app mounted twice.**
- **An app mounted inside another mounted app's URLs.**
- **Two apps mounted with `main=True`.**

```python
urlpatterns = [
    mount("library/", library),
    mount("shelf/", library),  # refused
]
```

`manage.py check`, `runserver` and `migrate` report the problem as error `mvp.E001`, naming the
app:

```text
The app "Library" is mounted more than once. Mount each app in one place.
```

A nested mount names both apps:

```text
The app "Reading room" is mounted inside the app "Library". A mounted app cannot contain another one.
```

Two main apps name both:

```text
The apps "Library" and "Reading room" are both mounted with main=True. A project has one main app.
```

A server started with checks turned off raises `ImproperlyConfigured` with the same message the
first time it needs to know which apps are mounted.

## Reading the current app in a template

`{% mounted_app as shell %}` resolves the current page's app once. `shell.app` is the app to
name (`None` outside an app, and for the main app), and `shell.menu` is the menu to draw. The shell itself uses it in
`mvp/base.html`, and a project's own base template can do the same:

```html
{% load mvp %}
{% mounted_app as shell %}
{% if shell.app %}You are in {{ shell.app.name }}.{% endif %}
```

`MountedApp.for_request(request)` answers the same question in Python.
