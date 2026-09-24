"""Tests for ``mvp.pwa.resolver.resolve``, the one place installable-app values are worked out."""

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings
from django.urls import set_script_prefix

from mvp.config import MVP_CONFIG
from mvp.pwa.resolver import resolve


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


@pytest.mark.django_db
class TestResolveThemeColours:
    def test_colours_come_from_the_default_theme(self, request_):
        result = resolve(request_)

        assert result["theme_color"] == "#ffffff"
        assert result["background_color"] == "#ffffff"

    def test_a_theme_the_package_does_not_ship_has_no_colour(
        self, request_, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brand")

        result = resolve(request_)

        assert result["theme_color"] is None
        assert result["background_color"] is None


@pytest.mark.django_db
class TestResolveEachOverrideAlone:
    """Each value set on its own changes only itself (scenario 1)."""

    KEYS = (
        "name",
        "short_name",
        "start_url",
        "display",
        "theme_color",
        "background_color",
    )

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("name", "Configured"),
            ("short_name", "Short"),
            ("start_url", "/home/"),
            ("display", "minimal-ui"),
            ("theme_color", "#123456"),
            ("background_color", "#abcdef"),
        ],
    )
    def test_only_that_value_changes(self, request_, monkeypatch, key, value):
        before = resolve(request_)
        monkeypatch.setitem(MVP_CONFIG["pwa"], key, value)

        after = resolve(request_)

        assert after[key] == value
        changed = {k for k in before if before[k] != after[k]}
        # An unset short_name follows the name, so overriding the name moves both.
        expected = {key, "short_name"} if key == "name" else {key}
        assert changed == expected


@pytest.mark.django_db
class TestResolveServiceWorker:
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_packaged_worker_is_used_by_default(self, request_):
        assert resolve(request_)["worker_url"] == "/sw.js"

    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_a_configured_worker_replaces_the_packaged_one(
        self, request_, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["pwa"], "service_worker", "/my-worker.js")

        assert resolve(request_)["worker_url"] == "/my-worker.js"
