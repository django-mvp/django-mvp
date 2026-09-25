# Research — 032 Mounted apps

Each entry records a design choice the plan rests on, the evidence behind it, and what was
rejected.

## R1. The declaration is one class, `MountedApp`, in a new module `mvp/mounted.py`

A package writes:

```python
# literature/mounted.py
from django.utils.translation import gettext_lazy as _
from mvp.mounted import MountedApp

from .menus import LiteratureMenu

literature = MountedApp(
    name=_("Literature"),
    icon="book",
    menu=LiteratureMenu,          # a flex_menu Menu, declared by the package
    urls="literature.urls",       # a dotted module path or a list of patterns
    landing="literature:index",   # a URL name inside those URLs
    check=None,                   # optional callable(request) -> bool (US-4)
)
```

`MountedApp` holds the declaration and every behaviour that shares it: building the host's menu
entry (`menu_item()`), running the check (`allows(request)`), and binding a view to the app when
a request is resolved. The lookup of the current app for a request is a classmethod on the same
class. Article XVII: one subject, one class. No base class, no registry object, no hierarchy.

The module name avoids `apps.py`, which Django owns for `AppConfig`.

## R2. The host mounts with `mount(route, app)`, which returns a URL resolver

```python
# the host's urls.py
from mvp.mounted import mount
from literature.mounted import literature

urlpatterns = [
    ...,
    mount("literature/", literature),
]
```

`mount()` is the thin module-level wrapper Article XVII allows. It builds what `path(route,
include(app.urls))` builds, but as a `MountedAppResolver`, a `URLResolver` subclass that knows
its app. Django's `path()` cannot return a subclass, which is why the host calls `mount()`
instead of `path(..., include(...))`. The namespace works exactly as `include()` sets it: an app
whose URL module declares `app_name` is reversed as `literature:index` wherever it is mounted
(US-1 scenario 7).

**Rejected:** a method on the app (`literature.mount("literature/")`). It reads well but hides
the route in a different position from every other line of a `urls.py`, and a function mirrors
`path(route, view)`.

## R3. A page belongs to an app because its resolver marked the matched view (FR-006)

`MountedAppResolver.resolve()` calls Django's own resolution, then returns the same
`ResolverMatch` with `func` replaced by a thin wrapper around the original view. The wrapper
carries the app as an attribute and runs the app's check before calling the view (R6). Outer
resolvers copy `func` from the inner match unchanged, so `request.resolver_match.func` on the
final request carries the app. `MountedApp.for_request(request)` reads it.

Wrappers are made with `functools.wraps`, so `view_class`, `view_initkwargs`, `csrf_exempt`,
`__name__` and `__module__` survive, and the existing `resolve(...).func.view_class` assertions in
`tests/test_urls.py` keep passing. An async view gets an async wrapper
(`markcoroutinefunction`). One wrapper is cached per original view, so the object is stable
across requests.

**Evidence that the alternatives fail:**

- **Namespaces** (`match.app_names`) cannot identify the Account Center. Its landing page is
  deliberately un-namespaced (`account-center`, FS-028 D2), and adding a namespace would break
  every `reverse("account-center")` already written.
- **Route strings** (`match.route`) start with the language prefix under `i18n_patterns`, which
  changes with the active language, and a mount's route is a prefix of unrelated pages
  (`account/` versus `account/login/`). This is the path-prefix comparison D2 rejected.
- **A set of view objects collected by walking the app's URLs** works, but a module-level
  function view served by both host and app cannot be told apart. The wrapper also gives the
  check (US-4) the one place it needs to run, so one mechanism serves both.
- **Tagging the match with a custom attribute** is lost: every outer `URLResolver.resolve()`
  constructs a fresh `ResolverMatch` from the inner one's fields.
- **`captured_kwargs`/`extra_kwargs`** reach the view as keyword arguments.

## R4. Mounting registers the app, read back from the URL tree (FR-002, FR-014, FR-015, FR-018)

Nothing is written to a global list when `mount()` runs. The registry is the set of
`MountedAppResolver`s found by walking the resolved URLconf, cached as an attribute on the
root `URLResolver` object. `get_resolver()` caches that object per `ROOT_URLCONF` and
`clear_url_caches()` drops it, so the registry follows URLconf changes in tests without a reset
hook of its own.

The walk refuses, with `ImproperlyConfigured` naming the app:

- the same `MountedApp` found twice (FR-014);
- a `MountedAppResolver` inside another one's patterns, naming both (FR-015);
- more than one mount with `main=True` (FR-018).

A system check (`Tags.urls`) runs the walk, so `runserver`, `check` and `migrate` refuse a bad
project when it starts. A server started without checks raises the same error on the first
request that needs the registry.

