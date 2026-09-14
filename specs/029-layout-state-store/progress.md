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
