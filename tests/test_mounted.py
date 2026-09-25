"""Tests for ``mvp.mounted`` — mounting one django-mvp app inside another.

Source: mvp/mounted.py
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser

from mvp.menus import AppMenu

PLAIN_URLCONF = "tests.urls_mounted_plain"


@pytest.mark.django_db
@pytest.mark.urls(PLAIN_URLCONF)
class TestFixtureApp:
    """The fixture app's two pages render through a plain ``include()``."""

    def test_index_page_renders(self, client):
        response = client.get("/mounted/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-index"' in response.content

    def test_detail_page_renders(self, client):
        response = client.get("/mounted/detail/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-detail"' in response.content


def normalised_title(response):
    """The ``<title>`` text with the template's whitespace collapsed."""
    soup = BeautifulSoup(response.content, "html.parser")
    return " ".join(soup.title.get_text().split())


def sidebar_links(response):
    """Every ``(text, href)`` link inside the sidebar, header brand included."""
    soup = BeautifulSoup(response.content, "html.parser")
    sidebar = soup.select_one("aside.mvp-sidebar")
    return [(a.get_text(" ", strip=True), a["href"]) for a in sidebar.select("a")]


def app_menu_links(rf):
    """The ``(label, url)`` of every visible leaf ``AppMenu`` resolves to."""
    request = rf.get("/")
    request.user = AnonymousUser()
    links = []

    def walk(item):
        for child in item.visible_children:
            if child.has_url:
                links.append((child.extra_context["label"], child.url))
            walk(child)

    walk(AppMenu.process(request))
    return links


@pytest.mark.django_db
@pytest.mark.urls(PLAIN_URLCONF)
class TestPageBelongingToNoApp:
    """A project that mounts nothing renders as it always has (FR-010, SC-004).

    Pinned before the shell learns about mounted apps, and green at every
    commit after.
    """

    def test_sidebar_carries_the_app_menu_entries_and_nothing_else(self, client, rf):
        response = client.get("/layout/")

        links = sidebar_links(response)

        brand, *rest = links
        assert brand == ("", "/")
        menu_links = [link for link in rest if link in app_menu_links(rf)]
        assert menu_links == app_menu_links(rf)
        assert links[1:4] == [
            ("Home", "/"),
            ("Layout", "/layout/"),
            ("Theme Customization", "/theme/"),
        ]

    def test_sidebar_draws_no_mounted_app_entries(self, client):
        response = client.get("/mounted/")

        texts = [text for text, _href in sidebar_links(response)]

        assert "Mounted Index" not in texts
        assert "Mounted Detail" not in texts

    def test_sidebar_has_no_back_link(self, client):
        response = client.get("/layout/")

        assert "Back to" not in response.content.decode()

    def test_titled_page_title_is_the_page_then_the_site(self, client):
        response = client.get("/layout/")

        assert normalised_title(response) == "Layout Demo | example.com"

    def test_titled_fixture_page_title_is_the_page_then_the_site(self, client):
        response = client.get("/mounted/detail/")

        assert normalised_title(response) == "Detail | example.com"

    def test_untitled_page_title_is_the_site_alone_after_a_bar(self, client):
        response = client.get("/mounted/")

        assert normalised_title(response) == "| example.com"
