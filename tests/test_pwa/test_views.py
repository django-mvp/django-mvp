"""Tests for the manifest and worker views, through a URLconf mounted at the root."""

import json

import pytest
from django.contrib.sites.models import Site
from django.test import override_settings

from mvp.config import MVP_CONFIG


@pytest.fixture(autouse=True)
def mounted_at_root():
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

    def test_it_carries_colours_for_a_shipped_theme(self, client):
        manifest = client.get("/manifest.webmanifest").json()

        assert manifest["theme_color"] == "#ffffff"
        assert manifest["background_color"] == "#ffffff"

    def test_it_omits_colours_for_an_unknown_theme(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "brand")

        manifest = client.get("/manifest.webmanifest").json()

        assert "theme_color" not in manifest
        assert "background_color" not in manifest

    def test_it_answers_with_the_feature_off(self, client):
        assert MVP_CONFIG["pwa"]["enabled"] is False
        assert client.get("/manifest.webmanifest").status_code == 200

    def test_it_answers_with_the_feature_on(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["pwa"], "enabled", True)

        assert client.get("/manifest.webmanifest").status_code == 200

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

    def test_it_answers_with_the_feature_on(self, client, monkeypatch):
        monkeypatch.setitem(MVP_CONFIG["pwa"], "enabled", True)

        assert client.get("/sw.js").status_code == 200
