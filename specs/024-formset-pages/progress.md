# FS-024 — progress

## Gates

- **Spec gate: APPROVED** by Sam, 2026-08-05, in session. No changes requested.
  - Surface reviewed: epic #162 (body + six story sub-issues), `spec.md`, `decisions.md`, draft PR #169.
  - Machine gate at S2 exit: `forge check-issue-titles --repo django-mvp/django-mvp --epic 162 --num 024` green.
  - Carried forward: R8/R12 scope correction (R12's crispy-removal deliverable is settled the other way by this feature).

## Stages

- S0 INTAKE — done (issue #162 filed, `accepted`).
- S1 SPECIFY — done (spec.md + decisions.md, clarify run).
- S2 SETUP — done (epic promoted, stories #163–#168, draft PR #169, milestone v1.0.0).
- S3 PLAN — started 2026-08-05.

## S3 PLAN — 2026-08-05

Artifacts: `plan.md`, `research.md` (R1–R8), `data-model.md`, `contracts/formset-component.md`,
`contracts/inline-view.md`, `quickstart.md`, `tasks.md`, `feature-state.json`.

- Constitution Check: PASS against v4.1.0, with two recorded justifications — the runtime
  dependency addition (Article VII, which FR-001 states) and one browser test (Article XIV,
  which permits it where a rendered-template assertion cannot express the behaviour). No
  Complexity Tracking entry.
- Ledger: 40 tasks across six stories, schema-valid.
- `tasks.md` carries three further convergence tasks (then T041–T043, now **T044–T046** after the
  S3R renumbering: stylesheet rebuild, simplification pass, full machine gate). They belong to S5
  and are driven by the pipeline, not by a story, so they are deliberately absent from the story
  ledger. Under the current numbering T041–T043 are live US6 story tasks.
- Planning decisions D10–D16 recorded in `decisions.md`.

## S3R DESIGN_REVIEW — 2026-08-05

Three lenses in parallel against `spec.md` + `plan.md` + `research.md` + `tasks.md` + the
constitution, with no diff in existence. Craft-skill gate green both ways: `check-skills` before
dispatch, `check-receipts` per lens against its own dispatch brief on the way back.

| Lens | Verdict | Findings |
|---|---|---|
| spec-compliance | request_changes | 11 (1 high, 5 medium, 5 low) |
| security | request_changes | 3 (1 high, 1 medium, 1 low) |
| architecture | request_changes | 7 (3 medium, 4 low) |

Two verified HIGH findings forced the one permitted re-plan cycle:

- **SPEC-001** — no task tested a valid parent submitted with invalid rows, the one branch
  `form_valid` adds. The formset-validation guard could have been deleted with every other test in
  that story still passing.
- **SEC-001** — `inline_max_num` was passed to Django as `max_num` without `validate_max`, so a
  cap of three would have accepted and saved a submission carrying a thousand rows.

Eighteen further findings were accepted and applied in the same pass rather than carried, because
the cycle was already open. One finding (SEC-002, the CDN-loaded Alpine runtime) is carried rather
than fixed: it predates the feature and is wider than it. Decisions D17–D23 record the outcomes;
the three reports are archived at
`engineering-org/runs/django-mvp/024-formset-pages/findings-<lens>.json`.

Task ids were renumbered in the re-plan. 43 story tasks plus three convergence tasks; the ledger
is schema-valid at 43.

**Design-review budget: 1 of 1 used.** A second red round escalates rather than re-plans.

## S3R round 2 — 2026-08-05 — ESCALATED

Re-ran the two lenses that raised blocking findings in round 1. Both reports gated green on
receipts.

| Lens | Verdict | Round-1 dispositions | New findings |
|---|---|---|---|
| spec-compliance | **approve** | 10 closed, 1 partly closed and accepted | 4 (1 medium, 3 low) |
| security | **request_changes** | SEC-002 and SEC-003 closed, SEC-001 partly closed | 3 (1 high, 1 medium, 1 low) |

The spec-compliance lens re-ran the two-way FR/SC-to-task trace from scratch against the
renumbered task list and found no orphaned requirement and no orphaned task.

**Design-review budget is 1 of 1, and the second round is still red, so the run escalates rather
than re-planning.** The three findings Sam needs to rule on:

- **SEC-101 (verified high)** — the `absolute_max` half of the round-1 fix is wrong. Bounding it
  to the cap plus the extras rejects submissions that are legitimately within the cap, because
  Django's `absolute_max` check reads the raw submitted `TOTAL_FORMS` without subtracting deleted
  rows, and drops every row past the bound before validation. It contradicts D18's monotonic
  counter and breaks FR-013. The reviewer demonstrated both cases against the project venv rather
  than reasoning about them. The remedy is subtractive: keep `validate_max=True`, drop the
  `absolute_max` bound. R9's justification for the bound is also false — the formset is validated
  before the transaction opens, so no write transaction is held during `full_clean`.
- **SEC-102 (verified medium)** — producing the flash by calling `super().form_valid()` after the
  atomic block re-enters `ModelFormMixin.form_valid`, which saves the parent a second time outside
  the transaction. `MVPDeleteView.form_valid` is the house precedent for doing it directly.
- **SPEC-101 (verified medium)** — a **spec** fault, not a plan fault. `spec.md`'s Assumptions
  reserve "the list-page dependency" for R12, but the list page and the form page load the same
  distribution, which this feature declares. R12's deliverable is settled for both pages. Fixing
  the R12 annotation correctly needs a spec amendment and a re-gate, which is why it is not being
  applied quietly.

Four low-severity findings (SEC-103, SPEC-102, SPEC-103, SPEC-104) are documentation drift left by
the round-1 edits and are applied with whichever disposition Sam chooses.

Reports archived at `engineering-org/runs/django-mvp/024-formset-pages/findings-<lens>-round2.json`.

## S3R re-plan, cycle 2 — 2026-08-05

Sam authorised a second re-plan cycle rather than treating the escalation as a spec failure, on
the reading that both blocking findings were defects in the round-1 remedy and both fixes were
subtractive. Applied in full:

- **SEC-101** — the `absolute_max` bound is withdrawn. `validate_max=True` alone enforces the cap.
  `contracts/inline-view.md`, `research.md` R9 (including the false write-transaction
  justification), `data-model.md`, `plan.md`'s Article V row and T022 all corrected, and T021 now
  tests both directions: over the cap is rejected, and within-the-cap-after-removals is accepted.
  That second test is what pins the decision. Recorded as D25.
- **SEC-102** — `form_valid` no longer calls `super().form_valid()`. It queues the message and
  returns the redirect directly, as `MVPDeleteView.form_valid` already does. T023 rewritten, and
  T016 gained a parent-saved-exactly-once assertion. Recorded as D26.
- **SPEC-101** — **spec amendment.** The Assumption reserving a list-page dependency for R12 is
  struck through in place and replaced with a dated `**Refined**` note: both pages load the same
  distribution, so this feature settles that deliverable whole, and it is R12's second deliverable
  rather than its first. T043 rewritten against the corrected reading. Recorded as D24.
- **SEC-103, SPEC-102, SPEC-103, SPEC-104** — documentation drift left by the round-1 edits, all
  four applied. Recorded as D27.

The spec amendment is the one change that alters what Sam signed off, so it goes to him as a delta
brief before S4 begins.

## S3R round 3 — security lens — 2026-08-05

Re-ran the security lens alone, as the only one still red. It confirmed SEC-101, SEC-102 and
SEC-103 closed, and found that the SEC-102 remedy had itself introduced a regression:

- **SEC-201 (verified high)** — resolving the success URL above the atomic block breaks the create
  path, where `self.object` is `None`: the no-`success_url` case raises `ImproperlyConfigured`
  after the rows commit, and `success_url = "detail"` silently redirects to an unresolved literal
  path. Verified independently against `mvp/views/edit.py:203-260` and
  `mvp/views/detail.py:78-99,130-149` before accepting. Fixed by moving the resolution below the
  block, and T016 now exercises FR-012 on the create path with an object-dependent success URL —
  `success_url = "list"` resolves without the object and would have hidden it. Recorded as D28.
- **SEC-202 (verified low)** — one residue of the withdrawn `absolute_max` bound in `research.md`'s
  summary table. Removed. Recorded as D29.

The reviewer also confirmed, in its own words, that leaving `absolute_max` at Django's default is
safe here: the ceiling is bounded rather than absent, validation runs outside the transaction, the
attacker must already hold the parent's edit permission, and the cost matches what every Django
inline formset in the consuming project already carries. It separately cleared row identity for
IDOR — a submitted `id` belonging to another parent's row creates a new row rather than hijacking
the other record, because `_existing_object` resolves only within the parent-scoped queryset.

**The D28 and D29 edits have not themselves been through a review round.** Both are subtractive or
one-statement moves, and T016 and T021 are written to fail if either is undone.

## S3R closed — 2026-08-05

Confirmation pass on the two round-3 fixes came back closed with no new findings, verified in the
files rather than from my report. The reviewer added one observation worth keeping: resolving the
success URL after the save is not merely safe on the update path but slightly better, because
`get_absolute_url()` then reflects persisted values rather than pending ones — a slug the
submission changed, for instance. It also noted that a genuinely misconfigured view still raises
`ImproperlyConfigured` after the commit, and that this is parity with the packaged single-form
pages rather than a regression, which is what FR-012 asks for.

**Panel status: clean.** spec-compliance approve, security approve, architecture raised no blocking
finding and all seven of its findings were applied. `forge stage-exit --stage S3R` green across
clarifications, ledger schema, issue titles and PR title. Design-review budget 2 of 2, both cycles
authorised.

Two items travel forward rather than being closed here:

- The **spec amendment** (D24, the R12 scope correction) changes what Sam signed off at the Spec
  gate, so it goes to him as a delta brief. Only T043 depends on it; it is held until he rules.
- **SEC-002**, the CDN-loaded Alpine runtime, is filed as its own issue rather than fixed on this
  branch.
