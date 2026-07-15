"""Integration tests for brand logo rendering on the app shell.

The resolver logic (default + custom, light/dark routing, None/empty/raising)
is unit-tested in tests/test_templatetags.py. These tests add the one thing a
unit test can't: confirmation that the shell templates actually wire the brand
logo onto a real rendered page. They use the Django test client — no browser,
because nothing here exercises a user interaction.
"""

import re

import pytest


@pytest.mark.django_db
def test_home_page_renders_brand_logo(client):
    """GET / renders a brand logo <img> pointing at the bundled logo asset."""
    html = client.get("/").content.decode()
    srcs = re.findall(r'<img[^>]*\bsrc="([^"]*)"', html)
    logo_srcs = [s for s in srcs if "logo.svg" in s]
    assert logo_srcs, f"No brand logo img rendered on the home page; imgs: {srcs}"


@pytest.mark.django_db
def test_home_page_has_no_broken_img_src(client):
    """No <img> renders with an empty src (which would be a broken image)."""
    html = client.get("/").content.decode()
    assert 'src=""' not in html, "An <img> with an empty src rendered on the home page"
