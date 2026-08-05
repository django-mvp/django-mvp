# Implementation Plan: Formset Pages

**Branch**: `024-formset-pages` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/024-formset-pages/spec.md`

## Summary

Put a Django formset on a page with the packaged look, and package the view that pairs a record
with its related rows.

Three pieces, in dependency order. First, the crispy pair becomes a declared runtime dependency
and the documented setup gains its two `INSTALLED_APPS` entries, so the packaged form rendering
works on a clean install at all. Second, a `<c-form.formset>` Cotton component renders any
formset — management form, one row per form, set-level errors above the set, row errors beside
their fields — by delegating each field to the same crispy field template a single form's fields
go through, which is what makes a row indistinguishable from a single form. Third,
`MVPInlineCreateView` and `MVPInlineUpdateView` build an inline formset from configuration,
validate it alongside the parent form, and save both inside one transaction.

The rendering is generic and the view is not. A formset reaches the page through a
`{% block formset %}` in the existing `form_view.html`, so any packaged form view that puts a
`formset` in its context gets it rendered — including the existing `MVPFormView` with a
standalone formset. Adding and removing rows is Alpine driving Django's own `TOTAL_FORMS` and
`DELETE` bookkeeping, with no build tooling and no request before submission.

## Technical Context

**Language/Version**: Python 3.12+ (`requires-python >=3.12`), Django 5.2 and 6.0

**Primary Dependencies**: django-cotton 2.6.1 (components), django-crispy-forms ^2.7 and
crispy-tailwind ^1.0.3 (**promoted to runtime by this feature**), Alpine.js 3 with the sort and
persist plugins (CDN, already loaded), Tailwind v4 + DaisyUI 5 (build-time)

**Storage**: N/A — the package ships no models. The demo application uses SQLite.

**Testing**: pytest + pytest-django, `tests.settings`, factory_boy, bs4 for markup assertions.
Cotton components are exercised through compiled-source rendering
(`tests/test_components/`, declared under `[tool.forge.conformance] non-mirror-paths`).

**Target Platform**: A reusable Django package installed into a consuming project.

**Project Type**: Single Python package (`mvp`) plus a `demo` application used for
documentation and tests.

**Performance Goals**: None specific. The rendering path adds one template include per row over
what a single form costs.

**Constraints**: No front-end build tooling in the consuming project (FR-025). No request
between a row change and submission (FR-024). The committed stylesheet must carry any new class
(Article XV). Coverage floors project ≥ 90%, patch ≥ 85%.

**Scale/Scope**: Two new Cotton component templates, one new view module with three classes, one
block added to an existing page template, one attribute added to an existing component, a
dependency promotion, one demo page, and documentation.

## Constitution Check

*Checked against `memory/constitution.md` v4.1.0. Re-checked after Phase 1 design — see the
second verdict column.*

| Article | Bearing on this feature | Pre-design | Post-design |
|---|---|---|---|
| I — Test-First | Every task writes a failing test first. Component tests via compiled-source rendering, view tests via the Django test client. | PASS | PASS |
| II — Simplicity | Reuses `form_view.html` rather than adding a page template; reuses `Product`/`OrderLine` rather than adding a demo model; declines a system check that no requirement asks for. | PASS | PASS |
| III — Anti-Abstraction | One mixin holding the formset configuration, consumed by two views. No registry, no base hierarchy, no second implementation anticipated. | PASS | PASS |
| IV — Integration-First | The component and view contracts are written before internals (`contracts/`), and acceptance scenarios drive the tests. | PASS | PASS |
| V — Security & data-safety | All values render through the template layer. `__prefix__` substitution operates on markup Django produced, and the index substituted in is seeded from `formset.total_form_count` rather than from the management form's DOM value. `inline_max_num` is enforced on the server, not only in the browser. No auth or crypto surface of its own. **Qualified**: the browser behaviour rests on Alpine loaded from a CDN at a floating version with no subresource integrity — pre-existing, not introduced here, and recorded in Risks. | PASS | PASS (qualified) |
| VI — Documentation | README, `docs/getting-started.md`, `docs/views.md`, `docs/components.md`, `docs/integrations.md`, `CONTEXT.md` and `CHANGELOG.md` all ship in this PR. | PASS | PASS |
| VII — Dependency discipline | Two runtime dependencies added, justification stated in FR-001 and R5. No new distribution enters the tree — both are already installed transitively for development. deptry stays green. | PASS (justified) | PASS |
| VIII — Internationalization | Every user-facing string on the add and remove controls and in the demo uses `{% trans %}` or `gettext_lazy`. | PASS | PASS |
| IX — Data-model conventions | No new model. One migration, giving `demo.OrderLine`'s two fields the `verbose_name` and `help_text` the article makes mandatory and which they have never had. Squashed at convergence. | PASS | PASS |
| X — Test structure | `mvp/views/inline.py` → `tests/test_views/test_inline.py`; component tests, including the browser test, under the already-declared `tests/test_components/`. No new test directory and no new non-mirror path. The browser test carries its `e2e` marker and `skipif` at class level, never module level. | PASS | PASS |
| XI — Components are the public API | `<c-form.formset>` and `<c-form.formset.row>` are named for their domain role, live under `mvp/templates/cotton/`, are overridable at their template path, and expose attributes rather than utility classes. This is why crispy's own formset template is not used — see R1. | PASS | PASS |
| XII — Configuration-driven layout | Row presentation is controlled by component attributes; the view's shape by class attributes. Nothing new enters `MVP_CONFIG`. | PASS | PASS |
| XIII — Rendered markup is a contract | Both components get per-component tests asserting their rendered structure, and are automatically enrolled in `test_render_all.py`. Remove controls carry an accessible name; the set-level error region is announced. | PASS | PASS |
| XIV — Browser tests are the exception | The add and remove behaviour is the one genuinely browser-dependent surface. Everything provable from rendered markup or the test client is tested that way; only the Alpine interaction itself is a browser test. | PASS (justified) | PASS |
| XV — Stylesheet is a build artifact | `invoke build-stylesheet` runs at convergence and the rebuilt CSS is committed. New classes are written literally in `mvp/templates/`, so the scanner sees them and no `@source inline` entry is needed. | PASS | PASS |
| XVI — Compatibility | Additive only. One existing component gains an optional attribute; one existing template gains a block. No import path or component API changes. CHANGELOG records the new surface. | PASS | PASS |
| XVII — Cohesion | The formset configuration and its hooks live on `InlineFormsetMixin`, not as module-level helpers. Django owns the rest of the grouping (`inlineformset_factory`, the view classes). | PASS | PASS |

**Verdict**: PASS, with two justifications recorded — the runtime dependency addition under
Article VII (FR-001 states it, and the code already required it) and the single browser test
under Article XIV (Alpine interaction is not expressible as a rendered-template assertion).
No entry in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/024-formset-pages/
├── spec.md              # Signed off at the Spec gate
├── decisions.md         # Self-resolved decisions, from S1 onward
├── progress.md          # Gate and stage record
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── formset-component.md
│   └── inline-view.md
└── tasks.md             # Phase 2
```

