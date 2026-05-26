# Data Model: Vendored Theme Variable Overrides

This feature does not add database models. The "entities" below are build-time and filesystem artifacts that define the SCSS theming contract.

## Entity: Vendor Source Tree

- **Represents**: The refreshed AdminLTE SCSS source files copied into `mvp/static/adminlte/scss/`.
- **Key fields**:
  - `source_package`: The npm package providing the upstream files.
  - `resolved_version`: The exact package version captured by the lockfile.
  - `destination_path`: The vendored filesystem location under `mvp/static/`.
  - `refresh_mode`: Full replacement (`delete then copy`).
- **Validation rules**:
  - Must be replaceable as a whole directory.
  - Must not retain stale files from prior versions.
  - Must correspond to the lockfile-resolved package version.

## Entity: Theme Override File

- **Represents**: The app-owned SCSS override entrypoint at `mvp/static/scss/_mvp_variables.scss`.
- **Key fields**:
  - `variable_name`: The Sass variable being overridden.
  - `variable_value`: The downstream theme value.
  - `scope`: App-wide theme configuration.
- **Validation rules**:
  - Must be loaded before vendor defaults.
  - Must contain valid Sass-compatible values.
  - Must not require edits to vendored source files.

## Entity: Sass Compilation Pipeline

- **Represents**: The Django compressor plus django-libsass build path that converts SCSS into CSS.
- **Key fields**:
  - `precompiler`: `django_libsass.SassCompiler`.
  - `compressor_app`: `compressor`.
  - `source_entrypoint`: `mvp/static/scss/mvp.scss`.
  - `output_artifact`: Compiled CSS consumed by the app.
- **Validation rules**:
  - Must process the override file and vendor sources in the documented order.
  - Must surface actionable build errors when Sass compilation fails.

## Entity: Vendor Refresh Operation

- **Represents**: The repeatable update action that installs the latest package and copies the new SCSS tree into place.
- **Key fields**:
  - `package_manager`: npm.
  - `refresh_target`: AdminLTE 4 SCSS source tree.
  - `lockfile_role`: Pin the resolved version.
  - `directory_policy`: Replace existing tree before copy.
- **Validation rules**:
  - Must be safe to repeat.
  - Must preserve downstream override files.
  - Must leave the repo in a compilable state after refresh.
