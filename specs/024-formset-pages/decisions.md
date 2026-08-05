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