### Source Code (repository root)

```text
mvp/
├── templates/
│   ├── form_view.html                        # MODIFIED: {% block formset %}, formset media
│   └── cotton/form/
│       ├── index.html                        # MODIFIED: formset attribute for enctype
│       └── formset/
│           ├── index.html                    # NEW: <c-form.formset>
│           └── row.html                      # NEW: <c-form.formset.row>
├── views/
│   ├── __init__.py                           # MODIFIED: export the two views
│   └── inline.py                             # NEW: InlineFormsetMixin, MVPInlineCreateView,
│                                             #      MVPInlineUpdateView
└── static/css/django-mvp.css(.br)            # REBUILT at convergence

demo/
├── models.py                                 # MODIFIED: OrderLine field metadata (Article IX)
├── migrations/                               # NEW: one, for that metadata
├── views.py                                  # MODIFIED: ProductOrderLinesView
├── urls.py                                   # MODIFIED: its route
└── templates/demo/components/formset.html    # NEW: component doc page

tests/
├── test_components/
│   ├── test_form_formset.py                  # NEW: both components, plus the one
│   │                                         #      browser test as its own class
│   └── test_form_index.py                    # MODIFIED or NEW: enctype contract
├── test_views/
│   └── test_inline.py                        # NEW: the configured view
└── test_smoke.py                             # MODIFIED: the declared-dependency check

docs/
├── formsets.md                               # NEW: the worked example
├── getting-started.md, views.md, components.md,
│   integrations.md, index.md, ROADMAP.md     # MODIFIED
CONTEXT.md                                    # MODIFIED: vocabulary
CHANGELOG.md                                  # MODIFIED: Unreleased
pyproject.toml                                # MODIFIED: dependencies, deptry
README.md                                     # MODIFIED: required setup
```

