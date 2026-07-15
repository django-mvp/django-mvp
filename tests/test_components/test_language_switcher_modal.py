"""Tests for the modal-based language switcher action component.

<c-actions.language-switcher-modal> is a drop-in alternative to the dropdown
<c-actions.language-switcher>: a globe trigger button opens a native <dialog>
holding a responsive grid of languages. Selecting one posts the set_language
form. Rendered via tests/language_switcher_modal.html.
"""

import re

import pytest
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import translation


def _render(language_code="en"):
    """Render the component with a request whose active language is set."""
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/some/path/")
    request.user = AnonymousUser()
    request.LANGUAGE_CODE = language_code
    with translation.override(language_code):
        return render_to_string("tests/language_switcher_modal.html", request=request)


@pytest.mark.django_db
def test_renders_trigger_and_dialog():
    """A globe trigger opens the dialog; the dialog posts set_language."""
    html = _render()
    # trigger button opens the modal via the native dialog API
    assert "showModal()" in html
    assert "<dialog" in html
    # the form targets set_language and preserves the current path for redirect
    assert 'method="post"' in html
    assert 'name="next"' in html
    assert 'value="/some/path/"' in html


@pytest.mark.django_db
def test_lists_available_languages_as_submit_buttons():
    """Each available language is a submit button posting its code."""
    html = _render()
    codes = re.findall(r'<button type="submit"\s+name="language"\s+value="([^"]+)"', html)
    assert "en" in codes
    assert "fr" in codes
    # every language renders exactly one option
    assert len(codes) == len(set(codes))


@pytest.mark.django_db
def test_active_language_is_marked():
    """The current language gets aria-current and the primary highlight; only one."""
    html = _render("fr")
    assert html.count('aria-current="true"') == 1
    # the active option carries the primary highlight classes
    match = re.search(
        r'<button type="submit"\s+name="language"\s+value="fr"[^>]*aria-current="true"[^>]*'
        r'class="([^"]*)"',
        html,
    )
    assert match is not None
    assert "border-primary" in match.group(1)


@pytest.mark.django_db
def test_id_prop_overrides_dialog_id():
    """The id prop lets more than one instance coexist on a page."""
    from django.contrib.auth.models import AnonymousUser

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    request.LANGUAGE_CODE = "en"
    with translation.override("en"):
        html = render_to_string(
            "tests/language_switcher_modal_id.html", request=request
        )
    assert 'id="footerLangModal"' in html
    assert "footerLangModal.showModal()" in html
