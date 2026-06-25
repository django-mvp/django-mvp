"""Tests for mvp.views.error — all four error handler functions.

Consolidated from 24 parameterized tests (4 codes × 6 assertions each) to 6
non-parameterized integration tests that verify real user-facing behavior once.
Direct-call unit tests (status code, content bytes) were removed because
they test Django's render() output, not our app's functionality.
"""

import pytest
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import Client, RequestFactory, override_settings
from django.urls import path

from mvp.views.error import server_error


def _crashing_urlconf(*patterns):
    """Return a minimal URLconf module-like object with the given url patterns."""
    return type("_URLConf", (), {"urlpatterns": list(patterns)})


# ---------------------------------------------------------------------------
# Integration tests: real handler fires on missing/forbidden/bad URLs
# These verify the custom error pages actually render instead of Django's debug pages.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_error_pages_render_without_sidebar(client):
    """All four error preview pages render without AdminLTE sidebar."""
    for code in ["400", "403", "404", "500"]:
        response = client.get(f"/errors/{code}/")
        assert response.status_code == 200
        assert b"main-sidebar" not in response.content


@pytest.mark.django_db
def test_error_pages_show_code_and_home_link(client):
    """All four error preview pages show the numeric code and a home link."""
    for code in ["400", "403", "404", "500"]:
        content = client.get(f"/errors/{code}/").content.decode()
        assert code in content
        assert b'href="/"' in client.get(f"/errors/{code}/").content
        assert content.count("<h1") == 1


@pytest.mark.django_db
def test_error_pages_have_title_with_code(client):
    """All four error preview pages have <title> containing the numeric code."""
    for code in ["400", "403", "404", "500"]:
        content = client.get(f"/errors/{code}/").content.decode()
        title_start = content.find("<title")
        title_end = content.find("</title>")
        title_text = content[title_start:title_end] if title_start != -1 else ""
        assert code in title_text


# ---------------------------------------------------------------------------
# 404: real handler fires on missing URL
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_404_real_handler_fires():
    """Missing URL renders custom 404, not Django's debug page."""
    client = Client()
    response = client.get("/this-url-does-not-exist-at-all-xyz/")
    assert response.status_code == 404
    assert b"Page not found" in response.content or b"Oops" in response.content


# ---------------------------------------------------------------------------
# 500: real handler fires on view crash, no traceback leaked
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="support@example.com")
def test_500_real_handler_no_traceback():
    """Crashing view returns 500 with custom page, no traceback in output."""

    def crashing_view(request):
        raise RuntimeError("Deliberate crash for testing")

    urlconf = _crashing_urlconf(path("crash/", crashing_view))
    with override_settings(ROOT_URLCONF=urlconf):
        client = Client(raise_request_exception=False)
        response = client.get("/crash/")
    assert response.status_code == 500
    assert b"Traceback" not in response.content


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="support@example.com")
def test_500_support_email_appears():
    """DEFAULT_FROM_EMAIL renders as contact link on 500 page."""
    response = server_error(RequestFactory().get("/"))
    assert b"support@example.com" in response.content


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="")
def test_500_no_support_email_when_empty():
    """When DEFAULT_FROM_EMAIL is empty, no mailto: link renders."""
    response = server_error(RequestFactory().get("/"))
    assert b"mailto:" not in response.content


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="support@example.com")
def test_500_zero_db_queries(django_assert_num_queries):
    """SC-007: zero DB queries even during error handling."""
    with django_assert_num_queries(0):
        server_error(RequestFactory().get("/"))


# ---------------------------------------------------------------------------
# 403: real handler fires on permission denied
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_403_real_handler_fires():
    """PermissionDenied renders custom 403, not Django's debug page."""

    def forbidden_view(request):
        raise PermissionDenied

    urlconf = _crashing_urlconf(path("forbidden/", forbidden_view))
    with override_settings(ROOT_URLCONF=urlconf):
        client = Client()
        response = client.get("/forbidden/")
    assert response.status_code == 403
    assert b"Access Denied" in response.content or b"403" in response.content


# ---------------------------------------------------------------------------
# 400: real handler fires on bad request
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_400_real_handler_fires():
    """SuspiciousOperation renders custom 400, not Django's debug page."""

    def bad_view(request):
        raise SuspiciousOperation("bad data")

    urlconf = _crashing_urlconf(path("bad/", bad_view))
    with override_settings(ROOT_URLCONF=urlconf):
        client = Client()
        response = client.get("/bad/")
    assert response.status_code == 400
    assert b"Bad Request" in response.content or b"400" in response.content


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="")
def test_500_no_support_email_when_empty():
    """When DEFAULT_FROM_EMAIL is empty, no mailto: link renders."""
    response = server_error(RequestFactory().get("/"))
    assert b"mailto:" not in response.content


@pytest.mark.django_db
@override_settings(DEFAULT_FROM_EMAIL="support@example.com")
def test_500_zero_db_queries(django_assert_num_queries):
    """SC-007: zero DB queries even during error handling."""
    with django_assert_num_queries(0):
        server_error(RequestFactory().get("/"))


# ---------------------------------------------------------------------------
# 403: real handler fires on permission denied
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_403_real_handler_fires():
    """PermissionDenied renders custom 403, not Django's debug page."""

    def forbidden_view(request):
        raise PermissionDenied

    urlconf = _crashing_urlconf(path("forbidden/", forbidden_view))
    with override_settings(ROOT_URLCONF=urlconf):
        client = Client()
        response = client.get("/forbidden/")
    assert response.status_code == 403
    assert b"Access Denied" in response.content or b"403" in response.content


# ---------------------------------------------------------------------------
# 400: real handler fires on bad request
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_400_real_handler_fires():
    """SuspiciousOperation renders custom 400, not Django's debug page."""

    def bad_view(request):
        raise SuspiciousOperation("bad data")

    urlconf = _crashing_urlconf(path("bad/", bad_view))
    with override_settings(ROOT_URLCONF=urlconf):
        client = Client()
        response = client.get("/bad/")
    assert response.status_code == 400
    assert b"Bad Request" in response.content or b"400" in response.content
