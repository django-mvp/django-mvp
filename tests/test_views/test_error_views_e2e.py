"""Accessibility E2E tests for error pages using axe-core (WCAG 2.1 AA).

Covers SC-005: critical WCAG 2.1 AA compliance for all four error page previews.
These tests genuinely require a real browser to execute axe-core JavaScript.

All other error-page preview tests (status, content, DOM structure) have been
converted to standard Django client tests in test_error_views.py.

Run with: ``pytest tests/test_views/test_error_views_e2e.py -m e2e``
Skip in CI without playwright: ``pytest -m "not e2e"``
"""

import pytest

pytest_playwright = pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

pytestmark = pytest.mark.e2e

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


@pytest.mark.django_db
@pytest.mark.parametrize("code,title_fragment", ERROR_PAGES)
def test_no_critical_wcag_aa_violations(page, live_server, code, title_fragment):
    """Axe-core reports zero critical WCAG 2.1 AA violations (SC-005)."""
    page.goto(f"{live_server.url}/errors/{code}/")
    violations = _inject_axe(page)
    violation_descriptions = [f"{v['id']}: {v['description']}" for v in violations]
    assert violations == [], f"Critical WCAG 2.1 AA violations on /{code}/: {violation_descriptions}"
