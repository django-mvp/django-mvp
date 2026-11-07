"""Middleware that applies a signed-in person's preferences to each request.

Source: mvp/preferences.py (the ``locale`` group).
"""

import zoneinfo
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils import timezone, translation
from object_preferences.registry import registry


class PreferencesMiddleware:
    """Show a signed-in person times in their timezone and pages in their language.

    List it directly below ``AuthenticationMiddleware``. Django's
    ``LocaleMiddleware`` runs before authentication and so cannot know the
    person; this replaces what it chose. A visitor is left alone, and so is a
    person's language when they have not chosen one.

    The language that was active is put back after the response, and
    ``Content-Language`` is set here, because a project without
    ``LocaleMiddleware`` has nothing else that resets the thread's language and
    the next request on it would otherwise be served in this person's.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Keep the next layer of the middleware stack.

        Args:
            get_response: The next middleware or the view.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Apply the person's timezone and language while the response is built.

        Args:
            request: The request, whose ``user`` authentication has set.

        Returns:
            The response, carrying ``Content-Language`` for a signed-in person.
        """
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return self.get_response(request)
        locale = registry.get_preferences(user)["locale"]
        previous = translation.get_language()
        timezone.activate(zoneinfo.ZoneInfo(locale["timezone"]))
        if locale.get("language"):
            translation.activate(locale["language"])
            request.LANGUAGE_CODE = translation.get_language()
        try:
            response = self.get_response(request)
            response.headers.setdefault("Content-Language", translation.get_language())
            return response
        finally:
            timezone.deactivate()
            translation.activate(previous)
