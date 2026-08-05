# Feature Specification: Formset Pages

**Feature Branch**: `024-formset-pages`

**Created**: 2026-08-05

**Status**: Draft

**Serves**: G4 — a usable front end for the Django features that ship backend machinery without one

**Roadmap**: R8 — formsets that render and work

**Tracking issue**: #162

**Input**: A developer configures one view to put a record and its related rows on a single page and gets what the single-form pages already give. The parent form and its rows render through the packaged form components with the packaged look. Rows can be added and removed in the browser without a reload, where an unsaved row simply goes and a saved one is marked for deletion and removed when the page is submitted. Validation errors appear beside the row that has one, or above the set when it is the set that is wrong, never collapsed into a single message. Everything commits in one submission. Formset rendering is generic and works anywhere the packaged form components already do, including a standalone formset on the existing form view, while the configured view covers one parent with one related set. django-crispy-forms and crispy-tailwind become declared dependencies. Documentation shows the whole path from a model to a working page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Packaged form rendering works on a clean install (Priority: P1)

A developer installs django-mvp into a project, follows the documented setup, and renders a form
page. The page renders. Today it raises a template error, because the packaged form rendering
loads two template tag libraries that belong to packages the project was never told to install.

**Why this priority**: Every other story in this feature renders through the same path. A formset
that only works when a project happens to have installed an undeclared package is not a delivered
feature, and this story is the difference between the rest of the spec working and appearing to.

**Independent Test**: Install the package and its declared dependencies into an environment with
nothing else present, render a form page, and confirm no template error. Delivers a working form
page to every project that installs the package as documented.

**Acceptance Scenarios**:

1. **Given** an environment with only django-mvp and its declared dependencies installed, **When** a page rendering a form through the packaged form components is requested, **Then** the page renders and the form appears in the packaged style.
2. **Given** the package metadata, **When** the declared runtime dependencies are read, **Then** both template tag libraries the packaged form rendering loads are present among them.
3. **Given** the dependency checker runs over the repository, **When** it reports, **Then** it names no missing or transitively-relied-upon runtime dependency.

---

### User Story 2 - A formset renders with the packaged look (Priority: P1)

A developer has a formset and wants it on a page. They hand it to the packaged rendering and get
the same presentation the package already gives a single form: each row's controls, labels and
help text in the packaged style, and the bookkeeping Django needs in order to read the submission
back. They write no markup for it. The formset need not belong to a parent object, and the page
need not be the configured view from User Story 3 — a formset renders wherever the packaged form
components already render.

**Why this priority**: This is the smallest thing that closes the gap the roadmap names. Nothing in
the package refers to formsets today, so a project that needs one drops out of the packaged look at
exactly the point where a page gets complicated.

**Independent Test**: Render a page carrying a standalone formset through the packaged components
and confirm every row appears in the packaged style with the hidden bookkeeping fields present.
Delivers a rendered formset without any of the parent-object machinery.

**Acceptance Scenarios**:

1. **Given** a formset with several rows, **When** the page is rendered, **Then** each row's fields appear with the same control, label and help-text presentation a single form's fields receive.
2. **Given** a formset, **When** the page is rendered, **Then** the formset's management form is present in the markup, so the submission can be read back.
3. **Given** a formset with no rows and a configured number of blank extras, **When** the page is rendered, **Then** the blank rows appear and are indistinguishable in presentation from populated ones.
4. **Given** a standalone formset supplied to the existing form view, **When** the page is rendered, **Then** it renders identically to the same formset rendered inside any other packaged form.

---

### User Story 3 - A record and its rows on one page (Priority: P1)

A developer configures one view with a model and its related rows — an order and its line items, a
survey and its questions — and gets a page carrying the parent's form and a row per related record.
The user edits both and submits once. Either everything saves or nothing does. The developer writes
no view logic to build the formset, to validate the two together, or to save them in the right
order.

