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
