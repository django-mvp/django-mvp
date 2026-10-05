# Feature Specification: Fields written by hand in a template use daisy-cotton's form controls

**Feature Branch**: `039-hand-written-fields`

**Created**: 2026-10-05

**Status**: Draft

**Serves**: G5 (a polished, modern look and feel out of the box), G2 (a component library covering what a data-centric web application needs, with small attribute APIs and deliberately limited variation)

**Roadmap**: R29 (the basic daisyUI components come from daisy-cotton)

**Issue**: #439

**Input**: A few templates write a field out themselves: the two sign-in fields and the list
search box. They should switch to daisy-cotton's input, label and fieldset, and the single-field
component goes away. Their help text and errors stay tied to the control, which is what #412 asks
for. Forms rendered from a Django form are untouched: they stay with django-crispy-forms and
django-mvp-forms.

## Summary

The package has two ways to draw a form field. A form built from a Django form goes through
`c-form.render`, which hands the work to django-crispy-forms and django-mvp-forms. A field written
out in a template, one control at a time, goes through `c-form.field`, a single component that
draws the control with its label, help text and errors. Three places in the package use the second
way: the username and password fields on the sign-in page, and the search box on a list page.

daisy-cotton ships a complete set of form controls, so the package no longer needs a single-field
component of its own. This feature moves those three fields onto daisy-cotton's input, label and
fieldset, removes `c-form.field`, and tells a developer who used it what to write instead.

