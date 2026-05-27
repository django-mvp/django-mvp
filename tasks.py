import shutil
from pathlib import Path

from invoke import task

# ---------------------------------------------------------------------------
# Vendor path constants
# ---------------------------------------------------------------------------

# Root of the repository (same directory as this file).
REPO_ROOT = Path(__file__).resolve().parent

# Destination for vendored AdminLTE SCSS sources inside the app static tree.
ADMINLTE_VENDOR_SCSS_DST = REPO_ROOT / "mvp" / "static" / "adminlte" / "scss"

# npm package specifier for AdminLTE 4.
ADMINLTE_NPM_PACKAGE = "admin-lte@^4"

# npm package source path (relative to node_modules) containing the SCSS tree.
ADMINLTE_NPM_SCSS_SRC = REPO_ROOT / "node_modules" / "admin-lte" / "src" / "scss"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _require_npm(c):
    """Raise RuntimeError if npm is not available on PATH."""
    result = c.run("npm --version", hide=True, warn=True)
    if result.failed:
        raise RuntimeError(
            "npm is not available. Install Node.js to use the vendor-refresh task."
        )
    return result.stdout.strip()


def _copy_vendor_scss(src: Path, dst: Path) -> None:
    """
    Replace the vendored SCSS tree at *dst* with a fresh copy from *src*.

    This performs a full directory replacement so stale upstream files cannot
    linger when AdminLTE adds, renames, or removes SCSS partials.
    """
    if not src.is_dir():
        raise FileNotFoundError(
            f"AdminLTE SCSS source not found at {src}. Ensure the npm install step completed successfully."
        )
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _patch_adminlte_scss(dst: Path) -> None:
    """
    Inject the ``adminlte_variables`` override hook into the vendored adminlte.scss.

    AdminLTE variables that reference Bootstrap tokens (e.g. ``$lte-sidebar-color:
    $gray-800 !default``) can only be overridden *after* Bootstrap's own variables
    have been imported.  The vendored ``adminlte.scss`` imports Bootstrap first and
    then its own ``_variables.scss``.  This function inserts a single import line
    immediately before that AdminLTE variables import so that users can provide
    overrides that reference Bootstrap variables.

    The injected import is resolved via include paths (not relative), so:
      - The default fallback lives at ``mvp/static/_adminlte_variables.scss``.
      - A user app can override it by placing ``_adminlte_variables.scss`` in its
        own static root and listing that app before ``mvp`` in INSTALLED_APPS.
    """
    adminlte_scss = dst / "adminlte.scss"
    if not adminlte_scss.exists():
        raise FileNotFoundError(f"adminlte.scss not found at {adminlte_scss}.")

    content = adminlte_scss.read_text(encoding="utf-8")
    hook_line = '@import "adminlte_variables"; // user AdminLTE variable overrides\n'
    marker = '@import "variables";'

    if hook_line.strip() in content:
        print("  Hook line already present in adminlte.scss — skipping patch.")
        return

    if marker not in content:
        raise RuntimeError(
            f"Could not find '{marker}' in adminlte.scss. "
            "The AdminLTE package layout may have changed — update the patch target."
        )

    patched = content.replace(marker, hook_line + marker, 1)
    adminlte_scss.write_text(patched, encoding="utf-8")
    print(
        "  Patched adminlte.scss: inserted adminlte_variables hook before AdminLTE variables."
    )


@task
def refresh_adminlte_scss(c):
    """
    Refresh the vendored AdminLTE 4 SCSS source tree.

    Steps:
    1. Verify npm is available.
    2. Install the latest AdminLTE 4 package with npm (lockfile pins the version).
    3. Delete the existing vendored SCSS tree under mvp/static/adminlte/scss/.
    4. Copy the refreshed SCSS sources from node_modules into the vendor tree.

    The committed package-lock.json pins the resolved AdminLTE version so
    subsequent `npm install` calls reproduce the same tree deterministically.

    Usage::

        invoke refresh-adminlte-scss
    """
    npm_version = _require_npm(c)
    print(f"npm {npm_version} detected.")

    print(f"Installing {ADMINLTE_NPM_PACKAGE} …")
    result = c.run(f"npm install {ADMINLTE_NPM_PACKAGE}", warn=True)
    if result.failed:
        raise RuntimeError(
            f"npm install failed for {ADMINLTE_NPM_PACKAGE}. Check your network connection and npm registry settings."
        )

    if not ADMINLTE_NPM_SCSS_SRC.is_dir():
        raise FileNotFoundError(
            f"Expected AdminLTE SCSS source at {ADMINLTE_NPM_SCSS_SRC} after install, "
            "but the directory was not found. The package layout may have changed."
        )

    print(f"Copying SCSS sources → {ADMINLTE_VENDOR_SCSS_DST} …")
    _copy_vendor_scss(ADMINLTE_NPM_SCSS_SRC, ADMINLTE_VENDOR_SCSS_DST)

    print("Patching adminlte.scss: inserting adminlte_variables hook …")
    _patch_adminlte_scss(ADMINLTE_VENDOR_SCSS_DST)

    pkg_lock = REPO_ROOT / "package-lock.json"
    if pkg_lock.exists():
        print(f"Lockfile present at {pkg_lock} — resolved version is pinned.")
    else:
        print(
            "⚠  No package-lock.json found. Commit the lockfile after this run to ensure reproducible vendor refreshes."
        )

    print("✅ AdminLTE SCSS vendor tree refreshed successfully.")
    print(
        "   Next: run the Django compressor pipeline to rebuild compiled CSS.\n"
        "   Hint: poetry run python manage.py compress"
    )