**Rejected:** a module-level list appended to by `mount()`. The test suite reloads `mvp.urls`
(`tests/conftest.py`) and switches `ROOT_URLCONF` per test, so an import-time list would carry
mounts from one URLconf into the next and report duplicates that are not there.

## R5. The sidebar, back link and title read one resolved value (FR-005, FR-007, FR-008, FR-010)

A template tag, `{% mounted_app as mounted_app %}`, placed once at the top of `mvp/base.html`,
resolves the current request's app. The shell reads that one value:

- `<c-app.sidebar>` draws the app's menu and a "Back to <site name>" link, which goes to the
  sidebar's own `brand_url`, the host's home page (FR-007).
- The page title renders `<page title> | <app name> | <site name>` through a `{% filter %}` around
  the existing `title` block. A filter sees the block's rendered text, so an empty block becomes
  `<app name> | <site name>` rather than ` | <app name> | ...`. With no app the filter returns its
  input unchanged, so FR-010 holds byte for byte.
- `mvp/error_base.html` renders the title with no app segment. The error pages already replace
  the whole shell (`{% block app %}`) and draw no sidebar, so the title is the only place an app
  could leak onto one, including onto the 403 a failed check produces.

**Explicit menus win.** `<c-app.sidebar>` loses its `menu="AppMenu"` default. A page that passes
`menu=` keeps that menu with no back link. One that passes nothing gets the resolved menu.

## R6. The check runs in the wrapper and refuses the way Django does (FR-012, FR-013, D4)

The view wrapper (R3) calls `app.allows(request)` first. On failure, an anonymous visitor is
redirected with `redirect_to_login(request.get_full_path())` and anyone signed in gets
`PermissionDenied`. This is the same branch as `AccessMixin.handle_no_permission`. The host's
menu entry (`menu_item()`) passes the same check to flex_menu as the item's own `check`, so the
entry is absent for the same requests.

**Rejected:** a middleware. It works, but a project would need a second edit to install it,
against FR-002 and SC-001.

## R7. A page an app's menu links to also belongs to it (FR-021, US-2 scenario 3)

The Account Center's contributors serve their pages from their own URLs, not from the Account
Center's mount. `django-accounts-center`'s pages, and the fixture pages in
`tests/testapp_account/`, are found only through entries in `AccountCenterMenu`. So when no mount
claims a request, `for_request()` processes each mounted app's menu and takes the app whose menu
marks an entry as current. flex_menu already decides "current" from
`request.resolver_match.view_name`, so this is still decided from the URLs the page was served
through (FR-006). A host page overriding the landing view ahead of the include, as
`docs/account-center.md` shows, is claimed the same way.

A main app (US-3) is skipped here, because its menu is already the sidebar on every unclaimed
page.

**Rejected:** marking membership in the Account Center's layout template. A template can't hand
a value up to the `<head>` that `mvp/base.html` renders before it, and `django-accounts-center`
does not extend that layout today.

## R8. The main app is a flag on its mount (FR-016 to FR-018)

```python
urlpatterns = [mount("", literature, main=True), path("", include("mvp.urls"))]
```

When no other app claims a request, the sidebar draws the main app's menu, with no back link and
no title segment. On the main app's own pages it behaves the same way. The flag lives on the
mount line, where D1 put everything else about mounting.

FR-018's two refusals: two `main=True` mounts are refused by the walk (R4). "Names an app the
project has not mounted" cannot be written, because the flag only exists on a mount. The
requirement holds by construction and the test proving it is the one proving `main` is a
`mount()` argument and nothing else. (A setting naming the main app would have made the first
case impossible and the second one checkable. Both designs leave one case with nothing to test.
The urls.py one keeps mounting in one place.)

**Rejected:** a standalone project overriding `{% block app.sidebar %}` with its app's menu. The
explicit menu would then win on the Account Center's pages too, which US-3 scenario 3 forbids.

## R9. The Account Center is mounted by `mvp.urls` and loses its second panel (FR-019, FR-020)

The declaration, `account_center`, lives in `mvp/views/account.py` beside the view it lands on.
`mvp/menus.py` stays a module of menus only. `mvp.urls` mounts it with
`mount("account/", account_center)`. Its URLs are the landing page alone, un-namespaced, so
`account-center` still reverses as before. The development sign-in and sign-out pages stay host
pages: a person signing in has no account to navigate.

`mvp/account/base.html` keeps its name and its `account.content` block (FR-021) and becomes a
container around it. The dropdown, the card and the breakpoint plumbing go.

## R10. The demo mounts a small app so the walkthrough has something to open

`demo/library/`: a two-page app declared as a mounted app and mounted at `library/`, with one
entry in the demo's `AppMenu` and the dock. It shows US-1 in the running demo. The Account Center
shows US-2. US-3 and US-4 are proved by tests. A staff-only check on the demo app would hide it
from the regular sign-in account, so the demo app carries none.