The move also fixes a fault in the component being removed. `c-form.field` draws its help text and
errors with no id, and its control never refers to them, so a screen reader announces neither when
the control has focus (#412). After this feature, a field written by hand in the package ties its
errors and help text to the control, and the documented replacement shows a developer how to do
the same.

Nothing changes for a form rendered from a Django form.

## Clarifications

### Session 2026-10-05

The coverage scan found six ambiguities. Each was resolved from the issue, the roadmap item, the
sibling issues under R29 and the source of daisy-cotton 0.1.2. Longer rationale is in
`decisions.md`.

- **Q: #412 proposes ids in Django's own form, `<id>_helptext` and `<id>_error`. Must the ids take
  that form?**
  A: No. What a screen reader needs is that the control refers to elements that exist on the page.
  The spec requires that and leaves the form of the ids to the components that draw them.
  daisy-cotton's fieldset already derives a pair of ids for its help text and errors. Recorded as
  FR-003 and FR-004.

- **Q: None of the three fields in the package has help text. Where is the help text half of #412
  shown to hold?**
  A: In the documented replacement and in the demo application. The demo's page for the
  single-field component becomes a page showing a field written by hand with a label, help text
  and an error, and that page is where the help text association is exercised. Recorded as FR-012
  and FR-013.

- **Q: The search box sits in a joined group with its submit button. Does this feature rebuild
  the group and the button too?**
  A: No. This feature changes the field only. The button comes from #435 and the joined group
  from #440. The search box must keep working inside whatever group it sits in when this is built.
  Recorded as FR-007.

- **Q: Does this feature wait for the `mvp.` prefix (#434)?**
  A: No. It depends only on daisy-cotton being installed (#433). If #434 has landed first, the
  templates and the component named here are found under their new names and the requirements
  apply to them unchanged. Recorded under Assumptions.

- **Q: Is a compatibility alias kept for `c-form.field`?**
  A: No. The removal is a breaking change, recorded in the changelog with the replacement beside
  it. It ships with the rest of R29 in one release. Recorded as FR-009 and FR-014.

- **Q: `c-form.field` draws a visible marker beside the label of a required field. Is the marker
  kept?**
  A: The spec does not require it. A required field must still be exposed as required to the
  browser and to assistive technology, which the control's own `required` attribute does. Whether
  a visible marker is drawn is a presentation choice left to the build. Recorded as FR-002.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The sign-in fields are drawn with daisy-cotton's controls and announce their errors (Priority: P1)

A person opens the sign-in page of a project built on django-mvp. They see a username field and a
password field, each with its label, as they do today. They submit the form with a mistake in it
and the page comes back with an error against a field. A person using a screen reader moves focus
to that field and hears its label, that it is invalid, and the error itself. Today they hear only
the label.

For the developer of the project nothing changes: the form still posts the same field names to the
same address, the browser still offers saved credentials, and a project that relabels the username
field still sees its own label.

**Why this priority**: The sign-in page is the one page every project using the package shows to
everyone, and it is where the fault in #412 reaches real users. It also proves the replacement
pattern, label and control and errors together, that the other two stories rely on.

**Independent Test**: In a test project, request the sign-in page and confirm each field is one
control with an associated label. Post invalid input that puts an error on a field and confirm the
control is marked invalid and refers to an element on the page that holds the error. Post valid
credentials and confirm the person is signed in and sent on as before.

**Acceptance Scenarios**:

1. **Given** the sign-in page, **When** it renders, **Then** the username and password fields are
   each one control whose label is associated with it, so that the label is the control's
   accessible name.
2. **Given** a submission that leaves an error on a field, **When** the page renders again,
   **Then** that field's control is marked invalid and refers to an element on the page that
   contains the field's error.
3. **Given** a field with more than one error, **When** the page renders, **Then** every one of
   its errors is inside what the control refers to.
4. **Given** a field with no error, **When** the page renders, **Then** its control is not marked
   invalid and refers to no element that is absent from the page.
5. **Given** valid credentials, **When** the form is submitted, **Then** the person is signed in
   and sent to the address they would have been sent to before this feature.
6. **Given** the sign-in page, **When** it renders, **Then** each control carries the form field's
   own name and id, is marked required, and carries the hint that lets a browser offer a saved
   username or current password.
7. **Given** a project whose sign-in form gives the username field a different label, **When** the
   page renders, **Then** the field's label is the one the form supplies.
8. **Given** a page context that holds a variable with the same name as one of the control's
   options, **When** the sign-in page renders, **Then** the control is drawn exactly as it is
   without that variable.

---

### User Story 2 - The list search box is drawn with daisy-cotton's input (Priority: P2)

A person on a list page types into the search box and submits it. The list narrows to the matching
records and the box still shows what they typed. A person using a screen reader hears the box
named as a search. None of this is new. What changes is that the box is drawn with daisy-cotton's
input instead of the package's single-field component, so a fix or improvement to that input
arrives on every list page without being made twice.

**Why this priority**: It is the last place in the package that uses the single-field component,
so the component cannot be removed until it moves. It carries no error or help text, which makes
it the simpler of the two moves.

**Independent Test**: Request a searchable list page with and without a search term. Confirm the
search control belongs to the list's filter form, carries the current term and has an accessible
name. Submit a term and confirm the list is filtered as before. Request a list that is not
searchable and confirm no search control is drawn.

**Acceptance Scenarios**:

1. **Given** a searchable list page, **When** it renders, **Then** it has one search control that
   belongs to the list's filter form and submits under the name the list's search already reads.
2. **Given** a list page requested with a search term, **When** it renders, **Then** the search
   control holds that term.
3. **Given** a searchable list page, **When** it renders, **Then** the search control has an
   accessible name.
4. **Given** a caller that passes its own placeholder to `c-page.list.actions.search`, **When**
   the page renders, **Then** the control's placeholder and its accessible name both follow what
   the caller passed.
5. **Given** a search term submitted from the control, **When** the list renders, **Then** it
   shows the records it would have shown before this feature, with ordering, filters and
   pagination behaving as before.
6. **Given** a list that is not searchable, **When** it renders, **Then** no search control is
   drawn.
7. **Given** a page context that holds a variable with the same name as one of the input's
   options, **When** the list page renders, **Then** the search control is drawn exactly as it is
   without that variable.

---

### User Story 3 - The single-field component is removed and its replacement is documented (Priority: P2)

A developer maintains a package built on django-mvp that writes a few fields by hand, for example
the one-field forms django-allauth builds for changing an email address. They upgrade django-mvp
and their templates no longer find `c-form.field`. The changelog names the removal and points to
the documentation. There they find the same field written with daisy-cotton's label, control and
fieldset, with its help text and errors tied to the control. They can open the demo application
and see that example rendered. They rewrite their fields from it, and their help text and errors
are now announced, which the old component never did.

A developer whose forms are rendered from a Django form reads the same changelog entry and has
nothing to do.

**Why this priority**: Removing the component is what keeps the package from carrying a second
copy of something daisy-cotton maintains. It comes after the first two stories because the
component cannot go while the package still calls it.

**Independent Test**: Search the package, the demo application and the documentation for a use of
the single-field component and confirm there is none. Render the demo's page for a field written
by hand and confirm the control refers to its help text and its error, and that both are on the
page. Render a Django form through `c-form.render` and a row set through `c-form.formset` and
confirm their output is what it was before this feature.

**Acceptance Scenarios**:

1. **Given** the package after this feature, **When** its templates, the demo application and the
   documentation are searched, **Then** nothing calls the single-field component and the package
   no longer ships it.
2. **Given** the component reference and the glossary's component list, **When** they are read,
   **Then** neither lists the single-field component.
3. **Given** the documentation, **When** a developer looks up how to write a field by hand,
   **Then** it shows a field composed from daisy-cotton's controls with a label, help text and
   errors, and states what makes the control refer to its help text and errors.
4. **Given** the demo application, **When** its page showing a field written by hand renders,
   **Then** the control refers to an element holding the help text and an element holding the
   error, and both are on the page.
5. **Given** the changelog, **When** the entry for this change is read, **Then** it marks the
   removal as breaking and names what replaces the component.
6. **Given** a form rendered from a Django form through `c-form.render`, and a row set rendered
   through `c-form.formset`, **When** they render, **Then** their output is what it was before
   this feature.
7. **Given** a project that calls the removed component, **When** the page renders, **Then** it
   fails the way a call to any component that does not exist fails, with no silent fallback.

---

### Edge Cases

- A field written by hand with no id. The association between a control and its help text or
  errors is made by id, so a field with no id cannot carry one. The documentation says so. The
  three fields in the package all have ids where they have errors to show: the sign-in fields
  take theirs from the form, and the search box has neither help text nor errors.
- The sign-in page's summary message. A failed sign-in also shows one message above the form that
  belongs to no field. It stays as it is. This feature concerns the errors attached to a field.
- A project that overrides the sign-in template or the list search component with its own copy.
  The override keeps working only as long as it does not call the removed component. One that
  does fails loudly on upgrade and is rewritten from the documented replacement.
- A project that overrides the single-field component itself. The override is no longer used by
  any package template. It still serves that project's own calls, since the project now owns the
  only copy.
- Packages built on django-mvp that call the removed component. They break on upgrade. Moving
  them is work for their own repositories and is listed among R29's deliverables.
- The package keeps its own `form` components (`c-form`, `c-form.render`, `c-form.formset`) while
  daisy-cotton supplies `c-form.input`, `c-form.label` and `c-form.fieldset` under the same
  namespace. Both sets must resolve side by side for as long as they share it.
- The search box sits beside its submit button as one joined control. It must still read as part
  of that group after the move.

## Requirements *(mandatory)*

### Functional Requirements

Sign-in fields (User Story 1)

- **FR-001**: The username and password fields on the sign-in page MUST be drawn with
  daisy-cotton's form controls and MUST NOT use the package's single-field component.
- **FR-002**: Each sign-in control MUST have a label associated with it, MUST carry the name and
  id the form gives the field, MUST be exposed as required, and MUST keep the hint that lets a
  browser offer saved credentials. The label MUST be the one the form supplies for the username
  field.
- **FR-003**: When a sign-in field has errors, its control MUST be marked invalid and MUST refer
  to an element on the page that contains every one of the field's errors.
- **FR-004**: A control MUST NOT refer to an element that is not on the page. A field with no
  errors and no help text MUST NOT be marked invalid and MUST carry no such reference.
- **FR-005**: Signing in MUST behave as before: the same field names are posted to the same
  address, valid credentials sign the person in, and they are sent where they were sent before.

List search box (User Story 2)

- **FR-006**: The search control in `c-page.list.actions.search` MUST be drawn with daisy-cotton's
  input and MUST NOT use the package's single-field component.
- **FR-007**: The search control MUST keep belonging to the list's filter form, submitting under
  the name the list's search reads, holding the current search term, and carrying an accessible
  name. It MUST keep working inside the joined group it shares with its submit button. The group
  and the button themselves are outside this feature.
- **FR-008**: The component attributes `c-page.list.actions.search` accepts today MUST keep their
  meaning, and the component MUST still draw nothing on a list that is not searchable.

Removal and replacement (User Story 3)

- **FR-009**: The package MUST stop shipping the single-field component. No compatibility alias
  is kept.
- **FR-010**: The package's templates, the demo application and the documentation MUST NOT call
  the single-field component. The tests written for it are removed with it.
- **FR-011**: The component reference and the glossary's component list MUST no longer name the
  single-field component.
- **FR-012**: The documentation MUST show how to write a field by hand with daisy-cotton's
  controls, including a label, help text and errors, and MUST state how the control comes to
  refer to its help text and errors.
- **FR-013**: The demo application MUST show a field written by hand with a label, help text and
  an error, in place of its page for the single-field component. On that page the control MUST
  refer to the elements holding the help text and the error, and both MUST be on the page.
- **FR-014**: The changelog MUST record the removal as a breaking change and name the
  replacement.

Across all three

- **FR-015**: Every call the package makes to a daisy-cotton form control in these templates MUST
  be isolated from the page context, so that a context variable sharing a name with one of the
  control's options cannot change how the control is drawn. Content the caller places inside the
  control MUST still see the page context.
- **FR-016**: Forms rendered from a Django form MUST be untouched. The output of `c-form`,
  `c-form.render`, `c-form.formset` and `c-form.formset.row` MUST be what it was before this
  feature.
- **FR-017**: The pages this feature touches MUST render fully styled from the stylesheet the
  package ships, with no build step added for the project.

### Out of scope

- How a form built from a Django form is rendered. That stays with django-crispy-forms and
  django-mvp-forms.
- The submit buttons and the alert on the sign-in page, and the search box's submit button. They
  move with the basic components in #435.
- The joined group around the search box, and the navbar's own search action. The shell's
  hand-written markup moves in #440.
- Renaming the package's kept components under the `mvp.` prefix (#434).
- Installing daisy-cotton and covering its classes in the prebuilt stylesheet (#433).
- Moving the packages built on django-mvp off the removed component. That happens in their own
  repositories.
- Any change to daisy-cotton. If its controls turn out to lack something these three fields need,
  the gap is raised in daisy-cotton's tracker and not worked around here.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three fields the package writes by hand, the two sign-in fields and the list
  search box, are drawn with daisy-cotton's controls, and the count of calls to the single-field
  component across the package, the demo application and the documentation is zero.
- **SC-002**: On the sign-in page, every error attached to a field is inside an element its
  control refers to, and every element a control refers to exists on the page. This holds for a
  field with one error, with several, and with none.
- **SC-003**: A person can sign in, and can search a list, exactly as before. The tests that
  already cover signing in, searching, ordering and filtering pass without a change to the
  behaviour they assert.
- **SC-004**: A developer who used the single-field component can replace a use of it from the
  changelog entry and the documentation alone, and the documented example is one the demo
  application renders with its help text and error both tied to the control.
- **SC-005**: A form rendered from a Django form, and a row set, produce the same output before
  and after this feature.
- **SC-006**: The package ships one component fewer, and every field it writes by hand uses the
  same library of controls.

## Assumptions

- daisy-cotton is installed as a dependency of the package and its components resolve in every
  project, delivered by #433. That feature also makes the prebuilt stylesheet cover the classes
  daisy-cotton's templates write and proves that a component called in isolation from the page
  context still passes that context to content placed inside it.
- This feature does not wait for #434. The templates are named here as they stand today
  (`mvp/account/login.html`, `c-page.list.actions.search`, `c-form.field`). If #434 lands first,
  they are found under their new names and every requirement applies unchanged.
- daisy-cotton 0.1.2 ships an input, a label and a fieldset that between them cover what the
  three fields need: a control that takes native attributes, content placed inside the box before
  the field, a label tied to a control by id, and a fieldset that gives its help text and errors
  ids a control can refer to.
- This is a like-for-like change of markup. No page is redesigned, and small differences that
  follow from daisy-cotton's own markup are accepted without a design review. The feature is not
  prototyped before it is planned.
- The removal ships with the rest of R29 in one breaking release. This feature cuts no release of
  its own.
- #412 describes the fault this feature removes. Once this feature is delivered the component
  #412 names no longer exists, so that issue can be closed with a pointer to the documented
  replacement.
