"""Tests for ``demo.urls`` — the demo carries no sign-in or sign-out wiring
of its own; the packaged Account Center pages are what it shows (T016,
FR-014, SC-006).

Source: demo/urls.py, demo/settings.py, demo/templates/demo/components/link.html
"""

from pathlib import Path

import pytest
from django.urls import NoReverseMatch, reverse

DEMO_URLS = (
    Path(__file__).resolve().parent.parent.parent / "demo" / "urls.py"
).read_text()
DEMO_SETTINGS = (
    Path(__file__).resolve().parent.parent.parent / "demo" / "settings.py"
).read_text()
LINK_COMPONENT_DOC = (
    Path(__file__).resolve().parent.parent.parent
    / "demo"
    / "templates"
    / "demo"
    / "components"
    / "link.html"
).read_text()


class TestDemoCarriesNoAuthWiringOfItsOwn:
    def test_the_demos_own_account_logout_path_is_gone(self):
        assert "account/logout/" not in DEMO_URLS

    def test_djangos_auth_urls_are_no_longer_included(self):
        assert "django.contrib.auth.urls" not in DEMO_URLS

    def test_reversing_djangos_own_login_name_no_longer_resolves(self):
        with pytest.raises(NoReverseMatch):
            reverse("login")

    def test_the_registration_login_template_is_gone(self):
        template = (
            Path(__file__).resolve().parent.parent.parent
            / "demo"
            / "templates"
            / "registration"
            / "login.html"
        )
        assert not template.exists()

    def test_the_component_doc_example_points_at_account_login(self):
        assert "{% url 'account_login' %}" in LINK_COMPONENT_DOC
        assert "{% url 'login' %}" not in LINK_COMPONENT_DOC

    def test_settings_match_decision_d12(self):
        assert 'LOGIN_URL = "account_login"' in DEMO_SETTINGS
        assert 'LOGIN_REDIRECT_URL = "/"' in DEMO_SETTINGS
        assert "LOGOUT_REDIRECT_URL" not in DEMO_SETTINGS


@pytest.mark.django_db
class TestTheDemoShowsThePackagedPages:
    """The round trip a person actually makes against the demo's real,
    un-overridden settings (FR-014, SC-006)."""

    def test_a_protected_page_sends_an_anonymous_visitor_to_the_packaged_sign_in_page(
        self, client
    ):
        response = client.get(reverse("account-center"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))

    def test_signing_in_without_a_next_lands_on_home(self, client, django_user_model):
        django_user_model.objects.create_user(
            username="demovisitor1", password="correct-pass"
        )

        response = client.post(
            reverse("account_login"),
            {"username": "demovisitor1", "password": "correct-pass"},
        )

        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_signing_out_renders_the_packaged_signed_out_page(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="demovisitor2", password="correct-pass"
        )
        client.force_login(user)

        response = client.post(reverse("account_logout"))

        assert response.status_code == 200
        assert response.wsgi_request.user.is_anonymous
        assert response.templates[0].name == "mvp/account/logout.html"
