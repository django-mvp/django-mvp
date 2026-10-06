"""Tests for ``demo.urls`` — the demo carries no sign-in or sign-out wiring
of its own; the packaged Account Center pages are what it shows (T016,
FR-014, SC-006).

Source: demo/urls.py, demo/settings.py, demo/templates/demo/components/link.html
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTheDemoShowsThePackagedPages:
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
