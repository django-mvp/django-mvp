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
