"""Tests for the settings-driven layout configuration (MVP_CONFIG["layout"]).

Covers the three configurable layout concerns:
1. Sidebar collapse breakpoint (config default + per-page component override)
2. Sidebar collapse mode: offcanvas (default) vs icons rail
3. Navbar end widgets rendered from the component-name registry
"""

import json
import re
import runpy
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse

import mvp.config
from mvp.config import MVP_CONFIG
from mvp.layout import LayoutConfig
from mvp.templatetags.mvp import (
    breakpoint_px,
    resolve_layout_config,
    sidebar_breakpoint_class,
    sidebar_has_breakpoint,
)


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


class TestLayoutConfigResolution:
    def test_settings_override_replaces_navbar_list(self):
        expected = [
            "mvp.actions.theme-controller",
            "mvp.actions.language-switcher",
        ]
        assert MVP_CONFIG["layout"]["navbar"]["end"] == expected
        # sibling keys not mentioned in the override keep package defaults
        assert MVP_CONFIG["layout"]["sidebar"]["breakpoint"] == "lg"


def navbar_end(client):
    """The navbar's trailing region on the home page."""
    soup = BeautifulSoup(client.get("/").content.decode(), "html.parser")
    end = soup.select_one(".mvp-header .navbar-end")
    assert end is not None, "the navbar's end region must render"
    return end


class TestNavbarWidgetNames:
    """A widget is listed by the name it would follow ``c-`` with, used as written.

    A packaged widget by its prefixed name is also proved by
    ``TestShellRendersConfig.test_navbar_widgets_render_from_config``, which
    renders the list ``tests/settings.py`` names.
    """

    @pytest.fixture
    def packaged_list(self, settings):
        settings.MVP_CONFIG = {}
        fresh = runpy.run_path(str(Path(mvp.config.__file__)))["MVP_CONFIG"]
        return fresh["layout"]["navbar"]["end"]

    @pytest.mark.django_db
    def test_the_default_list_renders_the_theme_controller_and_login(
        self, client, monkeypatch, packaged_list
    ):
        monkeypatch.setitem(MVP_CONFIG["layout"]["navbar"], "end", packaged_list)
        login = f'a[href="{reverse("account_login")}"]'

        found = navbar_end(client).select(f"[data-toggle-theme], {login}")

        assert len(found) == 2

    @pytest.mark.django_db
    def test_a_name_for_the_projects_own_component_is_used_as_written(
        self, client, monkeypatch
    ):
        monkeypatch.setitem(
            MVP_CONFIG["layout"]["navbar"], "end", ["navbar.test-widget"]
        )

        found = navbar_end(client).select("li.nav-item")

        assert len(found) == 1

    @pytest.mark.django_db
    def test_the_widgets_are_drawn_once_at_every_width(self, client):
        end = navbar_end(client)

        assert len(end.select("[data-toggle-theme]")) == 1
        for element in [end, *end.find_all(True)]:
            classes = element.get("class") or []
            assert "mvp-mobile-only" not in classes
            assert "mvp-desktop-only" not in classes


def _class_list(html, marker):
    """Return the class list of the first element whose class attribute has ``marker``."""
    match = re.search(rf'class="((?:[^"]*\s)?{re.escape(marker)}(?:\s[^"]*)?)"', html)
    assert match is not None, f"no element carrying {marker!r} rendered"
    return match.group(1).split()


