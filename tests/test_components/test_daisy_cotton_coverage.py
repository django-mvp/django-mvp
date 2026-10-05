"""The prebuilt stylesheet styles every class daisy-cotton's components can render.

The class set is read from daisy-cotton's templates, never by rendering a
component, and the committed stylesheet is read as text.
"""

from pathlib import Path

import daisy_cotton
import pytest
from daisy_cotton.templatetags.daisy_cotton import BREAKPOINTS

import mvp
from tests.daisy_cotton_classes import (
    component_classes,
    safelisted_classes,
    unstyled_classes,
)

STYLESHEET = (
    Path(next(iter(mvp.__path__))).resolve() / "static" / "css" / "django-mvp.css"
)
DAISY_COTTON_TEMPLATES = Path(next(iter(daisy_cotton.__path__))).resolve() / "templates"
PREVIOUS_RELEASE_CLASSES = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "stylesheet_classes_0_26_0.txt"
)


@pytest.fixture
def templates_dir(tmp_path):
    """A made-up daisy-cotton templates directory to write component files into."""
    path = tmp_path / "templates"
    (path / "cotton").mkdir(parents=True)
    return path


def write_component(templates_dir, name, source):
    """Write a component template under the made-up directory."""
    (templates_dir / "cotton" / name).write_text(source, encoding="utf-8")


class TestClassDerivation:
    def test_literal_classes_are_returned(self, templates_dir):
        write_component(
            templates_dir, "box.html", '<div class="box  box-bordered">x</div>'
        )

        assert component_classes(templates_dir) == {"box", "box-bordered"}

    def test_classes_in_every_attribute_ending_in_class_are_returned(
        self, templates_dir
    ):
        write_component(
            templates_dir,
            "card.html",
            '<c-vars content_class="p-4" />'
            '<div class="card"><c-slot input_class="input-ghost" /></div>',
        )

        assert component_classes(templates_dir) == {"p-4", "card", "input-ghost"}

    def test_a_class_inside_a_comment_or_an_annotation_is_left_out(self, templates_dir):
        write_component(
            templates_dir,
            "note.html",
            '{# @description Use <div class="from-annotation"> #}'
            '{% comment %}<p class="from-block"></p>{% endcomment %}'
            '<!-- <p class="from-html"> --><p class="real"></p>',
        )

        assert component_classes(templates_dir) == {"real"}

    def test_a_variation_returns_one_class_per_option(self, templates_dir):
        write_component(
            templates_dir,
            "btn.html",
            '<button class="btn {% variation size "btn" "xs,sm" %} '
            "{% variation tone 'btn' 'ghost,link' as tone_class %}\">x</button>",
        )

        assert component_classes(templates_dir) == {
            "btn",
            "btn-xs",
            "btn-sm",
            "btn-ghost",
            "btn-link",
        }

    def test_a_responsive_class_is_returned_at_every_breakpoint(self, templates_dir):
        write_component(
            templates_dir,
            "split.html",
            '<div class="{% responsive horizontal "split-horizontal" %}">x</div>',
        )

        assert component_classes(templates_dir) == {
            "split-horizontal",
            *(f"{bp}:split-horizontal" for bp in BREAKPOINTS),
        }

    def test_a_class_the_caller_supplies_adds_nothing(self, templates_dir):
        write_component(
            templates_dir,
            "plain.html",
            '<div class="plain {{ class }}" id="{{ id }}">'
            '<p class="{{ content_class }}"></p></div>',
        )

        assert component_classes(templates_dir) == {"plain"}

    def test_a_literal_joined_to_a_known_stem_returns_its_values(self, templates_dir):
        write_component(
            templates_dir,
            "rating.html",
            '<div class="mask mask-half-{{ item.half }}"></div>',
        )

        assert component_classes(templates_dir) == {
            "mask",
            "mask-half-1",
            "mask-half-2",
        }

    def test_a_literal_joined_to_an_unknown_stem_raises_naming_it(self, templates_dir):
        write_component(
            templates_dir, "grid.html", '<div class="cols-{{ count }}"></div>'
        )

        with pytest.raises(ValueError, match="cols-") as error:
            component_classes(templates_dir)

        assert "grid.html" in str(error.value)

    def test_templates_in_nested_directories_are_read(self, templates_dir):
        (templates_dir / "cotton" / "menu").mkdir()
        write_component(templates_dir, "menu/item.html", '<li class="menu-item">')

        assert component_classes(templates_dir) == {"menu-item"}


