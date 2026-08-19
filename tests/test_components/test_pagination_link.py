"""Tests for <c-pagination.link>'s href and current-page styling (issue #270).

Every page link used to render as `?page=N`, which replaced the whole query
string and dropped a sort (`?o=`), a search (`?q=`) or any filter parameter on
every page change, even though the sortable column headings right above a
table preserve everything through `{% querystring_replace %}`. Django's
built-in `{% querystring %}` tag (5.1+) changes only `page` and leaves
everything else in the current query string untouched, so no custom
templatetag is needed here.

The current page was also visually indistinguishable from the rest:
`btn-active` alone resolves to the same background a plain `.btn` already
has, so nothing changed on screen even though the markup (`aria-current`,
the class) was correct.
"""

from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django import template
from django.core.paginator import Paginator
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, request, **context):
    """Compile a Cotton source string and render it against a real request.

    A ``RequestContext`` (rather than the plain ``Context`` most component
    tests use) is required here: the href now goes through Django's
    ``{% querystring %}`` tag, which reads ``context.request.GET``.
    """
    return template.Template(compiler.process(source)).render(
        RequestContext(request, context)
    )


class _AnchorCollector(HTMLParser):
    """Collect every `<a>` tag's attributes, in document order."""

    def __init__(self):
        super().__init__()
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchors.append(dict(attrs))


def collect_anchors(html):
    parser = _AnchorCollector()
    parser.feed(html)
    return parser.anchors


class TestPaginationLinkPreservesQueryString:
    """A page link changes only `page`, keeping every other parameter."""

    def test_page_link_preserves_sort_and_search(self):
        request = RequestFactory().get("/items/?o=name&q=widget")
        html = render('<c-pagination.link :page="2" text="2" />', request)
        anchors = collect_anchors(html)
        assert len(anchors) == 1
        query = parse_qs(urlsplit(anchors[0]["href"]).query)
        assert query == {"o": ["name"], "q": ["widget"], "page": ["2"]}

    def test_page_link_with_no_other_params_still_changes_the_page(self):
        request = RequestFactory().get("/items/")
        html = render('<c-pagination.link :page="4" text="4" />', request)
        anchors = collect_anchors(html)
        query = parse_qs(urlsplit(anchors[0]["href"]).query)
        assert query == {"page": ["4"]}


class TestPaginationWrapperLinksAllPreserveQueryString:
    """First, Previous, numbered, Next and Last links share one component,
    so the fix applies uniformly to every one of them."""

    def test_every_rendered_link_preserves_the_current_query_string(self):
        request = RequestFactory().get("/items/?o=name&q=widget")
        paginator = Paginator(range(9), 3)
        page_obj = paginator.page(2)
        html = render_to_string(
            "tests/pagination.html", {"page_obj": page_obj}, request=request
        )
        anchors = collect_anchors(html)
        # First, Previous, three numbered pages, Next, Last.
        assert len(anchors) == 7
        for anchor in anchors:
            query = parse_qs(urlsplit(anchor["href"]).query)
            assert query.get("o") == ["name"]
            assert query.get("q") == ["widget"]
            assert "page" in query


class TestPaginationCurrentPageIndicator:
    """The active page link is visually distinct, not just marked up."""

    def test_active_link_gets_a_colour_modifier_no_sibling_has(self):
        request = RequestFactory().get("/items/")
        paginator = Paginator(range(9), 3)
        page_obj = paginator.page(2)
        html = render_to_string(
            "tests/pagination.html", {"page_obj": page_obj}, request=request
        )
        anchors = collect_anchors(html)
        current = [a for a in anchors if a.get("aria-current") == "page"]
        assert len(current) == 1
        current_classes = set(current[0]["class"].split())
        assert "btn-primary" in current_classes

        siblings = [a for a in anchors if a.get("aria-current") != "page"]
        assert siblings, "expected at least one non-active link to compare against"
        for sibling in siblings:
            assert "btn-primary" not in sibling["class"].split()
