# Mounted apps

A package built on django-mvp can run inside another django-mvp project without changing its
code. The package declares itself once as a **mounted app**. The project that hosts it, the
**host project**, mounts an instance of it with one line in its own `urls.py`, adjusts it if it
wants to, and adds its own menu entry for it. On the app's pages the sidebar swaps to the app's own menu under a "Back to" link, and the
browser tab names the app. Every other page renders exactly as before.

The examples below use a small library app. The demo project ships the same thing in
`demo/library/`, mounted at `library/`: open `/library/` to see the sidebar, the back link and
the tab title, and look at the demo's own sidebar for the host's entry.

## Declaring an app

The package subclasses `MountedApp` in a module of its own, usually `mounted.py`, sets the
class attributes, and ships one instance for a host to mount:

```python
# library/mounted.py
from django.utils.translation import gettext_lazy as _

from mvp.mounted import MountedApp

from .menus import LibraryMenu


class LibraryApp(MountedApp):
    name = _("Library")
    icon = "book"
    menu = LibraryMenu
    urls = "library.urls"
    landing = "library:catalogue"
```

The package declares the class and nothing else. The host creates the instance it mounts.

| Attribute | What it is |
| --- | --- |
| `name` | What people call the app. Shown in the page title and on the host's menu entry. Use a lazy translation. |
| `icon` | An [icon name](icons.md) for the host's menu entry. |
| `menu` | The app's own [flex-menus](navigation.md) `Menu`. It is drawn in the sidebar on the app's pages. |
| `urls` | The app's URLs: a dotted module path or a list of patterns, exactly what `include()` takes. |
| `landing` | The URL name of the app's first page. The host's menu entry points here. |
| `check` | Who may see the app: `True` (everyone, the default), `False`, or a function of the request. See [Limiting who can reach an app](#limiting-who-can-reach-an-app). |

### Adjusting an instance

The host creates the instance it mounts, in a module of its own so that its URLs and its menus
use the same one. It can change any of these attributes on it by keyword argument, the way
`View.as_view()` takes them. This host shows the library under another name and icon, and the
package's `LibraryApp` is left as it was:

```python
# host project's mounted.py
from django.utils.translation import gettext_lazy as _

from library.mounted import LibraryApp

library = LibraryApp(name=_("Journal"), icon="journal")
```

A keyword must name an attribute the class already defines, including one a subclass adds, and
never a method. Any other keyword raises a `TypeError` naming it. A host that needs more than that, such as its own permission rule,
subclasses the package's class:

```python
class StaffLibraryApp(LibraryApp):
    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_staff
```

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
from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem

LibraryMenu = Menu(
    "LibraryMenu",
    children=[
        MenuItem(
            name="library-catalogue",
            view_name="library:catalogue",
            extra_context={"label": _("Catalogue"), "icon": "book"},
        ),
        MenuItem(
            name="library-reading-list",
            view_name="library:reading-list",
            extra_context={"label": _("Reading list"), "icon": "list"},
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

from mvp.mounted import mount

from .mounted import library

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

`AppMenu` is not drawn in a project with a main app (unless the main app's own check refuses the
request, when `AppMenu` is drawn instead), so the project adds its own entries to the
main app's menu instead. A project has one main app: mounting two with `main=True` is refused
when the project starts, with error `mvp.E001` naming both apps. `main` is an argument of
`mount()` only, so an app the project has not mounted cannot be named main. The same app mounted
without `main=True`, in another project, behaves as described above.

## The Account Center is a mounted app

django-mvp's own [Account Center](account-center.md) is the package's example of a mounted app.
It is declared in `mvp/views/account.py` as the class `AccountCenterApp`, with an instance,
`account_center`, that `mvp.urls` mounts. It uses `AccountCenterMenu` as its
menu and `account-center` as its landing, and `mvp.urls` mounts it at `account/`. On its pages
the sidebar draws the area's menu under "Back to *site name*", and the title reads
`| Account Center | <site name>`. The landing's URL name stays `account-center`, with no
namespace, so `reverse("account-center")` still gives `/account/`.

Pages other installed apps add to the Account Center are served from those apps' own URLs. They
belong to the Account Center by the second rule above, because `AccountCenterMenu` has an entry
for each of them.

## Adding the entry to the host's menus

The host adds its own entry for the app from the instance it mounted, in whichever menus it
wants it:

```python
# host project's menus.py
from mvp.menus import AppMenu, MobileFooterMenu

from .mounted import library

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
  ` | Library | Example` for a page with no title of its own.
- **The mobile dock is unchanged.**
- **Error pages name no app.** A 404 raised inside the app renders the ordinary error page, with
  no app in the title and no sidebar.

A page that passes `menu=` to `<c-app.sidebar>` explicitly keeps that menu with no back link, even
inside an app. Overriding the `app.sidebar` block this way is how a page opts out. An override
that passes no `menu` keeps the swap, because the sidebar reads the current app from the
context by itself.

Pages outside every mounted app, and every project that mounts none, render as they always have.

## Limiting who can reach an app

Set `check` on the class, or on an instance, to `True` (open to everyone, the default), `False`
(no one), or a function that takes the request and says whether that person may see the app. A
plain function set as the class attribute is called with the request alone. This one keeps the
library to staff:

```python
class LibraryApp(MountedApp):
    ...

    def check(request):
        return request.user.is_staff
```

The same on one instance: `LibraryApp(check=lambda request: request.user.is_staff)`. For a rule
a function of the request cannot express, override `has_permission(self, request)`. It is the one
method everything asks, and its default is `bool(check(request))` when `check` is callable and
`bool(check)` otherwise.

Everyone the check excludes loses the app in two ways:

- **The host's menu entry is absent.** `library.menu_item()` is drawn for staff and left out of
  every menu, the sidebar and the dock alike, for anyone else.
- **Its pages are refused**, the way Django's access mixins refuse. An anonymous visitor is sent
  to the sign-in page (`LOGIN_URL`) and returns to the page they asked for. A signed-in person
  the check excludes gets a 403 answered by the project's own `403.html`. It is never a 404.

A refused request shows no app anywhere. The 403 page's title carries no app name, and a
`403.html` that extends `mvp/base.html` draws `AppMenu` in the sidebar, not the app's menu. An
app left at `check = True` is open to everyone, as before.

The check runs before the view, for a synchronous or an asynchronous one. It is called on the
event loop for an asynchronous view, so there it must not query the database, and the user it
reads must already be loaded. Deciding between the sign-in redirect and the 403 reads
`request.user` the same way. A page an app's
menu claims (see above) is claimed only for people the check admits, and the check does not
guard it: only pages served through the mount are refused, so a page the app's menu claims from
other URLs must protect itself. The Account Center has no check.

## What is refused

Two shapes are turned away when the project starts, because each would make the choice of
sidebar depend on the order of URL patterns:

- **An app mounted inside another mounted app's URLs.**
- **Two apps mounted with `main=True`.**

Mounting one app twice is unsupported, not prevented. Nothing checks for it and nothing defines
which of its mounts a page belongs to, so mount each app in one place.

`manage.py check`, `runserver` and `migrate` report the problem as error `mvp.E001`. A nested
mount names both apps:

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

The package's context processor, `mvp.context_processors.mvp_config`, adds two values to every
template context. `mounted_app` is the app to name (false outside an app, and for the main app),
and `mounted_menu` is the menu to draw (false when the page belongs to no app). The sidebar and
the page title read them, and a project's own templates can do the same:

```html
{% if mounted_app %}You are in {{ mounted_app.name }}.{% endif %}
```

Both are lazy, so a page that never reads them does no lookup. They reach the sidebar under
Cotton's context isolation as well, because Cotton builds a request context for each component
and that runs the processor again.

`MountedApp.for_request(request)` answers the same question in Python.
