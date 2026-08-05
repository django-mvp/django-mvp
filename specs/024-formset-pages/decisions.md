# Decisions — 024 Formset Pages

Rationale too long to sit inside `spec.md`, plus every ambiguity resolved without asking. The
spec stands alone; this file explains why it says what it says.

## D1 — The feature owns the view, not only the rendering

**Ambiguous because** the roadmap item lists rendering first and the parent-and-rows case second,
which reads as a template feature with a note attached.

**Chosen**: the feature packages a configured view as well as the rendering components.

**Why defensible**: the package's whole model-to-pages story is view configuration. A developer
reaches a working create page by configuring `MVPCreateView`, not by assembling templates. A
formset feature that stopped at rendering would leave that developer writing the one piece the
package exists to remove — building the formset, validating it against the parent, and saving the
two in the right order inside a transaction. The tracking issue asks for a page that behaves "the
way the single-form pages already do", and the single-form pages are views.

## D2 — Rendering is generic, the view is not

**Ambiguous because** the same item asks both for "a form page that renders a formset" (any
formset) and for "a parent object edited alongside its related rows" (one specific shape).

**Chosen**: the rendering component takes any formset and works anywhere the packaged form
components work. The configured view covers a parent with one related set.

**Why defensible**: the two halves have different reasons to exist. Rendering is generic because a
formset is a formset — presentation does not care whether a parent exists. The view is specific
because its value is the decision it makes for the developer, and that decision (validate together,
save atomically, attach rows to a parent that may not exist yet) only has content in the
parent-and-rows case. A standalone formset needs no such decision: it goes on the existing form
view and is saved by the developer's own `form_valid`. Packaging a second view for it would be
machinery with no problem behind it.

## D3 — One related set, not many

**Ambiguous because** nothing in the issue or the roadmap says how many related sets a page may
have, and real pages sometimes have two.

**Chosen**: the configured view packages exactly one. Two remain buildable by composing the
rendering components.

**Why defensible**: designing a collection API — how sets are named, ordered, validated against
each other, and reported in errors — against a case that has not appeared is the kind of
speculative generality Article III forbids. The single-set case is what both the roadmap and the
issue describe. Widening later is additive and cheap; narrowing a shipped collection API is not.
Sam agreed the boundary at intake in these terms: start simple, revisit when there is a case.

## D4 — Deletion is deferred to submission

**Ambiguous because** "remove a row" has two coherent readings for a row that already exists: take
it out of the database now, or mark it and act on submission.

**Chosen**: mark and act on submission. An unsaved row is simply dropped from the page and the
management form's count adjusted.

**Why defensible**: this is what Django's own formset machinery is built for — `can_delete` puts a
deletion flag on each row precisely so the decision travels with the submission — and it is what
every established dynamic-formset implementation does. It also keeps the page one thing. Deleting
on click would make a page that otherwise commits nothing until submit start issuing destructive
requests mid-edit, with no undo, and would break the guarantee the whole feature rests on: one
submission, all or nothing. Sam's instruction at intake was to follow standard practice, and this
is what standard practice is.

## D5 — django-crispy-forms and crispy-tailwind become declared dependencies

**Ambiguous because** roadmap item R12 frames the packaged form rendering's reliance on
django-crispy-forms as a defect to be removed, with form pages falling back to "a reduced but
working level of polish" when it is absent. Read that way, this feature would have had to render
formsets without it.

**Chosen**: declare both distributions as runtime dependencies. `c-form.render` loads
`crispy_forms_tags` and `tailwind_filters`, which come from django-crispy-forms and crispy-tailwind
respectively, so both are needed for the template as written.

**Why defensible**: Sam's ruling at intake, and the reasoning holds independently. The package has
called into crispy since form rendering existed. What was wrong was the metadata, not the design —
a project that installs django-mvp as documented and renders a form gets a template error today,
and no amount of guarding makes an undeclared dependency correct. Article VII asks for a stated
justification for a new runtime dependency, and the justification is that this is not a new
dependency, only a newly honest one.

**Consequence for R12**: its first deliverable is now wrong for the form half. R12 keeps the
list-page case, the unguarded module-level import in a view module, and the documented-but-absent
form renderer setting. The roadmap text needs the corresponding correction, and this feature is
where the supersession is recorded.

## D6 — Atomicity is a requirement, not a database assumption

**Ambiguous because** a spec can treat "the parent and its rows save together" as something the
database provides rather than something the feature must arrange.

