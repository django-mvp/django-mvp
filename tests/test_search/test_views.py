"""Tests for the search's addresses: the dialog's partial and the results page.

Source: mvp/search/views.py
"""

import html
import re

import pytest
from django.urls import reverse

from mvp.search.kinds import Kind, Result

pytestmark = [pytest.mark.urls("tests.urls_search"), pytest.mark.django_db]


class CountedKind(Kind):
    """A kind that finds ``count`` results for any query."""

    def __init__(self, name, count, description="", more_url=None, title="Hit"):
        self.name = name
        self.label = name.title()
        self.icon = "file"
        self.description = description
        self.count = count
        self.title = title
        self.more = more_url

    def find(self, query, request):
        return [
            Result(
                title=f"{self.title} {self.name} {n}",
                url=f"/{self.name}/{n}/",
                where=f"Where {self.name}",
                passage=f"around {query}",
            )
            for n in range(self.count)
        ]

    def more_url(self, query):
        return self.more


@pytest.fixture
def kinds(search_registry):
    """Pages (nine), people (none) and notes (one), in that order."""
    return [
        search_registry.register(CountedKind("pages", 9, description="Page text")),
        search_registry.register(CountedKind("people", 0, description="Who")),
        search_registry.register(CountedKind("notes", 1, description="Jottings")),
    ]


def hrefs(response):
    """Every address the response links to, unescaped."""
    return [
        html.unescape(href) for href in re.findall(r'href="([^"]*)"', response.text)
    ]


def hit_links(response, name):
    """The result links the response draws for one kind."""
    return [href for href in hrefs(response) if href.startswith(f"/{name}/")]


class TestSearchPanel:
    @pytest.mark.parametrize("query", ["", "   "])
    def test_an_empty_query_lists_every_active_kind(self, client, kinds, query):
        response = client.get(reverse("mvp-search-panel"), {"q": query})

        assert response.status_code == 200
        for kind in kinds:
            assert kind.label in response.text
            assert kind.description in response.text
        assert hit_links(response, "pages") == []

    def test_a_query_shows_each_group_with_its_total_and_four_results(
        self, client, kinds
    ):
        response = client.get(reverse("mvp-search-panel"), {"q": "heat"})

        assert response.status_code == 200
        assert hit_links(response, "pages") == [f"/pages/{n}/" for n in range(4)]
        assert hit_links(response, "notes") == ["/notes/0/"]
        assert ">9<" in response.text.replace(" ", "").replace("\n", "")

    def test_a_group_with_more_links_to_the_rest_on_the_results_page(
        self, client, kinds
    ):
        response = client.get(reverse("mvp-search-panel"), {"q": "heat"})

        assert f"{reverse('mvp-search')}?q=heat&kind=pages" in hrefs(response)
        assert f"{reverse('mvp-search')}?q=heat&kind=notes" not in hrefs(response)

    def test_a_kinds_own_more_url_replaces_the_results_page(
        self, client, search_registry
    ):
        search_registry.register(CountedKind("pages", 9, more_url="/browse/?q=heat"))

        response = client.get(reverse("mvp-search-panel"), {"q": "heat"})

        assert "/browse/?q=heat" in hrefs(response)
        assert f"{reverse('mvp-search')}?q=heat&kind=pages" not in hrefs(response)

    def test_a_link_to_every_result_keeps_the_query(self, client, kinds):
        response = client.get(reverse("mvp-search-panel"), {"q": "a b&c"})

        assert f"{reverse('mvp-search')}?q=a%20b%26c" in hrefs(response)

    def test_an_empty_group_is_left_out(self, client, kinds):
        response = client.get(reverse("mvp-search-panel"), {"q": "heat"})

        assert "mvp-search-g-people" not in response.text
        assert "mvp-search-g-pages" in response.text

    def test_a_query_matching_nothing_says_so(self, client, search_registry):
        search_registry.register(CountedKind("pages", 0))

        response = client.get(reverse("mvp-search-panel"), {"q": "zzz"})

        assert 'role="status"' in response.text
        assert hit_links(response, "pages") == []

    def test_the_query_is_used_as_the_search_normalises_it(self, client, kinds):
        response = client.get(reverse("mvp-search-panel"), {"q": "  heat  "})

        assert f"{reverse('mvp-search')}?q=heat&kind=pages" in hrefs(response)

    def test_markup_in_a_result_is_escaped(self, client, search_registry):
        search_registry.register(
            CountedKind("pages", 1, title="<script>alert(1)</script>")
        )

        response = client.get(reverse("mvp-search-panel"), {"q": "x"})

        assert "<script>alert(1)</script>" not in response.text
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text

    def test_markup_in_the_query_is_escaped(self, client, kinds):
        response = client.get(reverse("mvp-search-panel"), {"q": "<script>x</script>"})

        assert "<script>x</script>" not in response.text