**Why this priority**: This is the case the roadmap calls "the common case this gap blocks", and it
is the one the tracking issue describes. It is also where the developer's own code is today: the
rendering in User Story 2 removes the markup they write, and this removes the view they write.

**Independent Test**: Configure the view against a parent model and a related model, submit the
page once with changes to both, and confirm both are persisted. Delivers the whole parent-and-rows
page from configuration alone.

**Acceptance Scenarios**:

1. **Given** a view configured with a parent model and one related set, **When** the page is requested for an existing record, **Then** the parent's form and one row per existing related record are rendered together on one page.
2. **Given** the page is submitted with valid changes to the parent and to its rows, **When** the submission is processed, **Then** both the parent and the rows are persisted and the user is sent onward exactly as the packaged single-form pages send them.
3. **Given** the page is submitted and saving the rows fails part-way, **When** the request completes, **Then** the parent's changes are not persisted either.
4. **Given** the page is submitted with an invalid parent form and valid rows, **When** the page is re-rendered, **Then** nothing is persisted and the values the user typed into both the parent and the rows are still present.
5. **Given** a view configured for creating a new parent record, **When** the page is submitted with valid rows, **Then** the parent is created and its rows are attached to it.

---

### User Story 4 - Errors appear where the problem is (Priority: P2)

A user submits a page and something is wrong. If one row is wrong, the message appears beside that
row, in the same place a single form shows it. If the problem belongs to the set rather than to any
one row — too few rows, a duplicate across rows — the message appears above the set. The user is
never handed one message at the top of the page and left to find which of eight rows it refers to.

**Why this priority**: The tracking issue names collapsing every error into a single page-level
message as the specific thing that drives developers to write their own view. It depends on the
rendering in User Story 2 existing, which is why it sits below it rather than beside it.

**Independent Test**: Submit a page with an error on one row and a separate error belonging to the
whole set, and confirm each message renders in its own place. Delivers correct error placement
independently of how rows are added or removed.

**Acceptance Scenarios**:

1. **Given** a submitted formset where one row fails validation, **When** the page is re-rendered, **Then** the message appears within that row, adjacent to the field that caused it, and no other row shows a message.
2. **Given** a submitted formset failing a rule that belongs to the set as a whole, **When** the page is re-rendered, **Then** the message appears above the set and is visually distinguishable from a row's message.
3. **Given** a submitted formset with errors on more than one row, **When** the page is re-rendered, **Then** every affected row carries its own message.
4. **Given** any of the above, **When** the page is re-rendered, **Then** the values the user typed are still in the controls.

---

### User Story 5 - Adding and removing rows in the browser (Priority: P2)

A user working through a page needs one more row and adds it, without saving and reloading to get
it. A row that is not wanted is removed. A row the user just added simply goes. A row that already
exists in the database is taken off the page and marked for removal, and is actually deleted when
the page is submitted, so a user who removes three rows and then leaves the page has changed
nothing. The project installs no build tooling for any of this.

**Why this priority**: The roadmap names it as a deliverable and it is what makes the page usable
rather than merely correct, but a page with a fixed number of rows is already a working page, which
is why it sits below the three stories that produce one.

**Independent Test**: Add rows, remove both a new row and an existing one, submit, and confirm the
database matches what the page showed. Delivers the in-browser editing independently of the error
presentation.

**Acceptance Scenarios**:

1. **Given** a rendered formset page, **When** the user adds a row, **Then** a blank row appears without the page reloading and is presented identically to the rows already there.
2. **Given** the user has added rows, **When** the page is submitted, **Then** every added row that carries data is saved.
3. **Given** a row the user added and has not saved, **When** the user removes it, **Then** it disappears from the page and submitting the page saves no record for it.
4. **Given** a row that already exists in the database, **When** the user removes it, **Then** it disappears from the page but the record still exists until the page is submitted.
5. **Given** a row that already exists and has been removed on the page, **When** the page is submitted, **Then** the record is deleted.
6. **Given** the user removes an existing row and then navigates away without submitting, **When** the record is looked up, **Then** it is unchanged.
7. **Given** a consuming project with no front-end build tooling installed, **When** the page is used, **Then** adding and removing rows works.

