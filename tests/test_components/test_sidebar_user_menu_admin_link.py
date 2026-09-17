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


class TestSidebarUserMenuLogOut:
    """The log-out row is bound to the same condition as the form it submits.

    The control is a ``<button type="submit" form="logoutForm">``, which does
    nothing at all unless an element with that id is in the document. The form
    has always been guarded on ``account_logout`` resolving while the button
    was drawn unconditionally, so a project without that URL name got a
    log-out button that silently did nothing when clicked.
    """

    @pytest.mark.django_db
    def test_the_log_out_row_submits_a_form_that_exists(self):
        user = get_user_model().objects.create_user(username="leaver", password="pw")
        html = _render(user)

        assert 'form="logoutForm"' in html
        assert 'id="logoutForm"' in html
        assert f'action="{reverse("account_logout")}"' in html

    @pytest.mark.django_db
    def test_no_log_out_row_when_the_project_has_no_logout_url(self, settings):
        """With no ``account_logout`` name there is no form to submit, so the
        row is absent rather than dead."""
        settings.ROOT_URLCONF = "tests.urls_without_logout"
        user = get_user_model().objects.create_user(username="stayer", password="pw")
        html = _render(user)

        assert "Log out" not in html
        assert 'form="logoutForm"' not in html

    @pytest.mark.django_db
    def test_no_dangling_divider_when_log_out_is_the_only_row(self, settings):
        """The divider separates the rows above from the log-out row. With
        neither an Account Center nor an admin row there is nothing for it to
        separate, so it must not render."""
        settings.ROOT_URLCONF = "tests.urls_logout_only"
        user = get_user_model().objects.create_user(username="lonely", password="pw")
        html = _render(user)

        assert "Log out" in html
        assert "divider" not in html