class TestHeaderAndDockBackground:
    """The header and the dock take their background from MVP_CONFIG (#422)."""

    @pytest.mark.django_db
    def test_the_background_is_on_the_header_shell(self, client):
        content = client.get("/").content.decode()
        match = re.search(r'<div class="([^"]*\bmvp-header\b[^"]*)"', content)
        assert match, "mvp-header wrapper must render"
        assert MVP_CONFIG["layout"]["navbar"]["class"] in match.group(1).split(), (
            "the background must be on .mvp-header so it covers the tray "
            "and any padding around the navbar, not just the .navbar row"
        )

    @pytest.mark.django_db
    def test_the_header_renders_the_configured_class(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["layout"]["navbar"], "class", "bg-base-300")
        header = _class_list(client.get("/").content.decode(), "mvp-header")
        assert "bg-base-300" in header

    @pytest.mark.django_db
    def test_the_dock_renders_the_configured_class(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["layout"]["dock"], "class", "bg-base-300")
        soup = BeautifulSoup(client.get("/").content.decode(), "html.parser")
        assert "bg-base-300" in soup.select_one("nav.dock")["class"]

    @pytest.mark.django_db
    def test_the_dock_takes_the_package_default_when_the_setting_is_absent(
        self, client, settings
    ):
        assert "dock" not in settings.MVP_CONFIG["layout"]
        soup = BeautifulSoup(client.get("/").content.decode(), "html.parser")
        settings.MVP_CONFIG = {}
        packaged = runpy.run_path(str(Path(mvp.config.__file__)))["MVP_CONFIG"]
        expected = packaged["layout"]["dock"]["class"].split()
        assert set(expected) <= set(soup.select_one("nav.dock")["class"])

    @pytest.mark.django_db
    def test_a_header_class_attribute_beats_the_setting(self):
        header = _class_list(_render("tests/header_class_override.html"), "mvp-header")
        assert "bg-base-200" in header
        assert MVP_CONFIG["layout"]["navbar"]["class"] not in header


class TestBreakpointTags:
    @pytest.mark.parametrize(
        ("bp", "klass", "px"),
        [
            ("sm", "sm:drawer-open", 640),
            ("md", "md:drawer-open", 768),
            ("lg", "lg:drawer-open", 1024),
            ("xl", "xl:drawer-open", 1280),
            ("2xl", "2xl:drawer-open", 1536),
        ],
    )
    def test_breakpoint_tags(self, bp, klass, px):
        assert sidebar_breakpoint_class(bp) == klass
        assert breakpoint_px(bp) == px

    def test_breakpoint_tags_fall_back_to_lg(self):
        assert sidebar_breakpoint_class("bogus") == "lg:drawer-open"
        assert breakpoint_px(None) == 1024

    @pytest.mark.parametrize("bp", ["never", "none", "NEVER"])
    def test_breakpoint_never_disables_persistent_sidebar(self, bp):
        assert sidebar_breakpoint_class(bp) == ""
        assert sidebar_has_breakpoint(bp) is False


class TestTagsReadLayoutConfig:
    def test_breakpoint_px_keeps_returning_the_lg_width_for_never(self):
        assert breakpoint_px("never") == 1024
        assert LayoutConfig("never").breakpoint_px is None

    def test_resolve_layout_config_tag_returns_a_layout_config(self):
        config = resolve_layout_config("xl", "icons", False, True)
        assert isinstance(config, LayoutConfig)
        assert config.breakpoint == "xl"
        assert config.collapse == "icons"
        assert config.sticky is False
        assert config.boost is True


class TestShellRendersConfig:
    @pytest.mark.django_db
    def test_default_breakpoint_renders_lg_drawer(self, client):
        response = client.get("/")
        content = response.content.decode()
        assert "lg:drawer-open" in content

    @pytest.mark.django_db
    def test_default_collapse_is_offcanvas(self, client):
        content = client.get("/").content.decode()
        assert "mvp-sidebar--icons" not in content

    @pytest.mark.django_db
    def test_navbar_widgets_render_from_config(self, client):
        content = client.get("/").content.decode()
        # theme controller marker
        theme_pos = content.find("data-toggle-theme")
        assert theme_pos != -1, "theme controller widget must render in navbar"
        # language switcher marker (set_language form from actions.language-switcher)
        lang_pos = content.find('name="language"')
        assert lang_pos != -1, "language switcher widget must render in navbar"
        assert theme_pos < lang_pos, "widgets must render in configured order"

    @pytest.mark.django_db
    def test_drawer_state_persisted_with_breakpoint_default(self, client):
        content = client.get("/").content.decode()
        assert 'data-mvp-persist-key="mvp-app-drawer-open"' in content
        assert "min-width: 1024px" in content

    @pytest.mark.django_db
    def test_persisted_state_applied_before_alpine_hydrates(self, client):
        content = client.get("/").content.decode()
        toggle_pos = content.find('id="mvp-app-toggle"')
        script_pos = content.find("localStorage.getItem(key)")
        drawer_side_pos = content.find('class="drawer-side')
        assert toggle_pos != -1
        assert script_pos != -1, (
            "a synchronous pre-hydration script must resolve the persisted "
            "open state before first paint"
        )
        assert toggle_pos < script_pos < drawer_side_pos, (
            "the correction script must sit between the checkbox and the "
            "sidebar markup, so it runs before that markup is painted"
        )
        assert "min-width: 1024px" in content[script_pos : drawer_side_pos + 1]


