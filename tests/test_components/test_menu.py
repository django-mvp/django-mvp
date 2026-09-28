"""Regression tests for issue #189: c-menu applied ``grow`` unconditionally.

``grow`` stretches the menu to fill a flex parent — correct for the sidebar
navigation, wrong for a menu inside a dropdown panel or card. ``grow`` is now
an opt-in ``<c-vars>`` boolean, default ``False``; the sidebar renderer
passes it explicitly.
"""

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG
from mvp.fixtures import _beautiful_soup

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    context.setdefault("mvp_config", MVP_CONFIG)
    return Template(compiler.process(source)).render(Context(context))


class TestMenuItemWithoutAnHref:
    def test_no_href_attribute_is_written_when_href_is_none(self):
        html = render('<c-menu.item :href="url" label="Placeholder" />', url=None)
        button = _beautiful_soup()(html, "html.parser").find("button")

        assert button is not None
        assert not button.has_attr("href")

    def test_an_href_draws_a_link_carrying_it(self):
        html = render('<c-menu.item href="/page/" label="Page" />')
        link = _beautiful_soup()(html, "html.parser").find("a")

        assert link["href"] == "/page/"


class TestMenuGrow:
    def test_grow_is_off_by_default(self):
        html = render('<c-menu label="Nav">item</c-menu>')

        assert "grow" not in html

    def test_grow_attribute_applies_the_grow_class(self):
        html = render('<c-menu label="Nav" grow>item</c-menu>')

        assert "grow" in html


class TestSidebarContainerPassesGrow:
    def test_sidebar_menu_container_still_grows(self):
        html = render_to_string(
            "menus/sidebar/container.html", {"children": [], "renderer": None}
        )

        assert "grow" in html


class TestSidebarContainerTakesItsNameFromContext:
    def test_the_label_comes_from_context_not_a_fixed_string(self):
        html = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Reports"},
        )
        assert 'aria-label="Reports"' in html
        assert "Main Navigation" not in html

    def test_two_different_menus_come_back_with_two_different_labels(self):
        first = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Main navigation"},
        )
        second = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Account navigation"},
        )
        assert 'aria-label="Main navigation"' in first
        assert 'aria-label="Account navigation"' in second


class TestTheSidebarDrawsOneNavigationLandmark:
    def test_the_app_sidebar_renders_exactly_one_navigation_landmark(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        html = render_to_string("cotton/app/sidebar/index.html", request=request)
        soup = _beautiful_soup()(html, "html.parser")
        landmarks = soup.find_all(
            lambda tag: tag.name == "nav" or tag.get("role") == "navigation"
        )
        assert len(landmarks) == 1


class TestDockItemForwardsAttrs:
    def test_button_variant_forwards_attrs(self):
        html = render_to_string(
            "menus/dock/item.html",
            {
                "label": "Log episode",
                "icon": "plus",
                "url": None,
                "selected": False,
                "toggle": None,
                "attrs": {"x-on:click": "modalOpen = true"},
            },
        )
        assert 'x-on:click="modalOpen = true"' in html

    def test_href_variant_forwards_attrs(self):
        html = render_to_string(
            "menus/dock/item.html",
            {
                "label": "Home",
                "icon": "house",
                "url": "/",
                "selected": False,
                "toggle": None,
                "attrs": {"data-testid": "dock-home"},
            },
        )
        assert 'data-testid="dock-home"' in html

    def test_toggle_variant_forwards_attrs(self):
        html = render_to_string(
            "menus/dock/item.html",
            {
                "label": "Menu",
                "icon": "list",
                "url": None,
                "selected": False,
                "toggle": "mvp-app-toggle",
                "attrs": {"data-testid": "dock-toggle"},
            },
        )
        assert 'data-testid="dock-toggle"' in html
