"""Regression tests for issue #367: rendering the shell without a request
raised ``KeyError: 'request'`` instead of drawing no menu.

Django renders the production error page in exactly that context —
``django.views.defaults.server_error`` calls ``template.render()`` with no
context and no request at all — so a project building its error page on this
shell lost the real error behind a ``KeyError`` of the shell's own making.

The cause was in django-flex-menus, whose ``process_menu`` read
``context["request"]`` directly, and it was fixed there in 0.4.4. These tests
hold this package's own contract: the three templates that draw a menu render
without a request, and still draw their menu with one. They fail again if the
dependency floor slips below the release that carries the fix.
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
