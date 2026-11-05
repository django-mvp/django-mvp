"""Tests for the ``mvp_email_logos`` command.

PNG sizes are read from the IHDR header, so the checks need nothing beyond the
standard library.
"""

import io
import struct
import sys

import pytest
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.core.management.base import CommandError

WIDE_LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10"><rect width="20" height="10" fill="#ff0000"/></svg>'
SQUARE_LOGO = WIDE_LOGO.replace("viewBox=\"0 0 20 10\"", 'viewBox="0 0 10 10"').replace('width="20"', 'width="10"')


def png_size(data):
    """Width and height from the IHDR chunk (bytes 16 to 24)."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


@pytest.fixture
def static_dir(tmp_path, settings):
    """A project static directory, the first ``STATICFILES_DIRS`` entry, holding a ``brand`` directory."""
    static = tmp_path / "project-static"
    (static / "brand").mkdir(parents=True)
    settings.STATICFILES_DIRS = [static]
    return static


@pytest.fixture
def logos(static_dir):
    """The project's light and dark logos, as SVG."""
    (static_dir / "brand" / "logo.svg").write_text(WIDE_LOGO)
    (static_dir / "brand" / "logo_dark.svg").write_text(SQUARE_LOGO)
    return static_dir / "brand"


def run(**options):
    """Run the command and give what it printed."""
    out = io.StringIO()
    call_command("mvp_email_logos", stdout=out, **options)
    return out.getvalue()


class TestMvpEmailLogos:
    def test_both_logos_are_written_64_pixels_high_into_the_first_static_directory(self, logos, static_dir):
        run()

        written = static_dir / "brand" / "email"
        assert png_size((written / "logo.png").read_bytes()) == (128, 64)
        assert png_size((written / "logo_dark.png").read_bytes()) == (64, 64)

    def test_the_output_directory_option_says_where_to_write(self, logos, tmp_path):
        run(output_dir=str(tmp_path / "out"))

        assert png_size((tmp_path / "out" / "brand" / "email" / "logo.png").read_bytes())[1] == 64
        assert not (logos.parent / "brand" / "email").exists()

    def test_the_static_finders_then_give_the_projects_png(self, logos, static_dir):
        run()

        assert finders.find("brand/email/logo.png") == str(static_dir / "brand" / "email" / "logo.png")
        assert finders.find("brand/email/logo_dark.png") == str(static_dir / "brand" / "email" / "logo_dark.png")

    def test_rerunning_after_the_logo_changes_rewrites_the_png(self, logos, static_dir):
        run()
        (logos / "logo.svg").write_text(SQUARE_LOGO)

        run()

        assert png_size((static_dir / "brand" / "email" / "logo.png").read_bytes()) == (64, 64)

    def test_a_missing_renderer_names_the_package_and_writes_nothing(self, logos, static_dir, monkeypatch):
        monkeypatch.setitem(sys.modules, "resvg_py", None)

        with pytest.raises(CommandError, match="resvg-py"):
            run()

        assert not (static_dir / "brand" / "email").exists()

    def test_a_missing_logo_names_the_file(self, tmp_path, settings):
        settings.STATICFILES_DIRS = [tmp_path]
        settings.STATICFILES_FINDERS = ["django.contrib.staticfiles.finders.FileSystemFinder"]

        with pytest.raises(CommandError, match=r"brand/logo\.svg"):
            run()

    def test_the_packages_own_logo_is_reported_when_the_project_has_none(self, static_dir):
        output = run()

        assert "package's own" in output
        assert png_size((static_dir / "brand" / "email" / "logo.png").read_bytes())[1] == 64

    def test_the_projects_own_logos_are_not_reported_as_the_packages(self, logos):
        assert "package's own" not in run()

    def test_only_prefixed_static_directories_name_the_option(self, logos, settings):
        settings.STATICFILES_DIRS = [("assets", logos.parent)]

        with pytest.raises(CommandError, match="--output-dir"):
            run()

    def test_a_missing_dark_logo_is_skipped(self, tmp_path, settings):
        settings.STATICFILES_DIRS = [tmp_path]
        settings.STATICFILES_FINDERS = ["django.contrib.staticfiles.finders.FileSystemFinder"]
        (tmp_path / "brand").mkdir()
        (tmp_path / "brand" / "logo.svg").write_text(WIDE_LOGO)

        run()

        assert (tmp_path / "brand" / "email" / "logo.png").exists()
        assert not (tmp_path / "brand" / "email" / "logo_dark.png").exists()

    def test_a_logo_that_is_not_svg_is_reported(self, logos):
        (logos / "logo.svg").write_text("not svg")

        with pytest.raises(CommandError, match=r"logo\.svg"):
            run()
