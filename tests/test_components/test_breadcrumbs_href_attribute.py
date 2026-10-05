"""Tests for the breadcrumb trail a page declares, as the header draws it.

The trail and its crumbs are daisy-cotton's components. What the package
promises is that the header hands the declared entries over: one crumb per
entry in order, a link where an entry has an address, the current page where
it has none, extra attributes on the crumb, and the address written once
(#127).

Source: mvp/templates/cotton/mvp/app/header/navbar.html
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
            "<c-mvp.app.header.navbar />",
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
        current = trail.select("li > [aria-current='page']")

        assert len(current) == 1
        assert current[0].name != "a"
        assert current[0].get_text(strip=True) == "Widget"

    def test_extra_attributes_land_on_the_list_item(self, trail):
        item = trail.select("ul > li")[1]

        assert item["data-crumb"] == "middle"
        assert not item.find("a").has_attr("data-crumb")

    def test_the_address_is_written_once(self, trail):
        assert str(trail).count('href="/products/"') == 1
        assert not trail.select_one("ul > li").has_attr("href")
