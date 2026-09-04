"""Tests for the <c-dropdown> component's rendered markup.

The panel is placed by ``assets/js/dropdown.js`` at run time, which needs two
things from the template and nothing else: a hook attribute saying "this is a
dropdown to upgrade", and the declared ``halign``/``valign`` pair already
resolved into the placement string Floating UI takes.

Everything else here is a no-JS regression guard. The upgrade is progressive:
with scripting off the markup has to keep behaving exactly as it did, which it
only does while daisyUI's own classes are still on the wrapper and the panel.
Article XIII makes the rendered markup the contract, so the classes are
asserted literally rather than sampled — a partial assertion would stay green
through the one change that matters, a class quietly dropped in favour of the
script.
"""

import pytest
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


PANEL = '<ul class="menu"><li>an item</li></ul>'

# Every pair the component accepts, and the Floating UI placement it means.
# `center` is the one case with no suffix: Floating UI spells a centred
# alignment as the bare side, so `bottom-center` is not a placement and
# `bottom` is.
PLACEMENTS = {
    ("bottom", "start"): "bottom-start",
    ("bottom", "center"): "bottom",
    ("bottom", "end"): "bottom-end",
    ("top", "start"): "top-start",
    ("top", "center"): "top",
    ("top", "end"): "top-end",
    ("left", "start"): "left-start",
    ("left", "center"): "left",
    ("left", "end"): "left-end",
    ("right", "start"): "right-start",
    ("right", "center"): "right",
    ("right", "end"): "right-end",
}

every_pair = pytest.mark.parametrize(
    "valign,halign",
    list(PLACEMENTS),
    ids=[f"{valign}-{halign}" for valign, halign in PLACEMENTS],
)


class TestDropdownUpgradeHook:
    """What the script looks for, and what it is told."""

    def test_the_wrapper_carries_the_hook_attribute_once(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert html.count("data-mvp-dropdown") == 1, (
            "the hook attribute marks the wrapper and nothing else — a second "
            "occurrence means the panel or the trigger carries it too, and the "
            "script would upgrade the same dropdown twice"
        )

    @every_pair
    def test_every_accepted_pair_resolves_to_its_placement(self, valign, halign):
        html = render(
            f'<c-dropdown valign="{valign}" halign="{halign}">{PANEL}</c-dropdown>'
        )

        assert f'data-mvp-placement="{PLACEMENTS[(valign, halign)]}"' in html

    def test_the_defaults_resolve_to_bottom_start(self):
        """``valign="bottom"``/``halign="start"`` are the component's defaults,
        so a dropdown declaring neither must still hand the script a placement
        rather than an empty attribute it would have to guess from."""
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert 'data-mvp-placement="bottom-start"' in html

    def test_a_centred_dropdown_gets_no_alignment_suffix(self):
        """The one pair that is not ``<side>-<alignment>``.

        Floating UI has no ``bottom-center``: it would be parsed as an unknown
        alignment and silently positioned as if none had been asked for. This
        is asserted on its own, and not only through the table above, because
        it is the case a naive ``{{ valign }}-{{ halign }}`` gets wrong.
        """
        html = render(f'<c-dropdown halign="center">{PANEL}</c-dropdown>')

        assert 'data-mvp-placement="bottom"' in html
        assert "bottom-center" not in html


class TestDropdownKeepsItsDaisyUIMarkup:
    """The no-JS path, which is the whole reason the upgrade is a script.

    A dropdown that never gets its JavaScript still opens, because daisyUI
    positions it in CSS from these classes. Losing one of them turns the
    enhancement into a replacement.
    """

    def test_the_wrapper_renders_todays_classes(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert 'class="dropdown dropdown-bottom dropdown-start "' in html

    def test_the_panel_renders_todays_classes(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert (
            'class="dropdown-content bg-base-100 rounded-box z-50 min-w-52'
            ' shadow-lg border border-base-300 "'
        ) in html

    @every_pair
    def test_every_accepted_pair_still_emits_its_daisyui_classes(self, valign, halign):
        html = render(
            f'<c-dropdown valign="{valign}" halign="{halign}">{PANEL}</c-dropdown>'
        )

        assert f'class="dropdown dropdown-{valign} dropdown-{halign} "' in html

    def test_there_is_exactly_one_panel(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert html.count("dropdown-content") == 1


class TestDropdownProps:
    """``full``, ``hover``, ``class`` and ``content_class`` are unchanged."""

    def test_full_stretches_the_panel_to_the_trigger(self):
        html = render(f"<c-dropdown full>{PANEL}</c-dropdown>")

        assert "min-w-52 w-full shadow-lg" in html

    def test_without_full_the_panel_sizes_to_its_content(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert "w-full" not in html

    def test_hover_marks_the_wrapper(self):
        html = render(f"<c-dropdown hover>{PANEL}</c-dropdown>")

        assert 'class="dropdown dropdown-bottom dropdown-start dropdown-hover "' in html

    def test_without_hover_the_wrapper_is_not_marked(self):
        html = render(f"<c-dropdown>{PANEL}</c-dropdown>")

        assert "dropdown-hover" not in html

    def test_class_lands_on_the_wrapper(self):
        html = render(f'<c-dropdown class="w-full mt-2">{PANEL}</c-dropdown>')

        assert 'class="dropdown dropdown-bottom dropdown-start w-full mt-2"' in html

    def test_content_class_lands_on_the_panel(self):
        html = render(f'<c-dropdown content_class="w-56 mt-4">{PANEL}</c-dropdown>')

        assert "border border-base-300 w-56 mt-4" in html


class TestDropdownTrigger:
    """Both trigger paths, and where extra attributes go in each."""

    def test_extra_attributes_configure_the_default_inner_button(self):
        html = render(
            f'<c-dropdown text="Options" icon="gears" variant="primary">{PANEL}'
            "</c-dropdown>"
        )

        assert (
            '<button class="btn btn-primary  inline-flex items-center '
            'justify-center gap-2 " tabindex="0" role="button">'
        ) in html
        assert "<span>Options</span>" in html
        assert 'class="bi bi-gear"' in html
        assert "text=" not in html, (
            "trigger attributes configure the button, so none of them may be "
            "written onto the wrapper as raw HTML"
        )

    def test_a_slot_trigger_is_rendered_as_given(self):
        html = render(
            '<c-dropdown><c-slot name="button">'
            '<div tabindex="0" role="button" class="btn">Menu</div>'
            f"</c-slot>{PANEL}</c-dropdown>"
        )

        assert '<div tabindex="0" role="button" class="btn">Menu</div>' in html
        assert "<button" not in html, (
            "the slot replaces the default trigger rather than adding to it"
        )

    def test_with_a_slot_trigger_extra_attributes_fall_through_to_the_wrapper(self):
        html = render(
            '<c-dropdown id="sort" x-data="{value: 1}">'
            '<c-slot name="button"><button type="button">Sort</button></c-slot>'
            f"{PANEL}</c-dropdown>"
        )

        assert 'id="sort" x-data="{value: 1}">' in html

    def test_fall_through_attributes_do_not_displace_the_hook(self):
        """The wrapper carries both, and the placement survives the merge."""
        html = render(
            '<c-dropdown halign="end" id="sort">'
            '<c-slot name="button"><button type="button">Sort</button></c-slot>'
            f"{PANEL}</c-dropdown>"
        )

        assert "data-mvp-dropdown" in html
        assert 'data-mvp-placement="bottom-end"' in html
        assert 'id="sort"' in html
