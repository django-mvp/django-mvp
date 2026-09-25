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

from django.http import HttpRequest
from django.urls import include
from django.urls.resolvers import ResolverMatch, RoutePattern, URLResolver
from flex_menu import Menu

#: Attribute a bound view carries to say which app it was served for.
VIEW_ATTRIBUTE = "mounted_app"


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
        bound = self._bound_views.get(view)
        if bound is None:
            bound = self._bound_views[view] = self._wrap(view)
        return bound

    def _wrap(self, view: Callable[..., Any]) -> Callable[..., Any]:
        wrapper: Callable[..., Any]
        if inspect.iscoroutinefunction(view):

            @functools.wraps(view)
            async def wrapper(request, *args, **kwargs):
                return await view(request, *args, **kwargs)

        else:

            @functools.wraps(view)
            def wrapper(request, *args, **kwargs):
                return view(request, *args, **kwargs)

        setattr(wrapper, VIEW_ATTRIBUTE, self)
        return wrapper

    @classmethod
    def for_request(cls, request: HttpRequest) -> MountedApp | None:
        """Return the app ``request`` was served through, or ``None``.

        Decided from the view Django resolved, never from the path, so a
        language prefix, a sub-path deployment or an app mounted at the root
        cannot mislead it. The answer is kept on the request.
        """
        try:
            return request._mounted_app  # type: ignore[attr-defined,no-any-return]
        except AttributeError:
            pass
        match = getattr(request, "resolver_match", None)
        app = getattr(getattr(match, "func", None), VIEW_ATTRIBUTE, None)
        request._mounted_app = app  # type: ignore[attr-defined]
        return app  # type: ignore[no-any-return]


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
