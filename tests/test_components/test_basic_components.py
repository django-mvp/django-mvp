"""The sixteen basic components are answered by daisy-cotton, not by this package.

Each tag resolves to a template inside the daisy-cotton package, this package
ships no file at that component path, and a project template placed in a
``TEMPLATES["DIRS"]`` directory still takes precedence over both.

Source: mvp/templates/cotton/
"""

from pathlib import Path

import pytest

from tests.test_components.test_daisy_cotton_install import ComponentTrees

BASIC_COMPONENTS = (
    "alert.html",
    "avatar/group.html",
    "badge.html",
    "breadcrumbs/index.html",
    "breadcrumbs/item.html",
    "button.html",
    "divider.html",
    "dock/index.html",
    "dock/item.html",
    "link.html",
    "menu/index.html",
    "mockup/browser.html",
    "mockup/code/index.html",
    "mockup/code/line.html",
    "mockup/phone.html",
    "mockup/window.html",
)

PROJECT_TEMPLATES = Path(__file__).resolve().parents[1] / "project_templates"


class TestBasicComponentsComeFromDaisyCotton:
    @pytest.mark.parametrize("path", BASIC_COMPONENTS)
    def test_the_tag_resolves_inside_the_daisy_cotton_package(self, path):
        origin = ComponentTrees.origin(path)

        assert origin.is_relative_to(ComponentTrees.daisy_templates)

    @pytest.mark.parametrize("path", BASIC_COMPONENTS)
    def test_this_package_ships_no_file_at_the_component_path(self, path):
        shipped = ComponentTrees.mvp_templates / "cotton" / path

        assert not shipped.exists()


class TestDaisyCottonAttributesTakeEffect:
    def test_a_dashed_button_takes_effect(self, cotton_render_string_soup):
        soup = cotton_render_string_soup("<c-button dash>Save</c-button>")

        assert "btn-dash" in soup.find("button")["class"]

    def test_the_former_full_attribute_is_not_translated(
        self, cotton_render_string_soup
    ):
        soup = cotton_render_string_soup("<c-button full>Save</c-button>")

        assert "btn-block" not in soup.find("button")["class"]


class TestKeptComponentsRenderInsideDaisyCotton:
    def test_a_menu_entry_renders_inside_the_menu(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-menu><c-mvp.menu.item label="Page" href="/page/" /></c-menu>'
        )

        assert soup.select_one("ul.menu > li > a[href='/page/']") is not None

    def test_an_avatar_renders_inside_the_avatar_group(self, cotton_render_string_soup):
        soup = cotton_render_string_soup(
            '<c-avatar.group><c-mvp.avatar src="/a.png" alt="Ada" /></c-avatar.group>'
        )

        assert soup.select_one(".avatar-group > .avatar img[src='/a.png']") is not None


class TestProjectTemplatesTakePrecedence:
    def test_a_project_badge_replaces_daisy_cottons(
        self, settings, cotton_render_string_soup
    ):
        engine = settings.TEMPLATES[0]
        settings.TEMPLATES = [
            {**engine, "DIRS": [str(PROJECT_TEMPLATES), *engine.get("DIRS", [])]}
        ]

        soup = cotton_render_string_soup('<c-badge text="New" />')

        assert soup.find(attrs={"data-project-badge": True}) is not None
        assert soup.select_one(".badge") is None
