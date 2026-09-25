"""Tests for the demo's ``library`` app, mounted at ``library/`` (FS-032, R10).

It exists so the running demo shows the host's menu entry and the dock entry
being current inside a mounted app.

Source: demo/library/, demo/urls.py, demo/menus.py
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.utils.translation.template import templatize

ROOT = Path(__file__).resolve().parent.parent.parent


def soup(response):
    return BeautifulSoup(response.content, "html.parser")


def normalised_title(response):
    return " ".join(soup(response).title.get_text().split())


def sidebar_links(response):
    links = soup(response).select(
        "aside.mvp-sidebar a.mvp-sidebar-brand, aside.mvp-sidebar ul a"
    )
    return [(a.get_text(" ", strip=True), a["href"]) for a in links]


@pytest.mark.django_db
class TestLibraryPages:
    """The library app's two pages render inside the mounted-app shell."""

    def test_landing_draws_the_library_menu_and_the_back_link(self, client):
        response = client.get("/library/")

        assert response.status_code == 200
        assert sidebar_links(response)[1:] == [
            ("Back to example.com", "/"),
            ("Catalogue", "/library/"),
            ("Reading list", "/library/reading-list/"),
        ]

    def test_landing_draws_none_of_the_demo_menu(self, client):
        labels = [text for text, _href in sidebar_links(client.get("/library/"))]

        assert "Layout" not in labels

    def test_landing_title_is_the_app_then_the_site(self, client):
        assert normalised_title(client.get("/library/")) == "Library | example.com"

    def test_reading_list_title_is_the_page_then_the_app_then_the_site(self, client):
        response = client.get("/library/reading-list/")

        assert normalised_title(response) == "Reading list | Library | example.com"


@pytest.mark.django_db
class TestLibraryEntriesInTheHostMenus:
    """The demo adds its own entries for the app, in the sidebar and the dock."""

    def test_sidebar_carries_a_library_entry_on_a_host_page(self, client):
        assert ("Library", "/library/") in sidebar_links(client.get("/layout/"))

    def test_dock_carries_a_library_entry_on_a_host_page(self, client):
        dock = soup(client.get("/layout/")).select(".dock a[href='/library/']")

        assert len(dock) == 1
        assert "dock-active" not in dock[0]["class"]

    def test_dock_entry_is_current_on_the_reading_list_page(self, client):
        dock = soup(client.get("/library/reading-list/")).select(
            ".dock a[href='/library/']"
        )

        assert "dock-active" in dock[0]["class"]

    def test_sidebar_entry_is_current_on_a_host_page_only_when_in_the_app(self, client):
        host = soup(client.get("/layout/")).select_one("aside a[href='/library/']")

        assert "menu-active" not in host["class"]


class TestBackLinkIsTranslatable:
    """``makemessages`` would extract the back link's strings (FR-026)."""

    def test_both_labels_are_in_the_extracted_catalogue(self):
        source = (
            ROOT / "mvp" / "templates" / "cotton" / "app" / "sidebar" / "back.html"
        ).read_text()

        extracted = templatize(source, origin="back.html")

        assert "gettext(u'Back to %(site_name)s')" in extracted
        assert "gettext(u'Back')" in extracted


class TestDemoAppIsDocumented:
    """The changelog and the guide say the demo has a mounted app (US-1
    scenarios 5 and 6)."""

    def test_changelog_names_the_demo_app(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()

        assert "demo/library" in changelog

    def test_guide_names_the_demo_app(self):
        guide = (ROOT / "docs" / "mounted-apps.md").read_text()

        assert "demo/library" in guide
