"""Tests for the manifest and worker views, through a URLconf that mounts ``mvp.urls``."""

import json

import pytest
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings

from mvp.config import MVP_CONFIG


@pytest.fixture(autouse=True)
def mounted_at_root(pwa_enabled):
    with override_settings(ROOT_URLCONF="tests.urls_pwa"):
        yield


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
        assert manifest["display"] == "standalone"

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

    def test_the_short_name_defaults_to_the_name(self, client):
        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["short_name"] == manifest["name"]

    def test_the_name_is_the_current_site_name_with_the_sites_framework(self, client):
        Site.objects.filter(pk=settings.SITE_ID).update(name="Corner Shop")
        Site.objects.clear_cache()

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
        Site.objects.clear_cache()

        manifest = client.get(
            "/manifest.webmanifest", HTTP_HOST="shop.example.org"
        ).json()

        assert manifest["name"] == "shop.example.org"
        assert manifest["short_name"] == "shop.example.org"

    def test_a_hostile_site_name_round_trips_exactly(self, client):
        name = 'Bob\'s "Shop" </script><b>&amp;'
        Site.objects.filter(pk=1).update(name=name)

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

    def test_it_listens_for_install_and_activate(self, client):
        body = client.get("/sw.js").content.decode()

        assert 'addEventListener("install"' in body
        assert 'addEventListener("activate"' in body

    def test_it_has_no_fetch_listener(self, client):
        body = client.get("/sw.js").content.decode()

        assert "fetch" not in body

    def test_it_widens_its_scope_to_the_site_root(self, client):
        assert client.get("/sw.js")["Service-Worker-Allowed"] == "/"

    def test_it_widens_its_scope_to_the_script_prefix(self, client):
        from django.urls import set_script_prefix

        set_script_prefix("/app/")
        try:
            response = client.get("/sw.js")
        finally:
            set_script_prefix("/")

        assert response["Service-Worker-Allowed"] == "/app/"


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

    def test_the_start_url_and_scope_follow_the_script_prefix(self, client):
        from django.urls import set_script_prefix

        set_script_prefix("/app/")
        try:
            manifest = client.get("/manifest.webmanifest").json()
        finally:
            set_script_prefix("/")

        assert manifest["start_url"] == "/app/"
        assert manifest["scope"] == "/app/"
