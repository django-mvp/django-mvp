"""
Asset pipeline contract tests — vendored AdminLTE SCSS and build-pipeline verification.

Tests in this module verify:
- The vendored SCSS directory exists and is structurally correct.
- The SCSS import load order enforces app-override-before-vendor-defaults semantics.
- The django-compressor / django-libsass compiler is configured correctly.
- The vendor-refresh task removes stale files and produces a clean replacement.
- Lockfile pinning is in effect after a refresh.
"""

import re
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Paths under test
# ---------------------------------------------------------------------------
ADMINLTE_VENDOR_SCSS_DIR = BASE_DIR / "mvp" / "static" / "adminlte" / "scss"
APP_SCSS_DIR = BASE_DIR / "mvp" / "static" / "scss"
MVp_SCSS = APP_SCSS_DIR / "mvp.scss"
MVP_VARIABLES_SCSS = BASE_DIR / "mvp" / "static" / "_bootstrap_variables.scss"

# ---------------------------------------------------------------------------
# Phase 2: Foundational — compiler configuration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_compress_precompilers_includes_libsass(settings):
    """COMPRESS_PRECOMPILERS routes text/x-scss through django_libsass.SassCompiler."""
    precompilers = dict(settings.COMPRESS_PRECOMPILERS)
    assert "text/x-scss" in precompilers, (
        "COMPRESS_PRECOMPILERS must contain a 'text/x-scss' entry so that "
        "django-compressor routes SCSS files to django-libsass."
    )
    assert "django_libsass" in precompilers["text/x-scss"], "The SCSS precompiler must use django_libsass.SassCompiler."


@pytest.mark.django_db
def test_compressor_in_installed_apps(settings):
    """'compressor' is listed in INSTALLED_APPS."""
    assert "compressor" in settings.INSTALLED_APPS


def test_adminlte_vendor_scss_dir_exists():
    """Vendored SCSS destination directory exists (may be empty before first refresh)."""
    assert ADMINLTE_VENDOR_SCSS_DIR.exists(), (
        f"Expected vendored SCSS directory at {ADMINLTE_VENDOR_SCSS_DIR}. "
        "Create it with a .gitkeep to track the directory in version control."
    )


def test_mvp_scss_entrypoint_exists():
    """Main SCSS entrypoint file is present."""
    assert MVp_SCSS.exists(), f"Expected mvp.scss at {MVp_SCSS}"


def test_mvp_scss_contains_include_path_contract_comment():
    """mvp.scss documents the Sass include path contract in a comment block."""
    content = MVp_SCSS.read_text(encoding="utf-8")
    assert "mvp/static/adminlte/scss/" in content, (
        "mvp.scss must document the vendored AdminLTE include path "
        "so developers know where vendored sources are resolved from."
    )
    assert "_bootstrap_variables.scss" in content, (
        "mvp.scss must reference the override entrypoint file name in its include-path contract comment."
    )


# ---------------------------------------------------------------------------
# Phase 3 [US1]: Sass load-order unit assertions (T011, T012)
# ---------------------------------------------------------------------------


def test_mvp_variables_scss_exists():
    """App override entrypoint _bootstrap_variables.scss is present."""
    assert MVP_VARIABLES_SCSS.exists(), (
        f"Expected _bootstrap_variables.scss at {MVP_VARIABLES_SCSS}. Create this file as the downstream override entrypoint."
    )


def test_mvp_scss_imports_variables_before_vendor_defaults():
    """_mvp_variables is imported before any vendor AdminLTE import in mvp.scss.

    This enforces the load-order contract: app overrides must be loaded before
    vendor !default declarations so that downstream values win.
    """
    content = MVp_SCSS.read_text(encoding="utf-8")

    # Find the line index of the _mvp_variables import.
    lines = content.splitlines()
    variables_import_line = None
    adminlte_import_line = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if variables_import_line is None and re.search(r'@import\s+["\']bootstrap_variables["\']', stripped):
            variables_import_line = i
        # Look for an uncommented AdminLTE vendor import (e.g. adminlte/scss/adminlte).
        if (
            adminlte_import_line is None
            and re.search(r'@import\s+["\'][^"\']*adminlte[^"\']*["\']', stripped)
            and not stripped.startswith("//")
        ):
            adminlte_import_line = i

    assert variables_import_line is not None, (
        "mvp.scss must contain '@import \"bootstrap_variables\"' (the override entrypoint)."
    )

    # If there are active (uncommented) vendor imports, verify load order.
    if adminlte_import_line is not None:
        assert variables_import_line < adminlte_import_line, (
            f"_bootstrap_variables must be imported (line {variables_import_line + 1}) "
            f"BEFORE any AdminLTE vendor import (line {adminlte_import_line + 1}). "
            "Move the @import 'bootstrap_variables' line to appear first."
        )


