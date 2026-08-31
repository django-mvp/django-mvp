# AGENTS.md — Agent Configuration for django-mvp

<!-- Thin index only. Details live in the pointed-to files. -->

django-mvp is a package that gets a Django project to a working product quickly: a
settings-configurable application shell, a library of override-able Cotton components, and
enhanced class-based views with search, ordering and pagination. Components are the public
API and template overrides are the primary extension point — see `CONTEXT.md` for the
vocabulary this repository uses.

## Stack & commands

- **Stack:** Python 3.12+ / Django 5.2+, Poetry-managed. Tailwind CSS v4 + DaisyUI 5 for the
  shipped stylesheet (Node, via npm).
- **Install:** `poetry install --with dev,test`
- **Test:** `poetry run pytest`
- **Lint:** `poetry run ruff check .` and `poetry run ruff format --check .`
- **Type-check:** `poetry run mypy mvp`
- **Dependencies:** `poetry run deptry .`
- **Build:** `poetry build`
- **Stylesheet:** `invoke build-stylesheet` (needs Node; the built CSS is a committed artifact)
- **Everything before a release pull request:** `invoke prerelease`

## Agent skills

### Issue tracker

GitHub issues via `gh` CLI; external PRs are a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

All five canonical labels use their default names. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout with `CONTEXT.md` at root and `docs/adr/` for ADRs. See `docs/agents/domain.md`.

### CI checks

Required status checks on the default branch (exact names):

- `call-build / Code Quality`
- `call-build / Security Scan`
- `call-build / Build Package`
- `call-tests / Test Python 3.12, Django 5.2`
- `call-tests / Test Python 3.12, Django 6.0`
- `call-tests / Test Python 3.13, Django 5.2`
- `call-tests / Test Python 3.13, Django 6.0`

Both workflows call reusable workflows from `django-mvp/shared`, pinned to a release tag, which
is why the check names carry the `call-build` / `call-tests` prefix. Neither has a paths filter
on `pull_request`: a path-filtered check never reports on an out-of-scope pull request, and a
required check that never reports blocks the merge.

`Stylesheet` is a repo-native check that proves the CSS still compiles. It is deliberately not
required, because the Tailwind build is non-deterministic and cannot be byte-compared.

## Releases

Releases go through the shared flow, not a local task:

1. Run `invoke prerelease` on a branch, commit the rebuilt stylesheet, and merge that pull request.
2. Run the **Prepare Release** workflow with a bump level. It opens a pull request carrying the
   version bump and the CHANGELOG section.
3. Merging that pull request tags the release and publishes to PyPI.

Nothing pushes to the default branch outside a pull request.

## Development workflow

Feature work follows a spec-driven process: spec → plan → tasks → implement → review → PR, with
`specs/NNN-slug/` directories generated per feature (there is no Spec Kit install in the repo).
Project standards and the quality bar live in `CONSTITUTION.md`.
