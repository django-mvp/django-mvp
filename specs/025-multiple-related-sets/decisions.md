# FS-025 — decisions

Rationale too long to inline in `spec.md`, plus every ambiguity resolved without asking Sam.
Each entry states what was ambiguous, what was chosen, and why the choice is defensible.

## D1 — The default prefix is derived from the relation, not the model

**Ambiguous**: FR-004 in the first draft said each set's prefix is "derived by default and
overridable" without saying what it is derived from. That decides whether two sets on the same
related model are a configuration error, and the answer changes an acceptance scenario.

**Chosen**: the prefix Django's own `BaseInlineFormSet.get_default_prefix()` returns, which is the
reverse accessor name for the specific foreign key, with any `+` stripped.

**Why defensible**: read from Django's source in the project's own environment rather than
inferred. Because the accessor belongs to the relation, two declarations naming the same related
model through two different foreign keys already differ, and a developer never has to know the
rule to get a working page. Only two declarations on the *same* relation collide, which is the
case FR-005 turns into an error. Inventing a derivation from the model name instead would have
made the common two-relations case fail for no reason, and would have diverged from what
django-extra-views produces for the same configuration.

**ADR:** none — this is Django's own documented behaviour, not a decision this package made. Where it matters to a developer it is stated in [ADR 0007](../../docs/adr/0007-a-row-set-is-declared-as-its-own-class.md) and in the formsets guide.

## D2 — The view class names do not change

**Ambiguous**: the feature folds django-extra-views' two view classes into one and removes the
whole `inline_*` attribute surface. Whether `MVPInlineCreateView` and `MVPInlineUpdateView` keep
their names was not stated anywhere.

**Chosen**: keep both names.

**Why defensible**: the breaking change this feature ships is a configuration change. Renaming the
import as well would double the size of the rewrite a project has to perform, and the migration
note would have to carry two unrelated changes. "Inline" is also still the right word: it is
Django admin's word for exactly this idea, and the rows-only page is an inline page with the
parent's fields hidden rather than a different kind of page. Recorded as FR-024.

**ADR:** none — a migration-cost judgement, local to this release and recorded in the changelog where an upgrading reader will meet it.

## D3 — The declaration class is not an exhaustive parameter surface

**Ambiguous**: whether the declaration class should expose an attribute for every parameter
Django's formset factory accepts (`min_num`, `validate_min`, a custom base formset class, and so
on), or a smaller set with an escape hatch.

**Chosen**: the declaration carries what the six `inline_*` attributes carried, plus the prefix
and the relation name. Anything further is reached by overriding the method that assembles that
group of parameters and mutating the result.

**Partly superseded 2026-08-11 by [D11]**: the boundary is not "what the six attributes carried".
It is Django's own inline surface, which also includes `min_num`. `can_order` stays out, but for
its own reason rather than because this line drew the edge there.

**Why defensible**: this is the pattern the current view already documents and the pattern Django
itself uses for `get_form_kwargs`. It also matches django-extra-views, whose `factory_kwargs` and
`formset_kwargs` are dictionaries a subclass extends rather than a fixed attribute list. An
attribute per Django kwarg would grow the public surface this package has to keep compatible for
every parameter Django ever adds, against constitution Article II. Recorded as FR-020.

**ADR:** docs/adr/0007-a-row-set-is-declared-as-its-own-class.md — graduated as part of the declaration's surface, which is what downstream inherits.

## D4 — The spec uses the repository's glossary, not the issue's wording

**Ambiguous**: the tracking issue says "related set"; `CONTEXT.md` defines **row set** and
**related row** for the same things. Using both would leave the spec and the code disagreeing with
the glossary.

**Chosen**: `CONTEXT.md`'s terms throughout, with a one-line note in the spec saying the issue's
phrase means the same thing. The declaration class itself has no glossary entry, so the feature
adds one rather than introducing an undefined term.

**Why defensible**: the repository glossary is canonical by constitution Article VI, and a spec
that invents a synonym for a defined term is how the glossary rots. Keeping the issue's phrase
visible once means a reader arriving from #194 is not left guessing.

**ADR:** none — a house-style ruling about this repository's glossary, with nothing downstream inheriting it.

## D5 — The row cap keeps FS-024's enforcement, per set

**Ambiguous**: whether a page carrying several sets changes what a cap means — in particular
whether the cap could be read against the page's total row count, and whether the ceiling
decision FS-024 arrived at still holds.

