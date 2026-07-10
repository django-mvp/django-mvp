"""Tests for the mvp_tailwind management command and the packaged preset.

The command generates a Tailwind v4 entry file for consumer projects that
build their own CSS (Tier 2 in docs/styling.md).
"""

from io import StringIO
from pathlib import Path

from django.core.management import call_command


def _run(*args):
    out = StringIO()
    call_command("mvp_tailwind", *args, stdout=out)
    return out.getvalue()


def test_entry_contains_daisyui_and_preset_import():
    output = _run()
    assert '@import "tailwindcss" source(none);' in output
    assert '@plugin "daisyui";' in output
    assert "mvp/tailwind/base.css" in output
    assert '@source "./templates";' in output


def test_entry_paths_exist_and_are_absolute():
    preset_line, templates_line = _run("--paths").strip().splitlines()
    preset, templates = Path(preset_line), Path(templates_line)
    assert preset.is_absolute() and preset.is_file()
    assert templates.is_absolute() and templates.is_dir()
    # forward slashes so the paths work in Tailwind's CSS syntax on Windows
    assert "\\" not in preset_line
    assert "\\" not in templates_line


def test_entry_sources_mvp_templates():
    output = _run()
    templates_path = _run("--paths").strip().splitlines()[1]
    assert f'@source "{templates_path}";' in output


def test_packaged_preset_provides_drawer_variants_and_rail_css():
    preset = Path(_run("--paths").strip().splitlines()[0])
    css = preset.read_text(encoding="utf-8")
    assert "@custom-variant is-drawer-open" in css
    assert "@custom-variant is-drawer-close" in css
    assert '@source inline("{sm,md,lg,xl,2xl}:drawer-open");' in css
    assert ".mvp-sidebar--icons" in css
    assert ".mvp-rail-only" in css
