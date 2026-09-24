"""Tests for the installable-app routes registered in ``mvp.urls``."""

import pytest
from django.test import override_settings
from django.urls import resolve as resolve_url
from django.urls import reverse

from mvp.pwa.resolver import resolve


class TestInstallableAppUrls:
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_two_routes_have_fixed_names_and_paths(self):
        assert reverse("mvp-pwa-manifest") == "/account/manifest.webmanifest"
        assert reverse("mvp-pwa-service-worker") == "/account/sw.js"

    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_routes_resolve_to_the_packaged_views(self):
        assert resolve_url("/account/manifest.webmanifest").func.__name__ == "manifest"
        assert resolve_url("/account/sw.js").func.__name__ == "service_worker"

    @pytest.mark.django_db
    @override_settings(ROOT_URLCONF="tests.urls_pwa")
    def test_the_resolver_reports_both_urls_when_mounted(self, rf):
        result = resolve(rf.get("/"))

        assert result["manifest_url"] == "/account/manifest.webmanifest"
        assert result["worker_url"] == "/account/sw.js"
