# Implementation Plan: Vendored Theme Variable Overrides

**Branch**: `018-vendor-adminlte-scss` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/018-vendor-adminlte-scss/spec.md`
**Propagated**: 2026-05-26 — Updated from spec.md refinement: UI verification principal tool changed from playwright-mcp to playwright-cli
**Propagated**: 2026-05-27 — Updated from spec.md refinement: renamed `_mvp_variables.scss` → `_bootstrap_variables.scss` and `_mvp_lte_variables.scss` → `_adminlte_variables.scss`; corrected file locations from `mvp/static/scss/` to `mvp/static/`; added second AdminLTE override hook and `_patch_adminlte_scss()` task step.
**Propagated**: 2026-05-27 — Updated from spec.md refinement: added US4 (demo page) — project structure, constitution check, design notes, and summary updated to include the SCSS variable override demo view.
**Propagated**: 2026-05-27 — Updated from spec.md refinement: demo page title is "Theme Customization"; sidebar menu entry is top-level (not group-nested); breadcrumbs are two-level (Home → Theme Customization).
**Goal**: Vendor the latest AdminLTE 4 SCSS sources into the Django MVP static tree, compile them through the existing django-compressor + django-libsass pipeline, and provide two downstream override entrypoints: `_bootstrap_variables.scss` (Bootstrap tokens + plain AdminLTE values) and `_adminlte_variables.scss` (AdminLTE vars that reference Bootstrap tokens).

## Summary

Add a repeatable vendor-refresh flow for AdminLTE 4 SCSS, store the upstream sources under `mvp/static/adminlte/scss/`, and keep downstream theme overrides isolated in two files at `mvp/static/`: `_bootstrap_variables.scss` (imported before all vendor defaults) and `_adminlte_variables.scss` (injected into `adminlte.scss` after Bootstrap vars but before AdminLTE defaults). The existing Django compressor pipeline will compile SCSS using django-libsass, with app overrides imported ahead of vendor defaults so downstream theme values win without editing vendored files. The `invoke refresh-adminlte-scss` task in `tasks.py` handles the full refresh including patching `adminlte.scss` to inject the second override hook. A dedicated demo page in the `demo` app provides live, in-app guidance so downstream developers can learn the override workflow from a running application.

## Technical Context

**Language/Version**: Python 3.12+ with SCSS authored for the AdminLTE 4 toolchain
**Primary Dependencies**: Django 5.2+, django-compressor 4.5.1+, django-libsass 0.9+, AdminLTE 4 npm package, Invoke
**Storage**: Filesystem only; no database schema changes
**Testing**: pytest, pytest-django, pytest-playwright, Django `check`, compressor/Sass build verification
**Target Platform**: Django web application for desktop and mobile browsers
**Project Type**: Reusable Django library
**Performance Goals**: N/A for runtime; maintain deterministic, reproducible asset compilation and refresh behavior
**Constraints**: Use the existing compressor/libsass pipeline; pin resolved AdminLTE versions via the lockfile; replace the vendored SCSS tree in full during refresh; patch `adminlte.scss` to inject `_adminlte_variables` hook after refresh; preserve downstream overrides in `_bootstrap_variables.scss` and `_adminlte_variables.scss`
**Scale/Scope**: Small-to-medium asset pipeline change affecting static sources, one Invoke task, documentation, and verification coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Design-First, Verify Implementation | UI changes require visual verification and test coverage | ✅ PASS — Sass output affects rendered UI; plan includes browser verification and pytest coverage |
| II. Documentation-First | Public theming surface and vendor refresh behavior must be documented | ✅ PASS — quickstart, contract docs, and spec updates are included |
| III. Component Quality & Accessibility | Compiled styles must preserve valid, accessible UI output | ✅ PASS — no markup API changes; style changes will be browser-verified |
| IV. Compatibility & Config-Driven Design | Preserve downstream customization without breaking existing consumers | ✅ PASS — overrides stay in `_bootstrap_variables.scss` and `_adminlte_variables.scss`; vendor files remain isolated |
| V. Tooling & Consistency | Must use the project’s existing toolchain and pass configured checks | ✅ PASS — plan uses django-compressor, django-libsass, Ruff/djlint-aligned docs, and existing Invoke workflow |
| VI. UI Verification (playwright-cli) | UI-affecting changes require browser verification | ✅ PASS — plan includes playwright-cli verification of compiled theme behavior |
| VII. Documentation Retrieval (context7) | Current dependency documentation should be consulted | ✅ PASS — current package documentation was consulted for the compiler stack; repo settings also confirm the pipeline |
| VIII. End-to-End Testing | User-visible styling changes require browser-level validation | ✅ PASS — browser verification is part of implementation and task planning |
| IX. Template Component Reuse Discipline | New demo page uses the existing demo app view pattern — no new reusable component fragments needed | ✅ PASS — demo view follows the existing `LayoutConfigMixin + TemplateView` pattern already established in `demo/views.py` |
| X. SKILL.md Currency | Relevant repo guidance must remain current | ✅ PASS — demo-views SKILL.md covers the view/URL/menu pattern; no conflict introduced |
| XI. Dual-Audience | Spec must support both maintainer and downstream developer workflows | ✅ PASS — refresh flow serves maintainers; `_bootstrap_variables.scss` and `_adminlte_variables.scss` serve downstream developers |
| XII. View Class Docstring Completeness | New view class added in demo/views.py | ✅ PASS — plan includes task to add docstring to the new `ThemeCustomizationView` |

## Project Structure

### Documentation (this feature)

```text
specs/018-vendor-adminlte-scss/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── public-api.md    # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks or Invoke-driven task generation)
```

### Source Code

```text
mvp/
├── static/
│   ├── adminlte/
│   │   └── scss/                    # Vendored AdminLTE SCSS source tree copied from npm
│   ├── _bootstrap_variables.scss    # NEW — override entrypoint 1 (Bootstrap tokens + plain AdminLTE values)
│   ├── _adminlte_variables.scss     # NEW — override entrypoint 2 (AdminLTE vars referencing Bootstrap tokens)
│   ├── scss/
│   │   └── mvp.scss                 # Main SCSS entrypoint that imports overrides + vendor sources
│   ├── css/                         # Existing compiled CSS assets
│   └── js/                          # Existing compiled JS assets
└── templates/
    └── [unchanged]                  # No template contract changes required for this feature

