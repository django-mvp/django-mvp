"""The pieces an email body is written with: ``c-mvp.email.*`` (FS-044).

Each piece is rendered inside a body extending the base email template, the way
an email uses it. Pixel values are never pinned: a test compares one rendering
with another.
"""

import re

import pytest
from bs4 import BeautifulSoup
from django.contrib.sites.models import Site

from mvp.config import MVP_CONFIG
from mvp.email.brand import EmailBrand

BASE = '{% extends "mvp/email/base.html" %}{% block body %}'
END = "{% endblock %}"


@pytest.fixture(autouse=True)
def fresh_brand(db, monkeypatch):
    """Read the brand afresh for each test, on a Site with a name."""
    monkeypatch.setitem(MVP_CONFIG, "site_name", None)
    Site.objects.clear_cache()
    EmailBrand.current.cache_clear()
    yield
    EmailBrand.current.cache_clear()
    Site.objects.clear_cache()


@pytest.fixture
def body(cotton_render_string):
    """Render ``markup`` as the body of an email and parse the result."""

    def _body(markup, **context):
        return BeautifulSoup(
            cotton_render_string(BASE + markup + END, context), "html.parser"
        )

    return _body


def margin_of(paragraph):
    """The ``margin`` declaration in a paragraph's inline style."""
    return re.search(r"margin:\s*[^;]+", paragraph["style"]).group(0)


class TestEmailText:
    def test_it_renders_a_paragraph_with_its_words(self, body):
        paragraph = body("<c-mvp.email.text>Hello there</c-mvp.email.text>").find(
            "p", string="Hello there"
        )

        assert paragraph is not None

    def test_the_spacing_is_inline_on_the_paragraph(self, body):
        paragraph = body("<c-mvp.email.text>Hello there</c-mvp.email.text>").find(
            "p", string="Hello there"
        )

        assert margin_of(paragraph)

    def test_a_named_space_below_differs_from_the_default(self, body):
        soup = body(
            '<c-mvp.email.text>plain</c-mvp.email.text><c-mvp.email.text mb="lg">larger</c-mvp.email.text>'
        )

        default, larger = (
            soup.find("p", string="plain"),
            soup.find("p", string="larger"),
        )

        assert margin_of(default) != margin_of(larger)

    def test_every_named_space_below_differs_from_the_others(self, body):
        names = ["none", "xs", "sm", "md", "lg", "xl"]
        soup = body(
            "".join(
                f'<c-mvp.email.text mb="{name}">{name}</c-mvp.email.text>'
                for name in names
            )
        )

        margins = {margin_of(soup.find("p", string=name)) for name in names}

        assert len(margins) == len(names)

    @pytest.mark.parametrize(
        ("option", "named"),
        [("mb", "lg"), ("size", "lg"), ("align", "center")],
    )
    def test_each_option_changes_the_paragraphs_style(self, body, option, named):
        soup = body(
            f'<c-mvp.email.text>plain</c-mvp.email.text><c-mvp.email.text {option}="{named}">named</c-mvp.email.text>'
        )

        assert (
            soup.find("p", string="plain")["style"]
            != soup.find("p", string="named")["style"]
        )

    @pytest.mark.parametrize(
        ("option", "default"), [("mb", "md"), ("size", "md"), ("align", "start")]
    )
    def test_the_default_can_be_asked_for_by_name(self, body, option, default):
        soup = body(
            f'<c-mvp.email.text>plain</c-mvp.email.text><c-mvp.email.text {option}="{default}">named</c-mvp.email.text>'
        )

        assert (
            soup.find("p", string="plain")["style"]
            == soup.find("p", string="named")["style"]
        )

    @pytest.mark.parametrize("option", ["mb", "size", "align"])
    def test_an_unknown_value_is_the_default(self, body, option):
        soup = body(
            f'<c-mvp.email.text>plain</c-mvp.email.text><c-mvp.email.text {option}="no-such-value">unknown</c-mvp.email.text>'
        )

        assert (
            soup.find("p", string="plain")["style"]
            == soup.find("p", string="unknown")["style"]
        )

    def test_a_plain_paragraph_in_a_body_is_spaced_by_the_base_template(self, body):
        paragraph = body("<p>plain markup</p>").find("p", string="plain markup")

        assert margin_of(paragraph)


class TestEmailButton:
    def test_the_colour_is_on_the_table_cell_that_holds_the_link(self, body):
        soup = body('<c-mvp.email.button href="https://example.org/go" text="Go" />')
        link = soup.find("a", href="https://example.org/go")
        cell = link.find_parent("td")
        primary = EmailBrand.current().light.primary

        assert cell["bgcolor"] == primary
        assert primary in cell["style"]

    def test_the_link_carries_the_address_and_the_text(self, body):
        link = body(
            '<c-mvp.email.button href="https://example.org/go" text="Go now" />'
        ).find("a", href="https://example.org/go")

        assert link.get_text(strip=True) == "Go now"

    def test_the_link_is_drawn_in_the_colour_that_reads_on_the_button(self, body):
        link = body(
            '<c-mvp.email.button href="https://example.org/go" text="Go" />'
        ).find("a", href="https://example.org/go")

        assert EmailBrand.current().light.primary_content in link["style"]

    def test_the_colour_holds_where_cotton_hides_the_templates_variables_from_a_component(
        self, body, settings
    ):
        settings.COTTON_ISOLATE_BY_DEFAULT = True

        link = body(
            '<c-mvp.email.button href="https://example.org/go" text="Go" />'
        ).find("a", href="https://example.org/go")

        assert link.find_parent("td")["bgcolor"] == EmailBrand.current().light.primary

    def test_a_variable_gives_the_address(self, body):
        soup = body(
            '<c-mvp.email.button :href="target" text="Go" />',
            target="https://example.org/from-a-variable",
        )

        assert soup.find("a", href="https://example.org/from-a-variable")


class TestEmailNote:
    def test_it_renders_its_slot_in_the_muted_colour(self, body):
        note = (
            body(
                "<c-mvp.email.note>Ignore this email if it was not you.</c-mvp.email.note>"
            )
            .find(string="Ignore this email if it was not you.")
            .find_parent("div")
        )

        assert EmailBrand.current().light.muted in note["style"]


class TestEmailDivider:
    def test_it_renders_a_rule_in_the_border_colour(self, body):
        soup = body("<c-mvp.email.divider />")

        rules = [
            td
            for td in soup.find_all("td")
            if EmailBrand.current().light.border in td.get("style", "")
        ]

        assert any("border-top" in td["style"] for td in rules)


class TestEmailCode:
    def test_it_renders_the_code_on_the_pages_colour(self, body):
        cell = body('<c-mvp.email.code code="482913" />').find("td", string="482913")

        assert cell is not None
        assert EmailBrand.current().light.page in cell["style"]

    def test_the_code_is_escaped(self, body):
        cell = body('<c-mvp.email.code :code="code" />', code="<b>1</b>").find(
            "td", string="<b>1</b>"
        )

        assert cell is not None
