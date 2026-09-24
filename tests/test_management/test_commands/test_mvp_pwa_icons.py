"""Tests for the ``mvp_pwa_icons`` command.

PNG sizes are read from the IHDR header and pixels from the first scanline, so
the checks need nothing beyond the standard library.
"""

import io
import struct
import sys
import zlib
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from mvp.config import MVP_CONFIG
from mvp.pwa.resolver import IMAGE_DIRECTORY, IMAGES

RED_SQUARE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    '<rect width="10" height="10" fill="#ff0000"/></svg>'
)
BLUE_SQUARE = RED_SQUARE.replace("#ff0000", "#0000ff")
ROUND_MARK = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    '<circle cx="5" cy="5" r="4" fill="#ff0000"/></svg>'
)
TALL_MARK = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 20">'
    '<rect width="10" height="20" fill="#ff0000"/></svg>'
)
SIZES = {
    "icon_192": 192,
    "icon_512": 512,
    "icon_maskable_512": 512,
    "apple_touch_icon": 180,
}


def png_size(data):
    """Width and height from the IHDR chunk (bytes 16 to 24)."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def first_row(data):
    """The RGBA pixels of a PNG's first scanline.

    The first row has no row above it, so undoing the filter needs only the
    pixel to the left.
    """
    width, _ = png_size(data)
    assert data[24:26] == b"\x08\x06", "expected 8-bit RGBA"
    stream = io.BytesIO(data[8:])
    idat = b""
    while chunk_header := stream.read(8):
        length, kind = struct.unpack(">I4s", chunk_header)
        body = stream.read(length)
        stream.read(4)
        if kind == b"IDAT":
            idat += body
    raw = zlib.decompress(idat)
    method, line = raw[0], bytearray(raw[1 : 1 + width * 4])
    for i in range(4, len(line)):
        left = line[i - 4]
        if method == 1:
            line[i] = (line[i] + left) & 0xFF
        elif method == 3:
            line[i] = (line[i] + left // 2) & 0xFF
        elif method == 4:
            line[i] = (line[i] + left) & 0xFF
    return [tuple(line[i : i + 4]) for i in range(0, len(line), 4)]


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "out"


@pytest.fixture
def brand_dir(tmp_path, settings):
    """A project static directory holding the project's own mark."""
    static = tmp_path / "project-static"
    (static / "brand").mkdir(parents=True)
    settings.STATICFILES_DIRS = [static]
    return static / "brand"


@pytest.fixture
def mark(brand_dir):
    path = brand_dir / "icon.svg"
    path.write_text(RED_SQUARE)
    return path


@pytest.fixture
def images(output_dir, mark):
    """Run the command and read the four images back, keyed like ``IMAGES``."""
    call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())
    directory = output_dir / IMAGE_DIRECTORY
    return {key: (directory / file).read_bytes() for key, file in IMAGES.items()}