demo/
├── views.py                          # NEW — ThemeCustomizationView (LayoutConfigMixin + TemplateView)
├── urls.py                           # NEW URL — /demo/theming/scss-variables/
├── menus.py                          # NEW sidebar menu entry for the demo page
├── static/
│   ├── _bootstrap_variables.scss     # Demo app Bootstrap overrides (e.g. $primary: #a80081)
│   └── _adminlte_variables.scss      # Demo app AdminLTE overrides
└── templates/demo/
    └── scss_variables.html           # NEW — demo page template

tasks.py                              # Add/extend Invoke task for vendor refresh + adminlte.scss patching

tests/
├── settings.py                       # Asset pipeline and compiler configuration assertions
├── test_static_assets.py             # Vendor tree / refresh contract checks
├── test_ui_theme.py                  # Browser verification of compiled theme output
└── test_smoke.py                     # Demo page URL accessibility and doc consistency checks
```

**Structure Decision**: Keep the feature inside the existing single Django library layout. Vendored AdminLTE SCSS lives under `mvp/static/adminlte/scss/`. App-specific variable override files live at `mvp/static/` (the static root, not a subdirectory) so that Sass include-path resolution can find them — and an app listed before `mvp` in INSTALLED_APPS can shadow them with its own copies. The `tasks.py` `refresh_adminlte_scss` task patches the vendored `adminlte.scss` after each copy to inject the `_adminlte_variables` hook.

## Phase 0: Research

### Completed Research Outcomes

- The repository already configures `compressor` in test settings and uses `COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)`.
- The repo already stores Sass sources under `mvp/static/scss/`, so `mvp.scss` remains the compilation entrypoint. Override files live at `mvp/static/` (not inside `scss/`) so include-path resolution works correctly.
- The vendor refresh must be deterministic: install latest AdminLTE 4 via npm, let the lockfile pin the exact version, delete the old vendored SCSS tree, then copy the new tree into `mvp/static/adminlte/scss/`.
- Sass override ordering must preserve `!default` semantics so downstream values are loaded before vendor defaults.

## Phase 1: Design

### Artifact Summary

- `research.md` captures the build-tooling and refresh decisions.
- `data-model.md` defines build-time filesystem entities and their validation rules.
- `contracts/public-api.md` documents the theming surface and vendor-refresh contract for downstream developers.
- `quickstart.md` documents how maintainers refresh vendor sources and how downstream developers customize the theme.

### Design Notes

- No database schema changes are needed.
- One new Django view (`ThemeCustomizationView`) and one new URL are introduced in the `demo` app using `MVPTemplateView`. The view sets `page_title = "Theme Customization"` and two-level breadcrumbs (Home → Theme Customization).
- One new template (`demo/templates/demo/scss_variables.html`) is added; it extends `page_view.html` and uses cotton components.
- One new **top-level** sidebar menu entry is added in `demo/menus.py`.
- The main implementation risk is keeping the vendor refresh repeatable while preserving downstream overrides and preventing stale files.

## Complexity Tracking

> No Constitution violations. This section remains empty.
