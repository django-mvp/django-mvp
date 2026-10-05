"""Regression test for issue #127: ``c-breadcrumbs.item`` renders ``href``
twice.

The crumb the package used to ship rendered an explicit ``href="{{ href }}"`` on
its anchor and also spread ``{{ attrs }}`` on the same element. Cotton only
strips a variable out of ``attrs`` when it is declared in ``<c-vars>``; ``href``
was not declared, so it stayed in ``attrs`` and was written a second time. The
crumb is now daisy-cotton's, and this module holds what the package's header
still promises about the trail a page declares.

Sources are compiled through the Cotton compiler (mirroring
``test_class_attribute_merge.py``) so the test exercises the component
exactly as a template invocation would — rendering the component's own
template file directly, as ``test_render_all.py`` does, never triggers
Cotton's c-vars / ``attrs`` extraction and would not reproduce this bug.
"""

from html.parser import HTMLParser

import pytest
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class _FirstTagAttrs(HTMLParser):
    """Collect the raw attribute list of the first `<tag>` start tag.

    HTMLParser respects attribute quoting and — unlike a browser — reports
    every occurrence of a repeated attribute rather than silently dropping
    it, which is exactly what this bug needs to be caught.
    """

    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.attrs = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is None and tag == self.tag:
            self.attrs = attrs


def attrs_named_on(html, tag, name):
    """Every value found under ``name`` on the first ``<tag ...>`` open tag."""
    parser = _FirstTagAttrs(tag)
    parser.feed(html)
    assert parser.attrs is not None, f"no <{tag}> tag found in rendered output"
    return [value for attr_name, value in parser.attrs if attr_name == name]


class TestBreadcrumbItemHrefAttribute:
    def test_href_appears_once(self):
        html = render(
            '<c-breadcrumbs.item text="Account Center" href="/account-center/" />'
        )
        hrefs = attrs_named_on(html, "a", "href")
        assert len(hrefs) == 1, f"expected one href attribute, found {hrefs}"
        assert hrefs[0] == "/account-center/"

    def test_item_without_href_has_no_anchor(self):
        html = render('<c-breadcrumbs.item text="Current Page" />')
        assert "<a" not in html
        assert "Current Page" in html


class TestTheTrailsClassStaysOnTheTrail:
    def test_a_class_on_the_trail_does_not_reach_its_items(self):
        html = render(
            '<c-breadcrumbs class="overflow-x-auto" :items="items" />',
            items=[{"text": "Home", "href": "/"}, {"text": "Products"}],
        )
        assert "overflow-x-auto" in attrs_named_on(html, "nav", "class")[0]
        for value in attrs_named_on(html, "li", "class"):
            assert "overflow-x-auto" not in value

    def test_the_items_still_render(self):
        html = render(
            '<c-breadcrumbs :items="items" />',
            items=[{"text": "Home", "href": "/"}, {"text": "Products"}],
        )
        assert attrs_named_on(html, "a", "href") == ["/"]
        assert "Products" in html


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
