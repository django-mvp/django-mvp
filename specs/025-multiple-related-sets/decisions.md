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

## D2 — The view class names do not change

**Ambiguous**: the feature folds django-extra-views' two view classes into one and removes the
whole `inline_*` attribute surface. Whether `MVPInlineCreateView` and `MVPInlineUpdateView` keep
their names was not stated anywhere.

**Chosen**: keep both names.

**Why defensible**: the breaking change this feature ships is a configuration change. Renaming the
import as well would double the size of the rewrite a project has to perform, and the migration
note would have to carry two unrelated changes. "Inline" is also still the right word: it is
Django admin's word for exactly this idea, and the rows-only page is an inline page with the
parent's fields hidden rather than a different kind of page. Recorded as FR-020.

## D3 — The declaration class is not an exhaustive parameter surface

**Ambiguous**: whether the declaration class should expose an attribute for every parameter
Django's formset factory accepts (`min_num`, `validate_min`, a custom base formset class, and so
on), or a smaller set with an escape hatch.

**Chosen**: the declaration carries what the six `inline_*` attributes carried, plus the prefix
and the relation name. Anything further is reached by overriding the method that assembles that
group of parameters and mutating the result.

**Why defensible**: this is the pattern the current view already documents and the pattern Django
itself uses for `get_form_kwargs`. It also matches django-extra-views, whose `factory_kwargs` and
`formset_kwargs` are dictionaries a subclass extends rather than a fixed attribute list. An
attribute per Django kwarg would grow the public surface this package has to keep compatible for
every parameter Django ever adds, against constitution Article II. Recorded as FR-019.

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

## D7 — No compatibility shim, and no parity requirement

**Ruled by Sam at the Spec gate**, 2026-08-11, confirming one point and correcting another.

**Confirmed**: the `inline_*` attributes are removed outright. The two configuration surfaces
never coexist and nothing is written to accept both. FR-020 already said so; it is restated in
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
  both D3's stated boundary and upstream's. Dropped from the shorthands; both remain reachable
  through `factory_kwargs`, which is what FR-019 says the escape hatch is for.
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
