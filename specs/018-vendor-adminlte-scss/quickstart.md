# Quickstart: Vendored Theme Variable Overrides

## Prerequisites

- Python dependencies installed for the Django project.
- npm available for refreshing the vendored AdminLTE source package.
- The repository lockfile committed so the resolved AdminLTE version remains reproducible.

## Refresh the Vendored SCSS Tree

Run the Invoke vendor-refresh task:

```bash
invoke refresh-adminlte-scss
```

This task will:

1. Verify that npm is available on PATH.
2. Install the latest AdminLTE 4 package with npm (`admin-lte@^4`).
3. Delete the existing vendored SCSS tree under `mvp/static/adminlte/scss/` in full.
4. Copy the refreshed AdminLTE SCSS sources into `mvp/static/adminlte/scss/`.
5. Patch the vendored `adminlte.scss` to inject the `_adminlte_variables` override hook.
6. Leave the `package-lock.json` as the version pinning mechanism for the resolved package version.

> **Lockfile pinning**: Commit `package-lock.json` after the first refresh. Future `npm install`
> calls will reproduce the exact resolved AdminLTE version on any machine or CI runner.

## Customize Theme Variables

There are two override entrypoints. Use whichever fits the variable you need to change:

### Override entrypoint 1: `mvp/static/_bootstrap_variables.scss`

Use this file for Bootstrap design tokens (`$primary`, `$gray-800`, etc.) and AdminLTE variables
that take plain literal values.

1. Edit `mvp/static/_bootstrap_variables.scss`.
2. Define your Sass variable overrides — for example:

   ```scss
   $primary:   #2c5f2e;
   $secondary: #606c38;
   ```

3. Keep all Bootstrap token changes in this file.

> **Why it works**: `_bootstrap_variables.scss` is imported _before_ Bootstrap and vendored
> AdminLTE defaults in `mvp.scss`. Sass `!default` only assigns a value when the variable is
> undefined, so any variable you define here wins.

### Override entrypoint 2: `mvp/static/_adminlte_variables.scss`

Use this file for AdminLTE variables that reference Bootstrap tokens, for example:

```scss
$lte-sidebar-color: $primary;   // references $primary defined in entrypoint 1
$lte-sidebar-width: 280px;
```

> **Why a second file**: AdminLTE variables that reference Bootstrap tokens (e.g. `$gray-800`)
> can only be overridden _after_ Bootstrap variables are resolved. The refresh task patches
> `adminlte.scss` to import `_adminlte_variables` at exactly that point.

### App-level overrides (INSTALLED_APPS)

To provide app-specific overrides without editing the `mvp` app files:

1. Create `<your-app>/static/_bootstrap_variables.scss` and/or `_adminlte_variables.scss`.
2. List your app **before** `mvp` in `INSTALLED_APPS`.

Django collects static files in INSTALLED_APPS order, so django-libsass will find your
app's override file first via its include paths.

Do **not** edit files under `mvp/static/adminlte/scss/` — they will be replaced on the next
vendor refresh.

## Build and Verify

1. Run the Django system check:

   ```bash
   poetry run python manage.py check --settings=tests.settings
   ```

2. Trigger Sass compilation via the Django compressor pipeline:

   ```bash
   poetry run python manage.py compress
   ```

3. Open the application in a browser and verify the compiled theme changes are visible.

4. Run the relevant pytest coverage:

   ```bash
   poetry run pytest tests/test_static_assets.py tests/test_ui_theme.py -q
   ```

## Troubleshooting Invalid Variable Overrides

If the Sass compiler fails with an error after editing `_bootstrap_variables.scss` or `_adminlte_variables.scss`:

1. **Read the error message** — it will include the problematic variable name, for example:

   ```
   Error: $primary: "not-a-colour" is not a color.
   ```

2. **Search for that variable** in `_bootstrap_variables.scss` or `_adminlte_variables.scss` and correct the value type.
   Check `mvp/static/adminlte/scss/` for the expected type in the upstream declaration.

3. **Re-run the build** after correcting the value:

   ```bash
   poetry run python manage.py compress
   ```

4. If you are unsure what type a variable expects, look for its `!default` declaration
   in the vendored `mvp/static/adminlte/scss/` source tree.

> The `invoke refresh-adminlte-scss` task also runs a pre-validation scan on
> `_bootstrap_variables.scss` and will print a warning if it detects common issues
> (such as empty string values) before compilation is attempted.

## SC-002: First-Time Developer Timing Protocol

This protocol measures the time for a new contributor to perform one theme override
using only this quickstart guide.

**Protocol steps** (record start and end times in seconds):

1. T₀ — Open this document.
2. T₁ — First successful edit saved to `_bootstrap_variables.scss`.
3. T₂ — First successful Sass compilation (`manage.py compress`) with the override active.
4. T₃ — Visual confirmation of the override in the browser.

**Target**: T₃ − T₀ ≤ 10 minutes for a developer already familiar with Django.

**Baseline run** (record results below when executed):

| Run | Date | T₀ (s) | T₁ (s) | T₂ (s) | T₃ (s) | Total (min) | Notes |
|-----|------|--------|--------|--------|--------|------------|-------|
| 1   |      |        |        |        |        |            |       |

## SC-003: Vendor Refresh Repeatability Protocol

This protocol verifies that running `invoke refresh-adminlte-scss` twice in a row
produces the same vendored SCSS tree and the same compiled CSS output.

**Protocol steps**:

1. Run `invoke refresh-adminlte-scss` (first run). Record the AdminLTE version from the lockfile.
2. Verify the application compiles and renders correctly.
3. Run `invoke refresh-adminlte-scss` again (second run, same lockfile).
4. Confirm the vendored SCSS tree is byte-for-byte identical to the first run.
5. Confirm compilation succeeds with no changes to the compiled CSS output.

**Baseline run** (record results below when executed):

| Run | Date | AdminLTE version | Compilation result | Notes |
|-----|------|-----------------|-------------------|-------|
| 1   |      |                 |                   |       |
| 2   |      |                 |                   |       |

## Recording Checklist

- [ ] SC-002 first-time developer timing protocol executed and results recorded above.
- [ ] SC-003 vendor refresh repeatability protocol executed and results recorded above.
- [ ] `package-lock.json` committed to the repository after the first refresh.
- [ ] `_bootstrap_variables.scss` contains at least one active override as evidence of end-to-end testing.
- [ ] Playwright screenshot captured showing the themed UI after override (see `tests/test_ui_theme.py`).

## Expected Outcome

- Vendored AdminLTE SCSS sources are updated in a repeatable way.
- App overrides remain isolated in `_bootstrap_variables.scss` and `_adminlte_variables.scss`.
- SCSS compilation uses django-compressor and django-libsass.
- A clean rebuild produces the expected app-specific theme without stale vendor files.