**Chosen**: FR-011 states it as a requirement on the feature, and SC-006 measures it.

**Why defensible**: it does not happen by itself. A view that saves the parent, then saves the
rows, produces a half-saved page the moment a row fails a database constraint — an order with no
line items, created by a user who thought they had cancelled. The page's entire premise is one
submission, and one submission that half-applies is worse than two that do not, because the user
has no way to see what happened.

## D7 — No per-row permission surface

**Ambiguous because** a page that edits several records could plausibly ask whether the user may
edit each one.

**Chosen**: none. The page behaves for permissions exactly as the packaged single-form pages
behave.

**Why defensible**: the rows belong to the parent, and the parent's own permission check is the
question the page is already asking. A per-row model is a genuinely larger design — it needs a
policy for a row the user may read but not change, and a presentation for it — with no case behind
it in either the issue or the roadmap. Adding a permission surface speculatively is worse than
adding none, because a half-designed one reads as a guarantee.

## D8 — The worked example lives against the demo application

**Ambiguous because** the package ships no models of its own, so a model-to-page example has
nothing to be written against inside the package.

**Chosen**: the demo application, as with the package's other model-to-pages documentation.

**Why defensible**: it is the existing convention, the demo models already carry the relationships
this feature needs, and Article IX explicitly extends the data-model conventions to `demo/`. An
example against invented models in prose cannot be executed, and an example that cannot be executed
is the documentation failure R20 exists to fix.

## D9 — Rulings inherited from the roadmap decomposition, and the one that was reversed

Two decisions were made when R8 was turned into a feature request, before this spec existed.

**Carried forward.** Adding and removing rows uses Alpine, not hand-written JavaScript. The
packaged base template already loads Alpine 3 and its sort plugin, and the form component already
carries an Alpine root, so the mechanism is present and a second one would be a second thing to
maintain. This is a constraint on the plan rather than on the requirements, which is why it appears
here and in the spec's assumptions rather than as a functional requirement.

**Reversed.** The decomposition recorded that django-crispy-forms would become a *guarded
integration* and that the work belonged to R12, not here. Sam reversed both at this feature's
intake: crispy-forms and crispy-tailwind become plain declared dependencies, and they are declared
in this feature. The reasoning is in D5. The earlier position is not deleted, because it explains
why R12's first deliverable is now written against a scope it no longer has.

---

*Decisions below were taken at planning (S3). Rationale in full lives in `research.md`; this
section is the record and the ADR-verdict surface.*

## D10 — The packaged component renders the set, crispy renders the fields

`|crispy` accepts a formset and switches to `<pack>/uni_formset.html`, so the shortest possible
route existed. It is not taken. crispy-tailwind's formset template never renders
`formset.non_form_errors`, which would silently drop every set-level error and violate FR-018,
and its sibling error templates emit raw utility colours rather than DaisyUI classes, which
Article XI forbids in a component template.

Instead `<c-form.formset>` owns the structure — management form, rows, set-level errors, the
blank-row template, the controls — and each row's fields go through `|as_crispy_field`, which is
the same `tailwind/field.html` a single form's fields go through. That identity is what makes
SC-008 true rather than approximately true, and it means FR-016 is satisfied by a template this
repository does not own, so the first task of that story is a test proving it.

**Why defensible**: the alternative was overriding a vendored template at `tailwind/`, which
would have produced a component invisible to `test_render_all.py`, unreachable by a consumer's
`cotton/` override, and in breach of Article XI's rule that reusable markup is a Cotton component.

## D11 — Removal is uniform; indices are never re-numbered

Removing a row sets Django's `DELETE` flag and hides the row, whether the row is saved or not.
`TOTAL_FORMS` is incremented when a row is added and never decremented.

Django already separates the two cases: `save_new_objects` skips extra forms marked for deletion,
and `save_existing_objects` deletes the saved ones. The page therefore sets one flag and lets
Django decide what it means. Not decrementing is the load-bearing half — Django reads submitted
rows by contiguous index, so removing a row from the middle and decrementing shifts every later
row onto the wrong index.

**Why defensible**: re-indexing is the standard source of off-by-one defects in hand-written
formset pages, it requires rewriting every `name`, `id` and `for` attribute in the surviving
rows, and it buys nothing the `DELETE` flag does not already give. It also makes the invalid-
resubmit edge case fall out for free, since the removal was submitted like any other value.

