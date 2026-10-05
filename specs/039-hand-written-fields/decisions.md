# Decisions: Fields written by hand in a template use daisy-cotton's form controls

Rationale too long to inline in `spec.md`, the rulings the maintainer gave for the whole of R29
that bear on this feature, and the ambiguities resolved while specifying.

The reading of #439 this specification was written from: the two sign-in fields and the list
search box move onto daisy-cotton's input, label and fieldset, each call isolated from the page
context. The single-field component is removed with no alias. A field's errors and help text are
tied to its control, which answers #412. Forms rendered from a Django form are not touched. The
maintainer handed this work over on 2026-10-05 without a round of questions, so that reading was
not put to him. D1 to D4 are his rulings. D5 onward are assumptions made here and open to his
veto on the specification pull request.

## Rulings given by the maintainer

### D1. Form rendering stays with django-crispy-forms and django-mvp-forms

**Chosen:** only fields written out by hand in a template move to daisy-cotton's form controls.
`c-form`, `c-form.render` and `c-form.formset` stay, and the single-field component is removed
(FR-009, FR-016).

**Rejected:** moving whole-form rendering onto daisy-cotton's controls as well. A Django form
already renders correctly through the crispy template pack, with its help text and errors tied to
each widget, and replacing that is a different and much larger piece of work.

**ADR:** none — it restates the boundary R29 already draws in the roadmap.

### D2. Calls to daisy-cotton's components are isolated from the page context

**Chosen:** every call the package makes to a daisy-cotton component passes Cotton's `only`
attribute (FR-015). Many of daisy-cotton's templates declare options with plain names such as
`text`, `class` and `variant`, and a page variable of the same name would otherwise be picked up
when the caller does not pass that option.

**Rejected:** waiting for a change in daisy-cotton. The call site can settle it today, and #433
proves that content placed inside an isolated component still sees the page context.

**ADR:** none here — the rule belongs to R29 as a whole and is recorded where #433 establishes it.

### D3. No compatibility alias for the removed component

**Chosen:** `c-form.field` is removed outright and the removal is recorded in the changelog as
breaking (FR-009, FR-014). All of R29 lands in one breaking release, and this feature cuts no
release of its own.

**Rejected:** keeping `c-form.field` as a thin wrapper over daisy-cotton's controls for a release
or two. The packages built on this one move once, with the rest of R29, and an alias would keep
alive the second copy this roadmap item exists to remove.

**ADR:** none — the compatibility article of the constitution already covers a breaking removal
recorded in the changelog.

### D4. The prebuilt stylesheet already covers daisy-cotton's form controls

**Chosen:** this feature adds no stylesheet work of its own (FR-017). The prebuilt stylesheet
scans all of daisyUI's components, and #433 extends the scan to the utility classes daisy-cotton's
templates write.

**ADR:** none — stylesheet coverage is decided in #433.

## Assumptions made while specifying

### D5. The ids are not required to take Django's form

**What was ambiguous:** #412 proposes `<id>_helptext` and `<id>_error`, the ids Django's
`BoundField` writes into `aria-describedby`. daisy-cotton's fieldset derives a different pair,
`<id>-description` and `<id>-errors`, from the fieldset's own id.

**Chosen:** the spec requires only that a control refers to elements that exist and that those
elements hold the help text and the errors (FR-003, FR-004). It does not fix the form of the ids.

**Why defensible:** a screen reader follows the reference, whatever it is called. Requiring
Django's form would force the package to bypass daisy-cotton's fieldset and draw the help text and
errors by hand, which is the duplication this feature removes. Nothing in the package reads these
ids from a script.

**ADR:** none — the ids are an implementation detail of the components that draw them.

### D6. The help text half of #412 is shown in the documentation and the demo

**What was ambiguous:** #439 says help text and errors stay tied to the control, but none of the
three fields in the package has help text, and the search box has neither.

**Chosen:** the sign-in page carries the requirement for errors. The documented replacement and a
demo page carry it for help text (FR-012, FR-013). The demo's page for the single-field component
is rewritten as a page showing a field written by hand, not deleted.

**Why defensible:** the people #412 was filed for are developers who write fields by hand in
packages built on this one. They need an example to copy, and an example that is rendered and
tested is the only place in this repository where the help text association can be held to. It
also keeps the demo showing how each kind of field is drawn after the component's own page goes.

**Rejected:** deleting the demo page and pointing at daisy-cotton's gallery. That leaves the
association untested here and sends the developer to another project for the half of the pattern
that matters most.

**ADR:** none — a documentation choice.

### D7. This feature does not depend on the `mvp.` prefix

**What was ambiguous:** #439 lists only #433 as a dependency, while #434 renames the templates
this feature edits.

**Chosen:** no dependency on #434. The spec names the templates as they stand today and says the
requirements apply unchanged under the new names if #434 lands first.

**Why defensible:** nothing here needs the prefix. daisy-cotton's `form.input`, `form.label` and
`form.fieldset` do not collide with any file the package ships under `form`, so both resolve side
by side today. Adding a dependency would hold this feature behind another for no gain.

**ADR:** none — an ordering note.

### D8. The search box's button and joined group stay with their own features

**What was ambiguous:** the search box is one control joined to a submit button. #435 owns the
button, and #440 lists the join among the shell markup it moves.

**Chosen:** this feature changes the field only and must keep it working inside the group
(FR-007).

**Why defensible:** each sibling issue names its own scope, and widening this one would have two
features editing the same lines for different reasons.

**ADR:** none — a scope boundary between sibling issues.

### D9. No visible required marker is required

**What was ambiguous:** `c-form.field` draws an asterisk beside the label of a required field.
daisy-cotton's label draws none.

**Chosen:** the spec requires the control to be exposed as required and says nothing about a
visible marker (FR-002).

**Why defensible:** a marker is appearance, which a specification here does not pin. Both sign-in
fields are required, so a marker on each tells the reader nothing.

**ADR:** none — a presentation choice.

### D10. No prototype before planning

**Chosen:** the feature is planned and built without a design prototype.

**Why defensible:** it swaps the markup of three existing fields for equivalent markup from
another library. No page, flow or layout is new, so there is nothing for a design review to
decide.

**ADR:** none — a process choice for this feature.

### D11. #412 is answered by this feature and not fixed separately

**Chosen:** the component #412 describes is removed, and the replacement keeps the association
#412 asks for. #412 is closed when this feature is delivered, with a pointer to the documented
replacement.

**Rejected:** fixing `c-form.field` first and removing it afterwards. That is two changes to a
component with one release left to live.

**ADR:** none — it follows from D1 and D3.
