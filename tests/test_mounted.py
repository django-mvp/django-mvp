"""Tests for ``mvp.mounted`` — mounting one django-mvp app inside another.

Source: mvp/mounted.py
"""

import pytest
from django.test import override_settings

PLAIN_URLCONF = "tests.urls_mounted_plain"


@pytest.mark.django_db
class TestFixtureApp:
    """The fixture app's two pages render through a plain ``include()``."""

    @override_settings(ROOT_URLCONF=PLAIN_URLCONF)
    def test_index_page_renders(self, client):
        response = client.get("/mounted/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-index"' in response.content

    @override_settings(ROOT_URLCONF=PLAIN_URLCONF)
    def test_detail_page_renders(self, client):
        response = client.get("/mounted/detail/")

        assert response.status_code == 200
        assert b'id="testapp-mounted-detail"' in response.content