---

### User Story 6 - The path from a model to a working page (Priority: P3)

A developer who has taken a model through to working pages with this package reaches the first
thing it did not cover, opens the documentation, and finds the whole path written down: the model,
the related model, the view configuration, and the page. The vocabulary this feature introduces is
recorded alongside the rest of the package's terms.

**Why this priority**: The capability has to exist before it can be documented, and a developer can
reach it from the code in the meantime. It is a roadmap deliverable in its own right and the
package's own scope statement points at formsets as its example, so shipping the capability without
the worked example leaves the claim still unillustrated.

**Independent Test**: Follow the documented example from an empty app to a rendered
parent-and-rows page without reading the package source. Delivers the documentation independently
of any further code change.

**Acceptance Scenarios**:

1. **Given** the documentation, **When** a developer follows the worked example end to end, **Then** they reach a working parent-and-rows page without consulting the package source.
2. **Given** the documentation, **When** the standalone formset case is looked up, **Then** it is covered as well as the parent-and-rows case.
3. **Given** the repository's domain vocabulary, **When** the terms this feature introduces are looked up, **Then** they are defined there.
4. **Given** the changelog, **When** the release carrying this feature is read, **Then** the new public surface is recorded.

---

### Edge Cases

- What happens when the formset does not allow deletion? No remove control is offered on any row, and the page cannot be made to delete a record.
- What happens when the formset is already at its maximum number of rows? The add control stops offering more, rather than adding a row the submission will reject.
- What happens when a user removes rows below the formset's minimum? That is an error belonging to the set, so it renders above the set, per User Story 4.
- What happens when every row is removed? The page renders with no rows and with the set-level messaging, rather than an empty area with no explanation.
- What happens when the parent form is valid but its rows are not, or the reverse? Neither is persisted, and both keep the values the user typed.
- What happens when a row contains a file upload? The page carries the encoding a file submission needs, as the packaged single-form pages already do.
- What happens when the user may not change the parent? The page behaves as the packaged single-form pages behave for that user. This feature adds no permission surface of its own.
- What happens when a submission's management form is absent or has been tampered with? The request is rejected rather than partly processed, as Django's own handling requires.
- What happens when a user removes a row and the submission then fails for an unrelated reason? The page re-renders with the removal still shown, so the user does not have to remove it a second time.

## Requirements *(mandatory)*

### Functional Requirements

**Dependencies (US1)**

- **FR-001**: The package MUST declare, as runtime dependencies, every distribution whose template tag libraries the packaged form rendering loads. The justification Article VII requires is that the packaged form rendering has always called into them, so the dependency existed in the code and was absent only from the metadata.
- **FR-002**: A project that installs the package and its declared dependencies and nothing else MUST be able to render a form page through the packaged form components without error.
- **FR-003**: The repository's dependency check MUST report no missing, unused or transitively-relied-upon runtime dependency after the change.

**Formset rendering (US2)**

- **FR-004**: The package MUST provide a component that renders a Django formset, giving each row's fields the same control, label and help-text presentation the packaged rendering already gives a single form's fields.
- **FR-005**: Formset rendering MUST emit the formset's management form, so a submission can be read back by Django's own machinery.
- **FR-006**: Formset rendering MUST be usable anywhere the packaged form components are usable, including a formset that has no parent object and a formset supplied to the existing packaged form view.
- **FR-007**: Formset rendering MUST require no attribute beyond the formset itself for its default presentation.
- **FR-008**: The component MUST be named after its domain role and MUST be override-able at the same template path a consumer would use for any other packaged component.

**The configured view (US3)**

