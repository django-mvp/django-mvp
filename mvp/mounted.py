"""Mount one django-mvp app inside another.

A package built on django-mvp declares itself once, as a :class:`MountedApp`
in its own ``mounted.py``::

    from django.utils.translation import gettext_lazy as _
    from mvp.mounted import MountedApp

    from .menus import LiteratureMenu

    literature = MountedApp(
        name=_("Literature"),
        icon="book",
        menu=LiteratureMenu,
        urls="literature.urls",
        landing="literature:index",
    )

The project that hosts it mounts it with one line in its own ``urls.py``::

    from mvp.mounted import mount

    from literature.mounted import literature

    urlpatterns = [
        mount("literature/", literature),
    ]

Pages served through that mount belong to the app. The package never writes
into the host's menus: the host adds its own entry from the declaration.
See docs/mounted-apps.md.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

from django.core.checks import CheckMessage, Error
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.urls import get_resolver, include
from django.urls.resolvers import ResolverMatch, RoutePattern, URLResolver
from flex_menu import Menu, MenuItem

#: Attribute a bound view carries to say which app it was served for.
VIEW_ATTRIBUTE = "mounted_app"

#: Attribute on a root URL resolver holding the mounts found beneath it.
REGISTRY_ATTRIBUTE = "mounted_apps"


class MountedApp:
    """A django-mvp app that can run inside another django-mvp project.

    Holds the declaration and every behaviour that shares it: binding a view to
    the app when a request is resolved, and looking the app up again from a
    request.

    Args:
        name: What people call the app. Shown in the page title and the host's
            menu entry. Usually a lazy translation.
        icon: The icon name for the host's menu entry.
        menu: The app's own ``flex_menu`` :class:`~flex_menu.Menu`, drawn in
            the sidebar on the app's pages.
        urls: The app's URLs, as a dotted module path or a list of patterns,
            exactly what ``include()`` takes. A module declaring ``app_name``
            is reversed as ``app_name:name`` wherever it is mounted.
        landing: The URL name of the app's first page.
        check: Optional ``callable(request) -> bool`` deciding who may see the
            app. Stored here; a request it refuses is not yet turned away.

    Example::

        literature = MountedApp(
            name=_("Literature"),
            icon="book",
            menu=LiteratureMenu,
            urls="literature.urls",
            landing="literature:index",
        )
    """

    def __init__(
        self,
        name: Any,
        icon: str,
        menu: Menu,
        urls: str | list[Any],
        landing: str,
        check: Callable[[HttpRequest], bool] | None = None,
    ) -> None:
        self.name = name
        self.icon = icon
        self.menu = menu
        self.urls = urls
        self.landing = landing
        self.check = check
        self._bound_views: dict[Callable[..., Any], Callable[..., Any]] = {}

    def __repr__(self) -> str:
        return f"<MountedApp {self.name!s}>"

    def bind(self, view: Callable[..., Any]) -> Callable[..., Any]:
        """Return ``view`` wrapped so the request it serves knows this app.

        The wrapper keeps everything Django and the decorators read off a view
        (``view_class``, ``csrf_exempt``, ``__name__``), stays a coroutine
        function when the view is one, and is made once per view.
        """
        cached = self._bound_views.get(view)
        if cached is not None:
            return cached

        if inspect.iscoroutinefunction(view):

            @functools.wraps(view)
            async def bound(request, *args, **kwargs):
                return await view(request, *args, **kwargs)

        else:

            @functools.wraps(view)
            def bound(request, *args, **kwargs):
                return view(request, *args, **kwargs)

        setattr(bound, VIEW_ATTRIBUTE, self)
        self._bound_views[view] = bound
        return bound

    def menu_item(self, name: str | None = None, **extra_context: Any) -> MenuItem:
        """Return the host's menu entry for this app, to add to its own menus.

        The entry points at the app's landing page and carries the app's name
        and icon as its label and icon. It is current on every page of the app,
        not only the landing page, in whichever menu it is drawn: the sidebar
        or the mobile dock.

        Args:
            name: The entry's name in the menu. Defaults to one made from the
                landing's URL name.
            **extra_context: More display data for the entry, such as ``badge``.
                ``label`` and ``icon`` set here replace the app's.

        Example::

            AppMenu.append(literature.menu_item())
        """
        app = self

        class MountedAppMenuItem(MenuItem):
            """flex_menu processes a copy built from constructor arguments alone,
            so the app is held on this per-app class, which the copy keeps."""

            def match_url(self) -> bool:
                request = self.request
                self.selected = request is not None and (
                    MountedApp.for_request(request) is app
                )
                return self.selected

        return MountedAppMenuItem(
            name=name or app.landing.replace(":", "-"),
            view_name=app.landing,
            extra_context={"label": app.name, "icon": app.icon, **extra_context},
        )

    @classmethod
    def for_request(cls, request: HttpRequest) -> MountedApp | None:
        """Return the app ``request`` was served through, or ``None``.

        Decided from the view Django resolved, never from the path, so a
        language prefix, a sub-path deployment or an app mounted at the root
        cannot mislead it. A page no mount served, such as one an installed app
        adds to the Account Center from its own URLs, belongs to the first
        mounted app in URL order whose menu marks it current. The answer is
        kept on the request.
        """
        try:
            return request._mounted_app  # type: ignore[attr-defined,no-any-return]
        except AttributeError:
            pass
        match = getattr(request, "resolver_match", None)
        app = getattr(getattr(match, "func", None), VIEW_ATTRIBUTE, None)
        if app is None and match is not None:
            # An entry built by menu_item() asks for this request's app from
            # its own match_url(). Answering None first stops that call from
            # walking the menus again.
            request._mounted_app = None  # type: ignore[attr-defined]
            app = cls.claiming_menu(request)
        request._mounted_app = app  # type: ignore[attr-defined]
        return app  # type: ignore[no-any-return]

    @classmethod
    def claiming_menu(cls, request: HttpRequest) -> MountedApp | None:
        """Return the first mounted app whose menu marks ``request`` current."""
        for mount_ in cls.mounts(request):
            # US-3: a main app's menu does not claim pages. Skip it here.
            if mount_.app.menu.process(request).selected:
                return mount_.app
        return None

    @classmethod
    def mounts(cls, request: HttpRequest | None = None) -> list[MountedAppResolver]:
        """Return every mount in the URLconf ``request`` is served from.

        Nothing is recorded when :func:`mount` runs. The mounts are found by
        walking the resolved URLconf and kept on its root resolver, so a
        changed ``ROOT_URLCONF`` or a per-request ``urlconf`` gets its own
        answer with nothing to reset.

        Raises:
            ImproperlyConfigured: The same app is mounted twice, or one is
                mounted inside another.
        """
        root = get_resolver(getattr(request, "urlconf", None))
        found: list[MountedAppResolver] | None = getattr(root, REGISTRY_ATTRIBUTE, None)
        if found is None:
            found = cls.scan(root)
            setattr(root, REGISTRY_ATTRIBUTE, found)
        return list(found)

    @classmethod
    def scan(
        cls,
        resolver: URLResolver,
        inside: MountedApp | None = None,
        found: list[MountedAppResolver] | None = None,
    ) -> list[MountedAppResolver]:
        """Walk ``resolver``'s patterns for mounts, refusing the two bad shapes.

        ``inside`` is the app whose patterns are being walked, and ``found``
        the mounts met so far. Callers leave both out.
        """
        found = [] if found is None else found
        for pattern in resolver.url_patterns:
            if not isinstance(pattern, URLResolver):
                continue
            if not isinstance(pattern, MountedAppResolver):
                cls.scan(pattern, inside, found)
                continue
            if inside is not None:
                raise ImproperlyConfigured(
                    f'The app "{pattern.app.name}" is mounted inside the app '
                    f'"{inside.name}". A mounted app cannot contain another one.'
                )
            if any(mount.app is pattern.app for mount in found):
                raise ImproperlyConfigured(
                    f'The app "{pattern.app.name}" is mounted more than once. '
                    "Mount each app in one place."
                )
            found.append(pattern)
            cls.scan(pattern, pattern.app, found)
        return found


class MountedAppResolver(URLResolver):
    """A URL resolver that marks the views it resolves with its app.

    ``path()`` cannot return a subclass, and no other hook sees the matched
    view with a request in hand, so :func:`mount` builds this instead.
    """

    def __init__(
        self, *args: Any, app: MountedApp, main: bool = False, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.app = app
        self.main = main

    def resolve(self, path: str) -> ResolverMatch:
        match = super().resolve(path)
        # ResolverMatch reads its view name and function path once, in its
        # constructor, so swapping the callable afterwards leaves both intact.
        match.func = self.app.bind(match.func)
        return match


def mount(route: str, app: MountedApp, main: bool = False) -> MountedAppResolver:
    """Mount ``app`` in a URLconf, the way ``path(route, include(...))`` would.

    Args:
        route: The prefix the app's pages live under, as ``path()`` takes it.
        app: The declaration to mount.
        main: Accepted and stored. It has no behaviour yet.

    Example::

        urlpatterns = [
            mount("literature/", literature),
        ]
    """
    urlconf_module, app_name, namespace = include(app.urls)
    return MountedAppResolver(
        RoutePattern(route, is_endpoint=False),
        urlconf_module,
        None,
        app_name=app_name,
        namespace=namespace,
        app=app,
        main=main,
    )


def check_mounted_apps(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """System check: refuse a bad set of mounts when the project starts."""
    try:
        MountedApp.mounts()
    except ImproperlyConfigured as error:
        return [Error(str(error), id="mvp.E001")]
    return []