**Structure Decision**: The package's existing layout is kept exactly. Components go under
`mvp/templates/cotton/form/formset/` because the directory is the Cotton namespace, matching
`cotton/page/list/actions/`. The view goes in a new `mvp/views/inline.py` rather than into
`mvp/views/edit.py`, which already carries four view classes across roughly six hundred lines —
see R7. Tests mirror that split under Article X.

**No new test directory.** The one browser test lives in `tests/test_components/test_form_formset.py`
as its own class, carrying the `e2e` marker and the playwright `skipif` at class level. That is the
precedent `tests/test_views/test_error.py` already sets, it keeps the test beside the components it
exercises, and it avoids declaring a second `non-mirror-path` for a directory with no source module
behind it. Article X's warning is about *module-level* `pytestmark` hiding the unit tests underneath
it, which a class-level marker does not do — a separate module was never the remedy it called for.

## Phase breakdown

Ordered by dependency, matching the story priorities. Each phase is independently verifiable.

1. **Foundation — US1.** Promote the crispy pair to runtime dependencies, extend the deptry
   ignores, update the documented setup. Proves the rest of the feature works on a clean
   install. Nothing after this depends on it in code, but everything depends on it in truth.
2. **US2 — the component.** `<c-form.formset>` and `<c-form.formset.row>`, the `form_view.html`
   block, the `<c-form>` enctype attribute. Delivers a rendered formset anywhere.
3. **US3 — the configured view.** `mvp/views/inline.py` and its exports. Delivers the
   parent-and-rows page.
4. **US4 — error placement.** Set-level errors above the set. Row-level errors are already
   correct from phase 2; this phase proves them and adds what is missing.
5. **US5 — rows in the browser.** The Alpine root, the `<template>` blank row, add and remove
   controls, the cap and the no-delete cases.
6. **US6 — documentation.** `docs/formsets.md`, the demo page, `CONTEXT.md`, `CHANGELOG.md`,
   README.

Phase 2 gates everything after it. Phases 4 and 5 both edit the component it creates, so they run
after it and sequentially with each other, never concurrently. Phase 3 needs no code from phase 2,
but its page tests assert against rendered rows, which only reach the page through the block phase
2 adds — so it follows phase 2 too.

## Risks

- **Error placement is the least predictable part.** Row-level placement is inherited from
  crispy's field template and should need no work, but that is a claim about a vendored template
  and the first task in phase 4 is a test that proves it before anything is built on it.
- **`test_render_all.py` renders every packaged component with a near-empty context.** Both new
  templates are enrolled automatically and must render without a formset present. They are
  written to tolerate it rather than added to that module's `SKIP` dictionary.
- **The stylesheet rebuild is not verifiable by CI.** Article XV makes it an author
  responsibility; it is an explicit convergence task, not a step anyone is trusted to remember.
- **Promoting a dependency changes what a consumer must install.** It is additive for anyone
  already rendering forms, since they necessarily had both packages, but it is a real metadata
  change and belongs in the CHANGELOG with an "On upgrade:" note, matching the house style.
- **The browser behaviour rests on an unpinned third-party script.** `mvp/templates/mvp/base.html`
  loads Alpine and its plugins from a public CDN at `3.x.x`, with no subresource integrity — and a
  floating range makes integrity impossible by construction. Anyone who compromises that package or
  its CDN path executes code in every consuming project's authenticated pages, with no deployment
  on the consumer's side. This is pre-existing and predates the feature, and two other script tags
  in the same block have the same shape, so it is not fixed here. It is named because this feature
  is what makes it load-bearing, and it is filed separately.

## Complexity Tracking

No Constitution Check violations require justification beyond the two recorded in the table
above, both of which are permitted by their articles rather than exceptions to them.