## D12 — No new page template, and no second view for the standalone case

`form_view.html` gains a `{% block formset %}` whose default content renders `<c-form.formset>`
when a `formset` is in context. Any packaged form view that supplies one gets it rendered in the
right place, which covers US2 scenario 4 and FR-006 without a second configured view, and leaves
the US3 view with no template of its own.

A dedicated `inline_form_view.html` was written into the first draft of this plan and removed:
it carried one line and left the standalone case unsolved.

**Why defensible**: Article II. The block sits where `{% block actions %}` already sits, so the
pattern is the one the template already uses.

## D13 — `<c-form>` learns about the formset, for one reason

`<c-form>` decides the form's `enctype` from `form_obj.is_multipart` alone. A file field on a row
would therefore submit without the multipart encoding, which is the edge case the spec names. The
component gains an optional `formset` attribute consulted in the same condition, and nothing else.

**Why defensible**: the narrowest change that closes a real defect. Widening `<c-form>` to render
the formset itself was rejected because the actions must follow the set, and the slot cannot
express that ordering.

## D14 — The view lives in its own module

`mvp/views/inline.py` holds `InlineFormsetMixin`, `MVPInlineCreateView` and `MVPInlineUpdateView`;
tests mirror it at `tests/test_views/test_inline.py`. Article X permits either placement, so the
choice is cohesion: `mvp/views/edit.py` already carries four view classes across roughly six
hundred lines, and the parent-and-rows page is a distinct concern with its own configuration
surface. "Inline" is Django's own word for a formset bound to a parent through a foreign key.

The configuration is six class attributes for the common cases plus `get_formset_factory_kwargs()`
for everything else, rather than one attribute per Django parameter.

**Why defensible**: Article XVII wants related behaviour grouped on a class with an extension
point, and Article III wants no layer between the caller and the work. One mixin with hooks is
both. The mixin is not exported, matching the rule already stated in `mvp/views/__init__.py`.

## D15 — `get_formset()` memoises, deliberately

The formset is built once per request and reused. `form_invalid` re-renders through
`get_context_data`, and constructing a second formset there would discard the bound one carrying
the user's values and its errors — the page would come back blank and FR-013 would fail.

**Why defensible**: it is a correctness requirement disguised as a performance detail, which is
why it is recorded rather than left to an implementer to rediscover.

## D16 — A startup system check for the crispy apps was declined

Installing the two distributions is not sufficient: Django resolves template tag libraries only
from apps in `INSTALLED_APPS`, so a consumer who installs and does not configure still meets a
`TemplateSyntaxError`. A Django system check would turn that into an actionable startup error.

It is not built. No requirement asks for it, and a check is a public surface of its own needing an
id, documentation and a CHANGELOG entry. The documented setup in README and
`docs/getting-started.md` carries the requirement instead.

**Why defensible**: Article II, and scope. If the failure recurs in the wild it is a small,
well-shaped issue of its own rather than something smuggled into this feature.

---

*Decisions below came out of the S3R design review (2026-08-05). Three lenses ran in parallel —
spec-compliance, security, architecture — against the plan before any code existed. All three
returned `request_changes`, and every accepted finding is applied in the re-plan. The full reports
are archived with the run record.*

## D17 — `inline_max_num` is enforced on the server, not only in the browser

The plan passed `inline_max_num` to Django as `max_num` and had the add control stop at it.
`inlineformset_factory` defaults `validate_max=False`, so `max_num` alone rejects nothing: a view
configured for three rows would have accepted and saved a submission carrying a thousand.
`get_formset_factory_kwargs()` now sets `validate_max=True`, and bounds `absolute_max` to the cap
plus the extras rather than leaving Django's `max_num + 1000`.

The second half is the part that is easy to miss and is not about validity. `full_clean` constructs
and validates every submitted form *before* it reaches the too-many-forms check, so with the
default bound a single request can force a thousand form constructions and a thousand primary-key
lookups while holding a write transaction open. `absolute_max` is what bounds the work.

**Why defensible**: the spec's own edge case says the add control stops "rather than adding a row
the submission will reject", which assumes a rejection the design had not arranged. A cap a
consumer sets and reasonably believes binds is a design property, not a documentation one.

## D18 — The set carries two counters, not one

