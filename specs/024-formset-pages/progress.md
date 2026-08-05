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
- `tasks.md` carries three further convergence tasks (T041–T043: stylesheet rebuild,
  simplification pass, full machine gate). They belong to S5 and are driven by the pipeline, not
  by a story, so they are deliberately absent from the story ledger.
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
