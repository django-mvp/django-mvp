from pathlib import Path

from invoke import task

# ---------------------------------------------------------------------------
# Vendor path constants
# ---------------------------------------------------------------------------

# Root of the repository (same directory as this file).
REPO_ROOT = Path(__file__).resolve().parent


@task
def prerelease(c):
    """
    Run comprehensive pre-release checks and update all required files.

    This task performs all necessary steps to prepare the repository for release:
    1. Build, minify and brotli-compress the stylesheets (committed artifacts)
    2. Run linting, formatting, type checking, and dependency checks via pre-commit hooks
    3. Run quality checks and tests

    Run this on a branch before opening the release pull request, so the
    stylesheet lands in the same PR as the version bump.

    The stylesheet is a committed build artifact shipped in the wheel. Building
    it here keeps it in sync with the templates and lets the lint/test steps run
    against fresh output. This is the *only* place stylesheet drift is
    prevented: the Tailwind/daisyUI build is non-deterministic (identical
    toolchain, different bytes each run), so CI cannot byte-compare committed
    output against a fresh build — the Stylesheet workflow only checks that the
    CSS still compiles. Commit the rebuilt CSS on your branch.

    Pre-commit hooks include:
    - Code formatting (Ruff)
    - Type checking (mypy)
    - Dependency analysis (deptry)
    - Poetry validation
    """
    print("🚀 Starting comprehensive pre-release checks...")
    print("=" * 60)

    # Step 1: Build, minify and compress the stylesheets
    print("\n🎨 Step 1: Building, minifying and compressing stylesheets")
    build_stylesheet(c)

    # Step 2: Run comprehensive linting, type checking, and dependency analysis
    print("\n🧹 Step 2: Running comprehensive linting, type checking, and dependency analysis")
    print("🚀 Running pre-commit hooks (includes mypy and deptry)")
    c.run("poetry run pre-commit run -a")

    # Step 3: Check Poetry lock file consistency
    print("\n🔍 Step 3: Checking Poetry lock file consistency")
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    # Step 4: Run comprehensive test suite
    print("\n🧪 Step 4: Running comprehensive test suite")
    print("🚀 Running pytest with coverage")
    c.run("poetry run pytest --cov --cov-config=pyproject.toml --cov-report=html --cov-report=term --tb=no -qq")

    print("\n" + "=" * 60)
    print("✅ Pre-release checks completed successfully!")
    print("🎉 Repository is ready for release. Next steps:")
    print("   1. Commit the rebuilt stylesheet and open a pull request.")
    print("   2. Once it is merged, run the 'Prepare Release' workflow with the")
    print("      bump level — it opens the release PR (version + CHANGELOG).")
    print("   3. Merging that PR tags the release and publishes to PyPI.")


# The `release` task was removed when the repository adopted the shared release
# flow. Releases are now cut by the "Prepare Release" workflow (which opens a
# pull request carrying the version bump and CHANGELOG section), then tagged and
# published automatically when that pull request merges. The old task pushed the
# version commit and tag straight to main, which branch protection now forbids.


@task
def build_stylesheet(c):
    import brotli

    c.run("npm run build:css:prod")

    with open("mvp/static/css/django-mvp.css", "rb") as f:
        compressed = brotli.compress(f.read(), quality=11)

    with open("mvp/static/css/django-mvp.css.br", "wb") as f:
        f.write(compressed)
    print("Built and compressed stylesheet to django-mvp.css.br")

    # Demo site stylesheet: a superset scanning mvp + demo, used only by the
    # demo pages (not shipped in the wheel), so no brotli step is needed.
    c.run("npm run build:demo:prod")
    print("Built demo stylesheet to demo/static/css/demo.css")
