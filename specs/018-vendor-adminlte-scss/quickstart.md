# Quickstart: Vendored Theme Variable Overrides

## Prerequisites

- Python dependencies installed for the Django project.
- npm available for refreshing the vendored AdminLTE source package.
- The repository lockfile committed so the resolved AdminLTE version remains reproducible.

## Refresh the Vendored SCSS Tree

1. Run the repository's Invoke task for the vendor refresh once it has been added to `tasks.py`.
2. The task should install the latest AdminLTE 4 package with npm.
3. The task should delete the existing vendored SCSS tree under `mvp/static/`.
4. The task should copy the refreshed AdminLTE SCSS sources into `mvp/static/adminlte/scss/`.
5. The task should leave the lockfile as the version pinning mechanism for the resolved package version.

## Customize Theme Variables

1. Edit `mvp/static/scss/_mvp_variables.scss`.
2. Define the app-specific Sass values that should override the AdminLTE defaults.
3. Keep all downstream branding changes in this file rather than editing vendored source files.

## Build and Verify

1. Run the Django system check.
2. Run the Sass compilation path through the existing Django compressor pipeline.
3. Verify the rendered UI in a browser so the compiled theme changes are visible on the page.
4. Run the relevant pytest coverage for the touched settings, asset pipeline, and UI behavior.

## Expected Outcome

- Vendored AdminLTE SCSS sources are updated in a repeatable way.
- App overrides remain isolated in `_mvp_variables.scss`.
- SCSS compilation uses django-compressor and django-libsass.
- A clean rebuild produces the expected app-specific theme without stale vendor files.
