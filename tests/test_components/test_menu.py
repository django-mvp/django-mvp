"""Regression tests for issue #189: c-menu applied ``grow`` unconditionally.

``grow`` stretches the menu to fill a flex parent — correct for the sidebar
navigation, wrong for a menu inside a dropdown panel or card. ``grow`` is now
an opt-in ``<c-vars>`` boolean, default ``False``; the sidebar renderer
passes it explicitly.
"""

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
    """[#343] The container used to hard-code "Main Navigation" as its
    `c-menu` label, so every menu drawn through the sidebar renderer came
    back with the same accessible name regardless of which menu it was.
    The label now comes from the template context, the way
    ``flex_menu.renderers.BaseRenderer.get_context_data`` already resolves
    it: a `label` passed to ``{% render_menu %}``, then the menu's own
    ``extra_context["label"]``, then its name."""

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
    """[#343] ``<c-app.sidebar>`` wrapped the rendered menu in its own
    ``<nav>``, and ``c-menu`` already renders ``<ul role="navigation">`` —
    a second, unnamed landmark around the named one."""

    def test_the_app_sidebar_renders_exactly_one_navigation_landmark(self):
        """A bare ``<nav>`` is a navigation landmark by its implicit ARIA
        role, with no ``role`` attribute to find — so this counts both an
        explicit ``role="navigation"`` and a plain ``<nav>`` tag, or the
        wrapper this fix removes would go uncounted."""
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        html = render_to_string("cotton/app/sidebar/index.html", request=request)
        soup = _beautiful_soup()(html, "html.parser")
        landmarks = soup.find_all(
            lambda tag: tag.name == "nav" or tag.get("role") == "navigation"
        )
        assert len(landmarks) == 1
