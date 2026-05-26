# Research: Vendored Theme Variable Overrides

## Decision 1: Keep the existing Sass pipeline and add a vendor refresh source tree under `mvp/static/`

- **Decision**: Store refreshed AdminLTE SCSS sources in a dedicated vendored subtree under `mvp/static/adminlte/scss/`, while app-owned override entrypoints remain in `mvp/static/scss/`.
- **Rationale**: The repository already keeps custom Sass entrypoints in `mvp/static/scss/` and already vendors compiled AdminLTE CSS/JS under `mvp/static/css/` and `mvp/static/js/`. A separate vendored source subtree makes the refresh boundary obvious and supports full directory replacement.
- **Alternatives considered**:
  - Merge vendor sources directly into `mvp/static/scss/`: rejected because it blurs ownership between upstream files and app-specific overrides.
  - Store vendor sources outside `mvp/static/`: rejected because the spec requires the canonical vendored source location to live in `mvp/static`.

## Decision 2: Compile SCSS through `django-compressor` and `django-libsass`

- **Decision**: Use the existing compressor pipeline with `COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)`.
- **Rationale**: The test settings already show compressor and django-libsass configured, which makes this the lowest-risk path and avoids introducing a second build system. It also keeps the SCSS compilation behavior aligned with the current project settings and test environment.
- **Alternatives considered**:
  - Standalone CLI compilation scripts: rejected because they duplicate behavior already provided by the Django pipeline.
  - A Node-only Sass pipeline: rejected because the project already has the Python-side compressor integration in place.

## Decision 3: Apply app overrides before vendor defaults in the Sass import order

- **Decision**: Import `_mvp_variables.scss` ahead of the vendored AdminLTE defaults so downstream values can override `!default` declarations.
- **Rationale**: This matches standard Sass override semantics and gives downstream apps a single, predictable customization point.
- **Alternatives considered**:
  - Import overrides after vendor defaults: rejected because `!default` values would already be fixed in many cases.
  - Allow mixed ordering: rejected because it makes the theming contract ambiguous for downstream teams.

## Decision 4: Refresh vendor sources via npm latest plus lockfile pinning

- **Decision**: The refresh step installs the latest AdminLTE 4 package with npm, then relies on the committed lockfile to pin the resolved version for reproducible builds.
- **Rationale**: This satisfies the request for easy upstream updates while preserving deterministic installs in CI and local development.
- **Alternatives considered**:
  - Hard-pin the package version in the refresh task: rejected because it would make routine vendor updates more manual.
  - Rely on a floating install with no lockfile pinning: rejected because it makes refreshes nondeterministic.

## Decision 5: Replace the vendored SCSS directory on refresh

- **Decision**: Delete the current vendored SCSS tree before copying the refreshed AdminLTE source tree.
- **Rationale**: Full replacement prevents stale upstream files from lingering when AdminLTE adds, renames, or removes SCSS files.
- **Alternatives considered**:
  - In-place copy/merge: rejected because stale files can survive unnoticed.
  - Partial subtree updates: rejected because the feature specifically calls for vendoring the source tree as a repeatable refresh unit.
