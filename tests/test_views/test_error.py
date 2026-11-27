"""Tests for mvp.views.error — all four error handler functions.

Each error page is rendered once per module. 404 is the representative page
and 500 is the boundary, because it has its own template and context.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.test import Client, RequestFactory, override_settings
from django.urls import path

from mvp.views.error import server_error
from tests.conftest import requires_browser


def _crashing_urlconf(*patterns):
    """Return a minimal URLconf module-like object with the given url patterns."""
    return type("_URLConf", (), {"urlpatterns": list(patterns)})


@pytest.fixture(scope="module")
def error_pages(django_db_setup, django_db_blocker):
    """Each error page rendered once per module, keyed by code.

    404 is the representative page. 500 is the boundary: its own template, and
    the only one that takes a context variable from its handler. The pages
    are only read, so they are rendered once for every test in the module.
    """
    client = Client()
    with django_db_blocker.unblock():
        return {code: client.get(f"/errors/{code}/") for code in ("404", "500")}


class TestErrorPageRendering:
    @pytest.mark.parametrize("code", ["404", "500"])
    def test_error_pages_render_with_their_code(self, error_pages, code):
        response = error_pages[code]
        assert response.status_code == 200
        assert code in response.content.decode()

    @pytest.mark.parametrize("code", ["404", "500"])
    def test_error_pages_draw_no_sidebar(self, error_pages, code):
        soup = BeautifulSoup(error_pages[code].content, "html.parser")
        assert soup.select_one("aside.mvp-sidebar") is None

    def test_the_sidebar_check_finds_a_sidebar_on_an_app_page(self, client, user):
        """Guards the check above: it is the selector the shell really draws."""
        client.force_login(user)
        soup = BeautifulSoup(client.get("/").content, "html.parser")
        assert soup.select_one("aside.mvp-sidebar") is not None

    @pytest.mark.parametrize("code", ["404", "500"])
    def test_error_pages_have_one_heading_and_a_home_link(self, error_pages, code):
        soup = BeautifulSoup(error_pages[code].content, "html.parser")
        assert len(soup.find_all("h1")) == 1
        assert soup.select_one('a[href="/"]') is not None

    @pytest.mark.parametrize("code", ["404", "500"])
    def test_error_pages_have_title_with_code(self, error_pages, code):
        soup = BeautifulSoup(error_pages[code].content, "html.parser")
        assert code in soup.title.get_text()

    @pytest.mark.parametrize("code", ["404", "500"])
    def test_error_page_logo_img_has_alt_text(self, error_pages, code):
        soup = BeautifulSoup(error_pages[code].content, "html.parser")
        imgs = soup.find_all("img")
        assert imgs, f"/errors/{code}/ renders no <img> to check"
        for img in imgs:
            assert (img.get("alt") or "").strip(), (
                f"<img> without alt text on /{code}/: {img}"
            )


class TestNotFoundHandler:
    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_404_real_handler_fires(self, client):
        response = client.get("/this-url-does-not-exist-at-all-xyz/")
        assert response.status_code == 404
        assert b"404" in response.content


class TestServerErrorHandler:
    @pytest.mark.django_db
    @override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="support@example.com")
    def test_500_real_handler_no_traceback(self):

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
        response = server_error(RequestFactory().get("/"))
        assert b"support@example.com" in response.content

    @pytest.mark.django_db
    @override_settings(DEFAULT_FROM_EMAIL="")
    def test_500_no_support_email_when_empty(self):
        response = server_error(RequestFactory().get("/"))
        assert b"mailto:" not in response.content

    @pytest.mark.django_db
    @override_settings(DEFAULT_FROM_EMAIL="support@example.com")
    def test_500_zero_db_queries(self, django_assert_num_queries):
        with django_assert_num_queries(0):
            server_error(RequestFactory().get("/"))


class TestPermissionDeniedHandler:
    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_403_real_handler_fires(self, client):

        def forbidden_view(request):
            raise PermissionDenied

        urlconf = _crashing_urlconf(path("forbidden/", forbidden_view))
        with override_settings(ROOT_URLCONF=urlconf):
            response = client.get("/forbidden/")
        assert response.status_code == 403
        assert b"403" in response.content


class TestBadRequestHandler:
    @pytest.mark.django_db
    @override_settings(DEBUG=False)
    def test_400_real_handler_fires(self, client):

        def bad_view(request):
            raise SuspiciousOperation("bad data")

        urlconf = _crashing_urlconf(path("bad/", bad_view))
        with override_settings(ROOT_URLCONF=urlconf):
            response = client.get("/bad/")
        assert response.status_code == 400
        assert b"400" in response.content


# Scoped to the class below, not the module: a module-level importorskip or
# pytestmark would skip and re-mark this module's unit tests too.

# axe-core 4.9.1 (Mozilla Public License 2.0, header kept in the file), vendored so
# the test needs no network.
AXE_JS = Path(__file__).parent / "vendor" / "axe.min.js"


def _inject_axe(page):
    """Inject axe-core into the page and run it; return list of critical violations."""
    page.add_script_tag(path=str(AXE_JS))
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


@pytest.mark.e2e
@requires_browser
class TestErrorPagesAccessibilityE2E:
    """One page: the four error pages share one base template."""

    @pytest.mark.django_db
    def test_no_critical_wcag_aa_violations(self, page, live_server):
        page.goto(f"{live_server.url}/errors/404/")
        violations = _inject_axe(page)
        violation_descriptions = [f"{v['id']}: {v['description']}" for v in violations]
        assert violations == [], (
            f"Critical WCAG 2.1 AA violations on /404/: {violation_descriptions}"
        )
