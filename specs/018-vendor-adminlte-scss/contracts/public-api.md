# Contract: SCSS Theming Surface

## Purpose

This feature exposes a filesystem and build-pipeline contract rather than a runtime API. Downstream apps customize the theme by overriding Sass variables and allowing the Django compressor pipeline to compile the result.

## Public Entry Points

- `mvp/static/scss/_mvp_variables.scss`: app-owned override file.
- `mvp/static/scss/mvp.scss`: main Sass entrypoint that composes the theme.
- `mvp/static/adminlte/scss/`: vendored AdminLTE source tree copied from npm.

## Load Order Contract

- `_mvp_variables.scss` must be imported before the vendored AdminLTE defaults.
- Vendor defaults must be loaded with Sass `!default` behavior intact so downstream values can override them.
- App-specific customizations must not require edits to vendored files.

## Refresh Contract

- Vendor refreshes must install the latest AdminLTE 4 package with npm.
- The committed lockfile must pin the resolved package version for deterministic builds.
- Refreshes must replace the vendored SCSS directory in full before copying the new tree.

## Build Contract

- SCSS compilation must flow through `django-compressor` and `django-libsass`.
- Compilation failures must be actionable and point to the source or override value that needs correction.
- The build output must remain compatible with the existing Django static asset pipeline.

## Minimal Usage Example

1. Set theme variables in `_mvp_variables.scss`.
2. Run the vendor refresh task when updating AdminLTE.
3. Build the project so compressor and libsass generate the final CSS.
4. Verify the application renders the updated theme.