`total` is monotonic and seeds `__prefix__` and `TOTAL_FORMS`. `visible` counts rows not marked for
removal and is what the add control compares against the cap. With one counter, removing a row on a
capped set would permanently forfeit its slot — the page would refuse a replacement the submission
would happily accept, since Django tests `total_form_count() - len(deleted_forms) > max_num`.

`total` is seeded from `{{ formset.total_form_count }}`, never from the management form's DOM value.
That value is a string the server re-emits verbatim after an invalid submission, and substituting it
into cloned markup would put a user-supplied string into a new row's `name` and `id` attributes. The
template variable is an integer Django has already clamped.

**Why defensible**: D11's "never decrement" is about the index Django reads rows by, and it stays.
It was never a statement about what the add control should count, and collapsing the two into one
number is what created the defect.

## D19 — The success message is produced outside the transaction

`super().form_valid()` reaches `SuccessMessageMixin`, and Django's message storage is not
transactional. A flash queued inside the atomic block survives the rollback, so a request that
persisted nothing would still tell the user the record was saved. The transaction wraps the parent
save and the formset save, and nothing else; the message and the redirect follow it.

**Why defensible**: FR-011 and SC-006 are about what persists, and a lie in the interface is a
failure of the same requirement by a different route.

## D20 — The browser test lives with the components, not in a new directory

The plan created `tests/test_e2e/` and its own Constitution Check then claimed no new
`non-mirror-path` was declared. Both cannot be true. The browser test moves into
`tests/test_components/test_form_formset.py` as its own class, with the `e2e` marker and the
playwright `skipif` at class level.

The separate module had been justified as protection against a module-level `pytestmark` hiding
unit tests. The task always specified a class-level marker, which does not do that, so the module
was solving a problem the plan had already avoided. `tests/test_views/test_error.py` sets the
precedent.

Its coverage grew by one case: **removing the row that was just added**. An added row is a clone of
the `<template>` content, and cloned markup appended into a live Alpine tree is inert until it is
initialised — so its remove control can do nothing while every markup and view test stays green.
That is the one behaviour no server-side test can reach, which is the only justification Article XIV
accepts for a browser test at all.

**Why defensible**: it removes a directory, removes a conformance declaration, and repairs a false
statement in the Constitution Check, while making the remaining test cover the case that needed a
browser.

## D21 — Two test gaps the plan had left

**A valid parent with an invalid row.** The plan tested the reverse and not this. It is the branch
`form_valid` adds: without it, the formset-validation guard could be deleted and every other test in
that story would still pass. FR-010 and the spec's edge case both name it.

**Errors on more than one row.** FR-019 and US4 scenario 3 require every affected row to carry its
own message; the task tagged with FR-019 asserted only the single-error case.

**Why defensible**: a requirement with no test that would fail if the behaviour regressed is not
delivered, whatever the task list says.

## D22 — Three corrections to the plan's own claims

- **`docs/ROADMAP.md` R12 gets a task.** The spec's Assumptions and D5 both commit this feature to
  correcting R12's framing, and no task did it. The annotation lands in this pull request with the
  change that causes it.
- **`demo.OrderLine` needs Article IX work after all.** An earlier draft of R8 said it did not.
  Neither of its fields carries `verbose_name` or `help_text`, both are mandatory, and Article IX
  says explicitly that it applies to `demo/`. It matters beyond conformance: this is the pair the
  worked example renders, and a page demonstrating that a row's field gets the same help text as a
  single form's field cannot demonstrate it with a field that has none.
- **The dependency graph and the parallelisation note were wrong.** The story that builds the view
  asserts against rendered rows, so it depends on the story that puts rows on the page. The two
  stories that follow the component both edit the same template and cannot run concurrently. Both
  notes now name the file rather than the phase.

## D23 — Work the review removed, and the one thing it flagged that is not ours to fix

**Removed**: a task duplicating the render-smoke floor that already enrols every packaged component
automatically; a `legend` attribute on `<c-form.formset>` with no requirement behind it, which would
have invited an implementer to build it; and half of the view's configuration-error surface, since
Django's own `modelform_factory` already raises a clear `ImproperlyConfigured` when neither fields
nor a form class is given. The declared-dependency test also moved out of the module about guarded
optional integrations, and now parses `pyproject.toml` rather than installed distribution metadata,
which would not have changed when the fix landed.

