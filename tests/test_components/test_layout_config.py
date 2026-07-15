"""Tests for the settings-driven layout configuration (MVP_CONFIG["layout"]).

Covers the three configurable layout concerns:
1. Sidebar collapse breakpoint (config default + per-page component override)
2. Sidebar collapse mode: offcanvas (default) vs icons rail
3. Navbar end widgets rendered from the component-name registry
"""

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from mvp.config import MVP_CONFIG
from mvp.context_processors import mvp_config as mvp_config_processor
from mvp.templatetags.mvp import (
    breakpoint_px,
    sidebar_breakpoint_class,
    sidebar_has_breakpoint,
    sidebar_navbar_toggle_class,
)


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


def _navbar_toggle_class(html):
    """Extract the class list of the navbar's sidebar-toggle button.

    That toggle is the one carrying the "Open sidebar" aria-label (the sidebar
    header and the drawer overlay reuse the same ``for`` target with different
    labels).
    """
    match = re.search(
        r'<label[^>]*aria-label="Open sidebar"[^>]*?class="([^"]*)"', html, re.S
    )
    return " ".join(match.group(1).split()) if match else None


# ---------------------------------------------------------------------------
# Config schema and context processor
# ---------------------------------------------------------------------------


def test_layout_defaults_present():
    """Package defaults define breakpoint, collapse mode and navbar widgets."""
    layout = MVP_CONFIG["layout"]
    assert layout["sidebar"]["breakpoint"] == "lg"
    assert layout["sidebar"]["collapse"] == "offcanvas"
    assert layout["sidebar"]["title"] is None
    assert isinstance(layout["navbar"]["end"], list)
    assert isinstance(layout["sidebar"]["footer"], list)


def test_settings_override_replaces_navbar_list():
    """tests/settings.py MVP_CONFIG overrides the navbar widget list wholesale."""
    assert MVP_CONFIG["layout"]["navbar"]["end"] == [
        "actions.theme-controller",
        "actions.language-switcher",
    ]
    # sibling keys not mentioned in the override keep package defaults
    assert MVP_CONFIG["layout"]["sidebar"]["breakpoint"] == "lg"


def test_context_processor_exposes_structured_config():
    """The context processor provides MVP_CONFIG as a dict, not JSON."""
    context = mvp_config_processor(RequestFactory().get("/"))
    assert context["mvp_config"] is MVP_CONFIG


# ---------------------------------------------------------------------------
# Breakpoint templatetags
# ---------------------------------------------------------------------------


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
def test_breakpoint_tags(bp, klass, px):
    assert sidebar_breakpoint_class(bp) == klass
    assert breakpoint_px(bp) == px


def test_breakpoint_tags_fall_back_to_lg():
    assert sidebar_breakpoint_class("bogus") == "lg:drawer-open"
    assert breakpoint_px(None) == 1024


@pytest.mark.parametrize("bp", ["never", "none", "NEVER"])
def test_breakpoint_never_disables_persistent_sidebar(bp):
    """"never"/"none" emit no drawer-open class and no navbar-toggle hiding."""
    assert sidebar_breakpoint_class(bp) == ""
    assert sidebar_has_breakpoint(bp) is False
    assert sidebar_navbar_toggle_class(bp, "offcanvas") == ""
    assert sidebar_navbar_toggle_class(bp, "icons") == ""


def test_navbar_toggle_class_hides_at_breakpoint():
    """Navbar toggle hides at the breakpoint: always for the icons rail,
    only while open for offcanvas (a hidden sidebar has no toggle left)."""
    assert sidebar_navbar_toggle_class("md", "icons") == "md:hidden"
    assert sidebar_navbar_toggle_class("md", "offcanvas") == "md:is-drawer-open:hidden"
    # unknown breakpoints fall back to lg, mirroring sidebar_breakpoint_class
    assert sidebar_navbar_toggle_class("bogus", "icons") == "lg:hidden"


# ---------------------------------------------------------------------------
# Rendered layout: defaults from config
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_default_breakpoint_renders_lg_drawer(client):
    """With no override, the drawer uses the configured lg breakpoint."""
    response = client.get("/")
    content = response.content.decode()
    assert "lg:drawer-open" in content


@pytest.mark.django_db
def test_default_collapse_is_offcanvas(client):
    """Default collapse mode slides the sidebar fully away (w-0, no rail)."""
    content = client.get("/").content.decode()
    assert "is-drawer-close:w-0" in content
    assert "mvp-sidebar--icons" not in content


@pytest.mark.django_db
def test_navbar_widgets_render_from_config(client):
    """Configured navbar end components render, in declaration order."""
    content = client.get("/").content.decode()
    # theme controller marker
    theme_pos = content.find("data-toggle-theme")
    assert theme_pos != -1, "theme controller widget must render in navbar"
    # language switcher marker (set_language form from actions.language-switcher)
    lang_pos = content.find('name="language"')
    assert lang_pos != -1, "language switcher widget must render in navbar"
    assert theme_pos < lang_pos, "widgets must render in configured order"


@pytest.mark.django_db
def test_sidebar_footer_widgets_render_from_config(client):
    """Configured sidebar footer components render in a centered, wrapping row."""
    content = client.get("/").content.decode()
    # the footer actions live in a centered wrapping flex row
    assert re.search(
        r'<div class="flex flex-wrap items-center justify-center gap-2">', content
    ), "sidebar footer must wrap its actions in a centered wrapping flex row"
    # the configured component renders (theme controller marker)
    assert "data-toggle-theme" in content


