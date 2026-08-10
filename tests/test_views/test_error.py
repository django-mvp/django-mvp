"""Tests for mvp.views.error — all four error handler functions.

Consolidated from 24 parameterized tests (4 codes × 6 assertions each) to 6
non-parameterized integration tests that verify real user-facing behavior once.
Direct-call unit tests (status code, content bytes) were removed because
they test Django's render() output, not our app's functionality.
"""

import re

import pytest
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import Client, RequestFactory, override_settings
from django.urls import path

from mvp.views.error import server_error
from tests.conftest import requires_browser


def _crashing_urlconf(*patterns):
    """Return a minimal URLconf module-like object with the given url patterns."""
    return type("_URLConf", (), {"urlpatterns": list(patterns)})


# ---------------------------------------------------------------------------
# Integration tests: real handler fires on missing/forbidden/bad URLs
# These verify the custom error pages actually render instead of Django's debug pages.
# ---------------------------------------------------------------------------


class TestErrorPageRendering:
    """Shared chrome on every error page."""

    @pytest.mark.django_db
    def test_error_pages_render_without_sidebar(self, client):
        """All four error preview pages render without AdminLTE sidebar."""
        for code in ["400", "403", "404", "500"]:
            response = client.get(f"/errors/{code}/")
            assert response.status_code == 200
            assert b"main-sidebar" not in response.content

    @pytest.mark.django_db
    def test_error_pages_show_code_and_home_link(self, client):
        """All four error preview pages show the numeric code and a home link."""
        for code in ["400", "403", "404", "500"]:
            content = client.get(f"/errors/{code}/").content.decode()
            assert code in content
            assert b'href="/"' in client.get(f"/errors/{code}/").content
            assert content.count("<h1") == 1

    @pytest.mark.django_db
    def test_error_pages_have_title_with_code(self, client):
        """All four error preview pages have <title> containing the numeric code."""
        for code in ["400", "403", "404", "500"]:
            content = client.get(f"/errors/{code}/").content.decode()
            title_start = content.find("<title")
            title_end = content.find("</title>")
            title_text = content[title_start:title_end] if title_start != -1 else ""
            assert code in title_text

    @pytest.mark.django_db
    def test_error_page_logo_img_has_alt_text(self, client):
        """The error page's brand logo <img> carries non-empty alt text (WCAG image-alt).

        Regression: the error template rendered a raw <img> with no alt attribute,
        which axe-core flagged as a critical WCAG 2.1 AA violation on every error page.
        """
        for code in ["400", "403", "404", "500"]:
            content = client.get(f"/errors/{code}/").content.decode()
            imgs = re.findall(r"<img\b[^>]*>", content, re.S)
            assert imgs, f"/errors/{code}/ renders no <img> to check"
            for img in imgs:
                alt = re.search(r'\balt="([^"]*)"', img, re.S)
                assert alt and alt.group(1).strip(), (
                    f"<img> without alt text on /{code}/: {img}"
                )


# ---------------------------------------------------------------------------
# 404: real handler fires on missing URL
# ---------------------------------------------------------------------------


class TestNotFoundHandler:
    """The 404 handler fires on a missing URL."""

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_404_real_handler_fires(self, client):
        """Missing URL renders custom 404, not Django's debug page."""
        response = client.get("/this-url-does-not-exist-at-all-xyz/")
        assert response.status_code == 404
        assert b"Page not found" in response.content or b"Oops" in response.content


# ---------------------------------------------------------------------------
# 500: real handler fires on view crash, no traceback leaked
# ---------------------------------------------------------------------------


class TestServerErrorHandler:
    """The 500 handler leaks no traceback and touches no database."""

    @pytest.mark.django_db
    @override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="support@example.com")
    def test_500_real_handler_no_traceback(self):
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
    def test_500_support_email_appears(self):
        """DEFAULT_FROM_EMAIL renders as contact link on 500 page."""
        response = server_error(RequestFactory().get("/"))
        assert b"support@example.com" in response.content

    @pytest.mark.django_db
    @override_settings(DEFAULT_FROM_EMAIL="")
    def test_500_no_support_email_when_empty(self):
        """When DEFAULT_FROM_EMAIL is empty, no mailto: link renders."""
        response = server_error(RequestFactory().get("/"))
        assert b"mailto:" not in response.content

    @pytest.mark.django_db
    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_500_zero_db_queries(self, django_assert_num_queries):
        """SC-007: zero DB queries even during error handling."""
        with django_assert_num_queries(0):
            server_error(RequestFactory().get("/"))


# ---------------------------------------------------------------------------
# 403: real handler fires on permission denied
# ---------------------------------------------------------------------------


class TestPermissionDeniedHandler:
    """The 403 handler fires on a denied request."""

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_403_real_handler_fires(self, client):
        """PermissionDenied renders custom 403, not Django's debug page."""

        def forbidden_view(request):
            raise PermissionDenied

        urlconf = _crashing_urlconf(path("forbidden/", forbidden_view))
        with override_settings(ROOT_URLCONF=urlconf):
            response = client.get("/forbidden/")
        assert response.status_code == 403
        assert b"Access Denied" in response.content or b"403" in response.content


# ---------------------------------------------------------------------------
# 400: real handler fires on bad request
# ---------------------------------------------------------------------------


class TestBadRequestHandler:
    """The 400 handler fires on a suspicious request."""

    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_400_real_handler_fires(self, client):
        """SuspiciousOperation renders custom 400, not Django's debug page."""

        def bad_view(request):
            raise SuspiciousOperation("bad data")

        urlconf = _crashing_urlconf(path("bad/", bad_view))
        with override_settings(ROOT_URLCONF=urlconf):
            response = client.get("/bad/")
        assert response.status_code == 400
        assert b"Bad Request" in response.content or b"400" in response.content


# -------------------------------------------------------------------------
# Browser tests (error pages)
# -------------------------------------------------------------------------

# Scoped to the class below, not the module: a module-level importorskip or
# pytestmark would skip and re-mark this module's unit tests too.

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"


def _inject_axe(page):
    """Inject axe-core into the page and run it; return list of critical violations."""
    page.add_script_tag(url=AXE_CDN)
    violations = page.evaluate(
        """
        async () => {
            const results = await axe.run({
                runOnly: {
                    type: 'tag',
                    values: ['wcag2a', 'wcag2aa'],
                },
            });
            return results.violations.filter(v => v.impact === 'critical');
        }
        """
    )
    return violations


ERROR_PAGES = [
    ("400", "400 Bad Request"),
    ("403", "403 Forbidden"),
    ("404", "404 Not Found"),
    ("500", "500 Server Error"),
]


@pytest.mark.e2e
@requires_browser
class TestErrorPagesAccessibilityE2E:
    """Browser accessibility checks for the rendered error pages."""

    @pytest.mark.django_db
    @pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
    def test_no_critical_wcag_aa_violations(
        self, page, live_server, code, title_fragment
    ):
        """Axe-core reports zero critical WCAG 2.1 AA violations (SC-005)."""
        page.goto(f"{live_server.url}/errors/{code}/")
        violations = _inject_axe(page)
        violation_descriptions = [f"{v['id']}: {v['description']}" for v in violations]
        assert violations == [], (
            f"Critical WCAG 2.1 AA violations on /{code}/: {violation_descriptions}"
        )
