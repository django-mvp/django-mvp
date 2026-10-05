"""Tests for ``c-mvp.page.info`` and its wiring into ``c-mvp.page.title`` (issue #321).

Sources are compiled through the Cotton compiler (mirroring
``test_breadcrumbs_href_attribute.py``), which is what exercises ``<c-vars>``
and ``attrs`` extraction the way a real template invocation would. Rendering a
component's template file directly never triggers that extraction, so the
action dicts would not be spread onto ``c-button`` at all.
"""

from html import unescape

from django import template
from django.template.context import Context
from django.utils.safestring import mark_safe
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


class TestPageInfoRendersOnlyWhenThereIsText:
    def test_no_dialog_without_text(self):
        html = render("<c-mvp.page.info />")
        assert "<dialog" not in html

    def test_no_trigger_without_text(self):
        html = render("<c-mvp.page.info />")
        assert "pageInfoModal.showModal()" not in html

    def test_actions_alone_render_nothing(self):
        html = render(
            '<c-mvp.page.info :actions="actions" />',
            actions=[{"text": "Read the docs", "href": "/docs/"}],
        )
        assert "<dialog" not in html
        assert "Read the docs" not in html

    def test_dialog_present_with_text(self):
        html = render('<c-mvp.page.info text="What this page is for." />')
        assert "<dialog" in html
        assert "What this page is for." in html


class TestPageInfoTrigger:
    def test_trigger_opens_the_dialog(self):
        html = render('<c-mvp.page.info text="Body" />')
        assert "pageInfoModal.showModal()" in html

    def test_dialog_carries_the_matching_id(self):
        html = render('<c-mvp.page.info text="Body" />')
        assert 'id="pageInfoModal"' in html

    def test_trigger_is_a_button_element(self):
        html = render('<c-mvp.page.info text="Body" />')
        assert "<button" in html

    def test_trigger_has_an_accessible_name(self):
        html = render('<c-mvp.page.info text="Body" />')
        assert "aria-label=" in html

    def test_trigger_uses_the_info_icon(self):
        html = render('<c-mvp.page.info text="Body" />')
        assert "bi-info-circle-fill" in html

    def test_trigger_is_icon_only(self):
        rendered = render('<c-mvp.page.info text="What this page is for." />')
        assert rendered.count("What this page is for.") == 1


class TestPageInfoText:
    def test_plain_text_is_escaped(self):
        html = render(
            '<c-mvp.page.info :text="text" />',
            text="Use <em>sparingly</em>",
        )
        assert "&lt;em&gt;sparingly&lt;/em&gt;" in html
        assert "<em>sparingly</em>" not in html

    def test_safe_text_renders_as_markup(self):
        html = render(
            '<c-mvp.page.info :text="text" />',
            text=mark_safe("<p>Rendered <strong>markup</strong>.</p>"),
        )
        assert "<p>Rendered <strong>markup</strong>.</p>" in html

    def test_heading_uses_the_supplied_title(self):
        html = render('<c-mvp.page.info text="Body" title="Products" />')
        assert "Products" in html


class TestPageInfoActions:
    def test_action_renders_as_a_link(self):
        html = render(
            '<c-mvp.page.info text="Body" :actions="actions" />',
            actions=[{"text": "Read the docs", "href": "/docs/"}],
        )
        assert 'href="/docs/"' in html
        assert "Read the docs" in html

    def test_action_carries_arbitrary_button_attributes(self):
        html = render(
            '<c-mvp.page.info text="Body" :actions="actions" />',
            actions=[
                {
                    "text": "Read the docs",
                    "href": "/docs/",
                    "variant": "primary",
                    "icon": "external-link",
                    "target": "_blank",
                }
            ],
        )
        assert "btn-primary" in html
        assert "bi-box-arrow-up-right" in html
        assert 'target="_blank"' in html

    def test_action_dicts_are_never_printed_raw(self):
        rendered = render(
            '<c-mvp.page.info text="Body" :actions="actions" />',
            actions=[{"text": "Read the docs", "href": "/docs/"}],
        )
        assert "'text':" not in unescape(rendered)

    def test_body_text_survives_alongside_actions(self):
        rendered = render(
            '<c-mvp.page.info text="What this page is for." :actions="actions" />',
            actions=[{"text": "Read the docs", "href": "/docs/"}],
        )
        assert "What this page is for." in rendered

    def test_every_action_is_rendered(self):
        html = render(
            '<c-mvp.page.info text="Body" :actions="actions" />',
            actions=[
                {"text": "Guide", "href": "/guide/"},
                {"text": "Reference", "href": "/reference/"},
            ],
        )
        assert "Guide" in html
        assert "Reference" in html


class TestPageTitleWiring:
    def test_no_info_leaves_the_title_unchanged(self):
        html = render('<c-mvp.page.title title="Products" />')
        assert "<dialog" not in html
        assert "Products" in html

    def test_info_renders_the_dialog(self):
        html = render(
            '<c-mvp.page.title title="Products" :info="info" />',
            info="What this page is for.",
        )
        assert "<dialog" in html
        assert "What this page is for." in html

    def test_dialog_heading_defaults_to_the_page_title(self):
        html = render(
            '<c-mvp.page.title title="Products" :info="info" />',
            info="Body",
        )
        assert html.count("Products") >= 2

    def test_info_actions_reach_the_dialog(self):
        html = render(
            '<c-mvp.page.title title="Products" :info="info" '
            ':info_actions="actions" />',
            info="Body",
            actions=[{"text": "Read the docs", "href": "/docs/"}],
        )
        assert 'href="/docs/"' in html
        assert "Read the docs" in html

    def test_heading_holds_only_the_title(self):
        html = render(
            '<c-mvp.page.title title="Products" :info="info" />',
            info="Body",
        )
        heading = html.split("<h1", 1)[1].split("</h1>", 1)[0]
        assert "<button" not in heading
