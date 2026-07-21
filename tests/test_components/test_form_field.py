"""Tests for the <c-form.field> component.

A single, presentational form field: one control plus an optional label, help
text, and errors — rendered entirely from explicit attributes (whole-form
rendering is <c-form.render>'s job). Sources are compiled through the Cotton
compiler so the tests exercise the component exactly as a template would.
"""

from django import template
from django.template.context import Context
from django_cotton.compiler_regex import CottonCompiler

compiler = CottonCompiler()


def render(source, **context):
    """Compile a Cotton source string and render it."""
    return template.Template(compiler.process(source)).render(Context(context))


# ---------------------------------------------------------------------------
# Bare fields (no label/help/errors)
# ---------------------------------------------------------------------------


def test_bare_field_renders_control_only():
    """Without label/help/errors there is no fieldset wrapper — just the control."""
    html = render('<c-form.field name="q" placeholder="Search" />')
    assert 'class="input w-full' in html
    assert '<input type="text"' in html
    assert 'name="q"' in html
    assert 'placeholder="Search"' in html
    assert "fieldset" not in html


def test_type_is_emitted_on_the_input():
    html = render('<c-form.field type="password" name="password" />')
    assert '<input type="password"' in html


def test_attrs_pass_through_to_the_control():
    html = render('<c-form.field name="q" id="id_q" value="abc" form="filterForm" disabled />')
    assert 'id="id_q"' in html
    assert 'value="abc"' in html
    assert 'form="filterForm"' in html
    assert "disabled" in html


def test_class_lands_on_the_control_wrapper():
    """`class` styles the visible control box (e.g. join-item, widths)."""
    html = render('<c-form.field name="q" class="join-item" />')
    assert 'class="input w-full join-item"' in html


# ---------------------------------------------------------------------------
# Label
# ---------------------------------------------------------------------------


def test_label_renders_and_points_at_the_control():
    html = render('<c-form.field label="Email" type="email" name="email" id="id_email" />')
    assert 'class="fieldset' in html
    assert "fieldset-legend" in html
    assert ">Email<" in html or "Email" in html
    assert 'for="id_email"' in html
    assert 'id="id_email"' in html  # the control keeps its id too


def test_label_slot_allows_rich_content():
    html = render(
        '<c-form.field name="email">'
        '<c-slot name="label">Email <c-badge variant="success">Verified</c-badge></c-slot>'
        "</c-form.field>"
    )
    assert "fieldset-legend" in html
    assert "badge-success" in html


def test_hide_label_is_screen_reader_only():
    html = render('<c-form.field label="Confirm" hide-label name="confirmation" />')
    assert "sr-only" in html
    assert "Confirm" in html
    # the control itself must stay visible
    assert 'class="input w-full' in html


def test_required_adds_indicator_and_html_attribute():
    html = render('<c-form.field label="Name" name="name" required />')
    assert 'aria-hidden="true">*</span>' in html
    assert "required" in html.split("<input", 1)[1]


# ---------------------------------------------------------------------------
# Help text and errors
# ---------------------------------------------------------------------------


def test_help_text_attribute_and_slot():
    attr = render('<c-form.field label="U" name="u" help-text="Digits only." />')
    assert '<p class="label">Digits only.</p>' in attr

    slot = render(
        '<c-form.field label="U" name="u">'
        '<c-slot name="help_text">See the <a href="#">docs</a>.</c-slot>'
        "</c-form.field>"
    )
    assert 'href="#"' in slot


def test_errors_string_styles_the_control():
    html = render('<c-form.field label="Email" name="email" errors="Invalid email." />')
    assert "input-error" in html
    assert 'aria-invalid="true"' in html
    assert "text-error" in html
    assert "Invalid email." in html


def test_errors_accepts_a_list():
    """A BoundField's error list renders one line per error."""
    html = render(
        '<c-form.field label="Email" name="email" :errors="errs" />',
        errs=["Too short.", "Invalid domain."],
    )
    assert "Too short." in html
    assert "Invalid domain." in html
    assert "input-error" in html


def test_errors_alone_do_not_render_a_label():
    html = render('<c-form.field name="email" errors="Nope." />')
    assert "fieldset-legend" not in html
    assert "text-error" in html


# ---------------------------------------------------------------------------
# Control types
# ---------------------------------------------------------------------------


def test_textarea_takes_value_from_slot_without_extra_whitespace():
    html = render('<c-form.field type="textarea" label="Bio" name="bio" rows="3">Hello</c-form.field>')
    assert 'class="textarea w-full' in html
    assert ">Hello</textarea>" in html
    assert 'rows="3"' in html


def test_textarea_error_style():
    html = render('<c-form.field type="textarea" name="bio" errors="Too long." />')
    assert "textarea-error" in html


def test_select_renders_options_from_slot():
    html = render('<c-form.field type="select" label="Plan" name="plan"><option>Free</option></c-form.field>')
    assert 'class="select w-full' in html
    assert "<select" in html
    assert "<option>Free</option>" in html


def test_select_error_style():
    html = render('<c-form.field type="select" name="plan" errors="Pick one." />')
    assert "select-error" in html


def test_file_input():
    html = render('<c-form.field type="file" label="Avatar" name="avatar" accept="image/*" />')
    assert '<input type="file"' in html
    assert "file-input" in html
    assert 'accept="image/*"' in html


def test_checkbox_renders_inline_label():
    html = render('<c-form.field type="checkbox" label="Remember me" name="remember" checked />')
    assert '<input type="checkbox"' in html
    assert 'class="checkbox' in html
    assert "Remember me" in html
    assert "checked" in html
    # no legend-style label and no wrapper for a bare checkbox
    assert "fieldset-legend" not in html
    assert "fieldset" not in html


def test_radio_renders_radio_input():
    html = render('<c-form.field type="radio" label="Standard" name="ship" value="std" />')
    assert '<input type="radio"' in html
    assert 'class="radio' in html


def test_toggle_is_a_checkbox_styled_as_a_switch():
    html = render('<c-form.field type="toggle" label="Notify" name="notify" />')
    assert '<input type="checkbox"' in html
    assert 'class="toggle' in html


def test_check_style_field_with_help_text_wraps_without_legend():
    html = render('<c-form.field type="toggle" label="Notify" name="notify" help-text="Weekly." />')
    assert 'class="fieldset' in html
    assert "fieldset-legend" not in html
    assert '<p class="label">Weekly.</p>' in html


def test_checkbox_error_style():
    html = render('<c-form.field type="checkbox" label="Terms" name="terms" errors="Required." />')
    assert "checkbox-error" in html


# ---------------------------------------------------------------------------
# Prefix / suffix and wrapper
# ---------------------------------------------------------------------------


def test_prelabel_and_postlabel_attributes():
    html = render('<c-form.field name="site" prelabel="https://" postlabel=".com" />')
    assert '<span class="label">https://</span>' in html
    assert '<span class="label">.com</span>' in html


def test_prelabel_slot():
    html = render('<c-form.field name="q"><c-slot name="prelabel"><c-icon name="search" /></c-slot></c-form.field>')
    assert '<span class="label">' in html
    assert "bi-search" in html


def test_wrapper_class_lands_on_the_fieldset():
    html = render('<c-form.field label="Name" name="name" wrapper-class="mb-4" />')
    assert 'class="fieldset mb-4"' in html
