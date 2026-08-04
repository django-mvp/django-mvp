"""Regression tests for issue #121: components that hardcode a literal
``class="..."`` on their root element *and* also spread ``{{ attrs }}`` on
that same element must declare ``class`` as a ``<c-vars>`` variable and merge
it into the hardcoded string.

Without that, an undeclared ``class`` passed by the caller is not stripped
from ``{{ attrs }}`` by Cotton, so the element ends up with **two**
``class="..."`` attributes. Per the HTML spec a duplicate attribute is
ignored and the browser keeps only the first, so the caller's classes are
silently dropped with no error.

Sources are compiled through the Cotton compiler (mirroring
``test_form_field.py``) so the tests exercise each component exactly as a
template invocation would — rendering the component's own template file
directly, as ``test_render_all.py`` does, never triggers Cotton's c-vars /
``attrs`` extraction and would not reproduce this bug.

Covers every component the audit for #121 found with this exact shape:
c-text, c-menu, c-menu.item, c-dock.item, c-page.list.empty and
c-layout.sidebar. Peers that already merge ``{{ class }}`` correctly
(c-button, c-badge, c-alert, ...) are unaffected and untouched here.
"""

from html.parser import HTMLParser

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

from mvp.config import MVP_CONFIG

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    context.setdefault("mvp_config", MVP_CONFIG)
    return template.Template(compiler.process(source)).render(Context(context))


class _FirstTagAttrs(HTMLParser):
    """Collect the raw attribute list of the first `<tag>` start tag.

    A regex over `[^>]*` is not safe here: some components embed Alpine.js
    expressions (e.g. `x-init="... => ..."`) with a literal `>` inside a
    quoted attribute value, which truncates a naive regex match before the
    real end of the opening tag. HTMLParser respects quoting, so it finds
    the tag's true boundary and — unlike a browser — reports every
    occurrence of a repeated attribute rather than silently dropping it,
    which is exactly what this bug needs to be caught.
    """

    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.attrs = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is None and tag == self.tag:
            self.attrs = attrs


def class_attrs_on(html, tag):
    """Every ``class="..."`` value found on the first ``<tag ...>`` open tag."""
    parser = _FirstTagAttrs(tag)
    parser.feed(html)
    assert parser.attrs is not None, f"no <{tag}> tag found in rendered output"
    return [value for name, value in parser.attrs if name == "class"]


class TestClassAttributeMerge:
    """A caller-supplied ``class`` merges into the built-in classes instead
    of producing a second, browser-ignored ``class`` attribute."""

    def test_text_merges_caller_class(self):
        html = render('<c-text class="dac-prose">hi</c-text>')
        attrs = class_attrs_on(html, "p")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "dac-prose" in attrs[0]
        assert "text-base" in attrs[0]

    def test_menu_merges_caller_class(self):
        html = render('<c-menu class="my-menu">items</c-menu>')
        attrs = class_attrs_on(html, "ul")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-menu" in attrs[0]
        assert "menu" in attrs[0]

    def test_dock_item_toggle_variant_merges_caller_class(self):
        html = render('<c-dock.item toggle="sidebar-toggle" class="my-dock-item" />')
        attrs = class_attrs_on(html, "label")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-dock-item" in attrs[0]

    def test_dock_item_href_variant_merges_caller_class(self):
        html = render('<c-dock.item href="/" class="my-dock-item" />')
        attrs = class_attrs_on(html, "a")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-dock-item" in attrs[0]

    def test_dock_item_button_variant_merges_caller_class(self):
        html = render('<c-dock.item class="my-dock-item" />')
        attrs = class_attrs_on(html, "button")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-dock-item" in attrs[0]

    def test_menu_item_merges_caller_class(self):
        html = render('<c-menu.item label="X" class="my-menu-item" />')
        attrs = class_attrs_on(html, "button")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-menu-item" in attrs[0]
        assert "group" in attrs[0]

    def test_page_list_empty_merges_caller_class(self):
        html = render(
            '<c-page.list.empty heading="Nothing here" class="my-empty-state" />'
        )
        attrs = class_attrs_on(html, "div")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-empty-state" in attrs[0]
        assert "w-full" in attrs[0]

    def test_layout_sidebar_merges_caller_class(self):
        html = render(
            '<c-layout.sidebar id="test-sidebar" class="my-sidebar">body</c-layout.sidebar>'
        )
        attrs = class_attrs_on(html, "div")
        assert len(attrs) == 1, f"expected one class attribute, found {attrs}"
        assert "my-sidebar" in attrs[0]
        assert "drawer" in attrs[0]
