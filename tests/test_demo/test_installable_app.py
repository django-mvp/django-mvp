"""The demo turns the installable app on and mounts its URLs at the root.

Source: demo/settings.py, demo/urls.py
"""

import pytest

from demo import settings as demo_settings


class TestDemoInstallableApp:
    def test_the_demo_settings_turn_the_feature_on(self):
        assert demo_settings.MVP_CONFIG["pwa"]["enabled"] is True

    @pytest.mark.django_db
    def test_the_manifest_answers_at_the_root(self, client):
        response = client.get("/manifest.webmanifest")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/manifest+json"

    @pytest.mark.django_db
    def test_the_worker_answers_at_the_root(self, client):
        assert client.get("/sw.js").status_code == 200


class TestDemoInstallableAppImages:
    def test_the_demo_raises_no_missing_image_warning(self, monkeypatch):
        from django.core.checks import run_checks

        from mvp.config import MVP_CONFIG

        # The test settings pin their own MVP_CONFIG, so turn the feature on
        # the way the demo does and read what the checks say about its files.
        monkeypatch.setitem(MVP_CONFIG["pwa"], "enabled", True)

        assert "mvp.W002" not in [message.id for message in run_checks()]
