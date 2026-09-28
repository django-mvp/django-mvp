"""Tests for the demo's ``library`` app, mounted at ``library/`` (FS-032, R10).

It exists so the running demo shows the host's menu entry being current inside
a mounted app.

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


def sidebar_hrefs(response):
    links = soup(response).select(
        "aside.mvp-sidebar a.mvp-sidebar-brand, aside.mvp-sidebar ul a"
    )
    return [a["href"] for a in links]


@pytest.mark.django_db
class TestLibraryPages:
    def test_landing_draws_the_library_menu_and_the_back_link(self, client):
        response = client.get("/library/")

        assert response.status_code == 200
        assert sidebar_hrefs(response)[1:] == [
            "/",
            "/library/",
            "/library/reading-list/",
        ]

    def test_landing_draws_none_of_the_demo_menu(self, client):
        hrefs = sidebar_hrefs(client.get("/library/"))

        assert "/layout/" not in hrefs

    def test_landing_title_is_a_bar_then_the_app_then_the_site(self, client):
        assert normalised_title(client.get("/library/")) == "| Library | example.com"

    def test_reading_list_title_is_the_page_then_the_app_then_the_site(self, client):
        response = client.get("/library/reading-list/")

        assert normalised_title(response) == "Reading list | Library | example.com"


@pytest.mark.django_db
class TestLibraryEntriesInTheHostMenus:
    def test_sidebar_carries_a_library_entry_on_a_host_page(self, client):
        assert "/library/" in sidebar_hrefs(client.get("/layout/"))

    def test_sidebar_entry_is_current_on_a_host_page_only_when_in_the_app(self, client):
        host = soup(client.get("/layout/")).select_one("aside a[href='/library/']")

        assert "menu-active" not in host["class"]


class TestBackLinkIsTranslatable:
    def test_both_labels_are_in_the_extracted_catalogue(self):
        source = (
            ROOT / "mvp" / "templates" / "cotton" / "app" / "sidebar" / "back.html"
        ).read_text()

        extracted = templatize(source, origin="back.html")

        assert "gettext(u'Back to %(site_name)s')" in extracted
        assert "gettext(u'Back')" in extracted


class TestDemoAppIsDocumented:
    def test_changelog_names_the_demo_app(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()

        assert "demo/library" in changelog

    def test_guide_names_the_demo_app(self):
        guide = (ROOT / "docs" / "mounted-apps.md").read_text()

        assert "demo/library" in guide