**Not ours to fix here**: `mvp/templates/mvp/base.html` loads Alpine and its plugins from a public
CDN at `3.x.x` with no subresource integrity, which a floating range makes impossible anyway. Anyone
who compromises that package or its CDN path runs code in every consuming project's authenticated
pages. It predates this feature and two other script tags in the same block have the same shape, so
fixing it here would be a second feature wearing this one's branch. It is named in the plan's Risks,
the Constitution Check's Article V row is qualified rather than a bare PASS, and the remedy is filed
as issue #170 — the same treatment D16 gave the declined system check.

Writing it up corrected part of the finding. Only the three Alpine tags float at `3.x.x`, which is
what makes subresource integrity impossible for them rather than merely absent. `theme-change@2.0.2`
and `bootstrap-icons@1.13.1` are pinned to exact versions and are only missing an `integrity` hash,
which is a smaller problem and a cheaper fix — the icons stylesheet even carries `crossorigin`
without the hash it exists to accompany. The issue states that split rather than repeating the
reviewer's "same shape" aside. Checking a claim before publishing it is what caught this.

---

*Decisions below came out of the S3R design review's **second** round (2026-08-05). The
spec-compliance lens approved; the security lens returned one verified high finding against the
round-1 remedy itself. The design-review budget was exhausted, so the run escalated and Sam
authorised a second re-plan cycle rather than treating it as a spec failure.*

## D24 — This feature settles the whole of R12's undeclared-dependency deliverable, not half

**This one amends the approved spec**, which is why it is recorded here and struck through in
`spec.md` rather than quietly edited.

The spec's Assumptions reserved "the list-page dependency" for R12, on the reading that this
feature fixed only the form-rendering half. That reading was wrong on the facts. The list page and
the form page load the *same* distribution: `mvp/templates/list_view.html` loads
`crispy_forms_tags`, `mvp/templates/cotton/form/render.html` loads `crispy_forms_tags` and
`tailwind_filters`, and an exhaustive search of `mvp/templates/` finds no other third-party tag
library on either path. Declaring the distribution resolves both pages at once, so after this
feature there is no list-page half left to do.

Two further corrections ride with it. R12's "at a reduced but working level of polish" framing is
also settled, because crispy is no longer optional and there is nothing to degrade to. And the
deliverable in question is R12's **second**, not its first — the first is the general
guarded-or-declared rule, which stays.

R12 keeps the unguarded module-level import in a view module, the documented-but-absent form
renderer setting, and the check covering every optional dependency.

**Why defensible**: a roadmap item that still claims a defect the repository no longer has sends a
future feature looking for it. The original text is struck rather than deleted, because it records
why R12 was scoped the way it was.

## D25 — `absolute_max` stays at Django's default; the cap is enforced by `validate_max` alone

D17 said `get_formset_factory_kwargs()` should also bound `absolute_max` to the cap plus the
extras. That half is withdrawn. It was wrong, and the design review demonstrated it against this
project's own environment rather than arguing it.

Django's `absolute_max` check reads the **raw** submitted `TOTAL_FORMS` and, unlike the
`validate_max` check beside it, does not subtract the rows marked for deletion. So a user working
inside a cap of three who adds four rows and removes two submits five forms with two `DELETE`
flags — `validate_max` passes, because 5 − 2 = 3, and a cap-derived `absolute_max` rejects it
anyway. Worse, `total_form_count()` clamps to `absolute_max`, so rows past the bound are never
constructed, never validated and never re-rendered, and what the user typed is gone: a direct
breach of FR-013. Worst, a record whose rows already exceed the cap after an import or a lowered
limit could never be brought back into compliance, because the submission that removes the surplus
is exactly the one refused.

The justification D17 gave was also false. It claimed the unbounded default lets a request force a
thousand form constructions "while holding a write transaction open". The formset is validated
**before** `transaction.atomic()` opens, so `full_clean` never runs inside a write transaction.

`validate_max=True` alone gives the enforcement the finding asked for. T021 now tests both
directions — over the cap is rejected, and within-the-cap-after-removals is accepted, which is the
test that pins this decision.

**Why defensible**: it is subtractive. The remaining ceiling is Django's own default, which every
inline formset in every Django project already carries, and the enforcement FR-026 needs is intact.

## D26 — `form_valid` never calls `super().form_valid()`

D19 moved the success message outside the transaction, which was right, but specified doing it by
calling `super().form_valid()` after the block. That re-enters `SuccessMessageMixin`, which
delegates to `ModelFormMixin.form_valid`, whose first statement is `self.object = form.save()`.
Neither `MVPCreateView` nor `MVPUpdateView` overrides it, so every inline submission would have
saved the parent a second time — outside the transaction, after the rows were written, re-running
`_save_m2m`, and firing a consuming project's `post_save` receivers twice for one user action.