**Chosen**: each set's cap is enforced on its own slice of the submission and never against a
page-wide total, using the enforcement FS-024 settled: reject a submission above the cap, and
leave Django's absolute ceiling at its default so a submission that is within the cap after
removals is accepted rather than silently truncated.

**Why defensible**: a cap is declared on a set, so reading it against a page total would mean a
number declared in one place constraining something else. The enforcement itself is not reopened:
FS-024 recorded it as D25 after a design-review round demonstrated that bounding the absolute
ceiling to the cap plus extras rejects legitimate submissions, because Django reads the raw
submitted total before subtracting deleted rows. Recorded as FR-013.

**ADR:** docs/adr/0008-the-inline-pages-save-path-across-many-sets.md — carried into the restated save path, since the reasoning about the absolute ceiling is the part most likely to be undone by someone tidying up.

## D6 — FS-024's single-set assumption is annotated, not left standing

**Ambiguous**: FS-024's spec states, under Assumptions and in an intake clarification, that the
configured view covers one parent and one row set, and that the shape would be revisited when a
case appeared. That text is now wrong, and it is a landed spec.

**Chosen**: strike the superseded text in place on `specs/024-formset-pages/spec.md` and forward-tag
it to FS-025, landing in this feature's pull request. Nothing is deleted.

**Why defensible**: a landed spec is a record of what was decided when, so removing the sentence
would erase the decision rather than supersede it, and leaving it untouched would leave a reader
believing a limit that no longer exists. The strike-and-forward-tag form is the established
convention for this across the family.

**ADR:** none — an editorial rule about how superseded specification text is annotated, not an architectural decision.

## D7 — No compatibility shim, and no parity requirement

**Ruled by Sam at the Spec gate**, 2026-08-11, confirming one point and correcting another.

**Confirmed**: the `inline_*` attributes are removed outright. The two configuration surfaces
never coexist and nothing is written to accept both. FR-024 already said so; it is restated in
the Clarifications because a shim that keeps the old names working for one release is the obvious
thing to reach for, and it is refused rather than merely unmentioned.

**Corrected**: the first draft required behavioural parity with the removed attributes. US-1 said
the page "behaves exactly as it did before", its independent test judged the story by comparison
with what the old attributes produced, and SC-005 asked for a rewrite "with no behaviour lost".
That is wrong. This feature is an overhaul of the previous one, and the specification is the whole
of what the page must do. A difference from what the removed attributes produced is not by itself
a defect.

**Why it matters beyond the wording**: parity language written into a story becomes a test written
against the old implementation, and an implementer reading it would treat the removed code as the
oracle — which would have quietly preserved decisions this feature exists to revisit. Where the
specification is silent, the precedent is the packaged single-form pages, not the removed
attributes.

Amended in place: US-1's narrative, its independent test and its first acceptance scenario;
SC-005; and Assumptions.

**ADR:** none — a scope ruling for this release. Its outcome is in the changelog; nothing downstream inherits the reasoning.

## D8 — Design review, one round: nine findings applied

**S3R, 2026-08-11.** One reviewer, three lenses, against the specification, plan, research and task
list with no diff in existence. Verdict `request_changes`, nine findings, all `verified`. Reports at
`engineering-org/runs/django-mvp/025-multiple-related-sets/findings-design.json`.

Every remedy was checked against the finding's own evidence before being accepted, rather than
applied on the reviewer's say-so. Three were high.

- **ARCH-001** — looping `inlines` in `form_view.html` would have deleted FS-024's standalone
  formset case, which is documented in `docs/formsets.md`, rendered by the demo, and pinned by a
  test at `tests/test_views/test_edit.py:2091`. The plan declared that case out of scope while
  quietly removing it. Both variables now coexist: `formset` for the standalone page, `inlines` for
  the configured one. **Confirmed by reading the doc section and the test.**
- **ARCH-002** — moving the multipart decision to an ambient context flag breaks Article XI, the
  house rule that Cotton components are configured by attributes, and
  `tests/test_components/test_form_index.py:41`, which renders the component directly with a
  `formset` attribute and asserts the encoding. The decision stays on the component. The plan's
  Constitution Check row for Article XI was wrong and is corrected. **Confirmed by reading the
  test.**
