"""Tests for the startup warning, run through Django's check framework."""

import pytest
from django.core.checks import run_checks

from mvp.config import MVP_CONFIG
from mvp.pwa.resolver import IMAGE_DIRECTORY, IMAGES


def mvp_warnings():
    return [m for m in run_checks() if m.id.startswith("mvp.")]


@pytest.fixture
def static_dir(tmp_path, settings):
    """A static directory the finders read, and nothing else."""
    settings.STATICFILES_DIRS = [tmp_path]
    settings.STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder"
    ]
    return tmp_path


@pytest.fixture
def images(static_dir):
    directory = static_dir / IMAGE_DIRECTORY
    directory.mkdir(parents=True)
    for file in IMAGES.values():
        (directory / file).write_bytes(b"\x89PNG placeholder")
    return directory


@pytest.fixture
def feature_on(monkeypatch):
    monkeypatch.setitem(MVP_CONFIG, "pwa", True)


class TestChecksWithTheFeatureOff:
    def test_nothing_is_reported_even_when_everything_is_missing(
        self, settings, static_dir
    ):
        settings.ROOT_URLCONF = "tests.urls_pwa_absent"

        assert mvp_warnings() == []


@pytest.mark.usefixtures("feature_on")
class TestUnmountedWarning:
    def test_an_unmounted_account_center_is_reported(self, settings, images):
        settings.ROOT_URLCONF = "tests.urls_pwa_absent"

        warnings = mvp_warnings()

        assert [w.id for w in warnings] == ["mvp.W001"]
        assert "include('mvp.urls')" in warnings[0].hint

    def test_mvp_urls_under_any_prefix_is_accepted(self, settings, images):
        settings.ROOT_URLCONF = "tests.urls_pwa"

        assert mvp_warnings() == []


@pytest.mark.usefixtures("feature_on")
class TestMissingImagesAreNotReported:
    def test_missing_images_raise_no_warning(self, settings, static_dir):
        # The images are a deployment step, so development starts clean
        # without them.
        settings.ROOT_URLCONF = "tests.urls_pwa"

        assert mvp_warnings() == []
