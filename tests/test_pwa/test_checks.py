"""Tests for the two startup warnings, run through Django's check framework."""

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
class TestRootIncludeWarning:
    def test_a_missing_include_is_reported(self, settings, images):
        settings.ROOT_URLCONF = "tests.urls_pwa_absent"

        warnings = mvp_warnings()

        assert [w.id for w in warnings] == ["mvp.W001"]
        assert "mvp.pwa.urls" in warnings[0].msg

    def test_an_include_under_a_sub_path_is_reported(self, settings, images):
        settings.ROOT_URLCONF = "tests.urls_pwa_subpath"

        assert [w.id for w in mvp_warnings()] == ["mvp.W001"]

    def test_an_include_at_the_root_is_accepted(self, settings, images):
        settings.ROOT_URLCONF = "tests.urls_pwa"

        assert mvp_warnings() == []


@pytest.mark.usefixtures("feature_on")
class TestMissingImagesWarning:
    @pytest.fixture(autouse=True)
    def include_mounted(self, settings):
        settings.ROOT_URLCONF = "tests.urls_pwa"

    def test_every_missing_image_is_named(self, static_dir):
        warnings = mvp_warnings()

        assert [w.id for w in warnings] == ["mvp.W002"]
        for file in IMAGES.values():
            assert IMAGE_DIRECTORY + file in warnings[0].msg

    def test_only_the_missing_image_is_named(self, images):
        (images / "icon-512.png").unlink()

        warnings = mvp_warnings()

        assert [w.id for w in warnings] == ["mvp.W002"]
        assert "brand/pwa/icon-512.png" in warnings[0].msg
        assert "icon-192.png" not in warnings[0].msg

    def test_the_hint_names_the_command_that_makes_them(self, static_dir):
        assert "python manage.py mvp_pwa_icons" in mvp_warnings()[0].hint

    def test_nothing_is_reported_when_everything_is_in_place(self, images):
        assert mvp_warnings() == []
