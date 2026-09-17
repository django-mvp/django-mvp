"""Tests for the ``tailwind/layout/field_errors.html`` and
``field_errors_block.html`` overrides (#295).

Django 5.2 composes ``aria-describedby`` in ``BoundField.build_widget_attrs``
from the help-text id and ``{auto_id}_error``, and expects the form template
to render the error container under that second id. crispy-tailwind's own
templates still mint their own scheme, ``error_{counter}_{auto_id}`` — so
``{auto_id}_error`` is never rendered, and a screen reader announces the
field as invalid without ever reading why.

crispy-tailwind ships this fix twice over: ``help_text_and_errors.html``
includes ``field_errors.html`` when ``error_text_inline`` is on (the default
for a ``FormHelper`` with a ``Layout``) and ``field_errors_block.html``
otherwise — which is every ``{{ form|crispy }}`` render with no
``FormHelper.Layout``, the common case in this project (exercised via
``cotton/form/render.html``, the same seam ``test_form_render.py`` uses).
"""

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string

from mvp.fixtures import _beautiful_soup


class FileForm(forms.Form):
    myfile = forms.FileField(help_text="Upload something")


class FileFormWithLayout(forms.Form):
    """Takes the ``{% crispy form %}`` path in ``cotton/form/render.html``,
    which needs a ``FormHelper`` carrying a ``Layout`` — a bare
    ``FormHelper()`` with no ``Layout`` is falsy in the template
    (``FormHelper.__len__`` reads the layout's field count), so
    ``{% if form.helper %}`` would not even take this branch without one."""

    myfile = forms.FileField(help_text="Upload something")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(Field("myfile"))


def _render_invalid():
    form = FileForm(data={}, files={})
    form.is_valid()
    return render_to_string("cotton/form/render.html", {"form": form})


class TestFieldErrorsAnnounceWhyAFieldIsInvalid:
    def test_every_id_named_in_aria_describedby_is_rendered(self):
        """Follows whatever scheme Django composes, rather than hard-coding
        ``id_myfile_error`` — so this keeps following Django if it changes
        the scheme again."""
        soup = _beautiful_soup()(_render_invalid(), "html.parser")
        control = soup.find(id="id_myfile")

        described_by_ids = control["aria-describedby"].split()
        assert described_by_ids  # the control actually names something

        for described_id in described_by_ids:
            assert soup.find(id=described_id) is not None, (
                f"aria-describedby names {described_id!r}, which is not rendered"
            )

    def test_the_error_container_carries_the_error_text(self):
        soup = _beautiful_soup()(_render_invalid(), "html.parser")
        control = soup.find(id="id_myfile")
        error_id = [
            i for i in control["aria-describedby"].split() if i.endswith("_error")
        ][0]

        container = soup.find(id=error_id)
        assert container is not None
        assert "This field is required." in container.get_text()

    def test_the_help_text_id_in_aria_describedby_also_resolves(self):
        soup = _beautiful_soup()(_render_invalid(), "html.parser")
        control = soup.find(id="id_myfile")
        helptext_id = [
            i
            for i in control["aria-describedby"].split()
            if i.endswith("_helptext")
        ][0]

        helptext = soup.find(id=helptext_id)
        assert helptext is not None
        assert "Upload something" in helptext.get_text()

    def test_the_old_per_error_id_is_still_present(self):
        html = _render_invalid()

        assert 'id="error_1_id_myfile"' in html

    def test_a_valid_field_renders_no_error_container(self):
        form = FileForm(
            data={}, files={"myfile": SimpleUploadedFile("test.txt", b"content")}
        )
        form.is_valid()
        html = render_to_string("cotton/form/render.html", {"form": form})

        assert "_error" not in html


class TestFieldErrorsAlsoAnnounceThroughTheHelperLayoutPath:
    """The ``{% crispy form %}`` path (``FormHelper`` with a ``Layout``)
    goes through ``field_errors.html``, not ``field_errors_block.html`` —
    the sibling template needs the same fix."""

    def test_every_id_named_in_aria_describedby_is_rendered(self):
        form = FileFormWithLayout(data={}, files={})
        form.is_valid()
        html = render_to_string("cotton/form/render.html", {"form": form})
        soup = _beautiful_soup()(html, "html.parser")
        control = soup.find(id="id_myfile")

        described_by_ids = control["aria-describedby"].split()
        assert described_by_ids

        for described_id in described_by_ids:
            assert soup.find(id=described_id) is not None, (
                f"aria-describedby names {described_id!r}, which is not rendered"
            )
