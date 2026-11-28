"""Tests for the values ``mvp_config`` adds for the shell to read.

Source: mvp/context_processors.py
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import override_settings
from django.urls import resolve

from mvp.config import MVP_CONFIG
from mvp.context_processors import mvp_config
from tests.testapp_mounted.mounted import testapp_mounted


def request_for(rf, path, urlconf):
    """A request as Django leaves it once ``path`` has been resolved."""
    request = rf.get(path)
    request.user = AnonymousUser()
    request.resolver_match = resolve(path, urlconf=urlconf)
    return request


class TestMvpConfig:
    def test_exposes_the_merged_configuration(self, rf):
        assert mvp_config(rf.get("/"))["mvp_config"] is MVP_CONFIG

    def test_a_request_that_was_never_routed_names_no_app_and_draws_no_menu(self, rf):
        context = mvp_config(rf.get("/"))

        assert not context["mounted_app"]
        assert not context["mounted_menu"]

    def test_nothing_is_looked_up_until_a_template_reads_a_value(self, rf):
        request = rf.get("/")

        class Unrouted(type(request)):
            @property
            def resolver_match(self):
                raise AssertionError("the request was read before a value was")

        request.__class__ = Unrouted

        context = mvp_config(request)

        with pytest.raises(AssertionError, match="read before a value"):
            bool(context["mounted_app"])


@pytest.mark.urls("tests.urls_mounted")
class TestMountedValues:
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
            context = mvp_config(request_for(rf, "/detail/", "tests.urls_mounted_main"))
            app, menu = context["mounted_app"], context["mounted_menu"]

            assert not app
            assert menu == testapp_mounted.menu
