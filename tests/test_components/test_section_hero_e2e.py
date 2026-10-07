"""E2E test for <c-mvp.section.hero> (issue #240).

Real-browser test, not a template-only assertion, and for the reason the issue
exists: the hero rendered perfectly valid markup the whole time it was broken.
Its root element carried `mvp-hero`, a class no stylesheet in the project ever
defined — the layout had come from a parallax script loaded from a CDN, and
when that went the class was left standing with nothing behind it. Every
template assertion still passed. What was gone was `display`, `place-items` and
`position`, none of which a string search over the response can see.

So the contract worth pinning is the computed one: content centred in the
banner, and an overlay actually covering the image it is there to dim.
"""

from importlib import import_module

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView
from playwright.sync_api import expect

from tests.conftest import requires_browser, urlconf_of

pytestmark = [pytest.mark.e2e, requires_browser]

DESKTOP = {"width": 1280, "height": 800}


HERO_URLCONF = urlconf_of(
    path("section-hero/", TemplateView.as_view(template_name="tests/section_hero.html")),
    *import_module(settings.ROOT_URLCONF).urlpatterns,
)


def _box(locator):
    box = locator.bounding_box()
    assert box is not None, "element has no layout box at all"
    return box


@pytest.mark.django_db
class TestHeroLayoutInABrowser:
    @pytest.fixture
    def hero_page(self, page, live_server):
        page.set_viewport_size(DESKTOP)
        with override_settings(ROOT_URLCONF=HERO_URLCONF):
            page.goto(f"{live_server.url}/section-hero/")
            yield page

    def test_the_hero_has_a_layout_box(self, hero_page):
        hero = hero_page.locator(".hero").first

        expect(hero).to_be_visible()
        assert _box(hero)["height"] > 0

    def test_content_is_centred_in_the_banner(self, hero_page):
        hero = _box(hero_page.locator(".hero").first)
        content = _box(hero_page.locator(".hero-content").first)

        assert content["x"] + content["width"] / 2 == pytest.approx(
            hero["x"] + hero["width"] / 2, abs=2
        ), "hero content is not horizontally centred"
        assert content["y"] + content["height"] / 2 == pytest.approx(
            hero["y"] + hero["height"] / 2, abs=2
        ), "hero content is not vertically centred"

    def test_the_height_attribute_reaches_the_rendered_box(self, hero_page):
        assert _box(hero_page.locator(".hero").first)["height"] == pytest.approx(
            640, abs=2
        )

    def test_the_overlay_covers_the_banner(self, hero_page):
        hero = _box(hero_page.locator(".hero").first)
        overlay = _box(hero_page.locator(".hero-overlay").first)

        assert overlay["x"] == pytest.approx(hero["x"], abs=1)
        assert overlay["y"] == pytest.approx(hero["y"], abs=1)
        assert overlay["width"] == pytest.approx(hero["width"], abs=1)
        assert overlay["height"] == pytest.approx(hero["height"], abs=1)
