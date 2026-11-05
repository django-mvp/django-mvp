"""Tests for mvp.email.previews and its discovery from ``MvpConfig.ready`` (FS-044)."""

import importlib
import sys

import pytest
from django.apps import apps
from django.template.loader import get_template

from mvp.email.previews import EmailPreview, register

TESTAPP_PREVIEWS = "tests.testapp_email.email_previews"
CONFIRM = "testapp_email/email/confirm_message.html"


@pytest.fixture(autouse=True)
def empty_registry(monkeypatch):
    """Give each test a registry of its own, and forget the test app's module so discovery imports it again."""
    monkeypatch.setattr(EmailPreview, "registry", {})
    monkeypatch.delitem(sys.modules, TESTAPP_PREVIEWS, raising=False)


class TestRegister:
    def test_a_registered_email_is_in_the_registry_with_everything_it_was_given(self):
        register(
            "shop/receipt_message.html",
            "Receipt",
            {"total": "9"},
            subject="shop/receipt_subject.txt",
            text="shop/receipt_message.txt",
            group="Payments",
        )

        preview = EmailPreview.registry["shop/receipt_message.html"]

        assert preview == EmailPreview(
            template="shop/receipt_message.html",
            label="Receipt",
            context={"total": "9"},
            subject="shop/receipt_subject.txt",
            text="shop/receipt_message.txt",
            group="Payments",
        )

    def test_subject_text_and_group_are_optional(self):
        register("shop/hello.html", "Hello", {})

        preview = EmailPreview.registry["shop/hello.html"]

        assert (preview.subject, preview.text, preview.group) == (None, None, "")

    def test_registering_a_template_again_replaces_its_preview(self):
        register("shop/hello.html", "First", {})
        register("shop/hello.html", "Second", {})

        assert [p.label for p in EmailPreview.all()] == ["Second"]

    def test_get_returns_none_for_a_template_nobody_registered(self):
        assert EmailPreview.get("shop/missing.html") is None


class TestDiscovery:
    def test_while_debug_is_on_an_installed_apps_email_previews_module_is_found(self, settings):
        settings.DEBUG = True

        apps.get_app_config("mvp").ready()

        assert CONFIRM in EmailPreview.registry

    def test_while_debug_is_off_discovery_does_not_run(self, settings):
        settings.DEBUG = False

        apps.get_app_config("mvp").ready()

        assert CONFIRM not in EmailPreview.registry
        assert TESTAPP_PREVIEWS not in sys.modules


class TestDemoPreviews:
    @pytest.fixture
    def demo(self):
        """The previews the demo declares, loaded into the empty registry."""
        import demo.email_previews

        importlib.reload(demo.email_previews)
        return {preview.label: preview for preview in EmailPreview.all()}

    def test_the_demo_declares_five_emails_in_four_groups_and_one_broken_one(self, demo):
        assert len(demo) == 6
        assert {preview.group for preview in demo.values()} == {"Accounts", "Payments", "Compliance", "Notifications"}

    def test_every_template_a_working_demo_email_names_exists(self, demo):
        working = [preview for preview in demo.values() if "Broken" not in preview.label]

        for preview in working:
            for name in (preview.template, preview.subject, preview.text):
                if name:
                    get_template(name)

    def test_only_the_policy_update_has_a_plain_text_template(self, demo):
        assert [p.label for p in demo.values() if p.text] == ["Privacy policy update (own plain text and footer)"]

    def test_the_broken_email_names_a_template_that_does_not_exist(self, demo):
        broken = next(p for p in demo.values() if "Broken" in p.label)

        with pytest.raises(Exception, match="does-not-exist"):
            get_template(broken.template)
