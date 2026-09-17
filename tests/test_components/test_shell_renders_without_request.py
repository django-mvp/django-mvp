"""Regression tests for issue #367: rendering the shell without a request
raised ``KeyError: 'request'`` instead of drawing no menu.

flex_menu's ``process_menu`` reads ``context["request"]`` directly, so any
of the three call sites that draw a menu (the sidebar, the dock, the Account
Center layout) raised the moment the context lacked one — exactly the
context Django renders an error page in: ``django.views.defaults.server_error``
calls ``template.render()`` with no context and no request at all.
"""

from django.contrib.auth.models import AnonymousUser
from django.template import loader
from django.template.loader import render_to_string
from django.test import RequestFactory

from mvp.menus import AppMenu


class TestShellRendersWithoutARequest:
    def test_the_shell_renders_without_raising(self):
        loader.get_template("mvp/base.html").render()

    def test_no_request_draws_no_sidebar_menu(self):
        html = loader.get_template("mvp/base.html").render()

        assert f'aria-label="{AppMenu.extra_context["label"]}"' not in html

    def test_a_request_still_draws_the_sidebar_menu(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        html = render_to_string("mvp/base.html", request=request)

        assert f'aria-label="{AppMenu.extra_context["label"]}"' in html

    def test_the_account_center_layout_renders_without_raising(self):
        loader.get_template("mvp/account/base.html").render()

    def test_a_project_base_extending_the_shell_renders_without_raising(self):
        """The scenario the issue is really about. A project builds its
        error page on the unqualified ``base.html`` (FR-012), not on
        ``mvp/base.html`` directly, and Django renders that page with no
        context and no request."""
        loader.get_template("base.html").render()
