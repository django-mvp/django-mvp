# Progress — 029 Layout state store and static responsive visibility

A dated, append-only record of what happened at each point in this feature's delivery.

## 2026-09-14 — Intake

Two open issues assessed together: #346 (publish layout state and configuration for the page to
read) and #345 (are the responsive visibility template tags necessary). They describe one piece of
work, so #346 became the feature and #345 is resolved by the same change.

Agreed with the maintainer before any artifact was written:

- Responsive visibility stays resolved by the browser. The tags go; their rules become stylesheet
  rules rather than client-side expressions.
- `sidebar_navbar_toggle_class` is in scope alongside the two tags #345 names.
- The tags are removed outright rather than deprecated for a release.

## 2026-09-14 — Specification

`spec.md` written: three user stories, FR-001 to FR-023, SC-001 to SC-006. Every requirement is
mapped to exactly one story. Five ambiguities resolved without escalation and recorded under
`## Clarifications`, with the longer reasoning in `decisions.md` as D1 to D6.

Issue graph built: #346 promoted to the feature's parent issue, with #347, #348 and #349 attached
as its stories. Draft pull request #351 opened from this branch, carrying a closing line for each
of the five issues.

Title lint: green.

## 2026-09-14 — Specification sign-off

Approved by the maintainer, unchanged. Planning starts. The maintainer also waived the
post-planning notification, so the next point he is involved is the merge decision.

## 2026-09-14T21:55:00Z · Implementer US0 · T001

Did: Added `mvp/layout.py` with `LayoutConfig` — one class carrying `breakpoint`, `persistent`,
`breakpoint_px`, `collapse`, `sticky`, `boost` and `as_dict()`. Normalisation (never/none in any
case, unrecognised name falls back to `lg`) lives only in this class's `breakpoint`/`persistent`/
`breakpoint_px` properties.

Verified: `poetry run pytest tests/test_layout.py -x` → 15 passed. `poetry run ruff check` and
`poetry run ruff format --check` on both new files → clean. `poetry run mypy mvp/layout.py` →
clean.

Next: T002 — the surviving tags read the resolver.

Watch: none.

## 2026-09-14T22:05:00Z · Implementer US0 · T002

Did: `sidebar_breakpoint_class`, `breakpoint_px` and `sidebar_has_breakpoint` in
`mvp/templatetags/mvp.py` now construct a `LayoutConfig` and read its `breakpoint`/`persistent`
properties instead of calling `_breakpoint_disabled` and repeating the `SIDEBAR_BREAKPOINTS`
lg-fallback lookup inline. Added `resolve_layout_config`, the tag T003 uses to resolve a
`LayoutConfig` for a template. Left `_breakpoint_disabled`, `SIDEBAR_BREAKPOINTS` and the three
visibility tags (`sidebar_navbar_toggle_class`, `navbar_wide_only_class`,
`navbar_narrow_only_class`) untouched — they are a later story's to remove and still use the
helper.

Verified: `poetry run pytest tests/test_components/test_layout_config.py -q` → 53 passed,
including every pre-existing test in the file, unmodified. `poetry run ruff check` and
`poetry run mypy` on `mvp/templatetags/mvp.py` → clean.

Next: T003 — the configuration payload.

Watch: `tests/test_components/test_layout_config.py` already failed `ruff format --check` before
this story touched it (two pre-existing lines, unrelated to T002) — confirmed by checking the
file at the pre-story commit. Left as-is per scope containment; noted in the completion report's
`concerns`.

## 2026-09-14T22:15:00Z · Implementer US0 · T003

Did: `mvp/templates/cotton/layout/sidebar/index.html` (the drawer, `<c-layout.sidebar>`) gained
three new component attributes — `collapse`, `sticky`, `boost` — each defaulting to its
`MVP_CONFIG["layout"]` value, and resolves a `LayoutConfig` via `resolve_layout_config`. Emits
`layout.as_dict()` through Django's `json_script` filter at id `"{{ id }}-layout-config"`, placed
next to the drawer checkbox rather than in `mvp/base.html` (D4/D6: a project overriding the base
template keeps `<c-app>` and therefore keeps the payload).

Verified: `poetry run pytest tests/test_components/test_layout_config.py -q` → 57 passed
(53 pre-existing + 4 new), pre-existing tests unmodified. `poetry run ruff check` on the test file
→ clean. `poetry run mypy mvp` → clean, 31 source files.

Next: none — US0 is Phase 0's last task. Handing off for the story's full verify.

Watch: `docs/components.md` and `skills/django-mvp/references/components.md` document
`<c-layout.sidebar>`'s attributes as `id`, `breakpoint`, `class` — now stale, since this task added
`collapse`, `sticky` and `boost`. Neither file is in this story's scope
(`files_you_may_create_or_edit`); flagged in the completion report's `concerns` for whichever story
or pass owns docs next.

## 2026-09-14 — Design review

Reviewed before implementation, across three lenses. Ten findings: six high, three medium, one
low. No critical, none about security. Every finding was checked against the code before being
acted on, and all six high findings were real.

Two of them changed the shape of the work. The collapse mode does not reach the element the
stylesheet rules need it on, so threading it through is now part of the task list. And the
characterisation tests could not have proved what they claimed — the class strings they would have
asserted on are the mechanism under substitution — so they assert computed visibility in a browser
instead.

The rest: the configuration payload moved into the foundational phase, the stories were declared
sequential, the persisted sidebar default got a single definition, and three task file lists were
corrected. Reasoning in `decisions.md` D7.

## 2026-09-14 — Foundational phase complete

T001, T002 and T003 done. `LayoutConfig` resolves the shell's layout facts once, the three
surviving template tags read it instead of reimplementing normalisation, and the drawer component
emits the resolved values to the client as escaped JSON.

Independently verified on the resulting commit: conformance, documentation, lint, type check, the
full test suite and the package build all green. The pre-existing-test guardrail flagged one file
and was cleared as additive. Two corrections were applied at acceptance — see `decisions.md` D8.
