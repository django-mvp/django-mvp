"""Regression tests for issue #137: components that build a breakpoint-prefixed
class at render time (``{% responsive vertical "divider-horizontal" %}``, or the
inline ``{{ row }}:flex-row`` pattern in ``cotton/toolbar.html``) must have every
class they can produce covered by an ``@source inline()`` entry in
``mvp/tailwind/base.css``. Tailwind's scanner only sees literal strings in
source, so a class assembled from a template variable is invisible to it and
silently missing from the shipped stylesheet unless explicitly safelisted.

Sources are compiled through the Cotton compiler and invoked as component tags
(mirroring ``test_class_attribute_merge.py``), not rendered as raw template
files — rendering ``cotton/toolbar.html`` directly with ``render_to_string``
does not route through Cotton's ``<c-vars>`` / ``attrs`` extraction, so an
attribute override like ``row="lg"`` is silently ignored and the component
renders its default instead. That would make this test pass regardless of
which breakpoint was requested, defeating its purpose.

The safelist-membership check (``_safelisted_classes``) parses the same
``@source inline()`` declarations Tailwind itself reads, brace-expansion
included, so this test fails the same way the shipped CSS would: a class
missing from the safelist is a class missing from the build.
"""

import itertools
import re
from pathlib import Path

import pytest
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

import mvp

compiler = CottonCompiler()

BASE_CSS = Path(next(iter(mvp.__path__))).resolve() / "tailwind" / "base.css"

BREAKPOINTS = ["sm", "md", "lg", "xl", "2xl"]

_SOURCE_INLINE_RE = re.compile(r'@source inline\("([^"]+)"\);')
_BRACE_RE = re.compile(r"\{([^{}]*)\}")


def _render(source, **context):
    """Compile a Cotton source string and render it as a real component
    invocation, so attribute overrides reach `<c-vars>` the way a caller's
    template would supply them."""
    return template.Template(compiler.process(source)).render(Context(context))


def _expand_braces(pattern):
    """Expand every `{a,b,c}` group in a Tailwind `@source inline()` pattern
    into the full set of literal class strings it declares safelisted."""
    # Split the pattern into the literal text between brace groups, so
    # reassembly never has to go through a regex replacement string (which
    # would mishandle a value containing a backslash or a digit after one).
    segments = _BRACE_RE.split(pattern)  # [literal, group, literal, group, ..., literal]
    literals, groups = segments[0::2], segments[1::2]
    options = [group.split(",") for group in groups]

    if not options:
        return {pattern}

    expanded = set()
    for combo in itertools.product(*options):
        parts = [literals[0]]
        for value, literal in zip(combo, literals[1:]):
            parts.append(value)
            parts.append(literal)
        expanded.add("".join(parts))
    return expanded


def _safelisted_classes():
    """Every literal class declared by an `@source inline()` entry in the
    packaged Tailwind preset."""
    css = BASE_CSS.read_text(encoding="utf-8")
    classes = set()
    for pattern in _SOURCE_INLINE_RE.findall(css):
        classes |= _expand_braces(pattern)
    return classes


def _responsive_classes(html, breakpoint):
    """Every `{breakpoint}:...` class token found in rendered HTML."""
    class_attrs = re.findall(r'class="([^"]*)"', html)
    tokens = set()
    for value in class_attrs:
        tokens |= set(value.split())
    return {token for token in tokens if token.startswith(f"{breakpoint}:")}


class TestResponsiveClassesAreSafelisted:
    """Every breakpoint-prefixed class a component can construct at render
    time is covered by the packaged Tailwind safelist."""

    @pytest.mark.parametrize("bp", BREAKPOINTS)
    def test_divider_vertical_breakpoint_is_safelisted(self, bp):
        html = _render(f'<c-divider vertical="{bp}" />')
        produced = _responsive_classes(html, bp)
        assert produced, f'<c-divider vertical="{bp}" /> produced no {bp}: class'

        missing = produced - _safelisted_classes()
        assert not missing, (
            f"{sorted(missing)} not covered by any @source inline() entry in "
            f"{BASE_CSS} — Tailwind's scanner cannot see a class built at "
            "render time, so it will be missing from the shipped stylesheet"
        )

    @pytest.mark.parametrize("bp", BREAKPOINTS)
    def test_toolbar_row_breakpoint_is_safelisted(self, bp):
        html = _render(f'<c-toolbar row="{bp}" />')
        produced = _responsive_classes(html, bp)
        assert produced, f'<c-toolbar row="{bp}" /> produced no {bp}: class'

        missing = produced - _safelisted_classes()
        assert not missing, (
            f"{sorted(missing)} not covered by any @source inline() entry in "
            f"{BASE_CSS} — Tailwind's scanner cannot see a class built at "
            "render time, so it will be missing from the shipped stylesheet"
        )