- **SPEC-001** — the per-declaration `prefix` override had no assembly point and no test, so
  FR-004 would have gone unimplemented and, worse, FR-005's collision error tells the developer to
  set a prefix, which would have done nothing. Now wired in `get_formset_kwargs()` and tested in
  both directions. **Confirmed by reading the task list.**

The medium and low findings: the invalid-parent test could not have failed (`BaseFormSet.errors`
calls `full_clean()` on access, so the guard could be deleted with the test still green — the same
vacuous-test shape FS-024's review caught, and confirmed by reading Django's source); the
documentation sweep both missed `docs/views.md` and would have rewritten ADR 0005 and a released
changelog entry, which are records rather than guidance; a set declared with `exclude` on a model
that reaches the parent twice renders the sibling relation as an unfiltered parent chooser, which
is a documentation fix rather than a code one; formset media were dropped when the variable became
a list.

Two findings **removed** work rather than adding it, which is the asymmetry that keeps this stage
cheap:

- **ARCH-003** — `min_num`, `can_order` and `validate_min` were unrequested public surface, outside
  both D3's stated boundary and the prior art's. Dropped from the shorthands; both remain reachable
  through `factory_kwargs`, which is what FR-020 says the escape hatch is for.
  **Half reversed 2026-08-11 by [D11]**: `min_num` and `validate_min` come back, because the
  boundary D3 drew was itself wrong. `can_order` stays out. The finding was right that the three
  had no stated demand behind them and wrong to treat them as one decision — they were adjacent in
  a list, not related to each other.
- **ARCH-004** — the memoisation rationale inherited from FS-024 is false. A rebuilt formset is
  bound to the same POST data and re-renders the same values and errors, so the page does not
  "come back blank". The memoisation is kept for the reasons that do hold; the false one is
  removed, because a fence with a wrong reason on it is a fence someone later removes after
  checking.

The reviewer separately checked and cleared three things rather than flagging them: the row-cap
decision still holds for several sets, row-id hijacking across sets is closed by Django's
parent-scoped queryset, and the rows-only page's authorisation is the same `get_object()` scoping
the single-form pages already use.

**Design-review budget: 1 of 1 used.** The reviewer was not re-dispatched on the fixes.

**ADR:** none — a record of one review round and its dispositions, local to this run.

## D9 — The surface is named after Django, not after its prior art

**Sam's ruling at the plan gate**, 2026-08-11, overturning the naming premise the spec and research
were built on.

The first draft justified its choices by asking whether a developer arriving from django-extra-views
would find the names where they expected them. That is the wrong question. That package is not
widely enough used to be owed compatibility, and the people this surface has to be legible to are
Django developers, who already know `django.contrib.admin`'s inlines.

**Chosen**: name everything after Django's own. The declaration class is `InlineFormSet`, its
options are admin's attribute names — which are also `inlineformset_factory`'s parameter names — and
where the two sources disagree Django wins. `title` and `description` stay ours, because admin's
`verbose_name_plural` covers only half of what they do.

**The research had this backwards and is corrected in place.** R7 previously described `extra`,
`max_num`, `can_delete` and `fk_name` as a "deliberate divergence from django-extra-views" needing
justification. They are Django's names, present both on `InlineModelAdmin` and in the factory
signature; the other package is the one that removed them. An entry that asks for a justification
that was never owed is worse than no entry, because the next reader inherits the false premise.
`InlineFormSetFactory` goes the same way — the class declares a set, it does not manufacture one,
and "Factory" was borrowed rather than chosen.

The prior art keeps its place: the `factory_kwargs`/`formset_kwargs` split is a good idea and is
taken. Read it for ideas, not for names.

**ADR:** docs/adr/0007-a-row-set-is-declared-as-its-own-class.md — graduated. This is the decision that governs every name in the public surface, so it is the one a later reader most needs to find.

## D10 — The rows-only page touches the parent's timestamp, and never saves its form

**Sam's ruling at the plan gate**, and the first draft was wrong about the requirement.

FR-015 originally said the page must leave the parent's stored values unchanged, full stop. Sam's
case is that a record and its related rows are one thing to a reader: a project whose description
changed should show as having changed. Leaving no trace is the surprising outcome, not the safe one.

**Chosen**: the page records the change on the parent's own last-modified timestamp, on by default,
switchable off on the view. But **not** by saving the empty parent form, which is the obvious
implementation and a data-loss bug. Three measurements against the project's database (R12):

