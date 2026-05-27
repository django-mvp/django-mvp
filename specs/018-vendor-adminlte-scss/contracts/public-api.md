# Contract: SCSS Theming Surface

## Purpose

This feature exposes a filesystem and build-pipeline contract rather than a runtime API. Downstream apps customize the theme by overriding Sass variables and allowing the Django compressor pipeline to compile the result.

## Public Entry Points

- `mvp/static/_bootstrap_variables.scss`: override entrypoint 1 — Bootstrap design tokens and plain AdminLTE variables with literal values. Resolved via Sass include paths; shadow it by placing a same-named file in your app's static root and listing your app before `mvp` in INSTALLED_APPS.
- `mvp/static/_adminlte_variables.scss`: override entrypoint 2 — AdminLTE variables that reference Bootstrap tokens (e.g. `$lte-sidebar-color: $gray-800`). Injected into the vendored `adminlte.scss` by the refresh task. Shadow it the same way as above.
- `mvp/static/scss/mvp.scss`: main Sass entrypoint that composes the theme.
- `mvp/static/adminlte/scss/`: vendored AdminLTE source tree copied from npm.

## Load Order Contract

- `_bootstrap_variables.scss` must be imported before Bootstrap and all vendored AdminLTE defaults so Bootstrap design tokens and plain AdminLTE variable overrides take precedence.
- `_adminlte_variables.scss` is injected into the vendored `adminlte.scss` immediately before AdminLTE's own `_variables.scss` import, after Bootstrap variables are fully resolved, so it can safely reference Bootstrap tokens.
- Vendor defaults must be loaded with Sass `!default` behavior intact so downstream values override them.
- App-specific customizations must not require edits to vendored files.

## Refresh Contract

- Vendor refreshes must install the latest AdminLTE 4 package with npm (`admin-lte@^4`).
- The committed lockfile (`package-lock.json`) must pin the resolved package version for deterministic builds.
- Refreshes must replace the vendored SCSS directory in full before copying the new tree.
- Downstream override files (`_bootstrap_variables.scss` and `_adminlte_variables.scss`) must not be modified or deleted during a refresh.
- The refresh task must patch the vendored `adminlte.scss` to inject the `_adminlte_variables` import hook after each full directory copy.

## Build Contract

- SCSS compilation must flow through `django-compressor` and `django-libsass`.
- Compilation failures must be actionable and point to the source or override value that needs correction.
- The build output must remain compatible with the existing Django static asset pipeline.

## Diagnostic Output Contract

- When `invoke refresh-adminlte-scss` detects obvious issues in `_bootstrap_variables.scss` or `_adminlte_variables.scss`, it must:
  - Print the line number and variable name of each problematic declaration.
  - Explain that Sass error output will include the variable name to help locate the issue.
  - Describe how to find the expected value type in the vendored SCSS source tree.

## SC-003: Refresh Repeatability Sampling Protocol

**Goal**: Verify that running `invoke refresh-adminlte-scss` twice in a row with the same lockfile
produces an identical vendored SCSS tree and identical compiled CSS output.

**Sample collection steps**:

1. Commit a clean `package-lock.json` to the repository.
2. Run `invoke refresh-adminlte-scss` (run A). Record the AdminLTE version.
3. Run `invoke refresh-adminlte-scss` again (run B). Record the AdminLTE version.
4. Compare the vendored SCSS tree from run A and run B (should be byte-for-byte identical).
5. Compare compiled CSS from run A and run B (should be identical with no diff).

**Pass criteria**: Both runs produce the same vendored tree and compiled output.

**Sample results** (fill in when protocol is executed):

| Sample | Date | AdminLTE version | Tree diff | CSS diff | Result |
|--------|------|-----------------|-----------|----------|--------|
| Run A  |      |                 | N/A       | N/A      |        |
| Run B  |      | (same as A)     | none      | none     | PASS   |

## Minimal Usage Example

1. Set Bootstrap token overrides in `_bootstrap_variables.scss`.
2. Set AdminLTE variable overrides that reference Bootstrap tokens in `_adminlte_variables.scss`.
3. Run `invoke refresh-adminlte-scss` when updating AdminLTE.
4. Build the project so compressor and libsass generate the final CSS.
5. Verify the application renders the updated theme.