class TestComponentOverrides:
    @pytest.mark.django_db
    def test_breakpoint_component_override(self):
        html = _render("tests/app_breakpoint_override.html")
        assert "xl:drawer-open" in html
        assert "lg:drawer-open" not in html
        assert "min-width: 1280px" in html

    @pytest.mark.django_db
    def test_breakpoint_never_component_override(self):
        from mvp.templatetags.mvp import SIDEBAR_BREAKPOINTS

        html = _render("tests/app_breakpoint_never.html")
        assert "data-mvp-persist-key" not in html
        assert "localStorage" not in html
        assert "matchMedia" not in html
        for klass, _px in SIDEBAR_BREAKPOINTS.values():
            assert klass not in html

    @pytest.mark.django_db
    def test_collapse_icons_component_override(self):
        html = _render("tests/sidebar_icons_override.html")
        assert "mvp-sidebar--icons" in html


class TestSidebarTitle:
    @pytest.mark.django_db
    def test_default_title_renders_nothing(self, client):
        content = client.get("/").content.decode()
        assert "mvp-sidebar-title" not in content

    @pytest.mark.django_db
    def test_title_component_override(self):
        html = _render("tests/sidebar_title_override.html")
        match = re.search(r'<span class="mvp-sidebar-title[^"]*">([^<]*)</span>', html)
        assert match is not None, "title span must render when title is set"
        assert match.group(1).strip() == "Acme Admin"
        assert "mvp-rail-hide" in match.group(0)


class TestHeaderStickiness:
    @pytest.mark.django_db
    def test_default_header_is_sticky(self, client):
        content = client.get("/").content.decode()
        assert "$store.mvp.header.stuck = window.scrollY > 0" in content

    @pytest.mark.django_db
    def test_static_header_component_override(self):
        html = _render("tests/header_static_override.html")
        assert "scrollY" not in html
        # the header still renders, just without the pinning behaviour
        assert "mvp-header" in html


class TestAnnouncementBlock:
    @pytest.mark.django_db
    def test_default_renders_nothing(self, client):
        content = client.get("/").content.decode()
        body_start = content.index("<body>") + len("<body>")
        shell_start = content.index('<div id="mvp-app"')
        assert content[body_start:shell_start].strip() == ""

    @pytest.mark.django_db
    def test_block_override_renders_before_the_app_shell(self):
        html = _render("tests/announcement_override.html")
        announcement_pos = html.find("announcement-banner-content")
        shell_pos = html.find('id="mvp-app"')
        assert announcement_pos != -1, "block override must render"
        assert shell_pos != -1
        assert announcement_pos < shell_pos, (
            "the announcement block must render outside (before) the app "
            "shell so it scrolls away independently of the sticky header"
        )


class TestFullPageFill:
    def test_page_fill_marks_itself_for_the_shell(self):
        html = _render("tests/page_fill.html")
        assert "mvp-page-fill" in html

    @pytest.mark.django_db
    def test_an_ordinary_page_carries_no_marker(self, client):
        content = client.get("/").content.decode()
        assert "mvp-page-fill" not in content