- `save(update_fields=[<auto_now fields>])` bumps the timestamp;
- it leaves a concurrent write to other fields intact;
- a full `save()` — what an empty `ModelForm.save()` does — **discards that concurrent write.**

An empty model form is always valid and writes every column from values read when the page was
opened, so the naive version silently loses whatever changed in between. That risk is worst on
exactly this page: a long-lived editing screen for a shared record.

**Why the default is on**: a model with no `auto_now` field has nothing to write, so the feature is
a no-op there. It acts only where the developer has already declared, by putting such a field on the
model, that they care when the record last changed. That bounds it to the case that asked for it.

Two consequences stated rather than left to be discovered: the touch happens inside the rows'
transaction, and it fires the model's save signals and any lifecycle hooks. Both are intended — a
parent-level "something changed" is not observable otherwise — but neither is silent.

**ADR:** docs/adr/0009-a-rows-only-page-touches-the-parent-rather-than-saving-it.md — graduated, with the measurements, because the obvious implementation loses data and someone will reach for it.

## D11 — `min_num` is in, `can_order` is not, and display order is a third thing

The S3R round dropped `min_num`, `can_order` and `validate_min` together as unrequested surface
(ARCH-003). Half right. They were adjacent in one list and were treated as one decision, which they
are not.

- **`min_num` is in**, with `validate_min` paired to it for the same reason `validate_max` pairs
  with `max_num`: Django's factory defaults both to `False`, so a bound that is not validated
  rejects nothing. Recorded as FR-023.
- **`can_order` is out for now.** It is a user-facing feature — an `ORDER` field on every form so a
  person can reorder rows — and nothing asks for it. It remains reachable through `factory_kwargs`.
- **Display order is neither of those**, and is what was actually wanted: the developer deciding the
  sequence forms appear in, so a set renders in a meaningful order rather than "rows already saved,
  then blanks". It is a method, `sort_forms`, and it is **display only** — reordering the sequence a
  formset validates or writes in would change which submitted row maps to which record. Recorded as
  FR-022, with a test that pins the saved order as unaffected.

**ADR:** docs/adr/0007-a-row-set-is-declared-as-its-own-class.md — graduated as part of the surface; the ADR states why `can_order` is absent and where it remains reachable.

## D12 — Per-form keyword arguments use Django's signature

**Ambiguous**: whether one dictionary of form keyword arguments per set is enough.

It is not. A set that shows one form per permitted kind needs each form to know which kind it is; a
set that validates a row against its siblings needs each form to know what the others hold. Neither
is reachable when every form gets the same dictionary.

**Chosen**: the declaration exposes `get_form_kwargs(index)` — Django's own signature, where `index`
identifies the form and is `None` for the blank template form the browser clones to add a row. The
shared `form_kwargs` attribute stays as the default for the common case.

**Why defensible**: Django has carried this hook since 1.9 and calls it once per form from
`_construct_form`. What hides it is the prior art's `get_form_kwargs(self)`, with no index, whose
result is merged into a single shared dictionary — so a project needing per-form arguments has to
reach around the surface it is using and subclass the formset directly, ending with two APIs for
one job on the same page (R13). Taking Django's signature is a one-parameter difference and it is
the whole of what makes the requirement reachable.

**Scope**: this feature owes the hook and the display order. Building a set whose forms are derived
from a list of permitted kinds — one form per kind, present or not — is a thing a project assembles
on top, using this hook plus the formset's own initial data. Agreed with Sam; it does not come into
this package.

**ADR:** docs/adr/0007-a-row-set-is-declared-as-its-own-class.md — graduated as part of the surface, including why the hook takes an index.

## D13 — US1's tamper flags are approved; the regressions they hid are not

`forge tamper-check` flagged two pre-existing test files modified in US1: `tests/factories.py` and
`tests/test_views/test_inline.py`. Both are approved. FR-024 removes the `inline_*` attributes
outright, so the file that tested them has no honest way to survive unchanged, and `factories.py`
gains the fixtures the new tests are built on. Nothing was weakened — the file grew from 525 to
just over a thousand lines and every removed assertion targeted an attribute that no longer exists.

