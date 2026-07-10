"""Tests for the settings-driven layout configuration (MVP_CONFIG["layout"]).

Covers the three configurable layout concerns:
1. Sidebar collapse breakpoint (config default + per-page component override)
2. Sidebar collapse mode: offcanvas (default) vs icons rail
3. Navbar end widgets rendered from the component-name registry
"""

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory

from mvp.config import MVP_CONFIG
from mvp.context_processors import mvp_config as mvp_config_processor
from mvp.templatetags.mvp import breakpoint_px, sidebar_breakpoint_class


def _render(template_name):
    """Render a template with full request context (anonymous user)."""
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return render_to_string(template_name, request=request)


# ---------------------------------------------------------------------------
# Config schema and context processor
# ---------------------------------------------------------------------------


def test_layout_defaults_present():
    """Package defaults define breakpoint, collapse mode and navbar widgets."""
    layout = MVP_CONFIG["layout"]
    assert layout["sidebar"]["breakpoint"] == "lg"
    assert layout["sidebar"]["collapse"] == "offcanvas"
    assert isinstance(layout["navbar"]["end"], list)


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
def test_collapse_icons_component_override():
    """<c-app.sidebar collapse="icons"> renders the icon rail classes."""
    html = _render("tests/sidebar_icons_override.html")
    assert "mvp-sidebar--icons" in html
    assert "is-drawer-close:w-16" in html
    assert "is-drawer-close:w-0" not in html
