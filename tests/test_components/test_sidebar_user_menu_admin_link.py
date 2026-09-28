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
from django.test import RequestFactory, override_settings
from django.urls import include, path, reverse


def _render(user):
    request = RequestFactory().get("/")
    request.user = user
    return render_to_string("tests/sidebar_menu.html", request=request)


def _mvp_urls_only():
    """A project that mounts only the Account Center (T008)."""
    patterns = [path("", include("mvp.urls"))]
    return type("_MvpUrlsOnly", (), {"urlpatterns": patterns})


MVP_URLS_ONLY = _mvp_urls_only()


class TestSidebarUserMenuAdminLink:
    @pytest.mark.django_db
    def test_staff_user_sees_the_admin_link_pointing_at_the_admin_url(self):
        user = get_user_model().objects.create_user(
            username="staffer", password="pw", is_staff=True
        )
        html = _render(user)

        assert f'href="{reverse("admin:index")}"' in html

    @pytest.mark.django_db
    def test_non_staff_user_does_not_see_the_admin_link(self):
        user = get_user_model().objects.create_user(username="regular", password="pw")
        html = _render(user)

        assert f'href="{reverse("admin:index")}"' not in html

    @pytest.mark.django_db
    def test_staff_user_still_sees_account_center_and_log_out(self):
        user = get_user_model().objects.create_user(
            username="staffer2", password="pw", is_staff=True
        )
        html = _render(user)

        assert f'href="{reverse("account-center")}"' in html
        assert 'form="logoutForm"' in html

    @pytest.mark.django_db
    def test_non_staff_user_still_sees_account_center_and_log_out(self):
        user = get_user_model().objects.create_user(username="regular2", password="pw")
        html = _render(user)

        assert f'href="{reverse("account-center")}"' in html
        assert 'form="logoutForm"' in html


class TestSidebarUserMenuLogOut:
    @pytest.mark.django_db
    def test_the_log_out_row_submits_a_form_that_exists(self):
        user = get_user_model().objects.create_user(username="leaver", password="pw")
        html = _render(user)

        assert 'form="logoutForm"' in html
        assert 'id="logoutForm"' in html
        assert f'action="{reverse("account_logout")}"' in html

    @pytest.mark.django_db
    def test_no_log_out_row_when_the_project_has_no_logout_url(self, settings):
        settings.ROOT_URLCONF = "tests.urls_without_logout"
        user = get_user_model().objects.create_user(username="stayer", password="pw")
        html = _render(user)

        assert 'form="logoutForm"' not in html
        assert 'id="logoutForm"' not in html

    @pytest.mark.django_db
    def test_no_dangling_divider_when_log_out_is_the_only_row(self, settings):
        settings.ROOT_URLCONF = "tests.urls_logout_only"
        user = get_user_model().objects.create_user(username="lonely", password="pw")
        html = _render(user)

        assert 'form="logoutForm"' in html
        assert "divider" not in html


class TestSidebarUserMenuLogOutResolvesAccountLogout:
    @pytest.mark.django_db
    def test_a_signed_in_request_draws_the_log_out_row_and_form_at_account_logout(
        self,
    ):
        with override_settings(ROOT_URLCONF=MVP_URLS_ONLY):
            user = get_user_model().objects.create_user(
                username="departing", password="pw"
            )
            html = _render(user)

            assert 'form="logoutForm"' in html
            assert f'action="{reverse("account_logout")}"' in html