@pytest.mark.django_db
def test_drawer_state_persisted_with_breakpoint_default(client):
    """Drawer open state persists via Alpine and defaults by viewport width."""
    content = client.get("/").content.decode()
    assert "$persist" in content
    assert "min-width: 1024px" in content


# ---------------------------------------------------------------------------
# Rendered layout: per-page component attribute overrides
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_breakpoint_component_override():
    """<c-app breakpoint="xl"> beats the configured default."""
    html = _render("tests/app_breakpoint_override.html")
    assert "xl:drawer-open" in html
    assert "lg:drawer-open" not in html
    assert "min-width: 1280px" in html


@pytest.mark.django_db
def test_overlay_state_is_transient_desktop_state_persists():
    """Only the desktop (persistent) open state survives reloads: the drawer
    seeds closed, then x-init restores the persisted state at/above the
    breakpoint; $watch writes back only at desktop widths."""
    content = _render("tests/app_breakpoint_override.html")
    assert "desktopOpen" in content
    assert "$persist(true)" in content
    assert "open: false" in content
    assert "$watch" in content


@pytest.mark.django_db
def test_breakpoint_never_component_override():
    """<c-app breakpoint="never"> renders an overlay-only drawer: no
    *:drawer-open class, a closed initial Alpine state, and no persistence
    (overlay drawers are transient)."""
    from mvp.templatetags.mvp import SIDEBAR_BREAKPOINTS

    html = _render("tests/app_breakpoint_never.html")
    assert "{ open: false }" in html
    assert "$persist" not in html
    assert "matchMedia" not in html
    for klass, _px in SIDEBAR_BREAKPOINTS.values():
        assert klass not in html


@pytest.mark.django_db
def test_collapse_icons_component_override():
    """<c-app.sidebar collapse="icons"> renders the icon rail classes."""
    html = _render("tests/sidebar_icons_override.html")
    assert "mvp-sidebar--icons" in html
    assert "is-drawer-close:w-16" in html
    assert "is-drawer-close:w-0" not in html


# ---------------------------------------------------------------------------
# Sidebar title beside the brand icon
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_default_title_renders_nothing(client):
    """The default None title renders no title element in the sidebar header."""
    content = client.get("/").content.decode()
    assert "mvp-sidebar-title" not in content


@pytest.mark.django_db
def test_title_component_override():
    """<c-app.sidebar title="..."> renders the text beside the brand icon,
    marked mvp-rail-hide so it hides when collapsed to an icon rail."""
    html = _render("tests/sidebar_title_override.html")
    match = re.search(r'<span class="mvp-sidebar-title[^"]*">([^<]*)</span>', html)
    assert match is not None, "title span must render when title is set"
    assert match.group(1).strip() == "Acme Admin"
    assert "mvp-rail-hide" in match.group(0)


# ---------------------------------------------------------------------------
# Navbar sidebar-toggle follows the resolved layout knobs (issue #114)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_default_navbar_toggle_matches_config(client):
    """With no override the navbar toggle mirrors the config default: the
    offcanvas sidebar hides its navbar toggle only while open, at ``lg``."""
    toggle = _navbar_toggle_class(client.get("/").content.decode())
    assert toggle is not None
    assert "lg:is-drawer-open:hidden" in toggle


@pytest.mark.django_db
def test_navbar_toggle_follows_shell_override():
    """A per-page shell override of breakpoint+collapse reaches the navbar
    toggle, not just the drawer/sidebar (regression for issue #114).

    breakpoint=xl + collapse=icons => the toggle hides at ``xl`` unconditionally
    (the icon rail keeps its own toggle), i.e. ``xl:hidden`` — never the default
    ``lg:``-prefixed class."""
    html = _render("tests/app_shell_override.html")
    # sanity: the drawer and rail honour the override too
    assert "xl:drawer-open" in html
    assert "mvp-sidebar--icons" in html
    # the navbar toggle must agree with them
    toggle = _navbar_toggle_class(html)
    assert toggle is not None
    assert "xl:hidden" in toggle
    assert "lg:" not in toggle
    assert "is-drawer-open" not in toggle


# ---------------------------------------------------------------------------
# Navbar sticky vs static header
# ---------------------------------------------------------------------------


def test_navbar_sticky_default_present():
    """Package default pins the header to the top of the viewport."""
    assert MVP_CONFIG["layout"]["navbar"]["sticky"] is True


@pytest.mark.django_db
def test_default_header_is_sticky(client):
    """With the default config the header pins on scroll (sticky + scroll shadow)."""
    content = client.get("/").content.decode()
    assert "mvp-header w-full sticky z-10 top-0" in content
    assert "stuck = window.scrollY > 0" in content


@pytest.mark.django_db
def test_static_header_component_override():
    """<c-app.header :sticky="False"> drops the sticky classes and scroll logic."""
    html = _render("tests/header_static_override.html")
    assert "sticky z-10 top-0" not in html
    assert "scrollY" not in html
    # the header still renders, just without the pinning behaviour
    assert "mvp-header w-full" in html
