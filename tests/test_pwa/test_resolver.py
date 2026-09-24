"""Tests for ``mvp.pwa.resolver.resolve``, the one place installable-app values are worked out."""

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings
from django.urls import set_script_prefix

from mvp.config import MVP_CONFIG
from mvp.pwa.resolver import InstallableApp, resolve


@pytest.fixture
def request_(rf):
    return rf.get("/", HTTP_HOST="shop.example.org")


@pytest.mark.django_db
class TestResolveDefaults:
    def test_short_name_defaults_to_the_name(self, request_):
        result = resolve(request_)

        assert result["short_name"] == result["name"]

    def test_start_url_and_scope_are_the_site_root(self, request_):
        result = resolve(request_)

        assert result["start_url"] == "/"
        assert result["scope"] == "/"

    def test_image_urls_point_at_the_brand_pwa_directory(self, request_):
        result = resolve(request_)

        assert result["icon_192"] == "/static/brand/pwa/icon-192.png"
        assert result["icon_512"] == "/static/brand/pwa/icon-512.png"
        assert result["icon_maskable_512"] == "/static/brand/pwa/icon-maskable-512.png"
        assert result["apple_touch_icon"] == "/static/brand/pwa/apple-touch-icon.png"


@pytest.mark.django_db
class TestResolveName:
    def test_name_is_the_current_site_name_with_the_sites_framework(self, request_):
        Site.objects.filter(pk=settings.SITE_ID).update(name="Corner Shop")

        assert resolve(request_)["name"] == "Corner Shop"

    def test_name_is_the_request_host_without_the_sites_framework(self, request_):
        apps = [a for a in settings.INSTALLED_APPS if a != "django.contrib.sites"]
        with override_settings(INSTALLED_APPS=apps):
            assert resolve(request_)["name"] == "shop.example.org"

    def test_name_falls_back_to_the_host_when_no_site_matches(self, request_):
        Site.objects.all().delete()
        Site.objects.clear_cache()

        assert resolve(request_)["name"] == "shop.example.org"

    def test_name_falls_back_to_the_host_when_the_site_name_is_empty(
        self, request_
    ):
        Site.objects.filter(pk=settings.SITE_ID).update(name="")
        Site.objects.clear_cache()

        result = resolve(request_)

        assert result["name"] == "shop.example.org"
        assert result["short_name"] == "shop.example.org"

    def test_configured_site_name_wins(self, request_, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Configured")

        assert resolve(request_)["name"] == "Configured"

    def test_configured_short_name_wins(self, request_, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "short_name", "Short")

        result = resolve(request_)

        assert result["short_name"] == "Short"
        assert result["name"] != "Short"


@pytest.mark.django_db
class TestResolveScriptPrefix:
    @pytest.fixture(autouse=True)
    def restore_prefix(self):
        yield
        set_script_prefix("/")

    def test_start_url_and_scope_follow_the_script_prefix(self, request_):
        set_script_prefix("/app/")

        result = resolve(request_)

        assert result["start_url"] == "/app/"
        assert result["scope"] == "/app/"


@pytest.mark.django_db
class TestResolveUrls:
    @override_settings(ROOT_URLCONF="tests.urls_pwa_absent")
    def test_urls_are_none_when_the_include_is_unmounted(self, request_):
        result = resolve(request_)

        assert result["manifest_url"] is None
        assert result["worker_url"] is None


@pytest.mark.django_db
class TestResolveThemeColours:
    def test_colours_come_from_the_default_theme(self, request_):
        result = resolve(request_)

        assert result["theme_color"] == "#ffffff"

    def test_a_theme_the_package_does_not_ship_has_no_colour(
        self, request_, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brand")

        result = resolve(request_)

        assert result["theme_color"] is None

    def test_a_configured_colour_wins(self, request_, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})

        assert resolve(request_)["theme_color"] == "#123456"

    def test_a_configured_colour_is_used_for_a_theme_the_package_does_not_ship(
        self, request_, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brand")
        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})

        assert resolve(request_)["theme_color"] == "#123456"

    def test_a_dict_without_a_colour_falls_back_to_the_theme(
        self, request_, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": None})

        assert resolve(request_)["theme_color"] == "#ffffff"


class TestResolveShape:
    @pytest.mark.django_db
    def test_it_carries_no_display_or_background_colour(self, request_):
        result = resolve(request_)

        assert "display" not in result
        assert "background_color" not in result

    @pytest.mark.django_db
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_worker_is_the_packaged_one(self, request_):
        assert resolve(request_)["worker_url"] == "/account/sw.js"


class TestInstallableApp:
    """``MVP_CONFIG["pwa"]`` is on when truthy, and its colour is the one key."""

    @pytest.mark.parametrize("value", [False, None, {}])
    def test_a_falsey_value_is_off(self, monkeypatch, value):
        monkeypatch.setitem(MVP_CONFIG, "pwa", value)

        assert InstallableApp.enabled() is False

    def test_the_default_is_off(self):
        assert MVP_CONFIG["pwa"] is False
        assert InstallableApp.enabled() is False

    def test_true_is_on_with_the_theme_colour(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "pwa", True)

        assert InstallableApp.enabled() is True
        assert InstallableApp.theme_color() == "#ffffff"

    def test_a_dict_is_on_and_supplies_the_colour(self, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "pwa", {"theme_color": "#123456"})

        assert InstallableApp.enabled() is True
        assert InstallableApp.theme_color() == "#123456"

    def test_the_colour_is_none_for_a_theme_the_package_does_not_ship(
        self, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG, "pwa", True)
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brand")

        assert InstallableApp.theme_color() is None