What the flags did not cover, and what mattered more: `T024` deleted the mixin without migrating
its two consumers outside the story's file scope. `demo.ProductOrderLinesView` kept declaring
`inline_model`/`inline_fields`/`inline_extra`, which nothing reads any more, so the worked example
docs walk through silently rendered no rows at all. `tests/test_components/test_form_formset.py`
reached the same surface through a helper imported across files, and the story repointed that
helper at its own fixtures rather than migrating the caller — leaving five tests red that were
green at the branch point. The story's report classified all five as pre-existing; they were not.
Repaired in `842b75b`: the demo view declares an `OrderLineInline`, the component tests build their
own local view class over `Product`/`OrderLine`, and the cross-file helper import is gone.

**The rule this earns:** deleting a public attribute is not scoped to the file that defines it. A
removal task owns every live consumer in the repo, and a story that ends red has to prove the red
predates it — `git checkout <base> -- <paths>` and re-run is one command.

**ADR:** none — a run-level triage record and a working rule for implementers. The rule belongs in the org's own method notes rather than in this repository's architecture record.

## D14 — US2's tamper flag is a file-granularity false positive

`forge tamper-check` flagged `tests/test_views/test_inline.py` again. This time the flag carries no
information: the diff against the branch point is `436 insertions, 0 deletions`. Every US2 test is a
new class appended below the US1 material, and nothing pre-existing was touched. The check reports
at file granularity, so any addition to a file that held tests at `--base` raises it.

Worth knowing for the remaining stories, since US3, US4 and US5 all append to this same file: a flag
on a purely additive diff is not a triage event. `git diff --numstat <base>..HEAD` settles it in one
command, and a nonzero deletion count is the thing that actually warrants reading.

US2 also confirmed something the plan predicted but had not proven. Only `T029` needed production
code — the prefix-collision guard. The loop, the single transaction, the validate-everything-first
pass and per-set formset construction that US1 built for one set already generalise to many, which
is why eleven of the thirteen new tests were green on first run. Verified rather than accepted: the
production change was reverted against the US2 tests, and exactly the two collision tests went red.

**ADR:** none — an observation about a tooling check's granularity, with no bearing on the package's design.

## D15 — the surface rewrite dropped three landed guards, restored at US3

US3's own work held up. Its report claimed one of five tasks needed no production code, and the
revert probe confirms it: with `form_invalid` removed, exactly two of the new tests go red and the
other 56 stay green, T037 among them. Its test for the parent-invalid path reads `formset._errors
is not None` rather than `formset.errors`, which is right — both `errors` and `non_form_errors`
validate on access, so an assertion against either passes whether or not the view validated
anything. The tamper flag on the test file is D14's shape again: 147 insertions, 0 deletions.

What US3 surfaced by accident is the more interesting finding. T041 re-reads `self.object` before
redisplaying, which is the fix that landed on `main` as PR #195 (issue #193) on 2026-08-10 — and it
had to be written again because US1's `T001` replaced every class in
`tests/test_views/test_inline.py`, dropping that regression test, and US1's rewrite of `inline.py`
dropped the guard it protected. The feature branch carried the #193 defect from US1 until US3
happened to specify the same behaviour from the spec side. Nothing caught it in between.

Comparing class names between `origin/main` and the branch finds two more with no replacement:

- **The single transaction under a save-time failure** (FR-009, SC-002). The branch's remaining
  atomicity test uses a row that fails *validation*, which never enters the transaction at all, so
  it cannot distinguish wrapped writes from merely ordered ones. Restored and probed: replacing
  `transaction.atomic()` with a null context turns it red on the parent's changed name.
- **The remove control.** A submitted `DELETE` flag deleting an existing row, and creating nothing
  for a row added and removed in the same submission — the count FR-013 excludes from a cap.

A third, weaker gap: the create page refused by its own parent form. US3 covers the update path;
create is where `self.object` is `None` throughout. Restored too.

**The rule this earns:** Sam's ruling that this feature is an overhaul, not a port, licenses a
difference in *behaviour* from what the removed attributes produced. It does not license dropping
coverage of behaviour the new spec still requires. When a story replaces a test file wholesale,
diff the class names against the base and account for every one that disappears — a rename is fine,
an absence needs a replacement or a reason. `git show <base>:<path> | grep '^class '` against the
same grep on the branch is the whole check, and it would have caught the #193 regression on the day
US1 landed.

**ADR:** none — a record of guards dropped and restored during the rewrite. The guards themselves are tests in the repository; the incident is a run record.
