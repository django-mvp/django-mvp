"""Tests for the breadcrumb trail a page declares, as the header draws it.

The trail and its crumbs are daisy-cotton's components. What the package
promises is that the header hands the declared entries over: one crumb per
entry in order, a link where an entry has an address, the current page where
it has none, extra attributes on the crumb, and the address written once
(#127).

Source: mvp/templates/cotton/app/navbar.html
"""

import pytest

from mvp.config import MVP_CONFIG


class TestADeclaredTrailRendersInTheHeader:
    @pytest.fixture
    def trail(self, cotton_render_string_soup):
        page = {
            "breadcrumbs": [
                {"text": "Home", "href": "/"},
                {"text": "Products", "href": "/products/", "data-crumb": "middle"},
                {"text": "Widget"},
            ]
        }
        soup = cotton_render_string_soup(
            "<c-app.navbar />",
            context={"page": page, "mvp_config": MVP_CONFIG},
        )
        return soup.find("nav", class_="breadcrumbs")

    def test_one_crumb_renders_per_entry_in_order(self, trail):
        crumbs = trail.select("ul > li")

        assert len(crumbs) == 3
        assert [crumb.get_text(strip=True) for crumb in crumbs] == [
            "Home",
            "Products",
            "Widget",
        ]

    def test_an_entry_with_an_address_is_a_link_to_it(self, trail):
        links = trail.select("li > a")

        assert [link["href"] for link in links] == ["/", "/products/"]

    def test_an_entry_with_no_address_is_the_current_page(self, trail):
        last = trail.select("ul > li")[-1]

        assert last.find("a") is None
        assert last.get_text(strip=True) == "Widget"
