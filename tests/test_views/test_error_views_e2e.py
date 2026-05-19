"""End-to-end tests for all four error page preview routes using pytest-playwright.

Covers T029: error code visibility, single h1, home link, page title, HTTP status,
and axe-core accessibility sweep for WCAG 2.1 AA compliance (SC-005).

These tests require:
  - pytest-playwright installed and browsers downloaded (``playwright install``)
  - The ``e2e`` marker is registered in pytest configuration

Run with: ``pytest tests/test_views/test_error_views_e2e.py -m e2e``
Skip in CI without playwright: ``pytest -m "not e2e"``
"""

import pytest

pytest_playwright = pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

pytestmark = pytest.mark.e2e

# ---------------------------------------------------------------------------
# axe-core CDN URL for accessibility injection
# ---------------------------------------------------------------------------

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"


def _inject_axe(page):
    """Inject axe-core into the page and run it; return list of violations."""
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


# ---------------------------------------------------------------------------
# Parametrized error page tests
# ---------------------------------------------------------------------------


ERROR_PAGES = [
    ("400", "400 Bad Request"),
    ("403", "403 Forbidden"),
    ("404", "404 Not Found"),
    ("500", "500 Server Error"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_error_preview_returns_200(page, live_server, code, title_fragment):
    """Preview route responds HTTP 200."""
    response = page.goto(f"{live_server.url}/errors/{code}/")
    assert response.status == 200


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_error_code_visible_in_dom(page, live_server, code, title_fragment):
    """Numeric error code text is rendered prominently on the page."""
    page.goto(f"{live_server.url}/errors/{code}/")
    assert page.get_by_text(code, exact=True).count() > 0


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_single_h1_element_present(page, live_server, code, title_fragment):
    """Exactly one <h1> element is present (semantic heading)."""
    page.goto(f"{live_server.url}/errors/{code}/")
    assert page.locator("h1").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_home_link_present(page, live_server, code, title_fragment):
    """A link with href="/" exists on every error preview page."""
    page.goto(f"{live_server.url}/errors/{code}/")
    assert page.locator('a[href="/"]').count() >= 1


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_page_title_contains_error_code(page, live_server, code, title_fragment):
    """Page <title> contains the numeric error code."""
    page.goto(f"{live_server.url}/errors/{code}/")
    title = page.title()
    assert code in title


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_no_sidebar_on_error_page(page, live_server, code, title_fragment):
    """Error pages must NOT render the AdminLTE sidebar (standalone layout)."""
    page.goto(f"{live_server.url}/errors/{code}/")
    assert page.locator(".main-sidebar").count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_no_critical_wcag_aa_violations(page, live_server, code, title_fragment):
    """Axe-core reports zero critical WCAG 2.1 AA violations (SC-005)."""
    page.goto(f"{live_server.url}/errors/{code}/")
    violations = _inject_axe(page)
    violation_descriptions = [f"{v['id']}: {v['description']}" for v in violations]
    assert violations == [], f"Critical WCAG 2.1 AA violations on /{code}/: {violation_descriptions}"