class TestMvpPwaIcons:
    def test_all_four_images_are_written_at_their_sizes(self, images):
        for key, side in SIZES.items():
            assert png_size(images[key]) == (side, side)

    def test_rerunning_after_the_mark_changes_rewrites_the_images(
        self, images, mark, output_dir
    ):
        mark.write_text(BLUE_SQUARE)

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        rewritten = (output_dir / IMAGE_DIRECTORY / IMAGES["icon_512"]).read_bytes()
        assert rewritten != images["icon_512"]

    def test_a_non_square_mark_is_centred_not_stretched(self, mark, output_dir):
        mark.write_text(TALL_MARK)

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        row = first_row((output_dir / IMAGE_DIRECTORY / IMAGES["icon_512"]).read_bytes())
        assert row[0][3] == 0
        assert row[-1][3] == 0
        assert row[len(row) // 2] == (255, 0, 0, 255)

    def test_plain_icons_have_a_transparent_corner(self, mark, output_dir):
        mark.write_text(ROUND_MARK)

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        for key in ("icon_192", "icon_512"):
            data = (output_dir / IMAGE_DIRECTORY / IMAGES[key]).read_bytes()
            assert first_row(data)[0][3] == 0

    def test_maskable_and_apple_images_are_opaque_in_the_corner(
        self, mark, output_dir, monkeypatch
    ):
        mark.write_text(ROUND_MARK)
        monkeypatch.setitem(MVP_CONFIG["pwa"], "background_color", "#00ff00")

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        for key in ("icon_maskable_512", "apple_touch_icon"):
            data = (output_dir / IMAGE_DIRECTORY / IMAGES[key]).read_bytes()
            assert first_row(data)[0] == (0, 255, 0, 255)

    def test_the_padded_images_keep_the_mark_inside_the_safe_zone(
        self, images
    ):
        row = first_row(images["icon_maskable_512"])
        assert row[len(row) // 2] != (255, 0, 0, 255)

    def test_the_background_falls_back_to_the_theme_colour_then_white(
        self, mark, output_dir, monkeypatch
    ):
        monkeypatch.setitem(MVP_CONFIG["pwa"], "background_color", None)
        monkeypatch.setitem(MVP_CONFIG["theme"], "default", "no-such-theme")

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        data = (output_dir / IMAGE_DIRECTORY / IMAGES["apple_touch_icon"]).read_bytes()
        assert first_row(data)[0] == (255, 255, 255, 255)

    def test_the_output_directory_is_created_and_existing_files_overwritten(
        self, mark, output_dir
    ):
        stale = output_dir / IMAGE_DIRECTORY / IMAGES["icon_192"]
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"stale")

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        assert png_size(stale.read_bytes()) == (192, 192)

    def test_the_first_static_directory_is_the_default_output(self, mark, brand_dir):
        call_command("mvp_pwa_icons", stdout=io.StringIO())

        assert (brand_dir.parent / IMAGE_DIRECTORY / IMAGES["icon_192"]).exists()

    def test_a_prefixed_static_directory_is_skipped(
        self, mark, brand_dir, tmp_path, settings
    ):
        # Files in a prefixed entry are served under the prefix, where the
        # manifest never looks, so the first unprefixed entry is used instead.
        plain = tmp_path / "plain"
        settings.STATICFILES_DIRS = [("assets", brand_dir.parent), plain]

        call_command("mvp_pwa_icons", stdout=io.StringIO())

        assert (plain / IMAGE_DIRECTORY / IMAGES["icon_192"]).exists()
        assert not (brand_dir.parent / IMAGE_DIRECTORY / IMAGES["icon_192"]).exists()

    def test_only_prefixed_static_directories_name_the_option(
        self, mark, brand_dir, settings
    ):
        settings.STATICFILES_DIRS = [("assets", brand_dir.parent)]

        with pytest.raises(CommandError, match="--output-dir"):
            call_command("mvp_pwa_icons", stdout=io.StringIO())

    def test_a_pathlib_static_directory_is_accepted(self, mark, brand_dir, settings):
        settings.STATICFILES_DIRS = [Path(brand_dir.parent)]

        call_command("mvp_pwa_icons", stdout=io.StringIO())

        assert (brand_dir.parent / IMAGE_DIRECTORY / IMAGES["icon_512"]).exists()

    def test_without_an_output_directory_it_names_the_option(self, settings):
        settings.STATICFILES_DIRS = []

        with pytest.raises(CommandError, match="--output-dir"):
            call_command("mvp_pwa_icons", stdout=io.StringIO())

    def test_a_missing_renderer_names_the_package(
        self, mark, output_dir, monkeypatch
    ):
        monkeypatch.setitem(sys.modules, "resvg_py", None)

        with pytest.raises(CommandError, match="resvg-py"):
            call_command("mvp_pwa_icons", output_dir=str(output_dir))

    def test_the_packages_own_mark_is_reported_when_the_project_has_none(
        self, brand_dir, output_dir
    ):
        out = io.StringIO()

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=out)

        assert "package's own" in out.getvalue()
        assert png_size(
            (output_dir / IMAGE_DIRECTORY / IMAGES["icon_192"]).read_bytes()
        ) == (192, 192)

    def test_the_projects_own_mark_is_not_reported_as_the_packages(
        self, mark, output_dir
    ):
        out = io.StringIO()

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=out)

        assert "package's own" not in out.getvalue()

    def test_it_never_prompts(self, mark, output_dir, monkeypatch):
        monkeypatch.setattr(sys, "stdin", None)
        monkeypatch.setattr("builtins.input", pytest.fail)

        call_command("mvp_pwa_icons", output_dir=str(output_dir), stdout=io.StringIO())

        assert (output_dir / IMAGE_DIRECTORY / IMAGES["icon_192"]).exists()
