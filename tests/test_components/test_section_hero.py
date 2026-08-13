"""Tests for the <c-section.hero> component.

The hero's background image and height used to be written out as
``data-image`` and ``data-height`` and applied by parallaxx-js, a script the
package loaded from a CDN with no version pinned. That script is gone with the
rest of the CDN runtime, so the component applies both itself. These tests pin
that contract: without them the attributes would keep rendering into markup
nothing reads, which is exactly the state the removal was meant to avoid.

The ``parallax`` and ``speed`` attributes went with the script and are covered
here too, because a removed attribute that silently keeps being accepted is
indistinguishable from one that still works.
"""

import re

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


def hero_tag(html):
    """The opening ``<div class="mvp-hero ...">`` tag on its own.

    The hero nests a ``<c-backdrop>`` that renders its own ``style`` attribute
    with an ``rgba(...)`` colour, so a whole-document search for ``style=`` or
    for the default opacity value matches the backdrop and says nothing about
    the hero.
    """
    match = re.search(r"<div class=\"mvp-hero[^>]*>", html)
    assert match, f"no mvp-hero element in rendered output:\n{html}"
    return match.group(0)


class TestHeroBackgroundAndHeight:
    """What parallaxx-js used to do, the component now does."""

    def test_background_image_is_applied_as_css(self):
        html = render('<c-section.hero title="T" bg-image="/static/img/x.jpg" />')

        assert "background-image: url('/static/img/x.jpg')" in html
        assert "background-size: cover" in html

    def test_height_is_applied_as_a_minimum(self):
        html = render('<c-section.hero title="T" height="80vh" />')

        assert "min-height: 80vh" in html

    def test_no_style_attribute_when_neither_is_given(self):
        """A bare hero renders no empty style attribute."""
        html = render('<c-section.hero title="T" />')

        assert "style=" not in hero_tag(html)

    def test_the_dead_data_attributes_are_gone(self):
        """These were parallaxx-js's inputs and nothing reads them now."""
        html = render(
            '<c-section.hero title="T" bg-image="/static/img/x.jpg" height="80vh" />'
        )

        assert "data-image" not in html
        assert "data-height" not in html
        assert "data-speed" not in html


class TestRemovedParallaxAttributes:
    """`parallax` and `speed` are gone, not merely ignored."""

    def test_parallax_no_longer_adds_a_class(self):
        html = render('<c-section.hero title="T" parallax />')

        assert "parallax" not in hero_tag(html)

    def test_speed_is_not_rendered(self):
        html = render('<c-section.hero title="T" speed="0.5" />')

        assert "0.5" not in hero_tag(html)


class TestHeroContent:
    """The parts the change did not touch still render."""

    def test_title_and_subtitle_render(self):
        html = render('<c-section.hero title="Headline" subtitle="Sub" />')

        assert "Headline" in html
        assert "Sub" in html
