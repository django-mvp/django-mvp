"""Django error handler view functions for mvp."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Render the 400 Bad Request page.

    Args:
        request: The current request.
        exception: The exception that triggered the 400 response.

    Returns:
        The rendered 400 response.
    """
    return render(request, "400.html", status=400)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Render the 403 Forbidden page.

    Args:
        request: The current request.
        exception: The exception that triggered the 403 response.

    Returns:
        The rendered 403 response.
    """
    return render(request, "403.html", status=403)


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Render the 404 Not Found page.

    Args:
        request: The current request.
        exception: The exception that triggered the 404 response.

    Returns:
        The rendered 404 response.
    """
    return render(request, "404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """Render the 500 Internal Server Error page.

    No DB queries permitted — this handler may itself be running because
    the database is unavailable.

    Args:
        request: The current request.

    Returns:
        The rendered 500 response.
    """
    support_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
    return render(request, "500.html", {"support_email": support_email}, status=500)