@task
def prerelease(c):
    """
    Run comprehensive pre-release checks and update all required files.

    This task performs all necessary steps to prepare the repository for release:
    1. Run linting, formatting, type checking, and dependency checks via pre-commit hooks
    2. Run quality checks and tests

    Use this before running the release task to ensure everything is ready.

    Pre-commit hooks include:
    - Code formatting (Ruff)
    - Type checking (mypy)
    - Dependency analysis (deptry)
    - Poetry validation
    """
    print("🚀 Starting comprehensive pre-release checks...")
    print("=" * 60)

    # Step 1: Run comprehensive linting, type checking, and dependency analysis
    print(
        "\n🧹 Step 1: Running comprehensive linting, type checking, and dependency analysis"
    )
    print("🚀 Running pre-commit hooks (includes mypy and deptry)")
    c.run("poetry run pre-commit run -a")

    # Step 2: Check Poetry lock file consistency
    print("\n🔍 Step 2: Checking Poetry lock file consistency")
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    # Step 3: Run comprehensive test suite
    print("\n🧪 Step 3: Running comprehensive test suite")
    print("🚀 Running pytest with coverage")
    c.run(
        "poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html --cov-report=term --tb=no -qq"
    )

    print("\n" + "=" * 60)
    print("✅ Pre-release checks completed successfully!")
    print(
        "🎉 Repository is ready for release. You can now run 'invoke release' with the appropriate rule."
    )
    print("   Example: invoke release --rule=patch")


@task
def release(c, rule="", retry=False):
    """
    Create a new git tag and push it to trigger a PyPI release.

    Pushing a version tag triggers the Release workflow, which builds and
    publishes the package to PyPI and creates a GitHub Release.

    Args:
        rule: Version bump rule (major, minor, patch, premajor, preminor, prepatch, prerelease)
        retry: If True, delete local/remote tag and re-push at HEAD (use after
               fixing a failed CI run — no version bump, no new commit)

    RULE        BEFORE  AFTER
    major       1.3.0   2.0.0
    minor       2.1.4   2.2.0
    patch       4.1.1   4.1.2
    premajor    1.0.2   2.0.0a0
    preminor    1.0.2   1.1.0a0
    prepatch    1.0.2   1.0.3a0
    prerelease  1.0.2   1.0.3a0

    Examples:
        invoke release --rule=patch    # bump patch version and release
        invoke release --retry         # re-push existing tag after fixing CI
    """
    if retry:
        version_short = c.run("poetry version -s", hide=True).stdout.strip()
        version = c.run("poetry version", hide=True).stdout.strip()
        tag = f"v{version_short}"
        print(f"♻️  Retrying release for {tag}...")
        response = (
            input(
                f"This will delete local and remote tag {tag} and re-push it at HEAD. Continue? (y/N): "
            )
            .strip()
            .lower()
        )
        if response not in ("y", "yes"):
            print("❌ Retry cancelled.")
            return
        c.run(f"git tag -d {tag}", warn=True)
        c.run(f"git push origin :refs/tags/{tag}", warn=True)
        c.run(f'git tag -a {tag} -m "{version}"')
        c.run("git push origin main --follow-tags")
        print(f"✅ Tag {tag} re-pushed — Release workflow retriggered!")
        return

    if not rule:
        print("❌ Error: You must specify a version bump rule (or use --retry).")
        print("   Example: invoke release --rule=patch")
        print(
            "\n   Available rules: major, minor, patch, premajor, preminor, prepatch, prerelease"
        )
        return

    # Check for unstaged changes
    unstaged_result = c.run("git diff --name-only", hide=True, warn=True)
    if unstaged_result.stdout.strip():
        print("⚠️  WARNING: You have unstaged changes:")
        print(unstaged_result.stdout)
        response = input("Continue with release? (y/N): ").strip().lower()
        if response not in ("y", "yes"):
            print("❌ Release cancelled.")
            return

    # Bump the current version using the specified rule
    c.run(f"poetry version {rule}")
    version_short = c.run("poetry version -s", hide=True).stdout.strip()
    version = c.run("poetry version", hide=True).stdout.strip()

    # Commit the version bump and any staged changes
    staged_result = c.run("git diff --cached --name-only", hide=True, warn=True)
    if staged_result.stdout.strip():
        print(f"🚀 Committing staged changes and version bump for v{version_short}")
        c.run(f'git add pyproject.toml && git commit -m "Release v{version_short}"')
    else:
        print(f"🚀 Committing version bump for v{version_short}")
        c.run(f'git commit pyproject.toml -m "Release v{version_short}"')

    # Create an annotated tag and push commit + tag together
    c.run(f'git tag -a v{version_short} -m "{version}"')
    print(f"📤 Pushing v{version_short} to remote repository...")
    c.run("git push origin main --follow-tags")

    print(f"✅ Release v{version_short} created and pushed successfully!")
    print("🎉 GitHub Actions will now build and publish the package to PyPI.")
