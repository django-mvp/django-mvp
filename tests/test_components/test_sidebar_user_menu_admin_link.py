"""Tests for the "Admin Site" link in the sidebar user menu (issue #369).

Rendered via tests/sidebar_menu.html, the same pattern
test_user_display_compact.py uses for user/sidebar_menu.html's sole
component. The link is guarded on two conditions, both required: the user
is staff, and the admin URLs are actually mounted (django.contrib.admin
being installed does not mean a project mounted its URLs).
"""

import pytest
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.urls import reverse


def _render(user):
    request = RequestFactory().get("/")
    request.user = user
    return render_to_string("tests/sidebar_menu.html", request=request)


class TestSidebarUserMenuAdminLink:
    @pytest.mark.django_db
    def test_staff_user_sees_the_admin_link_pointing_at_the_admin_url(self):
        user = get_user_model().objects.create_user(
            username="staffer", password="pw", is_staff=True
        )
        html = _render(user)

        assert "Admin Site" in html
        assert f'href="{reverse("admin:index")}"' in html

    @pytest.mark.django_db
    def test_non_staff_user_does_not_see_the_admin_link(self):
        user = get_user_model().objects.create_user(username="regular", password="pw")
        html = _render(user)

        assert "Admin Site" not in html

    @pytest.mark.django_db
    def test_staff_user_still_sees_account_center_and_log_out(self):
        user = get_user_model().objects.create_user(
            username="staffer2", password="pw", is_staff=True
        )
        html = _render(user)

        assert "Account Center" in html
        assert "Log out" in html

    @pytest.mark.django_db
    def test_non_staff_user_still_sees_account_center_and_log_out(self):
        user = get_user_model().objects.create_user(username="regular2", password="pw")
        html = _render(user)

        assert "Account Center" in html
        assert "Log out" in html
