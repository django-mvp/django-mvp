"""Tests for ``mvp.urls`` — the Account Center's URLconf.

Source: mvp/urls.py
"""

from pathlib import Path

import pytest
from django.test import override_settings
from django.urls import include, path, reverse

LOGIN_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "mvp"
    / "templates"
    / "mvp"
    / "account"
    / "login.html"
)


def _urlconf():
    """A project that mounts only the Account Center, the way ``mvp/urls.py``'s
    own docstring shows a project doing it."""
    patterns = [path("account/", include("mvp.urls"))]
    return type("_URLConf", (), {"urlpatterns": patterns})


ACCOUNT_URLCONF = _urlconf()


class TestAccountLoginURL:
    """``account_login`` — the sign-in page (T002)."""

    @pytest.mark.django_db
    def test_reversing_account_login_serves_a_sign_in_form(self, client):
        with override_settings(ROOT_URLCONF=ACCOUNT_URLCONF):
            response = client.get(reverse("account_login"))

        assert response.status_code == 200
        content = response.content.decode()
        assert "<form" in content
        assert 'type="password"' in content

    def test_the_identifying_fields_label_is_not_hard_coded(self):
        """FR-005: the field's label comes from ``form.username.label`` —
        whatever the user model calls its identifying field — never a
        literal string in the template."""
        assert "form.username.label" in LOGIN_TEMPLATE.read_text()
