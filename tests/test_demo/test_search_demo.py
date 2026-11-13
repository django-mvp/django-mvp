"""Tests for the demo's site search, using the demo's own registered kinds.

Source: demo/search.py, demo/apps.py, demo/urls.py
"""

import pytest
from django.urls import reverse

from mvp.search.checks import check_search
from tests.factories import ArticleFactory, ProductFactory


@pytest.fixture
def search(client):
    """Return a function that runs the demo's search as the given client."""

    def run(query, as_client=client):
        return as_client.get(reverse("mvp-search"), {"q": query})

    return run


@pytest.mark.django_db
class TestDemoSearchKinds:
    def test_one_query_finds_a_product_and_a_component_page(self, search):
        ProductFactory(name="Avatar frame")

        response = search("avatar")

        assert response.status_code == 200
        content = response.content.decode()
        assert "Avatar frame" in content
        assert reverse("component-doc", kwargs={"slug": "avatar"}) in content
        labels = [group.kind.label for group in response.context["groups"]]
        assert {"Products", "Components"} <= {str(label) for label in labels}

    def test_the_groups_follow_the_order_the_settings_name(self, search):
        ProductFactory(name="Avatar frame")
        ArticleFactory(title="Avatar story", status="published")

        response = search("avatar")

        names = [group.kind.name for group in response.context["groups"]]
        assert names == ["products", "articles", "components"]

    def test_an_anonymous_request_does_not_see_a_draft_article(self, search):
        ArticleFactory(title="Quarterly roundup", status="draft")
        ArticleFactory(title="Quarterly review", status="published")

        content = search("quarterly").content.decode()

        assert "Quarterly review" in content
        assert "Quarterly roundup" not in content

    def test_a_staff_request_sees_a_draft_article(self, search, staff_user, client):
        ArticleFactory(title="Quarterly roundup", status="draft")
        client.force_login(staff_user)

        content = search("quarterly").content.decode()

        assert "Quarterly roundup" in content

    def test_an_article_result_links_to_its_detail_page(self, search):
        article = ArticleFactory(title="Quarterly review", status="published")

        content = search("quarterly").content.decode()

        assert reverse("article-detail", kwargs={"pk": article.pk}) in content


class TestDemoSearchSetup:
    def test_the_demos_settings_report_nothing(self):
        assert check_search(None) == []
