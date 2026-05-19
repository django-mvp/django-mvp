"""Django error handler view functions for mvp."""

from django.conf import settings
from django.shortcuts import render


def bad_request(request, exception):
    """Handle 400 Bad Request errors."""
    return render(request, "400.html", status=400)


def permission_denied(request, exception):
    """Handle 403 Forbidden errors."""
    return render(request, "403.html", status=403)


def not_found(request, exception):
    """Handle 404 Not Found errors."""
    return render(request, "404.html", status=404)


def server_error(request):
    """Handle 500 Internal Server Error — no DB queries permitted."""
    support_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or None
    return render(request, "500.html", {"support_email": support_email}, status=500)
