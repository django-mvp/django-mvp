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

    Use this before running the release task to ensure everything is ready.

    The stylesheet is a committed build artifact shipped in the wheel; building
    it here (before the release tag is cut) keeps it in sync with the templates
    and lets the lint/test steps run against fresh output. This is the *only*
    place stylesheet drift is prevented: the Tailwind/daisyUI build is
    non-deterministic (identical toolchain, different bytes each run), so CI
    cannot byte-compare committed output against a fresh build — the Stylesheet
    workflow only checks that the CSS still compiles. Remember to commit the
    rebuilt CSS before 'invoke release'.

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
    print(
        "\n🧹 Step 2: Running comprehensive linting, type checking, and dependency analysis"
    )
    print("🚀 Running pre-commit hooks (includes mypy and deptry)")
    c.run("poetry run pre-commit run -a")

    # Step 3: Check Poetry lock file consistency
    print("\n🔍 Step 3: Checking Poetry lock file consistency")
    print("🚀 Checking Poetry lock file consistency with 'pyproject.toml'")
    c.run("poetry check --lock")

    # Step 4: Run comprehensive test suite
    print("\n🧪 Step 4: Running comprehensive test suite")
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
    # Releases publish to PyPI and push to main, so they must run from main.
    # Running from a dev/feature branch is almost always an accident (it tags the
    # wrong ref and can push unintended commits), so no-op instead. Covers both
    # the --rule and --retry paths.
    current_branch = c.run("git rev-parse --abbrev-ref HEAD", hide=True).stdout.strip()
    if current_branch != "main":
        print(
            f"❌ 'invoke release' must run on 'main', but you are on '{current_branch}'."
        )
        print("   Run 'git checkout main && git pull' first. No changes made.")
        return

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
