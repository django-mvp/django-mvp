# CI/CD Workflows

Continuous integration runs on GitHub Actions. Most of the work lives in reusable workflows
published by [`django-mvp/shared`](https://github.com/django-mvp/shared), which this repository
calls at a pinned release tag. That is why the status checks are named `call-tests / …` and
`call-build / …` — the prefix is the local job that calls the shared workflow.

## Workflow overview

| Workflow | File | Trigger |
|---|---|---|
| **Tests** | `tests.yml` | Every pull request, pushes to `main` touching the package, `workflow_dispatch` |
| **Build** | `build.yml` | Every pull request, pushes to `main` touching the package, `workflow_dispatch` |
| **Stylesheet** | `stylesheet.yml` | Pull requests touching templates, assets or the npm manifest |
| **Prepare Release** | `prepare-release.yml` | `workflow_dispatch` with a bump level |
| **Tag Release** | `tag-release.yml` | Push to `main` that changes `pyproject.toml` |
| **Publish** | `publish.yml` | A published release, a pushed `v*` tag, or `workflow_dispatch` |
| **Auto-merge Dependabot** | `auto-merge-dependabot.yml` | Dependabot pull requests |
| **Deploy Docs** | `docs.yml` | `workflow_dispatch` only *(docs not yet configured)* |

## Checks on a pull request

Tests and Build both run on every pull request, and between them produce the seven required
status checks:

- `call-build / Code Quality` — lockfile consistency and `pre-commit run --all-files`
- `call-build / Security Scan`
- `call-build / Build Package`
- `call-tests / Test Python 3.12, Django 5.2`
- `call-tests / Test Python 3.12, Django 6.0`
- `call-tests / Test Python 3.13, Django 5.2`
- `call-tests / Test Python 3.13, Django 6.0`

Neither workflow filters on paths for the `pull_request` event. A path-filtered check does not
report at all on a pull request that misses its paths, and a required check that never reports
blocks the merge permanently. The `push` triggers keep their path filters, where the same problem
does not arise.

Coverage is uploaded to Codecov from one matrix cell. The floors are project 90% and patch 85%,
set in `codecov.yml`.

### Stylesheet

`stylesheet.yml` builds the shipped stylesheet and fails if it stops compiling. It
does **not** compare the result against the committed CSS: the Tailwind and DaisyUI build is
non-deterministic, so consecutive builds with an identical pinned toolchain produce different
bytes. An earlier byte-comparison gate failed pull requests for drift no contributor could fix.

Because of that, keeping `mvp/static/css/django-mvp.css` current is an author responsibility.
Run `invoke build-stylesheet` and commit the output whenever templates change classes.

## Releasing

Releases run entirely through pull requests. Nothing pushes to `main` directly.

1. **Prepare** — run the *Prepare Release* workflow with a bump level (`patch`, `minor`, `major`,
   or an explicit version). It opens a pull request carrying the version bump in `pyproject.toml`
   and the new CHANGELOG section.
2. **Tag** — merging that pull request changes `pyproject.toml` on `main`, which triggers *Tag
   Release*. It creates the `vX.Y.Z` tag and the GitHub Release.
3. **Publish** — the release event triggers *Publish*, which builds the package and uploads it to
   PyPI through trusted publishing (no API token, `id-token: write` only).

Before starting, run `invoke prerelease` on a branch: it rebuilds the stylesheet, runs the
pre-commit hooks, checks the lockfile, and runs the suite. Commit the rebuilt CSS on that branch
so it lands before the release pull request.

A release created by *Tag Release* using the default `GITHUB_TOKEN` does not trigger *Publish*,
because GitHub suppresses workflow events raised by the default token. Set the `RELEASE_TOKEN`
secret to lift that, or run *Publish* manually.

## Design decisions

| Decision | Rationale |
|---|---|
| Shared workflows, pinned to a tag | One definition of the test and build pipeline across the family. Pinning to `@v0.2.0` rather than `@main` means an upstream change cannot alter this repository's CI without a deliberate bump. |
| No paths filter on `pull_request` | A path-filtered required check never reports on an out-of-scope pull request, which deadlocks the merge. |
| No auto-commit of pre-commit fixes | Auto-committing back means the release builds from different code than was tested. Fixes belong in the author's commits. |
| Stylesheet compiles, not byte-compares | The Tailwind build is non-deterministic, so a byte comparison fails for drift nobody can fix. |
| Dependabot rather than a scheduled update job | Dependabot groups updates, respects the lockfile, and opens one pull request per ecosystem. The previous weekly `poetry update` job did the same job less well. |
