"""No demo template passes a former attribute name to a basic component.

A former name fails quietly: daisy-cotton's component ignores it and writes it onto
the element as an HTML attribute. The table holds only names daisy-cotton's
component does not declare. Changes of value or meaning, such as the divider's
``vertical`` and ``horizontal``, are not read here.

Source: demo/**/templates
"""

from pathlib import Path

from tests.daisy_cotton_calls import DaisyCottonCalls

DEMO = Path(__file__).resolve().parents[2] / "demo"

FORMER_ATTRIBUTES = {
    "button": {"full", "reverse", "align", "condition"},
    "avatar.group": {"size"},
    "divider": {"label", "position"},
    "menu": {"label", "grow", "responsive"},
}


def offenders(reader, directory):
    found = []
    for path, name, attrs, _ in reader.calls_with_examples(directory):
        for attr in attrs:
            if attr.lstrip(":") in FORMER_ATTRIBUTES.get(name, ()):
                found.append(f"{path.relative_to(directory)}: <c-{name}> {attr}")
    return found


class TestDemoTemplates:
    def test_no_demo_template_passes_a_former_attribute_name(self):
        reader = DaisyCottonCalls()
        found = []
        for directory in sorted(DEMO.rglob("templates")):
            found += [
                f"{directory.parent.name}/{line}"
                for line in offenders(reader, directory)
            ]

        assert found == []


class TestScanCanFail:
    def write(self, tmp_path, source):
        (tmp_path / "page.html").write_text(source, encoding="utf-8")
        return tmp_path

    def test_a_former_name_is_reported_by_template_tag_and_attribute(self, tmp_path):
        directory = self.write(tmp_path, '<c-button text="Go" full />')

        assert offenders(DaisyCottonCalls(), directory) == [
            "page.html: <c-button> full"
        ]

    def test_a_bound_former_name_is_reported(self, tmp_path):
        directory = self.write(tmp_path, '<c-divider :label="text" />')

        assert offenders(DaisyCottonCalls(), directory) == [
            "page.html: <c-divider> :label"
        ]

    def test_an_example_inside_cotton_verbatim_is_read(self, tmp_path):
        directory = self.write(
            tmp_path,
            "{% cotton:verbatim %}<c-menu grow>x</c-menu>{% endcotton:verbatim %}",
        )

        assert offenders(DaisyCottonCalls(), directory) == ["page.html: <c-menu> grow"]

    def test_a_name_daisy_cotton_declares_is_not_reported(self, tmp_path):
        directory = self.write(
            tmp_path, '<c-button text="Go" block /><c-divider text="Or" />'
        )

        assert offenders(DaisyCottonCalls(), directory) == []

    def test_a_name_on_another_tag_is_not_reported(self, tmp_path):
        directory = self.write(tmp_path, "<c-mvp.dropdown full>x</c-mvp.dropdown>")

        assert offenders(DaisyCottonCalls(), directory) == []
