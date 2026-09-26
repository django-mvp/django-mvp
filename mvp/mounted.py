"""Mount one django-mvp app inside another.

A package built on django-mvp declares itself once, as a :class:`MountedApp`
subclass in its own ``mounted.py``::

    from django.utils.translation import gettext_lazy as _
    from mvp.mounted import MountedApp

    from .menus import LiteratureMenu


    class LiteratureApp(MountedApp):
        name = _("Literature")
        icon = "book"
        menu = LiteratureMenu
        urls = "literature.urls"
        landing = "literature:index"

The project that hosts it creates the instance and mounts it with one line in
its own ``urls.py``. It may change the instance first, by keyword argument or
with a subclass of its own::

    from mvp.mounted import mount

    from literature.mounted import LiteratureApp

    literature = LiteratureApp(icon="journal")

    urlpatterns = [
        mount("literature/", literature),
    ]

It builds its menu entry from the same instance: ``literature.menu_item()``.

Pages served through that mount belong to the app. The package never writes
into the host's menus: the host adds its own entry from the declaration.
See docs/mounted-apps.md.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any, NamedTuple

from django.contrib.auth.views import redirect_to_login
from django.core.checks import CheckMessage, Error
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.urls import get_resolver, include
from django.urls.resolvers import ResolverMatch, RoutePattern, URLResolver
from flex_menu import Menu, MenuItem

#: Attribute a bound view carries to say which app it was served for.
VIEW_ATTRIBUTE = "mounted_app"

#: Attribute on a root URL resolver holding the mounts found beneath it.
REGISTRY_ATTRIBUTE = "mounted_apps"


class MountedShell(NamedTuple):
    """What the shell reads about the current page's mounted app.

    ``app`` is the app to name in the page title and the back link. ``menu`` is
    the menu the sidebar draws. Both are ``None`` when the page belongs to no
    app, and the sidebar then falls back to ``AppMenu``. In a project with a
    main app, a page that belongs to no other app draws the main app's menu
    with no ``app``, so no back link and no title segment.
    """

    app: MountedApp | None
    menu: Menu | None


class MountedApp:
    """A django-mvp app that can run inside another django-mvp project.

    A package subclasses it and sets the class attributes below. The host
    mounts an instance, and changes what it likes on that instance by keyword
    argument, in the way ``View.as_view()`` takes them: only an attribute the
    class already defines is accepted, and any other name, or a method's, raises
    ``TypeError``. A host that needs more subclasses the package's class instead.

    The class holds the declaration and every behaviour that shares it: binding
    a view to the app when a request is resolved, and looking the app up again
    from a request.

    Attributes:
        name: What people call the app. Shown in the page title and the host's
            menu entry. Usually a lazy translation.
        icon: The icon name for the host's menu entry.
        menu: The app's own ``flex_menu`` :class:`~flex_menu.Menu`, drawn in
            the sidebar on the app's pages.
        urls: The app's URLs, as a dotted module path or a list of patterns,
            exactly what ``include()`` takes. A module declaring ``app_name``
            is reversed as ``app_name:name`` wherever it is mounted.
        landing: The URL name of the app's first page.
        check: Who may see the app: ``True`` (everyone, the default), ``False``
            (no one), or a ``callable(request) -> bool``. A request it refuses
            gets no menu entry and no app in the page, and its pages send an
            anonymous visitor to the sign-in page and refuse a signed-in person
            as forbidden. A plain function set as the class attribute is called
            with the request alone. Override :meth:`has_permission` for anything
            a callable cannot say. A check must not touch the database from an
            async view.

    Example::

        class LiteratureApp(MountedApp):
            name = _("Literature")
            icon = "book"
            menu = LiteratureMenu
            urls = "literature.urls"
            landing = "literature:index"


        # in the host project
        literature = LiteratureApp(icon="journal", name=_("Journal"))
    """

    name: Any = ""
    icon: str = ""
    menu: Menu = None  # type: ignore[assignment]
    urls: str | list[Any] = []
    landing: str = ""
    check: bool | Callable[[HttpRequest], bool] = True

    #: The names an instance may set by keyword. A subclass that declares an
    #: attribute of its own adds it here.
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        declared = cls.__dict__.get("check")
        if inspect.isfunction(declared):
            # A plain function is the check itself, not a method: reading it
            # off the instance would otherwise pass the app as the request.
            cls.check = staticmethod(declared)  # type: ignore[assignment]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if not self.is_setting(key):
                raise TypeError(
                    f"{type(self).__name__}() received an unexpected keyword "
                    f'argument "{key}". Only an attribute the class already '
                    "defines can be set, and never a method."
                )
            setattr(self, key, value)
        self._bound_views: dict[Callable[..., Any], Callable[..., Any]] = {}

    @classmethod
    def is_setting(cls, key: str) -> bool:
        """Say whether ``key`` names an attribute a keyword may set.

        ``check`` always qualifies, since it may itself be a function. Any other
        attribute qualifies when the class defines it and it is not a method.
        """
        if key == "check":
            return True
        if key.startswith("_") or not hasattr(cls, key):
            return False
        return not inspect.isroutine(inspect.getattr_static(cls, key))

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name!s}>"

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
                refusal = self.refusal(request)
                if refusal is not None:
                    return refusal
                return await view(request, *args, **kwargs)

        else:

            @functools.wraps(view)
            def bound(request, *args, **kwargs):
                refusal = self.refusal(request)
                if refusal is not None:
                    return refusal
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

        def entry_check(request: HttpRequest | None, **kwargs: Any) -> bool:
            return request is None or app.has_permission(request)

        return MountedAppMenuItem(
            name=name or app.landing.replace(":", "-"),
            view_name=app.landing,
            check=entry_check,
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
        if app is not None and not app.has_permission(request):
            # A refused request shows no app anywhere, a project's own 403 page
            # included (decision D15).
            app = None
        request._mounted_app = app  # type: ignore[attr-defined]
        return app  # type: ignore[no-any-return]

    @classmethod
    def shell(cls, request: HttpRequest) -> MountedShell:
        """Return what the shell draws for ``request``: the app to name and the menu.

        A main app is named nowhere. One that refuses the request is not drawn
        either, and the page falls back to ``AppMenu`` (decision D14).
        """
        app = cls.for_request(request)
        main = cls.main(request)
        if main is not None and app in (None, main):
            return MountedShell(
                None, main.menu if main.has_permission(request) else None
            )
        return MountedShell(app, app.menu if app is not None else None)

    @classmethod
    def claiming_menu(cls, request: HttpRequest) -> MountedApp | None:
        """Return the first mounted app whose menu marks ``request`` current."""
        for mount_ in cls.mounts(request):
            if mount_.main:
                # The main app's menu draws on every unclaimed page already;
                # letting it claim them would give those pages a back link.
                continue
            if not mount_.app.has_permission(request):
                continue
            if mount_.app.menu.process(request).selected:
                return mount_.app
        return None

    @classmethod
    def main(cls, request: HttpRequest | None = None) -> MountedApp | None:
        """Return the app mounted with ``main=True``, or ``None``.

        Looked up in the URLconf ``request`` is served from, the same walk as
        :meth:`mounts`.
        """
        for mount_ in cls.mounts(request):
            if mount_.main:
                return mount_.app
        return None

    def has_permission(self, request: HttpRequest) -> bool:
        """Say whether ``request`` may see this app.

        A callable ``check`` is called with the request, and anything else is
        taken as the answer itself, so an app left at ``check = True`` permits
        everyone. This is the one place the rule lives: the view wrapper, the
        host's menu entry, the lookup of a request's app and the main app's menu
        all ask it. Override it to decide from more than the request alone,
        calling ``super()`` to keep the check.
        """
        check = self.check
        if callable(check):
            return bool(check(request))
        return bool(check)

    def refusal(self, request: HttpRequest) -> HttpResponse | None:
        """Turn away a request the check refuses, or return ``None``.

        An anonymous visitor is redirected to the sign-in page and comes back to
        the page they asked for. A signed-in person gets
        :class:`~django.core.exceptions.PermissionDenied`, so the project's own
        403 page answers. This is the branch of Django's ``AccessMixin``, and
        never a 404.
        """
        if self.has_permission(request):
            return None
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        raise PermissionDenied

    @classmethod
    def mounts(cls, request: HttpRequest | None = None) -> list[MountedAppResolver]:
        """Return every mount in the URLconf ``request`` is served from.

        Nothing is recorded when :func:`mount` runs. The mounts are found by
        walking the resolved URLconf and kept on its root resolver, so a
        changed ``ROOT_URLCONF`` or a per-request ``urlconf`` gets its own
        answer with nothing to reset.

        Raises:
            ImproperlyConfigured: One app is mounted inside another, or two
                are mounted with ``main=True``.
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

        An app mounted twice is not refused: it is unsupported, and which mount
        a page belongs to is not defined.

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
            first_main = next((mount for mount in found if mount.main), None)
            if pattern.main and first_main is not None:
                raise ImproperlyConfigured(
                    f'The apps "{first_main.app.name}" and "{pattern.app.name}" '
                    "are both mounted with main=True. A project has one main app."
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
        main: Run the app as the project's own site. Its menu is then the
            sidebar on every page that belongs to no other mounted app, its own
            pages included, with no back link and no app name in the title.
            Only one app may be main.

    Example::

        urlpatterns = [
            mount("", literature, main=True),
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
        return [
            Error(
                str(error),
                hint=(
                    "Mount apps side by side in the project's URLs, and mark at "
                    "most one of them main=True."
                ),
                id="mvp.E001",
            )
        ]
    return []
