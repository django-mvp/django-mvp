"""Tests for mvp.views.error — all four error handler functions.

Note: RequestFactory responses from django.shortcuts.render() do NOT expose
.templates or .context — those are only set by the test Client infrastructure.
Instead, we assert on response.content for direct-call tests, and use the test
Client with a custom URLconf for "real handler" integration tests.
"""

import pytest
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import Client, RequestFactory, override_settings
from django.urls import path

from mvp.views.error import bad_request, not_found, permission_denied, server_error

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_get(url="/"):
    return RequestFactory().get(url)


def _crashing_urlconf(*patterns):
    """Return a minimal URLconf module-like object with the given url patterns."""
    return type("_URLConf", (), {"urlpatterns": list(patterns)})


# ---------------------------------------------------------------------------
# T007: not_found (404)
# ---------------------------------------------------------------------------


class TestNotFoundView:
    def test_status_code_is_404(self):
        request = _make_get("/missing/")
        response = not_found(request, exception=Exception("test"))
        assert response.status_code == 404

    def test_response_contains_page_not_found_copy(self):
        request = _make_get("/missing/")
        response = not_found(request, exception=Exception("test"))
        assert b"Page not found" in response.content or b"404" in response.content

    def test_response_contains_home_link(self):
        request = _make_get("/missing/")
        response = not_found(request, exception=Exception("test"))
        assert b'href="/"' in response.content

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_real_handler_fires_on_missing_url(self):
        client = Client()
        response = client.get("/this-url-does-not-exist-at-all-xyz/")
        assert response.status_code == 404
        # Custom template was used (not Django's debug 404 page)
        assert b"Page not found" in response.content or b"Oops" in response.content


# ---------------------------------------------------------------------------
# T011: server_error (500)
# ---------------------------------------------------------------------------


class TestServerErrorView:
    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_status_code_is_500(self):
        request = _make_get("/")
        response = server_error(request)
        assert response.status_code == 500

    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_support_email_appears_in_rendered_content(self):
        """support_email is passed to context — verify it renders in output."""
        request = _make_get("/")
        response = server_error(request)
        assert b"support@example.com" in response.content

    @override_settings(DEFAULT_FROM_EMAIL="")
    def test_support_email_absent_when_setting_is_empty(self):
        """When DEFAULT_FROM_EMAIL is empty, contact link must not render."""
        request = _make_get("/")
        response = server_error(request)
        assert b"mailto:" not in response.content

    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_response_contains_no_debug_traceback(self):
        request = _make_get("/")
        response = server_error(request)
        assert b"Traceback" not in response.content

    @pytest.mark.django_db
    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_zero_db_queries(self, django_assert_num_queries):
        """SC-007: zero DB queries even during error handling."""
        request = _make_get("/")
        with django_assert_num_queries(0):
            server_error(request)

    @pytest.mark.django_db
    @override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="support@example.com")
    def test_real_handler_returns_500_without_debug_info(self):
        """Trigger 500 via a view that raises, confirm no traceback in output."""

        def crashing_view(request):
            raise RuntimeError("Deliberate crash for testing")

        urlconf = _crashing_urlconf(path("crash/", crashing_view))
        with override_settings(ROOT_URLCONF=urlconf):
            client = Client(raise_request_exception=False)
            response = client.get("/crash/")
        assert response.status_code == 500
        assert b"Traceback" not in response.content


# ---------------------------------------------------------------------------
# T016: permission_denied (403)
# ---------------------------------------------------------------------------


class TestPermissionDeniedView:
    def test_status_code_is_403(self):
        request = _make_get("/secret/")
        response = permission_denied(request, exception=Exception("test"))
        assert response.status_code == 403

    def test_response_contains_back_to_home_text(self):
        request = _make_get("/secret/")
        response = permission_denied(request, exception=Exception("test"))
        assert b"Return to site" in response.content

    def test_response_contains_home_link(self):
        request = _make_get("/secret/")
        response = permission_denied(request, exception=Exception("test"))
        assert b'href="/"' in response.content

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_real_handler_renders_custom_403_template(self):
        def forbidden_view(request):
            raise PermissionDenied

        urlconf = _crashing_urlconf(path("forbidden/", forbidden_view))
        with override_settings(ROOT_URLCONF=urlconf):
            client = Client()
            response = client.get("/forbidden/")
        assert response.status_code == 403
        assert b"Access Denied" in response.content or b"403" in response.content


# ---------------------------------------------------------------------------
# T020: bad_request (400)
# ---------------------------------------------------------------------------


class TestBadRequestView:
    def test_status_code_is_400(self):
        request = _make_get("/bad/")
        response = bad_request(request, exception=Exception("test"))
        assert response.status_code == 400

    def test_response_contains_back_to_home_text(self):
        request = _make_get("/bad/")
        response = bad_request(request, exception=Exception("test"))
        assert b"Return to site" in response.content

    def test_response_contains_home_link(self):
        request = _make_get("/bad/")
        response = bad_request(request, exception=Exception("test"))
        assert b'href="/"' in response.content

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_real_handler_renders_custom_400_template(self):
        def bad_view(request):
            raise SuspiciousOperation("bad data")

        urlconf = _crashing_urlconf(path("bad/", bad_view))
        with override_settings(ROOT_URLCONF=urlconf):
            client = Client()
            response = client.get("/bad/")
        assert response.status_code == 400
        assert b"Bad Request" in response.content or b"400" in response.content


# ---------------------------------------------------------------------------
# T029: Error page preview routes /errors/{code}/ — status, content, structure
# ---------------------------------------------------------------------------

_ERROR_PREVIEW_CODES = ["400", "403", "404", "500"]


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_error_preview_returns_200(client, code):
    """Preview route /errors/{code}/ responds HTTP 200."""
    response = client.get(f"/errors/{code}/")
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_error_code_visible_in_dom(client, code):
    """Numeric error code text is rendered prominently on the page."""
    response = client.get(f"/errors/{code}/")
    assert code.encode() in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_single_h1_element_present(client, code):
    """Exactly one <h1> element is present (semantic heading)."""
    content = client.get(f"/errors/{code}/").content.decode()
    assert content.count("<h1") == 1


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_home_link_present(client, code):
    """A link with href="/" exists on every error preview page."""
    response = client.get(f"/errors/{code}/")
    assert b'href="/"' in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_page_title_contains_error_code(client, code):
    """Page <title> contains the numeric error code."""
    content = client.get(f"/errors/{code}/").content.decode()
    title_start = content.find("<title")
    title_end = content.find("</title>")
    title_text = content[title_start:title_end] if title_start != -1 else ""
    assert code in title_text


@pytest.mark.django_db
@pytest.mark.parametrize("code", _ERROR_PREVIEW_CODES)
def test_no_sidebar_on_error_page(client, code):
    """Error pages must NOT render the AdminLTE sidebar (standalone layout)."""
    response = client.get(f"/errors/{code}/")
    assert b"main-sidebar" not in response.content