- **FR-009**: The package MUST provide a view configuration that takes a parent model and one related set and renders both on a single page, without the developer writing code to construct the formset.
- **FR-010**: The view MUST validate the parent form and the related rows as one submission, and MUST treat the submission as invalid if either part is.
- **FR-011**: On a valid submission the view MUST persist the parent and its rows atomically: a failure while saving either leaves neither persisted.
- **FR-012**: On a valid submission the view MUST send the user onward by the same rule the packaged single-form pages use.
- **FR-013**: On an invalid submission the view MUST re-render the page with every value the user submitted still present, in both the parent form and the rows.
- **FR-014**: The view MUST support both creating a new parent with its rows and editing an existing parent with its rows.
- **FR-015**: The view MUST behave, for page structure, permissions, titles and breadcrumbs, as the packaged single-form pages behave, adding no separate surface of its own.

**Error presentation (US4)**

- **FR-016**: An error belonging to one row MUST be rendered inside that row, adjacent to the field it concerns, in the same presentation a single form's field error receives.
- **FR-017**: An error belonging to the formset as a whole MUST be rendered above the set and MUST be distinguishable from a row's error.
- **FR-018**: No error may be rendered only as a single page-level message; every error MUST appear at its own level.
- **FR-019**: Where more than one row is in error, every affected row MUST carry its own message.

**Rows in the browser (US5)**

- **FR-020**: A user MUST be able to add a row without the page reloading, and the added row MUST be presented identically to the rows already rendered.
- **FR-021**: A user MUST be able to remove a row without the page reloading.
- **FR-022**: Removing a row that has not been saved MUST take it off the page and MUST leave no record for it on submission.
- **FR-023**: Removing a row that exists in the database MUST take it off the page and mark it for deletion, and the record MUST be deleted only when the page is submitted.
- **FR-024**: No row addition or removal may reach the server before the page is submitted.
- **FR-025**: Adding and removing rows MUST work in a consuming project that has installed no front-end build tooling.
- **FR-026**: Where the formset forbids deletion, no remove control may be offered; where the formset caps the number of rows, the add control MUST stop at the cap.

**Documentation and vocabulary (US6)**

- **FR-027**: The documentation MUST carry a worked example running from a model and its related model through view configuration to a rendered page.
- **FR-028**: The documentation MUST cover the standalone formset case as well as the parent-and-rows case.
- **FR-029**: The repository's domain vocabulary MUST define the terms this feature introduces.
- **FR-030**: The changelog and README MUST record the public surface this feature adds.

### Key Entities

- **Parent record**: the single object a page is about — an order, a survey. It is edited through one form, exactly as the packaged single-form pages edit it.
- **Related row**: one record belonging to the parent — a line item, a question. Rows are created, edited and removed on the parent's page and are only persisted when that page is submitted.
- **Row set**: the collection of related rows shown on the page, together with the bookkeeping that lets a submission be read back and tells the page how many rows may exist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project whose installed packages are exactly django-mvp and its declared dependencies renders a packaged form page with no error.
- **SC-002**: A developer puts a parent and its related rows on one page by configuring a view, writing no template markup for the rows and no code to build, validate or save the set.
- **SC-003**: Every validation error a submission produces is displayed at the level it belongs to — the row for a row's error, above the set for the set's — and none is displayed only as a page-level summary.
- **SC-004**: A user adds rows, removes rows, and submits, with the page never reloading between the first change and the submission.
- **SC-005**: A record whose row was removed on the page still exists until the page is submitted, and does not exist after it.
- **SC-006**: A submission that fails part-way through saving persists neither the parent nor any row.
- **SC-007**: A developer reaches a working parent-and-rows page by following the documentation alone, without reading the package source.
- **SC-008**: A formset rendered through the packaged component is presented indistinguishably from a single form rendered through the packaged component, field for field.

## Clarifications

*Recorded during this feature's intake grilling and the clarification scan. Each answer is
integrated into the requirement or scenario it affects; this section is the record, not the
requirement.*

### Session 2026-08-05 (intake)

- **Q**: Does this feature include the Python view machinery, or is it rendering only, with the project still writing its own view?
  **A**: It includes the view. The single-form path a developer follows today is a configured view, and rendering alone would leave them writing the same view they write now. Recorded as US3 and FR-009 to FR-015.
