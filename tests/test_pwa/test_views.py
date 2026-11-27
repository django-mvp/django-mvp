"""Tests for the manifest and worker views, through a URLconf that mounts ``mvp.urls``."""

import json

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings
from django.urls import set_script_prefix

from mvp.config import MVP_CONFIG


@pytest.fixture(autouse=True)
def mounted_at_root(pwa_enabled):
    with override_settings(ROOT_URLCONF="tests.urls_pwa"):
        yield


@pytest.fixture(autouse=True)
def fresh_site_cache():
    """The Site lookup is cached per process: clear it before and after each test."""
    Site.objects.clear_cache()
    yield
    Site.objects.clear_cache()


@pytest.fixture
def app_prefix():
    """Serve the project under ``/app/``, and restore the root prefix after."""
    set_script_prefix("/app/")
    yield "/app/"
    set_script_prefix("/")


@pytest.mark.django_db
class TestManifestView:
    def test_it_answers_as_a_web_app_manifest(self, client):
        response = client.get("/manifest.webmanifest")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/manifest+json"

    def test_it_carries_the_identity_keys(self, client):
        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["name"] == "example.com"
        assert manifest["short_name"] == "example.com"
        assert manifest["start_url"] == "/"
        assert manifest["scope"] == "/"

    def test_it_lists_the_three_icons(self, client):
        icons = client.get("/manifest.webmanifest").json()["icons"]

        assert icons == [
            {
                "src": "/static/brand/pwa/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/static/brand/pwa/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
            {
                "src": "/static/brand/pwa/icon-maskable-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ]

    def test_the_theme_and_background_colour_are_the_configured_colour(self, client):
        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["theme_color"] == "#123456"
        assert manifest["background_color"] == "#123456"

    def test_the_name_is_the_current_site_name_with_the_sites_framework(self, client):
        Site.objects.filter(pk=settings.SITE_ID).update(name="Corner Shop")

        assert client.get("/manifest.webmanifest").json()["name"] == "Corner Shop"

    def test_the_name_is_the_request_host_without_the_sites_framework(self, client):
        apps = [a for a in settings.INSTALLED_APPS if a != "django.contrib.sites"]
        with override_settings(INSTALLED_APPS=apps):
            manifest = client.get(
                "/manifest.webmanifest", HTTP_HOST="shop.example.org"
            ).json()

        assert manifest["name"] == "shop.example.org"

    def test_the_names_fall_back_to_the_host_when_the_site_name_is_empty(self, client):
        Site.objects.filter(pk=settings.SITE_ID).update(name="")

        manifest = client.get(
            "/manifest.webmanifest", HTTP_HOST="shop.example.org"
        ).json()

        assert manifest["name"] == "shop.example.org"
        assert manifest["short_name"] == "shop.example.org"

    def test_a_hostile_site_name_round_trips_exactly(self, client):
        name = 'Bob\'s "Shop" </script><b>&amp;'
        Site.objects.filter(pk=settings.SITE_ID).update(name=name)

        response = client.get("/manifest.webmanifest")
        manifest = json.loads(response.content)

        assert manifest["name"] == name
        assert manifest["short_name"] == name


@pytest.mark.django_db
class TestServiceWorkerView:
    def test_it_answers_as_javascript_that_is_never_cached(self, client):
        response = client.get("/sw.js")

        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/javascript")
        assert response["Cache-Control"] == "no-cache"

    def test_it_has_no_fetch_listener(self, client):
        body = client.get("/sw.js").content.decode()

        assert "fetch" not in body

    def test_it_widens_its_scope_to_the_site_root(self, client):
        assert client.get("/sw.js")["Service-Worker-Allowed"] == "/"

    def test_it_widens_its_scope_to_the_script_prefix(self, client, app_prefix):
        assert client.get("/sw.js")["Service-Worker-Allowed"] == app_prefix


@pytest.mark.django_db
class TestManifestOverrides:
    @pytest.mark.parametrize(
        ("key", "value"),
        [("site_name", "Configured"), ("short_name", "Short")],
    )
    def test_each_name_reaches_the_manifest(self, client, monkeypatch, key, value):
        monkeypatch.setitem(MVP_CONFIG, key, value)

        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["short_name" if key == "short_name" else "name"] == value

    def test_the_short_name_follows_a_configured_site_name(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Configured")

        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["short_name"] == "Configured"

    def test_the_start_url_and_scope_follow_the_script_prefix(self, client, app_prefix):
        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["start_url"] == app_prefix
        assert manifest["scope"] == app_prefix


@pytest.mark.django_db
class TestInstallView:
    @pytest.fixture(autouse=True)
    def in_the_app_shell(self):
        # The page draws the whole shell, whose menus link to the demo's pages.
        with override_settings(ROOT_URLCONF="demo.urls"):
            yield

    def test_the_other_devices_are_readable_without_the_script(self, client):
        response = client.get("/install/")
        assert response.status_code == 200
        html = response.content.decode()

        # Only what the script reveals starts hidden: the phone sections under
        # "Other devices" are drawn shown, so the page reads in full without it.
        assert '<div data-mvp-install-other="ios" x-bind' in html
        assert '<div data-mvp-install-other="android" x-bind' in html

    def test_the_title_names_the_short_name(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG, "site_name", "Corner Shop")
        monkeypatch.setitem(MVP_CONFIG, "short_name", "Corner")

        title = client.get("/install/").context["page"]["title"]

        assert "Corner" in str(title)
        assert "Corner Shop" not in str(title)

    def test_the_title_falls_back_to_the_site_name(self, client):
        Site.objects.filter(pk=settings.SITE_ID).update(name="Corner Shop")

        title = client.get("/install/").context["page"]["title"]

        assert "Corner Shop" in str(title)

    def test_a_hostile_site_name_is_escaped(self, client):
        Site.objects.filter(pk=settings.SITE_ID).update(name="<b>Shop</b>")

        html = client.get("/install/").content.decode()

        assert "<b>Shop</b>" not in html
        assert "&lt;b&gt;Shop&lt;/b&gt;" in html
