"""Tests for the package's menu entries and the sidebar menu's container.

The menu container itself is daisy-cotton's. What the package still promises
is its own entries and the navigation landmark the sidebar draws around the
menu, named by the label the menu declares.

Sources: mvp/templates/cotton/mvp/menu/, mvp/templates/menus/sidebar/
"""

from bs4 import BeautifulSoup
from django.template import Context, Template
from django.template.loader import render_to_string
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
        html = render('<c-mvp.menu.item :href="url" label="Placeholder" />', url=None)
        button = _beautiful_soup()(html, "html.parser").find("button")

        assert button is not None
        assert not button.has_attr("href")

    def test_an_href_draws_a_link_carrying_it(self):
        html = render('<c-mvp.menu.item href="/page/" label="Page" />')
        link = _beautiful_soup()(html, "html.parser").find("a")

        assert link["href"] == "/page/"


class TestSidebarContainerTakesItsNameFromContext:
    def test_the_label_comes_from_context_not_a_fixed_string(self):
        html = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Reports"},
        )
        soup = BeautifulSoup(html, "html.parser")

        assert soup.find("nav")["aria-label"] == "Reports"

    def test_the_menu_sits_inside_the_named_navigation_landmark(self):
        html = render_to_string(
            "menus/sidebar/container.html",
            {"children": [], "renderer": None, "label": "Reports"},
        )
        soup = BeautifulSoup(html, "html.parser")

        assert soup.select_one("nav[aria-label='Reports'] > ul.menu") is not None


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
