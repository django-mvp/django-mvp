"""Tests for the installable-app routes registered in ``mvp.urls``."""

from django.test import override_settings
from django.urls import resolve as resolve_url
from django.urls import reverse


class TestInstallableAppUrls:
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_two_routes_have_fixed_names_and_paths(self):
        assert reverse("mvp-pwa-manifest") == "/account/manifest.webmanifest"
        assert reverse("mvp-pwa-service-worker") == "/account/sw.js"

    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_routes_resolve_to_the_packaged_views(self):
        assert resolve_url("/account/manifest.webmanifest").func.__name__ == "manifest"
        assert resolve_url("/account/sw.js").func.__name__ == "service_worker"
