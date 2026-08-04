"""Tests for the <c-entrance> card's width scale (issue #126).

`size` names the width the page wants; the card is capped at that width from
the `md` breakpoint up and fills its container below it. `small` is the
deprecated boolean `size` replaces, kept working so callers that predate the
scale render exactly as they did.

Sources are compiled through the Cotton compiler and invoked as component
tags (mirroring `test_class_attribute_merge.py`), not rendered as raw template
files — rendering `cotton/entrance/index.html` directly with
`render_to_string` does not route through Cotton's `<c-vars>` extraction, so
an attribute override is silently ignored and the component renders its
default instead.
"""

import re

import pytest
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

# The safelist parser lives with the issue #137 tests, which own the general
# rule that a render-time class must be declared to Tailwind. Imported rather
# than copied so both suites read the same @source inline() declarations.
from tests.test_components.test_responsive_safelist import (
    BASE_CSS,
    _responsive_classes,
    _safelisted_classes,
)

compiler = CottonCompiler()

# Every width `size` accepts, and the one a page gets when it asks for none.
# Kept in step with the scale documented in cotton/entrance/index.html and
# with the @source inline() safelist checked by test_responsive_safelist.py.
SIZES = ["sm", "md", "lg", "xl", "2xl", "3xl", "4xl"]
DEFAULT_SIZE = "2xl"


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


def card_classes(html):
    """The class list of the entrance card."""
    match = re.search(r'class="(card [^"]*)"', html)
    assert match is not None, f"no entrance card rendered in: {html!r}"
    return match.group(1).split()


class TestEntranceSize:
    """`size` sets the width the card is capped at."""

    @pytest.mark.parametrize("size", SIZES)
    def test_each_size_caps_the_card_at_that_width(self, size):
        classes = card_classes(render(f'<c-entrance size="{size}">x</c-entrance>'))
        assert f"md:max-w-{size}" in classes

    def test_size_full_leaves_the_card_uncapped(self):
        classes = card_classes(render('<c-entrance size="full">x</c-entrance>'))
        assert not [c for c in classes if c.startswith("md:max-w-")]

    def test_card_fills_its_container_below_the_md_breakpoint(self):
        """Every cap is md-prefixed, so a narrow viewport is unaffected."""
        classes = card_classes(render('<c-entrance size="sm">x</c-entrance>'))
        assert "container" in classes
        assert not [
            c for c in classes if c.startswith("max-w-")
        ], "an unprefixed cap would narrow the card on mobile too"


class TestEntranceDefaultWidth:
    """A page that asks for no width keeps the one entrance pages always had."""

    def test_default_card_is_the_historic_width(self):
        classes = card_classes(render("<c-entrance>x</c-entrance>"))
        assert f"md:max-w-{DEFAULT_SIZE}" in classes


class TestEntranceDeprecatedSmall:
    """`small`, the boolean `size` replaces, still renders what it always did."""

    def test_falsy_small_still_gives_a_full_width_card(self):
        classes = card_classes(render('<c-entrance small="">x</c-entrance>'))
        assert not [c for c in classes if c.startswith("md:max-w-")]

    def test_truthy_small_still_gives_the_historic_width(self):
        classes = card_classes(render('<c-entrance small="1">x</c-entrance>'))
        assert f"md:max-w-{DEFAULT_SIZE}" in classes


class TestEntranceSizesAreSafelisted:
    """Every width `size` can build is declared to Tailwind (issue #137's rule
    applied to this component).

    `md:max-w-{{ size }}` is assembled from an attribute at render time, and
    Tailwind's scanner only sees literal strings in source. A width missing
    from the safelist is a width missing from the shipped stylesheet, so the
    card would render with no cap at all rather than the wrong one.
    """

    @pytest.mark.parametrize("size", SIZES)
    def test_each_size_is_safelisted(self, size):
        html = render(f'<c-entrance size="{size}">x</c-entrance>')
        produced = _responsive_classes(html, "md")
        assert produced, f'<c-entrance size="{size}" /> produced no md: class'

        missing = produced - _safelisted_classes()
        assert not missing, (
            f"{sorted(missing)} not covered by any @source inline() entry in "
            f"{BASE_CSS} — Tailwind's scanner cannot see a class built at "
            "render time, so it will be missing from the shipped stylesheet"
        )


class TestEntranceFullHeight:
    """`full-height` is unaffected by the width scale."""

    def test_full_height_combines_with_a_size(self):
        classes = card_classes(
            render('<c-entrance size="4xl" full-height>x</c-entrance>')
        )
        assert "md:max-w-4xl" in classes
        assert "h-90/100" in classes

    def test_card_is_not_full_height_by_default(self):
        assert "h-90/100" not in card_classes(render("<c-entrance>x</c-entrance>"))
