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
