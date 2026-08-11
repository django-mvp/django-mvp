# FS-025 — progress

## Gates

- **Spec gate: APPROVED** by Sam, 2026-08-11, in session, with two rulings applied before S3 began.
  - Surface reviewed: epic #194 (body + five story sub-issues #210–#214), `spec.md`, `decisions.md`, draft PR #215.
  - Machine gate at S2 exit: `forge check-issue-titles --repo django-mvp/django-mvp --epic 194 --num 025` green.
  - **Ruling 1 (confirmation)**: the `inline_*` attributes are removed outright. The two configuration surfaces never coexist and no compatibility shim is written. Already FR-020; restated in the Clarifications so it cannot be read as an omission.
  - **Ruling 2 (correction)**: behavioural parity with the removed attributes is not a requirement. This feature is an overhaul of the previous one. US-1's narrative, its independent test and its first acceptance scenario, SC-005, and Assumptions were amended. Recorded as D7.
- **Plan gate: promoted to a hard gate for this run** (Sam, 2026-08-11): "stop at the planning gate so I can review the plan before you implement." The pipeline's default is a veto notification that does not block. For FS-025 it blocks — S4 does not begin until Sam approves the plan.

## Stages

- S0 INTAKE — done. Issue #194 already existed as a `feature-request`; grilling accepted it and added `accepted`, removing `needs-approval`.
  - Grilling added scope the issue did not carry: the rows-only update page, folding django-extra-views' second view class into the same view class rather than shipping two. Create is excluded, since a page that never shows the parent's fields has nothing to create the record from.
  - Roadmap link settled with Sam: this extends R8 rather than opening a new item.
- S1 SPECIFY — done. `spec.md` (5 stories, 22 FRs, 6 SCs) and `decisions.md` (D1–D7). Clarify scan run in full: five questions, all self-answered, none escalated.
- S2 SETUP — done. Epic promoted in place, stories #210–#214 created with empty label sets, draft PR #215 opened bot-authored with the six-line `Closes` block, milestone v1.0.0 on the epic, every story and the PR.
- S3 PLAN — started 2026-08-11, after the Spec gate and the two amendments.

## Notes carried forward

- FS-024's Assumption limiting the configured view to one row set, and the intake clarification behind it, are struck and forward-tagged in place on `specs/024-formset-pages/spec.md` (D6). This lands in PR #215.
- FS-024's ledger was left with `state: PR_READY` and no merge record after PR #169 merged. The correction is committed on this branch, since it had been sitting uncommitted in the working tree.
- The local branch `024-multi-inline-wip` is a sketch of the shape and carries no authority over the spec. It is not merged, rebased or built on. Under D7 it is not a behavioural oracle either.
