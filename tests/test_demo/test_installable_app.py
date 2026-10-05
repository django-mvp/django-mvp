"""The demo turns the installable app on and serves its files through the Account Center mount.

Source: demo/settings.py, demo/urls.py
"""

import pytest


class TestDemoPwa:
    @pytest.mark.django_db
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_manifest_answers_beside_the_account_center(self, client):
        response = client.get("/manifest.webmanifest")

        assert response.status_code == 200
        assert response["Content-Type"] == "application/manifest+json"

    @pytest.mark.django_db
    @pytest.mark.usefixtures("pwa_enabled")
    def test_the_worker_answers_beside_the_account_center(self, client):
        assert client.get("/sw.js").status_code == 200
