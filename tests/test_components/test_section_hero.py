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

Dropping the script left a second, quieter hole (issue #240): the layout it had
been doing was never CSS in this repository. The root element carried
``mvp-hero``, a class with no rule behind it in any stylesheet, so the banner
had no positioning, no centring and nothing for the overlay to be positioned
against. The component now renders daisyUI's ``hero``, which the shipped
stylesheet defines — the assertions on ``background-size`` and on the
``mvp-hero`` class went with that change, since both were pinning the old
markup rather than the behaviour.
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
    """The opening ``<div class="hero ...">`` tag on its own.

    The hero nests an overlay that renders its own ``style`` attribute, so a
    whole-document search for ``style=`` or for the default opacity value
    matches the overlay and says nothing about the hero.
    """
    match = re.search(r"<div class=\"hero [^>]*>", html)
    assert match, f"no hero element in rendered output:\n{html}"
    return match.group(0)


class TestHeroLayout:
    """The layout comes from the shipped stylesheet, not from this template."""

    def test_it_renders_daisyui_hero_markup(self):
        """``hero`` and ``hero-content`` are what the stylesheet has rules for."""
        html = render('<c-section.hero title="T" />')

        assert "hero-content" in html
        assert re.search(r'class="hero\b', html)

    def test_the_dead_class_is_gone(self):
        """``mvp-hero`` had no rule in any stylesheet — that was the defect."""
        html = render('<c-section.hero title="T" />')

        assert "mvp-hero" not in html

    def test_caller_classes_survive_alongside_the_component_class(self):
        html = render('<c-section.hero title="T" class="mt-8" />')

        assert "mt-8" in hero_tag(html)
        assert "hero" in hero_tag(html)


class TestHeroBackgroundAndHeight:
    """What parallaxx-js used to do, the component now does."""

    def test_background_image_is_applied_as_css(self):
        html = render('<c-section.hero title="T" bg-image="/static/img/x.jpg" />')

        assert "background-image: url('/static/img/x.jpg')" in hero_tag(html)

    def test_height_is_applied_as_a_minimum(self):
        html = render('<c-section.hero title="T" height="80vh" />')

        assert "min-height: 80vh" in hero_tag(html)

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


class TestHeroOverlay:
    """The overlay dims a background image so the text stays readable."""

    def test_an_overlay_covers_a_background_image(self):
        html = render('<c-section.hero title="T" bg-image="/static/img/x.jpg" />')

        assert "hero-overlay" in html
        assert "opacity: 0.5" in html

    def test_opacity_is_the_dial_on_it(self):
        html = render(
            '<c-section.hero title="T" bg-image="/static/img/x.jpg" opacity="0.2" />'
        )

        assert "opacity: 0.2" in html

    def test_no_overlay_without_a_background_image(self):
        """Nothing to dim, and an overlay over the page colour only greys it."""
        html = render('<c-section.hero title="T" />')

        assert "hero-overlay" not in html


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
