"""No rendered page paints a surface that ignores the base colours' meanings (#626).

Source: docs/theming.md, specs/026-ship-prebuilt-daisyui/spec.md FR-036

base-100 is raised and base-300 is sunk, so either may be named. base-200 is the
page, and a part of a page that names it vanishes into the page behind it. A
border named after a base colour vanishes on that surface, which is what
``border-line`` is for. The entrance background is the one element that is the
page itself. Reading the rendered pages catches a new hardcoded surface whichever
template it came from, including one a component draws from an attribute.
"""

import re

import pytest
from bs4 import BeautifulSoup
from django.test import Client

from tests.factories import ProductFactory

pytestmark = pytest.mark.django_db

PAGES = (
    "/products/",
    "/products/create/",
    "/django-tables2/",
    "/layout/side/",
    "/layout/title/",
    "/components/",
    "/components/placeholder/",
    "/components/avatar/",
    "/components/card/",
    "/components/dropdown/",
    "/components/data-field/",
    "/components/modal/",
    "/components/formset/",
    "/errors/404/",
)

HARDCODED = re.compile(r"^(?:[\w-]+:)*(?:bg-base-200|border-base-\d+)$")

# The entrance page has no shell, so its background element is the page.
THE_PAGE_ITSELF = "min-h-screen"


def hardcoded_surfaces(html):
    """Every class on the page that paints a surface against the meanings."""
    found = []
    for element in BeautifulSoup(html, "html.parser").find_all(class_=True):
        classes = element["class"]
        if THE_PAGE_ITSELF in classes:
            continue
        found += [name for name in classes if HARDCODED.match(name)]
    return found


class TestHardcodedSurfaces:
    @pytest.fixture(autouse=True)
    def urls_mounted(self, settings):
        settings.ROOT_URLCONF = "demo.urls"

    @pytest.mark.parametrize("path", PAGES)
    def test_a_page_names_no_surface_against_its_meaning(self, path):
        ProductFactory.create_batch(2)

        response = Client().get(path)

        assert response.status_code == 200, path
        assert hardcoded_surfaces(response.content.decode()) == []

    def test_a_card_on_the_page_colour_is_found(self):
        html = '<div class="card bg-base-200">x</div><hr class="border-base-300">'

        assert hardcoded_surfaces(html) == ["bg-base-200", "border-base-300"]

    def test_the_entrance_background_is_the_page(self):
        html = '<div class="min-h-screen bg-base-200">x</div>'

        assert hardcoded_surfaces(html) == []
