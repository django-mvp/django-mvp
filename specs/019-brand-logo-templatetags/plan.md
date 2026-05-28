# Implementation Plan: Brand Logo & Icon Templatetags

**Branch**: `019-brand-logo-templatetags` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/019-brand-logo-templatetags/spec.md`

## Summary

Formalise, correct, and test the partially-implemented `logo_url` / `icon_url` templatetags and their resolver infrastructure. The core change renames two settings keys, updates the tag signature to accept `request` explicitly, adds proper error handling, writes a full pytest suite, and updates `skills/django-mvp/SKILL.md`. No database changes. No new static files. Zero new runtime dependencies.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Django 5.2+ (only); no additional runtime dependencies
**Storage**: N/A — no database entities; resolver returns URL strings
**Testing**: pytest, pytest-django
**Target Platform**: Django reusable app (library); consumed by host Django projects
**Project Type**: Library / reusable Django app
**Performance Goals**: Resolver called per tag invocation; Python import cache makes `import_string` cheap. No explicit performance target.
**Constraints**: No new runtime dependencies; no caching at tag level (per spec clarification); must not call `mark_safe()`; `ImproperlyConfigured` on bad import path only
**Scale/Scope**: 3 files modified (`config.py`, `utils.py`, `templatetags/mvp.py`); 1 new test file; 1 skill update

## Constitution Check

### Principle I — Design-First, Verify Implementation

This feature touches rendered HTML output (logo/icon `src` attributes). The plan MUST include a playwright-cli verification task confirming the logo and icon render correctly in the demo app for both light and dark themes.

- playwright-cli verification is required after the implementation phase.
- Assertion target: logo `<img>` renders with a non-empty `src`; dark-theme icon uses a different URL than light-theme icon.
- pytest-playwright E2E test required (Principle VIII).

### Principle II — Documentation-First

- `skills/django-mvp/SKILL.md` MUST be updated in the same PR with the new settings keys and tag signatures.
- `quickstart.md` is authored in Phase 1 (complete — see quickstart.md).

### Principle XI — Dual-Audience User Stories (amended)

**Initial status**: VIOLATION — all stories were developer-facing and unlabeled.
**Resolution**: Spec amended in Phase 0 to add audience labels to all stories and add User Story 5 (End User — correct branding in multi-tenant context). See research.md Decision 6.

**Gate result: PASS** (after spec amendment). No blocking violations.

## Project Structure

### Documentation (this feature)

```text
specs/019-brand-logo-templatetags/
├── plan.md                        # This file
├── research.md                    # Phase 0 — decisions
├── data-model.md                  # Phase 1 — configuration schema and callable contract
├── quickstart.md                  # Phase 1 — developer usage guide
├── contracts/
│   └── brand-resolver-api.md      # Phase 1 — public API contract
└── tasks.md                       # Phase 2 — /speckit.tasks output (not yet generated)
```

### Source Code Changes

```text
mvp/
├── config.py               # MODIFY — rename MVP_LOGO_URL_FUNC -> MVP_LOGO_RESOLVER
│                           #          rename MVP_ICON_URL_FUNC -> MVP_ICON_RESOLVER
├── utils.py                # MODIFY — update logo_url default resolver (light fallback)
│                           #          no behaviour change for icon_url
└── templatetags/
    └── mvp.py              # MODIFY — keep takes_context=True; make height/theme
                            #          keyword-only with defaults; add error handling

tests/
└── test_templatetags.py    # CREATE — new unit test file

skills/
└── django-mvp/
    └── SKILL.md            # MODIFY — document new settings keys and tag signatures
```

**Structure Decision**: Single reusable Django app. Changes are additive corrections to 3 existing files plus 1 new test file. Follows the project convention of mirroring `mvp/` source structure under `tests/`.

## Post-Design Constitution Check

| Principle | Status | Note |
|-----------|--------|------|
| I — Design-First | PASS | Playwright task required; no shortcuts |
| II — Docs-First | PASS | quickstart.md authored; SKILL.md update in scope |
| IV — Config-Driven | PASS | Resolver callable is the clean extension point |
| V — Tooling | PASS | pytest, ruff, djlint |
| VI — UI Verification | PASS | Playwright task scoped for logo/icon src attributes |
| IX — Cotton Reuse | PASS | N/A for this feature |
| X — SKILL.md | PASS | Mandatory task in implementation |
| XI — Dual-Audience | PASS | Spec amended; Story 5 added |

**Final gate: PASS**
