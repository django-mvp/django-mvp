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
- S3 PLAN — done. `plan.md`, `research.md` (R1–R11), `tasks.md`, `feature-state.json`. Constitution Check passes with one recorded justification (the shorthand attributes diverge from upstream 0.16 — research R7). No Complexity Tracking entry.
- S3R DESIGN_REVIEW — done, one round, budget 1 of 1. One reviewer, three lenses, no diff in existence. Verdict `request_changes`, nine verified findings, three of them high. All applied; every remedy checked against the finding's own evidence before acceptance; the reviewer was not re-dispatched. Craft-skill gate green both ways. Recorded as D8.
  - The three high findings were all real defects in the plan, not preferences: the template change would have silently deleted FS-024's standalone formset case, the multipart change would have broken Article XI and an existing component test, and FR-004's prefix override had no assembly point — which would also have made FR-005's error message suggest a fix that did nothing.
  - Two findings removed work: `min_num`/`can_order`/`validate_min` were unrequested surface, and the memoisation rationale inherited from FS-024 turned out to be false (the fence stays, its stated reason is corrected).
  - Task ids renumbered in the re-plan. 51 story tasks across five stories, plus three convergence tasks driven by the pipeline.
- **Plan gate, round 1 — changes requested** (Sam, 2026-08-11). Four rulings, all of which change the specification rather than only the plan, so this is a spec amendment and the gate re-runs.
  - **Naming** (D9). Stop justifying the surface against django-extra-views and name it after Django's own: `InlineFormSet`, admin's attribute names, `form`/`formset` rather than `form_class`/`formset_class`. The research had the argument backwards — the shorthand attributes it defended as a "divergence" are Django's own names, and that package is the one that dropped them. R7 rewritten in place.
  - **Parent timestamp on the rows-only page** (D10). The page records that its rows changed on the parent's own last-modified field, on by default, switchable off. Measured rather than assumed: saving the empty parent form — the obvious implementation — discards a concurrent write to the parent's other fields, so the touch writes only the `auto_now` fields instead. Recorded as R12 with the three probe results.
  - **`min_num` back, `can_order` still out, display order separate** (D11). The design review dropped all three together as unrequested surface; they were adjacent in a list rather than one decision.
  - **Per-form keyword arguments** (D12). Django's `get_form_kwargs(index)` signature, not a shared dictionary. This is what the prior art's no-index variant makes unreachable.
- **Plan gate: APPROVED** by Sam, 2026-08-11, in session, with one refinement: the set's heading defaults to the related model's `verbose_name_plural`. The attribute keeps the name `title`, so the admin name is where the default comes from rather than what the option is called. Recorded in FR-011, R7 and the plan.
- S4 IMPLEMENT — starting.

## Amendment, 2026-08-11 (plan gate round 1)

Spec: 22 FRs → 26, 6 SCs → 7. New FR-016 (parent timestamp), FR-021 (per-form arguments), FR-022 (display order), FR-023 (minimum rows); FR-002 and FR-015 rewritten; FR-016 onward renumbered, with every reference in the plan, task list, research and decisions remapped. US1 gained three scenarios, US4 gained two. Tasks 51 → 59 story tasks, ids renumbered.

The design review ran against the pre-amendment plan. Its nine findings all still stand and are all still applied, but three areas it did not see are new: the per-form kwargs hook, the display-order hook and the parent touch. The touch is the one carrying real risk, and its concurrency test is written to fail against the naive implementation.

## Notes carried forward

- FS-024's Assumption limiting the configured view to one row set, and the intake clarification behind it, are struck and forward-tagged in place on `specs/024-formset-pages/spec.md` (D6). This lands in PR #215.
- FS-024's ledger was left with `state: PR_READY` and no merge record after PR #169 merged. The correction is committed on this branch, since it had been sitting uncommitted in the working tree.
- The local branch `024-multi-inline-wip` is a sketch of the shape and carries no authority over the spec. It is not merged, rebased or built on. Under D7 it is not a behavioural oracle either.
