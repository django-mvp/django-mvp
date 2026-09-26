"""Tests for the values ``mvp_config`` adds for the shell to read.

Source: mvp/context_processors.py
"""

from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import override_settings
from django.urls import resolve

from mvp.config import MVP_CONFIG
from mvp.context_processors import mvp_config
from mvp.mounted import MountedApp
from tests.testapp_mounted.mounted import testapp_mounted


def request_for(rf, path, urlconf):
    """A request as Django leaves it once ``path`` has been resolved."""
    request = rf.get(path)
    request.user = AnonymousUser()
    request.resolver_match = resolve(path, urlconf=urlconf)
    return request


class TestMvpConfig:
    """The processor still exposes the merged configuration."""

    def test_exposes_the_merged_configuration(self, rf):
        assert mvp_config(rf.get("/"))["mvp_config"] is MVP_CONFIG


@pytest.mark.urls("tests.urls_mounted")
class TestMountedValues:
    """The current app and the menu to draw, for the sidebar and the title."""

    def test_an_app_page_carries_the_app_and_its_menu(self, rf):
        context = mvp_config(request_for(rf, "/mounted/", "tests.urls_mounted"))

        assert context["mounted_app"] == testapp_mounted
        assert context["mounted_menu"] == testapp_mounted.menu

    def test_a_host_page_carries_neither(self, rf):
        context = mvp_config(request_for(rf, "/layout/", "tests.urls_mounted"))

        assert not context["mounted_app"]
        assert not context["mounted_menu"]

    def test_a_host_page_reads_false_in_an_if_tag(self, rf):
        context = mvp_config(request_for(rf, "/layout/", "tests.urls_mounted"))
        template = Template("{% if mounted_app %}app{% else %}none{% endif %}")

        assert template.render(Context(context)) == "none"

    def test_the_main_app_is_never_named_but_its_menu_is_drawn(self, rf):
        with override_settings(ROOT_URLCONF="tests.urls_mounted_main"):
            context = mvp_config(
                request_for(rf, "/detail/", "tests.urls_mounted_main")
            )
            app, menu = context["mounted_app"], context["mounted_menu"]

            assert not app
            assert menu == testapp_mounted.menu

    def test_no_lookup_runs_until_a_value_is_read(self, rf):
        request = request_for(rf, "/mounted/", "tests.urls_mounted")

        with (
            mock.patch.object(MountedApp, "for_request") as for_request,
            mock.patch.object(MountedApp, "main") as main,
        ):
            context = mvp_config(request)

        for_request.assert_not_called()
        main.assert_not_called()
        assert context["mounted_app"] is not None

    def test_reading_a_value_runs_the_lookup(self, rf):
        request = request_for(rf, "/mounted/", "tests.urls_mounted")

        with mock.patch.object(
            MountedApp, "for_request", wraps=MountedApp.for_request
        ) as for_request:
            context = mvp_config(request)
            assert context["mounted_app"] == testapp_mounted

        for_request.assert_called()
