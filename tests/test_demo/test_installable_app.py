"""The demo turns the installable app on and mounts its URLs at the root.

Source: demo/settings.py, demo/urls.py
"""

import io

import pytest

from demo import settings as demo_settings


class TestDemoInstallableApp:
    def test_the_demo_settings_turn_the_feature_on(self):
        assert demo_settings.MVP_CONFIG["pwa"] == {"theme_color": "#f8f6f2"}

    @pytest.mark.django_db
    def test_the_manifest_answers_at_the_root(self, client):
        response = client.get("/manifest.webmanifest")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/manifest+json"

    @pytest.mark.django_db
    def test_the_worker_answers_at_the_root(self, client):
        assert client.get("/sw.js").status_code == 200


class TestDemoInstallableAppImages:
    def test_generated_images_clear_the_missing_image_warning(
        self, monkeypatch, settings, tmp_path
    ):
        # The images are generated, never committed: run the command the demo's
        # README tells a developer to run, then read what the checks say.
        from django.contrib.staticfiles import finders
        from django.core.checks import run_checks
        from django.core.management import call_command

        from mvp.config import MVP_CONFIG

        # The test settings pin their own MVP_CONFIG, so turn the feature on
        # the way the demo does.
        monkeypatch.setitem(MVP_CONFIG, "pwa", True)
        settings.STATICFILES_DIRS = [tmp_path]
        finders.get_finder.cache_clear()
        try:
            call_command("mvp_pwa_icons", output_dir=str(tmp_path), stdout=io.StringIO())

            assert "mvp.W002" not in [message.id for message in run_checks()]
        finally:
            finders.get_finder.cache_clear()
