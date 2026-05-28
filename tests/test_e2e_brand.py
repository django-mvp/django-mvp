"""End-to-end tests for brand logo and icon templatetags.

Verifies User Story 5 (US5) acceptance criteria at the browser level:
  AC-1: Logo renders correctly for the configured identity.
  AC-2: Light-theme and dark-theme icon src values differ.
  AC-3: Resolver returning None/"" produces no broken <img> element.

Requirements:
  - pytest-playwright installed and browsers downloaded (``playwright install``)
  - ``e2e`` marker registered in pytest configuration

Run interactively:
    poetry run pytest tests/test_e2e_brand.py --headed -m e2e

Run headless (CI):
    poetry run pytest tests/test_e2e_brand.py --headless -m e2e

Skip if playwright not installed:
    pytest -m "not e2e"
"""

import pytest

pytest_playwright = pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Module-level callables used as custom resolvers in multi-tenant tests.
# Referenced by import_string via their dotted path.
# ---------------------------------------------------------------------------


def _tenant_logo_resolver(request, height, theme):
    """Returns a tenant-specific logo URL based on the X-Test-Tenant header.

    Used to simulate multi-tenant identity switching in E2E tests without
    requiring demo app user accounts.
    """
    if request and request.headers.get("X-Test-Tenant") == "alpha":
        return "/static/brand/tenant_alpha_logo.svg"
    return "/static/brand/logo.svg"


def _empty_logo_resolver(request, height, theme):
    """Returns empty string — tag must produce an empty (not broken) img src."""
    return ""


_TENANT_RESOLVER = "tests.test_e2e_brand._tenant_logo_resolver"
_EMPTY_RESOLVER = "tests.test_e2e_brand._empty_logo_resolver"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_logo_src(page):
    """Return the src of the first logo img on the page, or None."""
    return page.evaluate(
        "() => {"
        "  const imgs = document.querySelectorAll('img');"
        "  for (const img of imgs) { if (img.src.includes('logo')) return img.src; }"
        "  return null;"
        "}"
    )


def _get_icon_srcs(page):
    """Return a list of all icon img src values on the page."""
    return page.evaluate(
        "() => Array.from(document.querySelectorAll('img')).filter(img => img.src.includes('icon')).map(img => img.src)"
    )


# ---------------------------------------------------------------------------
# US5 AC-1: Logo renders for the single configured identity (default resolver)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_logo_img_has_non_empty_src_containing_logo_svg(page, live_server):
    """US5 AC-1: A logo <img> with non-empty src containing 'logo.svg' is present."""
    page.goto(f"{live_server.url}/")
    logo_src = _get_logo_src(page)
    assert logo_src, "No logo img found on home page"
    assert "logo.svg" in logo_src, f"Logo src does not contain 'logo.svg': {logo_src}"


# ---------------------------------------------------------------------------
# US5 AC-2: Light-theme and dark-theme icon src values differ
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_light_and_dark_icon_srcs_differ(page, live_server):
    """US5 AC-2: Light and dark icon srcs are different (theme routing works)."""
    page.goto(f"{live_server.url}/")
    icon_srcs = _get_icon_srcs(page)
    light_icons = [s for s in icon_srcs if "icon_light" in s]
    dark_icons = [s for s in icon_srcs if "icon_dark" in s]
    assert light_icons, f"No light icon (icon_light) found; icons: {icon_srcs}"
    assert dark_icons, f"No dark icon (icon_dark) found; icons: {icon_srcs}"
    assert light_icons[0] != dark_icons[0], (
        f"Light and dark icon srcs must be different URLs. Got: {light_icons[0]!r} and {dark_icons[0]!r}"
    )


# ---------------------------------------------------------------------------
# US5 AC-1/AC-2: Multi-tenant — resolver output changes per identity
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_multi_tenant_resolver_changes_logo_src(page, live_server, monkeypatch):
    """US5 AC-1/AC-2: Custom resolver returns different logo URL per tenant identity.

    Simulates multi-tenant identity switching via the X-Test-Tenant request header
    without requiring demo app user accounts. Verifies that overriding
    MVP_LOGO_RESOLVER is sufficient to achieve per-tenant branding — no template
    changes required (SC-002 architectural verification).
    """
    import mvp.templatetags.mvp as mvp_tags

    monkeypatch.setattr(mvp_tags, "MVP_LOGO_RESOLVER", _TENANT_RESOLVER)

    # Default identity (no tenant header) → standard logo
    page.goto(f"{live_server.url}/")
    default_logo = _get_logo_src(page)
    assert default_logo, "Logo img missing for default identity"

    # Tenant 'alpha' identity → different logo URL
    page.set_extra_http_headers({"X-Test-Tenant": "alpha"})
    page.reload()
    alpha_logo = _get_logo_src(page)
    assert alpha_logo, "Logo img missing for alpha identity"

    assert default_logo != alpha_logo, (
        "Multi-tenant resolver should return different logo URLs per identity. "
        f"Default: {default_logo!r}, Alpha: {alpha_logo!r}"
    )


# ---------------------------------------------------------------------------
# US5 AC-3: Resolver returning "" produces no broken <img> element
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_empty_resolver_produces_no_broken_img_elements(page, live_server, monkeypatch):
    """US5 AC-3: Resolver returning '' → no <img> with empty src on page."""
    import mvp.templatetags.mvp as mvp_tags

    monkeypatch.setattr(mvp_tags, "MVP_LOGO_RESOLVER", _EMPTY_RESOLVER)
    page.goto(f"{live_server.url}/")
    broken_count = page.evaluate("() => Array.from(document.querySelectorAll('img[src=\"\"]')).length")
    assert broken_count == 0, (
        f"{broken_count} <img> element(s) with empty src found — "
        "resolver returning '' must not produce broken image elements"
    )
