"""The demo turns the installable app on and serves its files through the Account Center mount.

Source: demo/settings.py, demo/urls.py
"""

import pytest

from demo import settings as demo_settings


class TestDemoInstallableApp:
    def test_the_demo_settings_turn_the_feature_on(self):
        assert demo_settings.MVP_CONFIG["pwa"] == {"theme_color": "#f8f6f2"}

    @pytest.mark.django_db
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_manifest_answers_beside_the_account_center(self, client):
        response = client.get("/account/manifest.webmanifest")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/manifest+json"

    @pytest.mark.django_db
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_worker_answers_beside_the_account_center(self, client):
        assert client.get("/account/sw.js").status_code == 200
