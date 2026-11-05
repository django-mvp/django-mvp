"""Tests for ``mvp.checks`` — the start-up check on the ``daisy_cotton`` app line.

Source: mvp/checks.py
"""

from io import StringIO

import pytest
from django.core import checks
from django.core.checks.registry import registry
from django.core.management import call_command
from django.core.management.base import SystemCheckError

from mvp.checks import (
    check_daisy_cotton_app,
    check_email_brand,
    check_page_title_layout,
    daisy_cotton_app_messages,
    page_title_layout_messages,
)


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


class TestDaisyCottonAppCheck:
    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_daisy_cotton_app(None) == []

    def test_the_check_is_registered(self):
        assert check_daisy_cotton_app in registry.registered_checks

    def test_a_missing_daisy_cotton_stops_the_check_command(self, settings):
        settings.INSTALLED_APPS = [
            app for app in settings.INSTALLED_APPS if app != "daisy_cotton"
        ]

        with pytest.raises(SystemCheckError, match=r"mvp\.E002"):
            call_command("check", "mvp", stderr=StringIO())

    def test_a_misplaced_daisy_cotton_is_reported_on_stderr(self, settings):
        apps = [app for app in settings.INSTALLED_APPS if app != "daisy_cotton"]
        settings.INSTALLED_APPS = ["daisy_cotton", *apps]
        stderr = StringIO()

        call_command("check", "mvp", stderr=stderr)

        assert "mvp.W001" in stderr.getvalue()


@pytest.mark.usefixtures("project_components")
class TestPageTitleLayoutMessages:
    def test_a_shipped_name_passes(self):
        assert page_title_layout_messages("centred") == []

    def test_a_project_component_passes(self):
        assert page_title_layout_messages("fixture_title_file") == []

    def test_a_dict_of_valid_names_passes(self):
        layout = {"page": "default", "list": "fixture_title_dir", "table": "compact"}

        assert page_title_layout_messages(layout) == []

    def test_an_unknown_name_is_an_error_naming_it(self):
        messages = page_title_layout_messages("no_such_layout")

        assert [message.id for message in messages] == ["mvp.E003"]
        assert isinstance(messages[0], checks.Error)
        assert "no_such_layout" in messages[0].msg

    def test_an_unknown_name_among_valid_ones_in_a_dict_is_an_error_naming_it(self):
        layout = {"page": "default", "list": "no_such_layout", "table": "compact"}

        messages = page_title_layout_messages(layout)

        assert [message.id for message in messages] == ["mvp.E003"]
        assert "no_such_layout" in messages[0].msg

    def test_each_unknown_name_in_a_dict_is_reported(self):
        layout = {"page": "first_unknown", "list": "second_unknown"}

        messages = page_title_layout_messages(layout)

        assert len(messages) == 2
        assert "first_unknown" in messages[0].msg
        assert "second_unknown" in messages[1].msg

    def test_the_error_says_where_the_value_is_set(self):
        messages = page_title_layout_messages("no_such_layout")

        assert "page_title" in messages[0].hint


class TestPageTitleLayoutCheck:
    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_page_title_layout(None) == []

    def test_the_check_is_registered(self):
        assert check_page_title_layout in registry.registered_checks

    def test_an_unknown_name_in_the_setting_stops_the_check_command(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["page_title"], "layout", "no_such_layout")

        with pytest.raises(SystemCheckError, match=r"mvp\.E003"):
            call_command("check", "mvp", stderr=StringIO())


class TestEmailBrandCheck:
    @pytest.fixture(autouse=True)
    def fresh_brand(self):
        from mvp.email.brand import EmailBrand

        EmailBrand.current.cache_clear()
        yield
        EmailBrand.current.cache_clear()

    @pytest.fixture
    def project_css(self, tmp_path, settings):
        settings.STATICFILES_DIRS = [tmp_path]

        def write(text):
            (tmp_path / "css").mkdir(exist_ok=True)
            (tmp_path / "css" / "project.css").write_text(text)

        return write

    def test_the_repositorys_own_settings_report_nothing(self):
        assert check_email_brand(None) == []

    def test_the_check_is_registered(self):
        assert check_email_brand in registry.registered_checks

    def test_an_undefined_theme_is_a_warning_naming_it(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "nosuchtheme")

        messages = check_email_brand(None)

        assert [(message.level, message.id) for message in messages] == [(checks.WARNING, "mvp.W002")]
        assert "nosuchtheme" in messages[0].msg

    def test_an_unreadable_colour_is_a_warning_naming_the_theme_and_property(self, project_css, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brandx")
        project_css("[data-theme=brandx]{--color-primary:not-a-colour}")

        messages = check_email_brand(None)

        assert [(message.level, message.id) for message in messages] == [(checks.WARNING, "mvp.W003")]
        assert "brandx" in messages[0].msg
        assert "primary" in messages[0].msg

    def test_a_problem_does_not_stop_the_check_command(self, monkeypatch):
        from mvp.config import MVP_CONFIG

        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "nosuchtheme")
        stderr = StringIO()

        call_command("check", "mvp", stderr=stderr)

        assert "mvp.W002" in stderr.getvalue()

    def test_a_brand_that_cannot_be_read_is_a_warning_not_a_crash(self, monkeypatch):
        class UnreadableBrand:
            @staticmethod
            def problems():
                raise ValueError("Missing staticfiles manifest entry for 'brand/email/logo.png'")

        monkeypatch.setattr("mvp.checks.EmailBrand", UnreadableBrand)

        messages = check_email_brand(None)

        assert [message.level for message in messages] == [checks.WARNING]
        assert "manifest" in messages[0].msg


class TestEmailLogoCheck:
    LOGO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>'

    @pytest.fixture(autouse=True)
    def fresh_brand(self):
        from mvp.email.brand import EmailBrand

        EmailBrand.current.cache_clear()
        yield
        EmailBrand.current.cache_clear()

    @pytest.fixture
    def project_static(self, tmp_path, settings):
        settings.STATICFILES_DIRS = [tmp_path]
        (tmp_path / "brand").mkdir()
        return tmp_path / "brand"

    def test_a_project_logo_with_the_packages_png_is_a_warning_naming_the_command(self, project_static):
        (project_static / "logo.svg").write_text(self.LOGO_SVG)

        messages = check_email_brand(None)

        assert [(message.level, message.id) for message in messages] == [(checks.WARNING, "mvp.W004")]
        assert "mvp_email_logos" in messages[0].hint

    def test_a_project_png_means_no_warning(self, project_static):
        (project_static / "logo.svg").write_text(self.LOGO_SVG)
        (project_static / "email").mkdir()
        (project_static / "email" / "logo.png").write_bytes(b"")

        assert check_email_brand(None) == []

    def test_no_project_logo_means_no_warning(self, project_static):
        assert check_email_brand(None) == []
