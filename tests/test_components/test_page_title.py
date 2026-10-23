"""Tests for ``c-mvp.page.title``: the component every page's title is drawn by.

Sources are compiled through the Cotton compiler, as ``test_page_info.py`` does, so
``<c-vars>`` defaults and ``attrs`` extraction work the way a real template call works.
"""

import pytest
from bs4 import BeautifulSoup
from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string, render it and parse the result."""
    html = template.Template(compiler.process(source)).render(Context(context))
    return BeautifulSoup(html, "html.parser")


class TestPageTitleArguments:
    def test_the_title_is_the_heading(self):
        soup = render('<c-mvp.page.title title="Unique title" />')

        assert [h1.get_text(strip=True) for h1 in soup.find_all("h1")] == [
            "Unique title"
        ]

    def test_the_eyebrow_is_drawn_once(self):
        soup = render('<c-mvp.page.title title="T" eyebrow="Unique eyebrow" />')

        assert str(soup).count("Unique eyebrow") == 1

    def test_the_lead_is_drawn_once(self):
        soup = render('<c-mvp.page.title title="T" lead="Unique lead" />')

        assert str(soup).count("Unique lead") == 1

    def test_the_info_text_is_drawn_once_in_a_dialog(self):
        soup = render('<c-mvp.page.title title="T" info="Unique info" />')

        assert str(soup).count("Unique info") == 1
        assert soup.select_one("dialog").get_text().count("Unique info") == 1

    def test_the_info_actions_are_drawn_in_the_dialog(self):
        soup = render(
            '<c-mvp.page.title title="T" info="Body" :info_actions="actions" />',
            actions=[{"text": "Guide", "href": "/unique-guide/"}],
        )

        links = soup.select_one("dialog").select('a[href="/unique-guide/"]')
        assert len(links) == 1

    def test_the_heading_slot_replaces_the_title(self):
        soup = render(
            '<c-mvp.page.title title="From the attribute">'
            '<c-slot name="heading">From the slot</c-slot>'
            "</c-mvp.page.title>"
        )

        assert [h1.get_text(strip=True) for h1 in soup.find_all("h1")] == [
            "From the slot"
        ]
        assert "From the attribute" not in str(soup)

    def test_an_empty_heading_slot_falls_back_to_the_title(self):
        soup = render(
            '<c-mvp.page.title title="From the attribute">'
            '<c-slot name="heading"></c-slot>'
            "</c-mvp.page.title>"
        )

        assert [h1.get_text(strip=True) for h1 in soup.find_all("h1")] == [
            "From the attribute"
        ]

    def test_the_info_trigger_slot_replaces_the_trigger_drawn_from_info(self):
        soup = render(
            '<c-mvp.page.title title="T" info="Dialog text">'
            '<c-slot name="info_trigger"><button id="own-trigger" type="button">'
            "</button></c-slot>"
            "</c-mvp.page.title>"
        )

        assert len(soup.select("#own-trigger")) == 1
        assert soup.find("dialog") is None

    def test_the_info_trigger_is_a_sibling_of_the_heading(self):
        soup = render('<c-mvp.page.title title="T" info="Body" />')

        heading = soup.find("h1")
        assert heading.find("button") is None
        assert heading.parent.find("button") is not None

    def test_the_actions_slot_is_drawn_once(self):
        soup = render(
            '<c-mvp.page.title title="T">'
            '<c-slot name="actions"><a id="own-action" href="/go/">Go</a></c-slot>'
            "</c-mvp.page.title>"
        )

        assert len(soup.select("#own-action")) == 1

    def test_an_argument_given_nowhere_draws_no_element(self):
        soup = render('<c-mvp.page.title title="Only a title" />')

        assert soup.find_all(["p", "button", "dialog", "a"]) == []
        empty = [
            element
            for element in soup.find_all(True)
            if not element.get_text(strip=True) and not element.find(True)
        ]
        assert empty == []

    def test_a_bare_call_ignores_same_named_variables_in_the_callers_context(self):
        soup = render(
            '<c-mvp.page.title title="Called title" />',
            layout="a.layout.that.does.not.exist",
            title="Leaked title",
            heading="Leaked heading",
            eyebrow="Leaked eyebrow",
            lead="Leaked lead",
            info="Leaked info",
            actions="Leaked actions",
            inline_actions=True,
        )

        assert "Leaked" not in str(soup)
        assert [h1.get_text(strip=True) for h1 in soup.find_all("h1")] == [
            "Called title"
        ]

    def test_an_undeclared_attribute_lands_on_the_layouts_root_element(self):
        soup = render('<c-mvp.page.title title="T" id="product-heading" />')

        root = soup.find(True)
        assert root.get("id") == "product-heading"
        assert len(soup.select("#product-heading")) == 1

    @pytest.mark.parametrize("layout", ["default", "inline", "centred", "compact"])
    def test_an_undeclared_attribute_reaches_the_root_of_every_shipped_layout(
        self, layout
    ):
        soup = render(
            f'<c-mvp.page.title layout="{layout}" title="T" id="product-heading" />'
        )

        assert soup.find(True).get("id") == "product-heading"


LAYOUTS = ["default", "inline", "centred", "compact"]

ARGUMENTS = {
    "eyebrow": 'eyebrow="Unique eyebrow"',
    "title": 'title="Unique title"',
    "lead": 'lead="Unique lead"',
    "info": 'info="Unique info"',
}
OWN_ACTION = (
    '<c-slot name="actions"><a id="own-action" href="/go/">Go</a></c-slot>'
)


def render_layout(layout, leave_out=(), actions=True):
    """Render a title in ``layout`` with every argument but those left out."""
    attributes = " ".join(
        value for name, value in ARGUMENTS.items() if name not in leave_out
    )
    slot = OWN_ACTION if actions else ""
    return render(
        f'<c-mvp.page.title layout="{layout}" {attributes}>{slot}</c-mvp.page.title>'
    )


def empty_elements(soup):
    """The block elements of ``soup`` that hold no text and no element."""
    return [
        element
        for element in soup.find_all(["div", "p"])
        if not element.get_text(strip=True) and not element.find(True)
    ]


@pytest.mark.parametrize("layout", LAYOUTS)
class TestPageTitleLayouts:
    def test_every_argument_given_is_drawn_once(self, layout):
        soup = render_layout(layout)

        assert soup.select_one(".mvp-page-eyebrow").get_text(strip=True) == (
            "Unique eyebrow"
        )
        assert soup.select_one("h1").get_text(strip=True) == "Unique title"
        assert soup.select_one(".mvp-page-lead").get_text(strip=True) == "Unique lead"
        assert "Unique info" in soup.select_one("dialog").get_text()
        assert len(soup.select("#own-action")) == 1
        assert str(soup).count("Unique eyebrow") == 1
        assert str(soup).count("Unique lead") == 1

    @pytest.mark.parametrize(
        ("left_out", "selector"),
        [
            ("eyebrow", ".mvp-page-eyebrow"),
            ("lead", ".mvp-page-lead"),
            ("info", "dialog, button"),
            ("title", "h1"),
        ],
    )
    def test_an_argument_not_given_leaves_no_element_behind(
        self, layout, left_out, selector
    ):
        soup = render_layout(layout, leave_out=(left_out,))

        assert soup.select(selector) == []
        assert empty_elements(soup) == []

    def test_no_actions_leaves_no_element_behind(self, layout):
        soup = render_layout(layout, actions=False)

        assert soup.select("#own-action") == []
        assert empty_elements(soup) == []

    def test_a_title_alone_draws_one_heading_and_nothing_else(self, layout):
        soup = render_layout(layout, leave_out=("eyebrow", "lead", "info"), actions=False)

        assert [h1.get_text(strip=True) for h1 in soup.find_all("h1")] == [
            "Unique title"
        ]
        assert soup.find_all(["p", "button", "dialog", "a"]) == []
        assert empty_elements(soup) == []

    def test_the_page_has_exactly_one_heading_holding_only_the_title(self, layout):
        soup = render_layout(layout)

        headings = soup.find_all("h1")
        assert len(headings) == 1
        assert headings[0].get_text(strip=True) == "Unique title"
        assert headings[0].find(["button", "a", "dialog", "input"]) is None

    def test_the_info_trigger_is_a_sibling_of_the_heading(self, layout):
        soup = render_layout(layout)

        heading = soup.find("h1")
        assert heading.find("button") is None
        assert heading.parent.find("button", recursive=False) is not None

    def test_an_empty_title_draws_no_heading_and_keeps_the_info_trigger(self, layout):
        soup = render_layout(layout, leave_out=("title",))

        assert soup.find("h1") is None
        assert soup.find("button") is not None
        assert "Unique info" in soup.select_one("dialog").get_text()

    def test_an_empty_title_still_draws_the_other_arguments(self, layout):
        soup = render_layout(layout, leave_out=("title",))

        assert soup.select_one(".mvp-page-eyebrow") is not None
        assert soup.select_one(".mvp-page-lead") is not None
        assert len(soup.select("#own-action")) == 1
        assert empty_elements(soup) == []


class TestPageTitleLayoutName:
    def test_a_layout_that_cannot_be_found_raises_naming_it(self):
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="no_such_layout"):
            render('<c-mvp.page.title layout="no_such_layout" title="T" />')

    @pytest.mark.usefixtures("project_components")
    def test_a_project_component_draws_the_title(self):
        soup = render('<c-mvp.page.title layout="fixture_title_file" title="Own" />')

        assert soup.select_one("[data-fixture-title]").get_text(strip=True) == "Own"


@pytest.mark.usefixtures("project_components")
class TestProjectTitleLayoutSlots:
    def test_a_project_layout_receives_the_five_slots(self):
        soup = render(
            '<c-mvp.page.title layout="fixture_title_layout" title="Unique title"'
            ' eyebrow="Unique eyebrow" lead="Unique lead" info="Unique info">'
            '<c-slot name="actions"><a id="own-action" href="/go/">Go</a></c-slot>'
            "</c-mvp.page.title>"
        )

        slot = {
            name: soup.select_one(f'[data-slot="{name}"]')
            for name in ("eyebrow", "heading", "lead", "info", "actions")
        }
        assert slot["eyebrow"].get_text(strip=True) == "Unique eyebrow"
        assert slot["heading"].get_text(strip=True) == "Unique title"
        assert slot["lead"].get_text(strip=True) == "Unique lead"
        assert "Unique info" in slot["info"].find("dialog").get_text()
        assert len(slot["actions"].select("#own-action")) == 1

    def test_a_project_layout_draws_empty_slots_for_arguments_not_given(self):
        soup = render('<c-mvp.page.title layout="fixture_title_layout" />')

        slots = soup.select("[data-slot]")
        assert len(slots) == 5
        assert [slot.get_text(strip=True) for slot in slots] == [""] * 5

    def test_an_undeclared_attribute_lands_on_the_project_layouts_root(self):
        soup = render(
            '<c-mvp.page.title layout="fixture_title_layout" title="T"'
            ' id="product-heading" />'
        )

        assert soup.find(True).get("id") == "product-heading"
        assert soup.find(True).has_attr("data-own-layout")
