# Implementation Plan: Vendored Theme Variable Overrides

**Branch**: `018-vendor-adminlte-scss` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/018-vendor-adminlte-scss/spec.md`
**Propagated**: 2026-05-26 — Updated from spec.md refinement: UI verification principal tool changed from playwright-mcp to playwright-cli
**Goal**: Vendor the latest AdminLTE 4 SCSS sources into the Django MVP static tree, compile them through the existing django-compressor + django-libsass pipeline, and provide a single downstream override entrypoint via `_mvp_variables.scss`.

## Summary

Add a repeatable vendor-refresh flow for AdminLTE 4 SCSS, store the upstream sources under `mvp/static/adminlte/scss/`, and keep downstream theme overrides isolated in `mvp/static/scss/_mvp_variables.scss`. The existing Django compressor pipeline will compile SCSS using django-libsass, with app overrides imported ahead of vendor defaults so downstream theme values win without editing vendored files. Implementation will also add or extend an Invoke task in `tasks.py` so maintainers can refresh the vendor tree with a single command.

## Technical Context

**Language/Version**: Python 3.12+ with SCSS authored for the AdminLTE 4 toolchain
**Primary Dependencies**: Django 5.2+, django-compressor 4.5.1+, django-libsass 0.9+, AdminLTE 4 npm package, Invoke
**Storage**: Filesystem only; no database schema changes
**Testing**: pytest, pytest-django, pytest-playwright, Django `check`, compressor/Sass build verification
**Target Platform**: Django web application for desktop and mobile browsers
**Project Type**: Reusable Django library
**Performance Goals**: N/A for runtime; maintain deterministic, reproducible asset compilation and refresh behavior
**Constraints**: Use the existing compressor/libsass pipeline; pin resolved AdminLTE versions via the lockfile; replace the vendored SCSS tree in full during refresh; preserve downstream overrides in `_mvp_variables.scss`
**Scale/Scope**: Small-to-medium asset pipeline change affecting static sources, one Invoke task, documentation, and verification coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Design-First, Verify Implementation | UI changes require visual verification and test coverage | ✅ PASS — Sass output affects rendered UI; plan includes browser verification and pytest coverage |
| II. Documentation-First | Public theming surface and vendor refresh behavior must be documented | ✅ PASS — quickstart, contract docs, and spec updates are included |
| III. Component Quality & Accessibility | Compiled styles must preserve valid, accessible UI output | ✅ PASS — no markup API changes; style changes will be browser-verified |
| IV. Compatibility & Config-Driven Design | Preserve downstream customization without breaking existing consumers | ✅ PASS — overrides stay in `_mvp_variables.scss`; vendor files remain isolated |
| V. Tooling & Consistency | Must use the project’s existing toolchain and pass configured checks | ✅ PASS — plan uses django-compressor, django-libsass, Ruff/djlint-aligned docs, and existing Invoke workflow |
| VI. UI Verification (playwright-cli) | UI-affecting changes require browser verification | ✅ PASS — plan includes playwright-cli verification of compiled theme behavior |
| VII. Documentation Retrieval (context7) | Current dependency documentation should be consulted | ✅ PASS — current package documentation was consulted for the compiler stack; repo settings also confirm the pipeline |
| VIII. End-to-End Testing | User-visible styling changes require browser-level validation | ✅ PASS — browser verification is part of implementation and task planning |
| IX. Template Component Reuse Discipline | No new reusable template fragments are introduced here | ✅ PASS — feature is asset/build focused, not template-component focused |
| X. SKILL.md Currency | Relevant repo guidance must remain current | ✅ PASS — no skill conflict introduced; plan references existing repo conventions |
| XI. Dual-Audience | Spec must support both maintainer and downstream developer workflows | ✅ PASS — refresh flow serves maintainers; `_mvp_variables.scss` serves downstream developers |
| XII. View Class Docstring Completeness | No new view classes are introduced | ✅ PASS — not applicable |

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
│   ├── scss/
│   │   ├── _mvp_variables.scss      # NEW — app override entrypoint
│   │   └── mvp.scss                 # Main SCSS entrypoint that imports overrides + vendor sources
│   ├── css/                         # Existing compiled CSS assets
│   └── js/                          # Existing compiled JS assets
└── templates/
    └── [unchanged]                  # No template contract changes required for this feature

tasks.py                              # Add/extend Invoke task for vendor refresh

tests/
├── settings.py                       # Asset pipeline and compiler configuration assertions
├── test_static_assets.py             # Vendor tree / refresh contract checks
└── test_ui_theme.py                  # Browser verification of compiled theme output
```

**Structure Decision**: Keep the feature inside the existing single Django library layout. Vendored AdminLTE SCSS lives under `mvp/static/adminlte/scss/`, app-specific variable overrides live in `mvp/static/scss/_mvp_variables.scss`, and the existing `mvp/static/scss/mvp.scss` remains the compilation entrypoint. The repo’s existing `tasks.py` is the natural home for the Invoke-based vendor refresh task.

## Phase 0: Research

### Completed Research Outcomes

- The repository already configures `compressor` in test settings and uses `COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)`.
- The repo already stores Sass sources under `mvp/static/scss/`, so that remains the app-owned override surface.
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
- No new Django views, URLs, or model APIs are introduced.
- The main implementation risk is keeping the vendor refresh repeatable while preserving downstream overrides and preventing stale files.
- Because this feature affects rendered CSS, browser verification is required even though the code change is mostly static-asset and build-pipeline oriented.

## Complexity Tracking

> No Constitution violations. This section remains empty.
