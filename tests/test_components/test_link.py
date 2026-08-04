"""Tests for the <c-link> component (issue #122).

Mirrors ``test_button.py`` / ``test_class_attribute_merge.py`` conventions:
compile through the Cotton compiler and render as a real component
invocation, so attribute overrides reach ``<c-vars>`` the way a caller's
template would supply them.
"""

from html.parser import HTMLParser

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class _FirstTagAttrs(HTMLParser):
    """Collect the raw attribute list of the first `<tag>` start tag."""

    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.attrs = None

    def handle_starttag(self, tag, attrs):
        if self.attrs is None and tag == self.tag:
            self.attrs = dict(attrs)


def first_tag_attrs(html, tag):
    parser = _FirstTagAttrs(tag)
    parser.feed(html)
    assert parser.attrs is not None, f"no <{tag}> tag found in rendered output"
    return parser.attrs


class TestLinkDefaults:
    """With no attributes, `<c-link>` renders a bare `.link` anchor."""

    def test_default_renders_anchor_with_link_class(self):
        html = render('<c-link text="Sign in" />')
        attrs = first_tag_attrs(html, "a")
        assert attrs["class"].split()[0] == "link"
        assert "Sign in" in html

    def test_default_href_falls_back_to_hash(self):
        html = render('<c-link text="Sign in" />')
        attrs = first_tag_attrs(html, "a")
        assert attrs["href"] == "#"


class TestLinkVariant:
    """`variant` maps to a `link-{variant}` DaisyUI colour class."""

    def test_variant_adds_link_variant_class(self):
        html = render('<c-link text="Sign in" variant="primary" />')
        attrs = first_tag_attrs(html, "a")
        assert "link-primary" in attrs["class"].split()

    def test_no_variant_omits_variant_class(self):
        html = render('<c-link text="Sign in" />')
        attrs = first_tag_attrs(html, "a")
        assert not any(c.startswith("link-") for c in attrs["class"].split())


class TestLinkHover:
    """`hover` adds `link-hover` (underline only on hover)."""

    def test_hover_adds_link_hover_class(self):
        html = render('<c-link text="Sign in" hover />')
        attrs = first_tag_attrs(html, "a")
        assert "link-hover" in attrs["class"].split()

    def test_no_hover_omits_link_hover_class(self):
        html = render('<c-link text="Sign in" />')
        attrs = first_tag_attrs(html, "a")
        assert "link-hover" not in attrs["class"].split()


class TestLinkClassMerge:
    """A caller-supplied `class` merges into the built-in classes instead of
    producing a second, browser-ignored `class` attribute (issue #121)."""

    def test_caller_class_merges_with_built_in_classes(self):
        html = render('<c-link text="Sign in" class="dac-prose" />')
        assert html.count('class="') == 1
        attrs = first_tag_attrs(html, "a")
        assert "dac-prose" in attrs["class"].split()
        assert "link" in attrs["class"].split()


class TestLinkContent:
    """`text` and the default slot both populate the anchor's content."""

    def test_text_attribute_renders_as_content(self):
        html = render('<c-link href="/login/" text="Sign in" />')
        assert "Sign in" in html

    def test_slot_renders_as_content(self):
        html = render('<c-link href="/login/"><strong>Sign in</strong></c-link>')
        assert "<strong>Sign in</strong>" in html


class TestLinkPassthroughAttrs:
    """Undeclared attributes pass through to the anchor via `{{ attrs }}`."""

    def test_target_and_rel_pass_through(self):
        html = render(
            '<c-link href="https://example.com" text="Docs" target="_blank" rel="noopener" />'
        )
        attrs = first_tag_attrs(html, "a")
        assert attrs["target"] == "_blank"
        assert attrs["rel"] == "noopener"