def test_mvp_variables_file_documents_default_fallback_behavior():
    """_mvp_variables.scss contains guidance explaining the !default override mechanism."""
    content = MVP_VARIABLES_SCSS.read_text(encoding="utf-8")
    assert "!default" in content, (
        "_mvp_variables.scss must document the Sass !default override mechanism "
        "so downstream developers understand how variable overrides work."
    )


def test_mvp_variables_file_contains_usage_examples():
    """_mvp_variables.scss contains at least one commented usage example."""
    content = MVP_VARIABLES_SCSS.read_text(encoding="utf-8")
    # At least one Sass variable example (commented or active) like $primary or $sidebar-bg.
    assert re.search(r"\$[a-z][a-z0-9-]+\s*:", content), (
        "_mvp_variables.scss should contain at least one variable example "
        "(e.g. $primary: #2c5f2e;) so developers can quickly understand the pattern."
    )


# ---------------------------------------------------------------------------
# Phase 3 [US1]: Diagnostic error output contract (T043)
# ---------------------------------------------------------------------------


def test_mvp_variables_troubleshooting_section_present():
    """_mvp_variables.scss includes a TROUBLESHOOTING section that names variables.

    When SCSS compilation fails due to an invalid override value, the error from
    the Sass compiler will include the variable name.  This test verifies that
    the override file itself also documents how to read and act on that error,
    so developers know where to look when compilation breaks.
    """
    content = MVP_VARIABLES_SCSS.read_text(encoding="utf-8")
    assert "TROUBLESHOOTING" in content, (
        "_mvp_variables.scss must contain a TROUBLESHOOTING section so that "
        "developers encountering compilation errors know how to diagnose them."
    )
    # The troubleshooting section should mention that error output includes the variable name.
    assert "variable" in content.lower(), (
        "The TROUBLESHOOTING section should mention 'variable' so developers "
        "understand that Sass error output will name the problematic variable."
    )


# ---------------------------------------------------------------------------
# Phase 4 [US2]: Invoke refresh command behavior tests (T020, T021, T022)
# ---------------------------------------------------------------------------


def test_tasks_py_defines_refresh_adminlte_scss_task():
    """tasks.py exposes a refresh_adminlte_scss Invoke task."""
    tasks_py = BASE_DIR / "tasks.py"
    assert tasks_py.exists(), "tasks.py not found at repo root."
    content = tasks_py.read_text(encoding="utf-8")
    assert "def refresh_adminlte_scss" in content, "tasks.py must define a 'refresh_adminlte_scss' Invoke task."


def test_tasks_py_vendor_refresh_deletes_old_tree(tmp_path):
    """_copy_vendor_scss performs a full directory replacement.

    This regression test verifies that the helper function deletes the existing
    destination tree before copying the new sources, so stale upstream files
    cannot linger after a refresh.
    """
    import sys

    sys.path.insert(0, str(BASE_DIR))
    from tasks import _copy_vendor_scss

    # Create a source tree with one file.
    src = tmp_path / "src_scss"
    src.mkdir()
    (src / "new_file.scss").write_text("// new")

    # Create a destination tree with a STALE file not present in the source.
    dst = tmp_path / "dst_scss"
    dst.mkdir()
    stale_file = dst / "stale_old_file.scss"
    stale_file.write_text("// stale")

    _copy_vendor_scss(src, dst)

    # Stale file must be gone.
    assert not stale_file.exists(), (
        "_copy_vendor_scss must remove the old destination tree before copying, "
        "so stale files from previous vendor versions do not persist."
    )
    # New file must be present.
    assert (dst / "new_file.scss").exists(), "_copy_vendor_scss must copy all source files to the destination."


def test_tasks_py_vendor_refresh_uses_lockfile_for_pinning():
    """tasks.py documents that the lockfile pins the resolved AdminLTE version.

    The task implementation must reference package-lock.json (or lockfile) to
    explain deterministic version pinning to maintainers.
    """
    tasks_py = BASE_DIR / "tasks.py"
    content = tasks_py.read_text(encoding="utf-8")
    assert "package-lock.json" in content or "lockfile" in content.lower(), (
        "tasks.py must reference the package-lock.json or describe lockfile-based "
        "pinning so maintainers understand how the resolved version is reproduced."
    )


def test_tasks_py_refresh_task_documents_repeatability():
    """refresh_adminlte_scss docstring explains that the lockfile provides determinism."""
    tasks_py = BASE_DIR / "tasks.py"
    content = tasks_py.read_text(encoding="utf-8")
    assert "deterministic" in content or "reproducible" in content, (
        "The refresh task docstring must mention deterministic/reproducible installs "
        "so maintainers know the intent of committing the lockfile."
    )
