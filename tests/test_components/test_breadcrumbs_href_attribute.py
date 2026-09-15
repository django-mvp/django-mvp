"""Regression test for issue #127: ``c-breadcrumbs.item`` renders ``href``
twice.

``mvp/templates/cotton/breadcrumbs/item.html`` renders an explicit
``href="{{ href }}"`` on its anchor and also spreads ``{{ attrs }}`` on the
same element. Cotton only strips a variable out of ``attrs`` when it is
declared in ``<c-vars>``; ``href`` was not declared, so it stayed in
``attrs`` and was written a second time, verbatim and unrendered.

Sources are compiled through the Cotton compiler (mirroring
``test_class_attribute_merge.py``) so the test exercises the component
exactly as a template invocation would — rendering the component's own
template file directly, as ``test_render_all.py`` does, never triggers
Cotton's c-vars / ``attrs`` extraction and would not reproduce this bug.
"""

from html.parser import HTMLParser

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

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
    """A breadcrumb item's ``href`` is written once, not duplicated."""

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


class TestTheItemTextSpan:
    """[#354] The crumb's text lives in its own span, so the stylesheet can
    ellipsis a long crumb without touching the slot — which may hold an icon,
    and must not be truncated along with the text."""

    def test_the_link_branch_wraps_its_text_in_the_span(self):
        html = render('<c-breadcrumbs.item text="Products" href="/products/" />')
        assert '<span class="mvp-breadcrumb-text">Products</span>' in html

    def test_the_non_link_branch_wraps_its_text_in_the_span(self):
        html = render('<c-breadcrumbs.item text="Current Page" />')
        assert '<span class="mvp-breadcrumb-text">Current Page</span>' in html

    def test_the_slot_stays_outside_the_span(self):
        html = render(
            '<c-breadcrumbs.item text="Products" href="/products/">'
            "<b>marker</b>"
            "</c-breadcrumbs.item>"
        )
        assert html.index("</span>") < html.index("<b>marker</b>")

    def test_href_class_and_attrs_still_land_where_they_did(self):
        html = render(
            '<c-breadcrumbs.item text="Products" href="/products/" '
            'class="foo" data-x="1" />'
        )
        assert attrs_named_on(html, "a", "href") == ["/products/"]
        assert attrs_named_on(html, "li", "class") == ["foo"]
        assert attrs_named_on(html, "a", "data-x") == ["1"]


class TestTheTrailsClassStaysOnTheTrail:
    """A class given to ``c-breadcrumbs`` styles the trail, not its items.

    The trail and its items both declare a ``class`` prop, and a Cotton child
    rendered without ``only`` reads a prop it was not given out of the
    surrounding scope. So the trail's own class was written onto every ``<li>``
    inside it as well — invisible until the class was one that changes layout.
    """

    def test_a_class_on_the_trail_does_not_reach_its_items(self):
        html = render(
            '<c-breadcrumbs class="overflow-x-auto" :items="items" />',
            items=[{"text": "Home", "href": "/"}, {"text": "Products"}],
        )
        assert "overflow-x-auto" in attrs_named_on(html, "nav", "class")[0]
        for value in attrs_named_on(html, "li", "class"):
            assert "overflow-x-auto" not in value

    def test_the_items_still_render(self):
        """The isolation must not cost the items the attributes they are
        given: `:attrs` is an explicit prop and passes through `only`."""
        html = render(
            '<c-breadcrumbs :items="items" />',
            items=[{"text": "Home", "href": "/"}, {"text": "Products"}],
        )
        assert attrs_named_on(html, "a", "href") == ["/"]
        assert "Products" in html
