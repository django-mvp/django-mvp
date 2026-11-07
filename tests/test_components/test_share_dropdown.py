"""Tests for ``<c-mvp.addons.share-dropdown>``.

Source: mvp/templates/cotton/mvp/addons/share_dropdown.html
"""

import codecs
import re

from django.test import RequestFactory

from mvp.config import MVP_CONFIG


class TestShareDropdownMenu:
    def test_the_menu_has_an_accessible_name(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-mvp.addons.share-dropdown url="https://example.com/page/" />',
            context={"mvp_config": MVP_CONFIG},
        )

        assert soup.select_one("ul.menu")["aria-label"].strip()


class TestShareDropdownLinks:
    PAGE = "https://example.com/page/?a=1&b=2"

    def links(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            f'<c-mvp.addons.share-dropdown url="{self.PAGE}" title="My page" />',
            context={"mvp_config": MVP_CONFIG},
        )
        return soup.select("ul.menu a[href]")

    def test_every_network_link_carries_the_page_url_with_its_query_encoded(
        self, cotton_render_string_soup
    ):
        links = [
            link
            for link in self.links(cotton_render_string_soup)
            if link["href"].startswith("https://")
        ]

        assert len(links) == 4
        for link in links:
            assert "example.com/page/%3Fa%3D1%26b%3D2" in link["href"]

    def test_links_that_open_another_site_cannot_reach_back_to_this_page(
        self, cotton_render_string_soup
    ):
        links = [
            link
            for link in self.links(cotton_render_string_soup)
            if link.get("target") == "_blank"
        ]

        assert links
        for link in links:
            assert {"noopener", "noreferrer"} <= set(link["rel"])


class TestShareDropdownCopyLink:
    def copied_text(self, soup):
        """The text the copy item hands to the clipboard, decoded from its script."""
        script = soup.select_one("ul.menu a[onclick]")["onclick"]
        literal = re.search(r"writeText\('((?:[^'\\]|\\.)*)'", script)
        assert literal, script
        return codecs.decode(literal.group(1), "unicode_escape")

    def test_it_copies_the_url_it_was_given(self, cotton_render_string_soup):
        url = "https://example.com/shared/?a=1&b='2'"
        soup = cotton_render_string_soup(
            '<c-mvp.addons.share-dropdown :url="url" />',
            context={"mvp_config": MVP_CONFIG, "url": url},
        )

        assert self.copied_text(soup) == url

    def test_it_copies_the_page_address_when_given_no_url(
        self, cotton_render_string_soup
    ):
        request = RequestFactory().get("/notes/?q=x")
        soup = cotton_render_string_soup(
            "<c-mvp.addons.share-dropdown />",
            context={"mvp_config": MVP_CONFIG, "request": request},
        )

        assert self.copied_text(soup) == request.build_absolute_uri()
