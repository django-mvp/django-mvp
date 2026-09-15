"""Tests for the compact user display (docs/adr/0023): avatar plus name,
with no email line. Its one consumer is user/sidebar_menu.html. Rendered via
tests/user_display_compact.html.
"""

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory


def _render(user):
    request = RequestFactory().get("/")
    request.user = user
    return render_to_string("tests/user_display_compact.html", request=request)


class TestCompactUserDisplay:
    @pytest.mark.django_db
    def test_renders_the_users_display_name(self):
        user = get_user_model().objects.create_user(
            username="carol", password="pw", email="carol@example.com"
        )
        html = _render(user)

        assert "carol" in html

    @pytest.mark.django_db
    def test_does_not_render_the_users_email(self):
        """A test that only checks the name still passes if the email is
        also there — assert its absence explicitly."""
        user = get_user_model().objects.create_user(
            username="dave", password="pw", email="dave@example.com"
        )
        html = _render(user)

        assert "dave@example.com" not in html