`form_valid` resolves the success URL, does the two saves inside the block, queues the message with
`messages.success`, and returns the redirect itself. `MVPDeleteView.form_valid` already does
exactly this and is the house precedent. T016 now asserts the parent is saved exactly once.

**Why defensible**: the correct shape already existed in the same module. The defect came from
reaching for the inherited hook out of habit rather than reading what it does.

## D27 — Documentation drift the round-1 edits left behind

Three artefacts contradicted themselves after the first re-plan, and one instance of the standing
falsehood T005 exists to correct was missed:

- `research.md` R3's decision sentence still said `__prefix__` is replaced with "the current
  `TOTAL_FORMS` value" — the exact ambiguity SEC-003 was raised about — while the corrected
  wording sat three lines below it in the same section.
- `data-model.md` opened by saying there is no migration and closed by describing the one this
  feature generates.
- `progress.md`'s S3 record named T041–T043 as the convergence tasks. After the renumbering those
  ids are live US6 story tasks, so the reference resolved to the wrong three rather than failing
  to resolve.
- `docs/index.md` still describes crispy forms as an optional third-party integration. T004 now
  covers it.

**Why defensible**: none of these changes a decision, but each is the kind of stale sentence an
implementer reads as normative. The lesson is narrower than "proofread": an edit that corrects a
claim has to correct every copy of it, and a renumbering invalidates every id written down
elsewhere.

## D28 — The success URL is resolved after the saves, not before them

The round-2 fix for the double parent save (D26) introduced a regression, which round 3 caught. It
specified `success_url = self.get_success_url()` as the first statement of `form_valid`, above the
atomic block. On the create path Django sets `self.object = None` before `form_valid` runs, and
`MVPModelFormBase.get_success_url` needs the saved object:

- With no `success_url` set, it falls through to step 3 — `object.get_absolute_url()` — finds no
  object, and raises `ImproperlyConfigured`. The rows are already committed, so the user gets a 500
  on a submission that saved.
- With `success_url = "detail"`, `get_url_kwargs` has no pk to work with and returns `None`,
  `resolve_crud_url` returns `None`, and the chain falls to step 2b and returns the literal string
  `"detail"` as a relative path. The user is redirected to a 404 on a record that saved fine.

Neither shows up under `success_url = "list"`, which `get_url_kwargs` resolves to `{}` without the
object — and that is the value the contract's own worked configuration uses, so the obvious fixture
would have hidden it. T016 now exercises FR-012 on the create path with an object-dependent success
URL specifically.

The fix is to resolve the URL after the block, which is the same effective order
`ModelFormMixin.form_valid` uses: save, then resolve. The message and the redirect stay outside the
transaction, which is all D19 and D26 ever required.

**Where the mistake came from, because it is the more useful part.** `MVPDeleteView.form_valid` was
cited as the house precedent, and it does resolve the URL first — but for a reason that does not
transfer: its object is about to be deleted, and its success-URL chain has no `get_absolute_url()`
step. It was the right precedent for *producing the message and redirect directly* and the wrong
one for *ordering*. Copying a shape without its reason is what put the statement in the wrong place.

**Why defensible**: it restores Django's own ordering, it is a one-statement move, and the test that
pins it is now written against the case that fails.

## D29 — One residue from the D25 withdrawal

`research.md`'s technology summary table still listed "a bounded `absolute_max`" after R9 had
withdrawn it, contradicting the contract, the data model, the plan and the task. Removed. This is
the second instance of the pattern D27 named: a correction has to reach every copy of the claim,
including the summary that restates it.

## D30 — The US2 tamper flag is an append, and is approved

`forge tamper-check --base 3b3ef2f` raised one flag: `modified_preexisting_test` on
`tests/test_views/test_edit.py`. The check is file-granular, and the file existed at the base, so
any edit to it flags.

The diff is additive only: two import lines, a module-level helper, and one new test class appended
at the end. No pre-existing test function is modified, weakened or deleted, and the file's other 155
tests pass unchanged. T012 named this file explicitly, so the story could not have been done
without touching it.

Approved under the D4 triage rule rather than escalated. Recorded here because the policy requires
an approved flag to carry a written reason.