class TestSearchView:
    def test_it_answers_an_anonymous_request(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "heat"})

        assert response.status_code == 200

    def test_every_active_kind_is_a_narrowing_link_with_its_count(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "heat"})

        assert [(kind.name, count) for kind, count in response.context["chips"]] == [
            ("pages", 9),
            ("people", 0),
            ("notes", 1),
        ]
        assert "?q=heat&kind=people" in hrefs(response)

    def test_groups_with_results_show_six_each_and_link_to_the_rest(
        self, client, kinds
    ):
        response = client.get(reverse("mvp-search"), {"q": "heat"})

        assert hit_links(response, "pages") == [f"/pages/{n}/" for n in range(6)]
        assert hit_links(response, "notes") == ["/notes/0/"]
        assert hit_links(response, "people") == []
        assert "?q=heat&kind=pages" in hrefs(response)

    def test_a_kinds_own_more_url_is_offered_beside_the_narrowing(
        self, client, search_registry
    ):
        search_registry.register(CountedKind("pages", 9, more_url="/browse/"))

        response = client.get(reverse("mvp-search"), {"q": "heat"})

        assert "/browse/" in hrefs(response)

    def test_a_narrowed_kind_is_paged_at_twenty(self, client, search_registry):
        search_registry.register(CountedKind("pages", 45))
        search_registry.register(CountedKind("notes", 3))

        first = client.get(reverse("mvp-search"), {"q": "heat", "kind": "pages"})
        last = client.get(
            reverse("mvp-search"), {"q": "heat", "kind": "pages", "page": 3}
        )

        assert len(hit_links(first, "pages")) == 20
        assert hit_links(first, "notes") == []
        assert "?q=heat&kind=pages&page=2" in hrefs(first)
        assert len(hit_links(last, "pages")) == 5
        assert hit_links(last, "pages")[0] == "/pages/40/"

    def test_a_narrowed_page_still_counts_every_kind(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "heat", "kind": "notes"})

        assert [count for kind, count in response.context["chips"]] == [9, 0, 1]

    def test_an_unknown_kind_is_treated_as_none(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "heat", "kind": "nope"})

        assert response.status_code == 200
        assert response.context["kind"] is None
        assert hit_links(response, "pages") == [f"/pages/{n}/" for n in range(6)]

    def test_a_query_matching_nothing_says_so(self, client, search_registry):
        search_registry.register(CountedKind("pages", 0))
        search_registry.register(CountedKind("notes", 0))

        response = client.get(reverse("mvp-search"), {"q": "zzz"})

        assert 'role="status"' in response.text
        assert [count for kind, count in response.context["chips"]] == [0, 0]

    def test_no_query_lists_the_kinds_and_searches_nothing(self, client, kinds):
        response = client.get(reverse("mvp-search"))

        assert response.status_code == 200
        assert "Jottings" in response.text
        assert hit_links(response, "pages") == []

    def test_the_query_is_used_as_the_search_normalises_it(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "  heat  "})

        assert response.context["q"] == "heat"

    def test_markup_in_a_result_is_escaped(self, client, search_registry):
        search_registry.register(
            CountedKind("pages", 1, title="<script>alert(1)</script>")
        )

        response = client.get(reverse("mvp-search"), {"q": "x"})

        assert "<script>alert(1)</script>" not in response.text
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text

    def test_markup_in_the_query_is_escaped(self, client, kinds):
        response = client.get(reverse("mvp-search"), {"q": "<script>x</script>"})

        assert "<script>x</script>" not in response.text
