"""Every call a packaged template makes to a daisy-cotton component is isolated.

A call without Cotton's ``only`` lets a page variable named after one of the
component's attributes change what the component draws. No call passes a name
the package's former components took and daisy-cotton's do not.
"""

from pathlib import Path

from django.apps import apps

from tests.daisy_cotton_calls import DaisyCottonCalls

PACKAGED_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"


def offenders(reader, directory):
    return [
        f"{path.relative_to(directory)}: <c-{name}>"
        for path, name, _, _ in reader.unisolated(directory)
    ]


class TestPackagedCalls:
    def test_every_call_to_a_daisy_cotton_component_is_isolated(self):
        reader = DaisyCottonCalls()

        assert offenders(reader, PACKAGED_TEMPLATES) == []

    def test_no_call_passes_a_former_attribute_name(self):
        reader = DaisyCottonCalls()

        assert list(reader.former_attribute_uses(PACKAGED_TEMPLATES)) == []

    def test_the_templates_hold_calls_to_daisy_cotton_components(self):
        reader = DaisyCottonCalls()

        names = {name for _, name, _, _ in reader.calls(PACKAGED_TEMPLATES)}

        assert {"button", "menu", "dock"} <= {
            name for name in names if reader.is_daisy_cotton(name)
        }

    def test_a_call_to_this_packages_component_is_not_daisy_cottons(self):
        reader = DaisyCottonCalls()

        assert not reader.is_daisy_cotton("icon")
        assert not reader.is_daisy_cotton("mvp.card")


class TestCheckCanFail:
    def write(self, tmp_path, source):
        (tmp_path / "page.html").write_text(source, encoding="utf-8")
        return tmp_path

    def test_a_call_without_only_is_reported_by_template_and_tag(self, tmp_path):
        directory = self.write(tmp_path, '<c-hover-3d class="a">x</c-hover-3d>')

        found = list(DaisyCottonCalls().unisolated(directory))

        assert [(path.name, name) for path, name, _, _ in found] == [
            ("page.html", "hover-3d")
        ]
        assert offenders(DaisyCottonCalls(), directory) == ["page.html: <c-hover-3d>"]

    def test_a_call_with_only_is_not_reported(self, tmp_path):
        directory = self.write(tmp_path, '<c-hover-3d class="a" only>x</c-hover-3d>')

        assert list(DaisyCottonCalls().unisolated(directory)) == []

    def test_the_word_only_inside_a_value_is_not_the_flag(self, tmp_path):
        directory = self.write(
            tmp_path, '<c-hover-3d class="mvp-desktop-only">x</c-hover-3d>'
        )

        assert offenders(DaisyCottonCalls(), directory) == ["page.html: <c-hover-3d>"]

    def test_a_call_in_a_comment_is_not_read(self, tmp_path):
        directory = self.write(tmp_path, "{# <c-hover-3d /> #}")

        assert list(DaisyCottonCalls().calls(directory)) == []

    def test_each_call_gives_its_attribute_names_and_flag(self, tmp_path):
        directory = self.write(tmp_path, '<c-badge color="x" :size="s" only />')

        assert list(DaisyCottonCalls().calls(directory)) == [
            (directory / "page.html", "badge", ("color", ":size"), True)
        ]
