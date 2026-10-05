"""Tests for the mvp_tailwind management command and the packaged preset.

The command generates a Tailwind v4 entry file for consumer projects that
build their own CSS (Tier 2 in docs/styling.md).
"""

from io import StringIO
from pathlib import Path

import daisy_cotton
from django.core.management import call_command


def _run(*args):
    out = StringIO()
    call_command("mvp_tailwind", *args, stdout=out)
    return out.getvalue()


class TestMVPTailwindCommand:
    def test_entry_contains_daisyui_and_preset_import(self):
        output = _run()
        assert '@import "tailwindcss" source(none);' in output
        assert '@plugin "daisyui" {\n  themes: all;\n}' in output, (
            "the generated entry must enable every prebuilt theme, or a Tier 2 "
            "project (one that builds its own CSS) ships fewer themes than a "
            "Tier 1 project that uses the package's own prebuilt stylesheet "
            "(FR-011, FR-013)"
        )
        assert "mvp/tailwind/base.css" in output
        assert '@source "./templates";' in output

    def test_entry_paths_exist_and_are_absolute(self):
        lines = _run("--paths").strip().splitlines()
        preset_line, templates_line, forms_line = lines[:3]
        preset, templates = Path(preset_line), Path(templates_line)
        forms = Path(forms_line)
        assert preset.is_absolute() and preset.is_file()
        assert templates.is_absolute() and templates.is_dir()
        assert forms.is_absolute() and forms.is_dir()
        # forward slashes so the paths work in Tailwind's CSS syntax on Windows
        assert all("\\" not in line for line in lines)

    def test_entry_sources_mvp_templates(self):
        output = _run()
        templates_path = _run("--paths").strip().splitlines()[1]
        assert f'@source "{templates_path}";' in output

    def test_entry_sources_the_form_template_pack(self):
        # Forms are drawn by django-mvp-forms, whose classes are written in
        # its templates and its template tags, so the whole package is scanned.
        import mvp_forms

        output = _run()
        forms_path = Path(mvp_forms.__file__).resolve().parent.as_posix()
        assert f'@source "{forms_path}";' in output

    def test_paths_prints_daisy_cotton_templates_directory_last(self):
        lines = _run("--paths").strip().splitlines()
        assert len(lines) == 4
        daisy = Path(lines[3])
        assert daisy.is_absolute() and daisy.is_dir()
        assert "\\" not in lines[3]
        assert daisy == Path(daisy_cotton.__file__).resolve().parent / "templates"

    def test_entry_sources_daisy_cotton_templates_after_the_form_pack(self):
        output = _run()
        lines = _run("--paths").strip().splitlines()
        forms_source = f'@source "{lines[2]}";'
        daisy_source = f'@source "{lines[3]}";'
        assert daisy_source in output
        assert output.index(daisy_source) > output.index(forms_source)

    def test_packaged_preset_provides_drawer_variants_and_rail_css(self):
        preset = Path(_run("--paths").strip().splitlines()[0])
        css = preset.read_text(encoding="utf-8")
        assert "@custom-variant is-drawer-open" in css
        assert "@custom-variant is-drawer-close" in css
        assert '@source inline("{sm,md,lg,xl,2xl}:drawer-open");' in css
        assert ".mvp-sidebar--icons" in css
        assert ".mvp-rail-only" in css