def _layout_config_payload(html, script_id="mvp-app-layout-config"):
    """Extract and parse the JSON layout-config payload from rendered HTML."""
    match = re.search(
        rf'<script id="{re.escape(script_id)}" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    return json.loads(match.group(1)) if match else None


class TestLayoutConfigPayload:
    @pytest.mark.django_db
    def test_default_page_emits_the_payload(self, client):
        content = client.get("/").content.decode()
        assert _layout_config_payload(content) is not None, (
            "the layout config payload must render"
        )

    @pytest.mark.django_db
    def test_payload_carries_every_documented_key(self, client):
        content = client.get("/").content.decode()
        payload = _layout_config_payload(content)
        assert set(payload) == {"sidebar", "header"}
        assert set(payload["sidebar"]) == {
            "breakpoint",
            "persistent",
            "breakpointPx",
            "collapse",
            "boost",
        }
        assert set(payload["header"]) == {"sticky"}

    @pytest.mark.django_db
    def test_payload_reflects_the_project_default(self, client):
        content = client.get("/").content.decode()
        payload = _layout_config_payload(content)
        assert payload["sidebar"]["breakpoint"] == "lg"
        assert payload["sidebar"]["breakpointPx"] == 1024
        assert payload["sidebar"]["collapse"] == "offcanvas"

    @pytest.mark.django_db
    def test_payload_reflects_a_per_page_breakpoint_override(self):
        html = _render("tests/app_breakpoint_override.html")
        payload = _layout_config_payload(html)
        assert payload is not None, "the layout config payload must render"
        assert payload["sidebar"]["breakpoint"] == "xl"
        assert payload["sidebar"]["breakpointPx"] == 1280


def _drawer_attrs(html):
    """The ``id="mvp-app"`` drawer element's opening tag, so its attributes
    can be asserted on directly rather than searched for anywhere in the
    page."""
    match = re.search(r'<div id="mvp-app"[^>]*>', html, re.S)
    return match.group(0) if match else None


class TestDrawerRendersLayoutAttributes:
    @pytest.mark.django_db
    def test_default_page_renders_both_attributes(self, client):
        tag = _drawer_attrs(client.get("/").content.decode())
        assert tag is not None, "the drawer element must render"
        assert 'data-mvp-breakpoint="lg"' in tag
        assert 'data-mvp-collapse="offcanvas"' in tag

    def test_a_per_page_override_of_both_knobs_is_what_renders(self):
        tag = _drawer_attrs(_render("tests/app_shell_override.html"))
        assert tag is not None
        assert 'data-mvp-breakpoint="xl"' in tag
        assert 'data-mvp-collapse="icons"' in tag

    def test_an_unrecognised_breakpoint_is_rendered_already_normalised(self):
        tag = _drawer_attrs(_render("tests/app_breakpoint_bogus.html"))
        assert tag is not None
        assert 'data-mvp-breakpoint="lg"' in tag

    def test_the_never_breakpoint_is_rendered_literally(self):
        tag = _drawer_attrs(_render("tests/app_breakpoint_never.html"))
        assert tag is not None
        assert 'data-mvp-breakpoint="never"' in tag


def _sidebar_aside_tag(html):
    """Extract the opening ``<aside>`` tag of the app sidebar."""
    match = re.search(r"<aside[^>]*class=\"mvp-sidebar[^\"]*\"[^>]*>", html, re.S)
    return match.group(0) if match else None


class TestSidebarHtmxBoost:
    @pytest.mark.django_db
    def test_no_boost_attribute_by_default(self, client):
        aside = _sidebar_aside_tag(client.get("/").content.decode())
        assert aside is not None, "the app sidebar must render"
        assert "hx-boost" not in aside

    @pytest.mark.django_db
    def test_config_enables_the_boost_attribute(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["layout"]["sidebar"], "boost", True)
        aside = _sidebar_aside_tag(client.get("/").content.decode())
        assert aside is not None
        assert 'hx-boost="true"' in aside

    @pytest.mark.django_db
    def test_boost_component_override(self):
        aside = _sidebar_aside_tag(_render("tests/sidebar_boost_override.html"))
        assert aside is not None
        assert 'hx-boost="true"' in aside