- **Q**: Does the configured view cover standalone formsets as well as the parent-and-rows case?
  **A**: No. Rendering is generic and works for any formset anywhere the packaged form components do, including a standalone formset on the existing form view. The configured view targets the parent-and-rows case, because that is where the save flow needs a decision made for the developer. Recorded as FR-006 and US2 scenario 4.
- **Q**: What does removing a row mean for a row that already exists in the database?
  **A**: Standard practice: the row is taken off the page and marked for deletion, and the deletion happens on submission. Nothing reaches the server before then. Recorded as FR-021 to FR-024.
- **Q**: Must a formset page render with no third-party package installed?
  **A**: No. django-crispy-forms and crispy-tailwind become declared runtime dependencies in this feature. Their absence from the metadata is a packaging mistake, not a design decision, and the packaged form rendering has always called into both. Recorded as US1 and FR-001 to FR-003.
- **Q**: Does the configured view cover a parent with more than one related set on one page?
  **A**: No. One parent, one related set. A page needing two sets composes the rendering components and drives the extra set itself. The shape is revisited when a case for it appears rather than designed against a case neither the roadmap nor the tracking issue raises. Recorded under Assumptions.

### Session 2026-08-05 (clarification scan)

- **Q**: Where a formset is configured to forbid deletion or to cap the number of rows, what does the page do?
  **A**: It offers no remove control in the first case and stops offering rows at the cap in the second, rather than rendering a control whose use the submission would reject. Recorded as FR-026 and in Edge Cases.
- **Q**: What happens to a row removed in the browser when the submission comes back invalid for an unrelated reason?
  **A**: The re-rendered page still shows the removal, so the user does not repeat it. This follows from FR-013, which requires every submitted value to survive a re-render, and is recorded in Edge Cases.
- **Q**: Does this feature introduce a permission surface for the rows, separate from the parent?
  **A**: No. The page behaves as the packaged single-form pages behave for the same user. A per-row permission model is a larger question with no case behind it here. Recorded as FR-015 and in Edge Cases.
- **Q**: Does the parent-and-rows view cover creating a parent that does not yet exist, or only editing one that does?
  **A**: Both. Creating an order together with its first line items is as common as editing one, and Django's own machinery attaches the rows to the newly-created parent. Recorded as FR-014 and US3 scenario 5.
- **Q**: Is the atomicity in FR-011 a requirement on the feature or an assumption about the database?
  **A**: A requirement on the feature. A page that saves a parent and then fails on its rows leaves a record the user never intended, and the whole premise of the page is one submission. Recorded as FR-011 and SC-006.

## Assumptions

- The client-side runtime the browser behaviour needs is already loaded. The packaged base template pulls in Alpine 3 and its sort plugin, and the packaged form component already carries an Alpine root, so no new client-side dependency and no build step is needed in the consuming project. Alpine rather than hand-written JavaScript was settled when the roadmap item was decomposed. This is what makes FR-025 achievable rather than aspirational.
- Django's own formset machinery is used rather than reimplemented. The management form, the deletion flag, the extra-row count and the row limits are Django's, and this feature puts a front end on them. That is what the roadmap item asks for.
- The configured view packages one parent with one related set. A page with two related sets stays buildable by composing the rendering components and is not packaged. Agreed at intake, and revisited when a real case appears.
- Standalone formsets are a rendering concern only. No second configured view is packaged for a formset with no parent. Agreed at intake.
- Roadmap item R12 keeps the rest of its scope. Only the form-rendering half of its first deliverable moves here. The list-page dependency, the unguarded module-level import in a view module, and the documented-but-absent form renderer setting stay with R12, whose framing needs the matching correction.
- The worked example is written against the demo application. The package ships no models of its own, so the documented path is demonstrated against demo models, as the package's other model-to-pages documentation is.
- The shipped stylesheet is rebuilt on this branch. Any class the new components introduce has to reach the committed build artifact, per Article XV.
