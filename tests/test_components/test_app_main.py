"""Tests for ``<c-mvp.app.main>``, the shell's main content area (issue #420).

Source: mvp/templates/cotton/mvp/app/main.html

The main area is the containing block for positioned page content, so a page
can anchor an absolutely positioned element (a floating action button, an
overlay) to the content area rather than to the whole browser window. Pages
depend on that, so it is asserted against the rendered markup.
"""

from bs4 import BeautifulSoup
from django.template import engines
from django_cotton.compiler_regex import CottonCompiler


def render_main(markup):
    """Render Cotton ``markup`` and return the parsed result."""
    template = engines["django"].from_string(CottonCompiler().process(markup))
    return BeautifulSoup(template.render({}), "html.parser")


class TestAppMain:
    def test_main_is_the_containing_block_for_positioned_content(self):
        main = render_main("<c-mvp.app.main>content</c-mvp.app.main>").find("main")
        assert "relative" in main["class"]
