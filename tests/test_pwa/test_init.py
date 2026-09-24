"""Tests for ``mvp.pwa.resolve``, the one place installable-app values are worked out."""

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings
from django.urls import set_script_prefix

from mvp.pwa import resolve


@pytest.fixture
def request_(rf):
    return rf.get("/", HTTP_HOST="shop.example.org")


@pytest.mark.django_db
class TestResolveDefaults:
    def test_display_is_standalone(self, request_):
        assert resolve(request_)["display"] == "standalone"

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

    def test_configured_name_wins(self, request_, monkeypatch):
        monkeypatch.setitem(_pwa_config(), "name", "Configured")

        assert resolve(request_)["name"] == "Configured"

    def test_configured_short_name_wins(self, request_, monkeypatch):
        monkeypatch.setitem(_pwa_config(), "short_name", "Short")

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

    def test_configured_start_url_wins_but_scope_stays_the_prefix(
        self, request_, monkeypatch
    ):
        set_script_prefix("/app/")
        monkeypatch.setitem(_pwa_config(), "start_url", "/app/home/")

        result = resolve(request_)

        assert result["start_url"] == "/app/home/"
        assert result["scope"] == "/app/"


@pytest.mark.django_db
class TestResolveUrls:
    @override_settings(ROOT_URLCONF="tests.urls_pwa_absent")
    def test_urls_are_none_when_the_include_is_unmounted(self, request_):
        result = resolve(request_)

        assert result["manifest_url"] is None
        assert result["worker_url"] is None


@pytest.mark.django_db
class TestResolveColours:
    def test_configured_colours_win(self, request_, monkeypatch):
        monkeypatch.setitem(_pwa_config(), "theme_color", "#123456")
        monkeypatch.setitem(_pwa_config(), "background_color", "#abcdef")

        result = resolve(request_)

        assert result["theme_color"] == "#123456"
        assert result["background_color"] == "#abcdef"


def _pwa_config():
    from mvp.config import MVP_CONFIG

    return MVP_CONFIG["pwa"]
