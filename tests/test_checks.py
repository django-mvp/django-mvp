"""Tests for ``mvp.checks`` — the start-up check on the ``daisy_cotton`` app line.

Source: mvp/checks.py
"""

from io import StringIO

import pytest
from django.core import checks
from django.core.checks.registry import registry
from django.core.management import call_command
from django.core.management.base import SystemCheckError

from mvp.checks import check_daisy_cotton_app, daisy_cotton_app_messages


class TestDaisyCottonAppMessages:
    def test_a_missing_daisy_cotton_is_an_error(self):
        messages = daisy_cotton_app_messages(["mvp"])

        assert [message.id for message in messages] == ["mvp.E002"]
        assert isinstance(messages[0], checks.Error)

    def test_daisy_cotton_above_mvp_is_a_warning(self):
        messages = daisy_cotton_app_messages(["daisy_cotton", "mvp"])

        assert [message.id for message in messages] == ["mvp.W001"]
        assert isinstance(messages[0], checks.Warning)

    def test_daisy_cotton_directly_below_mvp_passes(self):
        assert daisy_cotton_app_messages(["mvp", "daisy_cotton"]) == []

    def test_daisy_cotton_anywhere_after_mvp_passes(self):
        assert daisy_cotton_app_messages(["mvp", "x", "daisy_cotton"]) == []

    @pytest.mark.parametrize(
        "app_names",
        [["mvp"], ["daisy_cotton", "mvp"]],
        ids=["missing", "misplaced"],
    )
    def test_each_message_says_where_the_line_belongs_and_names_the_apps(
        self, app_names
    ):
        (message,) = daisy_cotton_app_messages(app_names)

        assert message.hint
        assert "daisy_cotton" in message.msg
        assert "mvp" in message.hint


class TestDaisyCottonAppCheck:
    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_daisy_cotton_app(None) == []

    def test_the_check_is_registered_with_no_tag(self):
        assert check_daisy_cotton_app in registry.registered_checks
        assert not check_daisy_cotton_app.tags

    def test_a_missing_daisy_cotton_stops_the_check_command(self, settings):
        settings.INSTALLED_APPS = [
            app for app in settings.INSTALLED_APPS if app != "daisy_cotton"
        ]

        with pytest.raises(SystemCheckError, match=r"mvp\.E002"):
            call_command("check", stderr=StringIO())

    def test_a_missing_daisy_cotton_can_be_silenced_by_its_identifier(self, settings):
        settings.INSTALLED_APPS = [
            app for app in settings.INSTALLED_APPS if app != "daisy_cotton"
        ]
        settings.SILENCED_SYSTEM_CHECKS = ["mvp.E002"]

        call_command("check", stderr=StringIO())

    def test_a_misplaced_daisy_cotton_is_reported_on_stderr(self, settings):
        apps = [app for app in settings.INSTALLED_APPS if app != "daisy_cotton"]
        settings.INSTALLED_APPS = ["daisy_cotton", *apps]
        stderr = StringIO()

        call_command("check", stderr=stderr)

        assert "mvp.W001" in stderr.getvalue()

    def test_a_misplaced_daisy_cotton_can_be_silenced_by_its_identifier(self, settings):
        apps = [app for app in settings.INSTALLED_APPS if app != "daisy_cotton"]
        settings.INSTALLED_APPS = ["daisy_cotton", *apps]
        settings.SILENCED_SYSTEM_CHECKS = ["mvp.W001"]
        stderr = StringIO()

        call_command("check", stderr=stderr)

        assert "mvp.W001" not in stderr.getvalue()