class TestUnstyledClasses:
    stylesheet = (
        ".btn{display:flex}.btn-primary{color:red}"
        ".md\\:example{x:1}.group\\/item:hover{x:1}"
        ".\\32 xl\\:example{x:1}.gap-0\\.5{x:1}"
    )

    def test_a_class_with_no_selector_is_returned_by_name(self):
        assert unstyled_classes({"made-up-class"}, self.stylesheet) == {"made-up-class"}

    def test_a_class_with_a_selector_is_not_returned(self):
        assert unstyled_classes({"btn"}, self.stylesheet) == set()

    @pytest.mark.parametrize("name", ["md:example", "group/item", "2xl:example"])
    def test_a_name_that_needs_escaping_is_found_by_its_escaped_selector(self, name):
        assert unstyled_classes({name}, self.stylesheet) == set()

    def test_a_name_that_only_prefixes_another_selector_is_returned(self):
        assert unstyled_classes({"btn-pri"}, self.stylesheet) == {"btn-pri"}

    def test_a_name_that_only_starts_an_escaped_selector_is_returned(self):
        assert unstyled_classes({"md"}, self.stylesheet) == {"md"}

    def test_a_number_inside_a_selector_is_not_a_class(self):
        assert unstyled_classes({"5"}, self.stylesheet) == {"5"}


class TestSafelistedClasses:
    def test_a_plain_entry_is_returned(self):
        assert safelisted_classes('@source inline("table-pin-rows");') == {
            "table-pin-rows"
        }

    def test_a_brace_group_is_expanded(self):
        preset = '@source inline("btn-{sm,lg}");'

        assert safelisted_classes(preset) == {"btn-sm", "btn-lg"}

    def test_a_nested_brace_group_is_expanded(self):
        preset = '@source inline("{a,b{c,d}}-x");'

        assert safelisted_classes(preset) == {"a-x", "bc-x", "bd-x"}

    def test_an_empty_option_is_expanded(self):
        preset = '@source inline("{,md:}flex");'

        assert safelisted_classes(preset) == {"flex", "md:flex"}

    def test_entries_are_collected_and_other_css_is_ignored(self):
        preset = (
            '/* @source inline("in-comment") */ .x{y:z}\n'
            '@source inline("one");\n@source "../mvp";\n@source inline("two");'
        )

        assert safelisted_classes(preset) == {"two", "one"}


class TestPrebuiltStylesheet:
    def test_every_daisy_cotton_class_is_styled(self):
        classes = component_classes(DAISY_COTTON_TEMPLATES)

        missing = unstyled_classes(classes, STYLESHEET.read_text(encoding="utf-8"))

        assert classes
        assert not missing, (
            f"{len(missing)} classes daisy-cotton's components can render have no "
            f"selector in {STYLESHEET}: {sorted(missing)}"
        )

    def test_no_class_from_the_previous_release_is_lost(self):
        lines = PREVIOUS_RELEASE_CLASSES.read_text(encoding="utf-8").splitlines()
        previous = {line for line in lines if line and not line.startswith("#")}

        missing = unstyled_classes(previous, STYLESHEET.read_text(encoding="utf-8"))

        assert previous
        assert not missing, (
            f"{len(missing)} classes the 0.26.0 stylesheet styled have no selector "
            f"in {STYLESHEET}: {sorted(missing)}. If one was removed on purpose, "
            f"delete its line from {PREVIOUS_RELEASE_CLASSES}."
        )
