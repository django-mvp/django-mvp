<!--
Sync Impact Report
- Version change: 3.7.0 → 3.8.0
- Change type: MINOR — Added a Simplicity Mandate (NON-NEGOTIABLE) to Principle VIII
  explicitly prohibiting the use of pytest-playwright/live_server wherever standard
  pytest/Django testing workflows are sufficient. Clarifies that E2E tests are reserved
  for behaviours that genuinely require a real browser.
- Modified principles:
  - VIII. End-to-End Testing (pytest-playwright) — Simplicity Mandate bullet added
- Added sections: none
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md ⚠ Review: ensure task generation does not
    schedule Playwright tests for functionality testable without a browser
  - .specify/templates/spec-template.md ✅ No change needed
  - .specify/templates/tasks-template.md ⚠ Review: ensure E2E task generation respects
    the simplicity mandate and defaults to pytest/Django test client where applicable
  - .specify/templates/commands/*.md ✅ No change needed (directory not present)
- Runtime guidance updates: none
- Deferred items: none
-->

# Django MVP Constitution

## Core Principles

### I. Design-First, Verify Implementation (NON-NEGOTIABLE)

All behavior changes MUST follow a design-verify-test workflow to ensure alignment between expectations and implementation.

**Rationale**: Front-end specifications are difficult to communicate precisely through written descriptions alone. Implementing design first allows for visual verification and user feedback before investing time in test design. This reduces wasted effort on tests for designs that don't match user expectations.

**Workflow**:

1. **Design Phase**: Create the design (mockups, wireframes, or initial implementation) based on specifications
2. **Verification Phase**: Verify the design meets expectations using visual inspection
  (playwright-cli skill in a real browser for UI), user feedback, and manual testing
3. **Implementation Phase**: Refine implementation based on verification feedback
4. **Testing Phase**: Write comprehensive tests for the verified, approved implementation

**Testing Requirements** (after design verification):

- All new or changed Python behavior MUST have pytest coverage.
- Django integration behavior MUST have pytest-django coverage.
- Cotton component tests MUST use the fixtures and patterns defined in the
  `cotton-test-components` skill (`.github/skills/cotton-test-components/SKILL.md`).
  The skill MUST be consulted before writing any Cotton component test. Use
  `cotton_render` / `cotton_render_soup` / `cotton_render_string` / `cotton_render_string_soup`
  from `django-cotton-bs5` as appropriate (NOT `Template()` or `render_to_string`).
- Cotton component tests MUST live under `tests/test_components/` and MUST be grouped
  by top-level Cotton directory to keep discovery predictable: all
  `templates/cotton/app/**` components in one shared module, all
  `templates/cotton/forms/**` components in one shared module, and the same pattern
  for every additional top-level directory under `templates/cotton/`.
- Single-file top-level Cotton components (for example `templates/cotton/grid.html`
  and `templates/cotton/icon.html`) MUST be grouped into one shared top-level module
  rather than split into one file per tiny component.
- One-test-module-per-tiny-component sprawl is prohibited unless a strong, explicit
  exception is documented in the related spec/plan/tasks artifact.
- Test structure MUST mirror the `mvp/` source tree (e.g., `mvp/views.py` → `tests/test_views.py`; `mvp/context_processors.py` → `tests/test_context_processors.py`).
- Fixture factories MUST use factory-boy (`DjangoModelFactory`) for reusable test data; ad-hoc inline model creation is only acceptable for truly one-off fixtures with no reuse potential.
- Performance tests MUST NOT use wall-clock timing assertions; use deterministic guards (e.g., `django_assert_num_queries`) instead.
- User-visible/UI behavior MUST have pytest-playwright coverage when the change affects rendered output, interactions, or accessibility.
- Pull requests MUST NOT be merged with failing tests, or without new/updated tests for behavior changes.
- The only acceptable exception is a docs-only change (no runtime behavior impact).

**Story-Level Validation (NON-NEGOTIABLE)**:

- **Task Breakdown**: Tasks (`tasks.md`) MUST be grouped by user story so that each story
  can be implemented and tested independently where feasible. Shared foundational work
  MUST be captured as explicit blocking tasks. Every phase in `tasks.md` that modifies
  any Django code (models, views, forms, URLs, settings, migrations, templates) MUST
  include an explicit validation task running `python manage.py check` AND the pytest
  suite for the touched area (e.g., `pytest tests/test_views/` after a view phase).
  These validation tasks are REQUIRED regardless of which tool or agent generates
  `tasks.md`; they MUST NOT be omitted when regenerating, updating, or re-ordering
  task files. The hardcoded equivalent in any CLI tooling is a convenience, not a
  substitute for this constitutional mandate.
- **Test-First Discipline**: Tests MUST be written and observed failing before
  implementation begins. No change MAY be merged that causes the agreed test suite
  for the touched area to fail.
- **System Checks**: `python manage.py check` MUST pass after completing each user story
  or major phase; model errors, admin field references, and misconfiguration MUST be
  caught before they reach staging.
- **Validation Frequency**: For multi-phase implementations, run system checks after each
  phase and update documentation incrementally.

### II. Documentation-First

Documentation is part of the product surface area.

- Every public setting, template block, and component MUST be documented with at least one minimal usage example.
- Any change to public behavior MUST include a docs update in the same pull request.
- Examples MUST be kept working and reflect the current recommended usage.
- Docs MUST describe expected behavior in testable terms (inputs, outputs, and constraints).

### III. Component Quality & Accessibility

Components MUST be usable, accessible, and predictable.

- Components MUST render valid, semantic HTML.
- Components MUST be accessible by default (keyboard navigable where relevant, with appropriate ARIA when necessary).
- If a change affects markup structure, add/update tests that assert the rendered HTML contract.
- UI behavior changes SHOULD be covered by browser tests when feasible.

### IV. Compatibility & Config-Driven Design

This is a reusable Django app; upgrades and consumers matter.

- Prefer configuration and extension points over invasive template overrides.
- Breaking changes MUST be avoided; if unavoidable, they MUST be explicit, documented, and versioned.
- Default behavior MUST remain stable across minor releases.
- **Cotton-Only UI Configuration**: UI configuration and customization MUST be achieved
  exclusively through Django Cotton components and template-level overrides. Python-level
  configuration is reserved for structural settings (e.g., installed apps, database,
  middleware). No CSS/JS wiring, layout selection, or component behavior MAY be
  configured through Python code when a Cotton component attribute or slot override is
  sufficient.

### V. Tooling & Consistency

The project uses consistent tooling to keep quality high and contributions smooth.

- Project commands MUST run through Poetry (e.g., `poetry run pytest`).
- Code MUST satisfy linting/formatting and any configured static checks before merge.
- Static analysis: Ruff (lint + format) for Python; djlint for templates. Both MUST be
  configured in `pyproject.toml` and MUST pass in CI. Template files MUST NOT be
  committed with djlint violations.
- Keep changes minimal and focused; avoid incidental refactors.

### VI. UI Verification (playwright-cli skill)

Agents MUST verify UI changes using the playwright-cli skill in a real browser
during implementation.

- When building or modifying UI elements, agents MUST use the playwright-cli skill to
  open a real browser, interact with the rendered output, and confirm that
  implementation changes are visually and interactively represented as expected.
- Any phase in `tasks.md` that modifies the user experience — including HTML templates,
  Cotton components, form rendering, CSS, HTMX interactions, or any visible UI element —
  MUST include at least one Playwright verification task that uses the playwright-cli
  skill in a real browser to confirm the expected interactive or visual outcome.
- Playwright verification tasks MUST assert the specific UX behaviour described in the corresponding
  user story acceptance criteria (e.g., "the form displays an inline validation error
  adjacent to the field", "the delete confirmation modal appears") and MUST NOT merely
  assert that the page loads without error.
- Screenshot-file analysis MAY be used only as a fallback for multi-viewport
  differences, configuration-driven visual diffs, subtle layout/CSS regressions, or an
  explicit reviewer request. Screenshot-only checks are insufficient for normal
  acceptance-criteria verification.
- Visual verification MUST occur after each significant UI modification to catch
  rendering issues before they are committed.
- No UI-impacting change MAY be merged without completing this verification and
  documenting the behavior-level assertion outcomes.
- This requirement applies to all `tasks.md` files regardless of which agent or tool
  generates them.

### VII. Documentation Retrieval (context7)

Agents MUST use current documentation when working with dependencies.

- Agents MUST use context7 to retrieve up-to-date documentation for all packages and libraries they are working with.
- This ensures that code follows current API patterns and best practices rather than outdated examples.
- Context7 MUST be consulted before implementing features that rely on external libraries (Django, Cotton, Bootstrap, etc.).

### IX. Template Component Reuse Discipline (NON-NEGOTIABLE)

Template markup is a first-class authoring surface. Inconsistent use of raw HTML,
ad-hoc `{% include %}` partials, and duplicate markup fragments undermines the
Bootstrap 5 design language and makes the UI harder to maintain. Cotton components —
both prebuilt (django-cotton-bs5) and custom — are the single canonical abstraction
for reusable template segments.

- **Prebuilt-first mandate**: Any work adding or modifying templates MUST first
  consider whether a prebuilt `django-cotton-bs5` component already satisfies the
  need. The `django-cotton-bs5` skill (`.github/skills/django-cotton-bs5/SKILL.md`)
  MUST be consulted before authoring new template markup that could be served by an
  existing component. Reproducing functionality already available in `django-cotton-bs5`
  via raw HTML or custom markup is a defect.
- **Custom Cotton component fallback**: If no suitable prebuilt component exists AND the
  template segment appears in more than one location or is conceptually reusable,
  developers MUST create a custom Cotton component (following the `django-cotton` skill
  at `.github/skills/django-cotton/SKILL.md`) rather than an `{% include %}`-based
  partial. Django template partials used solely via `{% include %}` MUST NOT be
  introduced for reusable content.
- **Exemption**: Genuinely one-off, non-reusable markup unique to a single view and
  with no reasonable extraction path is exempt from the custom-component mandate.
  However, even within exempt fragments, prebuilt `django-cotton-bs5` components MUST
  still be used wherever they apply.
- **Component placement**: Custom Cotton component files MUST be placed under the
  `templates/cotton/` directory (or an appropriate app-scoped subdirectory) and named
  using lowercase-kebab convention (e.g., `my-widget.html`). Component files MUST NOT
  be placed alongside view templates or nested arbitrarily.
- **Skill consultation mandate**: Any agent (AI-assisted or human contributor) creating,
  modifying, or reviewing template files MUST consult the `django-cotton-bs5` skill
  (`.github/skills/django-cotton-bs5/SKILL.md`) and, where custom components are
  required, the `django-cotton` skill (`.github/skills/django-cotton/SKILL.md`), before
  implementation begins.
- **Testing mandate**: Every custom Cotton component MUST be covered by tests that
  exercise rendering, attributes, slots, and edge-case behaviour. Tests MUST be written
  following the `cotton-test-components` skill
  (`.github/skills/cotton-test-components/SKILL.md`), which MUST be consulted before
  any Cotton component test is authored or reviewed.
- **Test module topology mandate**: Cotton component tests MUST be organized under
  `tests/test_components/` by top-level Cotton directory (`app`, `forms`, etc.), with
  one module per top-level directory. Single-file top-level components MUST be grouped
  in one shared top-level module. Creating one test module per tiny component is
  prohibited unless the exception is documented and justified.
- **Rationale**: This structure reduces test sprawl, simplifies navigation, speeds
  maintenance, and keeps component test discovery predictable.

### VIII. End-to-End Testing (pytest-playwright)

Features MUST include comprehensive end-to-end test coverage using pytest-playwright,
but ONLY for behaviour that genuinely requires a real browser.

- **Simplicity Mandate (NON-NEGOTIABLE)**: Playwright MUST NOT be used to test
  functionality that can be adequately verified using standard pytest/Django testing
  workflows. If a test can be written using the Django test client, model assertions,
  form validation helpers, view response assertions, or any other non-browser mechanism,
  it MUST be written that way instead. Using `live_server` + Playwright for behaviour
  that a `@pytest.mark.django_db` test with the Django test client can cover equally
  well is a defect, not a test. Any such test MUST be refactored to use the simpler
  approach.
- **When Playwright is appropriate**: E2E tests using pytest-playwright are reserved for
  behaviours that genuinely require a real browser environment — for example:
  JavaScript-driven interactions (HTMX DOM mutations, dynamic form behaviour, client-side
  validation), multi-step navigation flows that depend on browser state (cookies,
  history, focus management), visual rendering or accessibility checks, and interactions
  with third-party browser APIs. These are cases where the Django test client cannot
  reproduce the actual user experience.
- All new features MUST include end-to-end tests using pytest-playwright to verify
  complete user workflows **only where the above criteria are met**.
- E2E tests MUST cover the entire user journey from initial page load through final
  action completion for flows that are genuinely browser-dependent.
- E2E tests serve as acceptance tests that validate feature requirements are fully met.
- **Distinction from Principle VI**: playwright-cli verification tasks (Principle VI) are the
  inline interactive verification step performed by agents during implementation;
  pytest-playwright tests (this principle) are the formal regression suite that persists
  in the repository and runs in CI.

### X. django-mvp Skill Currency

This project maintains a first-party usage skill at `skills/django-mvp/SKILL.md`. The
skill documents the public API of the `django-mvp` package — its components, template
tags, configuration options, and usage patterns — for consumption by agents and
contributors building applications on top of it.

- **Maintenance mandate**: Any change that adds, modifies, or removes publicly visible
  functionality (components, template tags, context processors, settings, Cotton
  component attributes, or documented behaviour) MUST include a corresponding update to
  `skills/django-mvp/SKILL.md` in the same pull request. A PR that changes the public
  API without updating the skill is incomplete and MUST NOT be merged.
- **Scope — demo app only**: The `skills/django-mvp/SKILL.md` skill MUST be
  consulted when creating or modifying pages in the `demo/` app (views, templates,
  menus, URLs). It MUST NOT be consulted during development of the underlying `mvp/`
  codebase itself — doing so risks circular reasoning where the skill describes
  behaviour being actively changed. Core codebase work MUST refer to source code,
  tests, and docstrings directly.
- **Location**: The skill file lives at `skills/django-mvp/SKILL.md` (project root
  `skills/` directory, NOT under `.github/`). This path MUST be used in all references.
- **Currency guard**: Before authoring new example-app pages, agents MUST read
  `skills/django-mvp/SKILL.md` to confirm it reflects the current package state. If
  the skill appears stale relative to the codebase, the agent MUST update it before
  proceeding with example-app work.

### XI. Dual-Audience User Stories (NON-NEGOTIABLE)

`django-mvp` is a reusable Django package consumed by two distinct audiences:
**developers** who integrate and configure it, and **end users** who interact with
the resulting UI at runtime. Both audiences MUST be represented in every feature
specification.

- **Developer stories** describe the integrator experience: configuring components via
  Cotton attributes, wiring views, consulting quickstart documentation, overriding
  defaults, and understanding the public API. Example: *"As a developer, I want to
  configure the sidebar layout via a Cotton attribute so I can set it up without
  writing custom Python."*
- **End-user stories** describe the runtime experience of visitors to an application
  built with `django-mvp`. Example: *"As a consumer of the list view, I want search
  to submit automatically when I finish typing, so I can filter results without
  clicking a button."*
- Every feature specification (`spec.md`) MUST include at least one developer story
  AND at least one end-user story before the spec is considered complete. A spec with
  only one audience represented MUST be treated as a failing acceptance criterion.
- Developer stories and end-user stories MUST be clearly labelled (for example,
  `Developer` / `End User` tags on the story heading or an explicit **Audience**
  field).
- Prioritisation (P1, P2 …) applies independently within each audience group; a P1
  developer story and a P1 end-user story may coexist and SHOULD be implemented
  together where they describe two sides of the same feature.

### XII. View Class Docstring Completeness (NON-NEGOTIABLE)

Every public view mixin and concrete base view class in `mvp/views/` MUST carry a
comprehensive class-level docstring that serves as the authoritative reference for
human contributors and AI agents navigating the codebase via code-lookup tools.

**Rationale**: Agents and new developers primarily learn the available surface area of
a class by reading its docstring, not by tracing the full class hierarchy. Without
complete, structured docstrings, configuration attributes inherited from mixins become
invisible, overridable hook methods go undiscovered, and the developer experience
degrades significantly. A well-structured docstring is therefore both a quality gate
and a knowledge-transfer artifact.

**Requirements**:

- **Scope**: Every public mixin and concrete base class in `mvp/views/` MUST have a
  class-level docstring. Private helpers (`_*` prefix) and internal detail classes are
  exempt.
- **Intended-use summary**: The docstring MUST open with one or two sentences
  describing what the class does and when a developer should reach for it.
- **Config section**: The docstring MUST include a `Config:` block listing every
  configuration attribute a downstream developer may set, using the format:

  ```
  Config:
      - ``attr_name`` (type, default): One-line description plus any special
        behaviour. Attributes inherited from mixins that are routinely overridden
        MUST also appear here; their provenance may be noted parenthetically
        (e.g., ``(inherited from NextURLMixin)``).
  ```

- **Override hooks**: Any method that downstream classes are expected to override MUST
  be listed under an `Override hooks:` subsection with a one-line summary of the
  expected return type and intended customisation point.
- **Minimal example**: Where the class is the primary entry point for a new developer,
  the docstring SHOULD include at minimum a short usage example showing the class
  wired to a URL and configured with common attributes.
- **Completeness gate**: A pull request that introduces a new view mixin or base class
  without a conforming docstring MUST NOT be merged. A PR that modifies the public
  interface of an existing class MUST update its docstring in the same PR.
- **AI-agent discoverability**: The docstrings are the canonical surface area
  description consumed by AI agents performing code lookups. They MUST be complete
  enough that an agent can determine all available knobs and extension points without
  reading every parent class.

## Quality Gates

The following gates MUST pass for every pull request that changes runtime behavior:

- Unit/integration tests pass (`pytest` via Poetry).
- Linting passes (Ruff).
- Formatting is applied (Ruff formatter).
- Documentation is updated when public behavior changes.
- `python manage.py check` passes with no errors.
- UI-impacting changes include completed playwright-cli verification evidence for
  acceptance-criteria behavior (not page-load-only checks).

If a change affects UI output or interaction, add or update pytest-playwright coverage.

## Development Workflow

- Start with the design that expresses the desired behavior and visual appearance
- Verify the design meets expectations through visual inspection and user feedback (use
  the playwright-cli skill in a real browser for UI verification)
- Refine the implementation based on verification feedback
- Write comprehensive tests for the verified implementation (unit, integration, and end-to-end)
- After each user story phase, run `python manage.py check` and the relevant pytest suite
- Update documentation alongside the change, not after
- Keep PRs small and reviewable; split unrelated changes

## Governance

This constitution defines non-negotiable project rules and supersedes local conventions.

- Amendments MUST be proposed via pull request and include a brief rationale.
- Amendments MUST state whether they are MAJOR/MINOR/PATCH changes to this constitution.
- Any PR that materially changes development norms MUST update this constitution and any dependent templates.
- Reviews MUST explicitly check compliance with the Core Principles and record any
  deviations with a remediation plan before merge.

### Versioning Policy (Constitution)

- MAJOR: Removes or redefines a principle in a backward-incompatible way.
- MINOR: Adds a principle/section or materially expands guidance.
- PATCH: Clarifies wording or fixes typos without changing intent.

**Version**: 3.8.0 | **Ratified**: 2026-01-05 | **Last Amended**: 2026-05-28
