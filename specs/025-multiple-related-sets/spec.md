# Feature Specification: More than one row set on an inline page

**Feature Branch**: `025-multiple-related-sets`

**Created**: 2026-08-11

**Status**: Draft

**Serves**: G4 — a usable front end for the Django features that ship backend machinery without one

**Roadmap**: R8 — formsets that render and work (extension; R8's first pass delivered the single-set page)

**Tracking issue**: #194

**Input**: One view class handles a parent record with any number of row sets. Each row set is declared as its own class carrying that set's configuration, and the view lists them in `inlines`, the way Django admin inlines are declared. Each set gets its own prefix, every set is validated even after one fails, the whole page commits in one transaction, and each set renders with a heading defaulting to the related model's plural name. The declaration also lets a developer decide each individual form's keyword arguments and the order the forms are displayed in, not only the set as a whole. The same view covers the rows-only case: on an update page, when the parent's own fields are falsy, no parent fields render and the page is purely the row sets attached to the record the URL identifies, with the option of recording that change on the parent's own timestamp. Create still requires parent fields. This replaces the `inline_*` attributes outright, a breaking change acceptable pre-1.0 in one release with a changelog note.

**Vocabulary**: this spec uses **row set** and **related row** as `CONTEXT.md` defines them. The tracking issue says "related set" for the same thing; they are one concept. The declaration class this feature introduces is a **row set declaration**, spelled `InlineFormSet` in code after `django.contrib.admin`'s inlines, a term `CONTEXT.md` does not yet carry — FR-025 adds it.

**Naming**: the surface is named after Django's own — `django.contrib.admin`'s inlines and the parameters of `inlineformset_factory` — because that is the vocabulary almost every Django developer already has. django-extra-views solved this problem first and is worth reading, but it is a source of ideas rather than a surface to reproduce, and where the two disagree Django's naming wins.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A row set is declared as its own class (Priority: P1)

A developer configures a page carrying one row set by writing a declaration class: one class per
related model, carrying that set's own configuration, listed on the view. The parent's form and
the set's rows render, validate and save together, and the configuration lives somewhere that can
hold more than one of itself.

**Why this priority**: Every other story in this feature is expressed in terms of the declaration
class. Until configuration moves off the view and onto a per-set object, there is nowhere for a
second set's parameters to go, and no amount of later work changes that. A working one-set page is
also the smallest thing this feature can ship that is worth having on its own.

**Independent Test**: Configure a view with one declaration class against a parent and one related
model, render the create and update pages, and submit both a valid and an invalid submission.
Judged against the acceptance scenarios below, not against what the removed attributes produced.
Delivers a working single-set page on the new configuration surface.

**Acceptance Scenarios**:

1. **Given** a view listing one declaration class naming a related model and its fields, **When** the update page is requested, **Then** the parent's form renders and the set's rows render beneath it, each row through the packaged form components.
2. **Given** the same view, **When** a valid submission is posted, **Then** the parent record and the set's rows are saved together and the page redirects to the success URL.
3. **Given** a declaration class that does not name a related model, **When** the view is used, **Then** the misconfiguration is reported when the page is built rather than producing an empty or partial page.
4. **Given** a declaration class carrying parameters that shape the generated formset class and parameters that shape the formset instance, **When** the set is built, **Then** each group reaches the stage it belongs to, named as Django names it.
5. **Given** a view configured with a queryset and no explicit parent model, **When** the page is built, **Then** the parent model is resolved the way Django's own model-form pages resolve it, and the sets are built against that model.
6. **Given** a declaration needing a formset parameter the declaration class does not expose as an attribute, **When** the developer overrides the method that assembles that group of parameters, **Then** their addition reaches the formset without the declaration class having to grow an attribute for it.
7. **Given** a declaration that gives each form in the set a different keyword argument according to its position, **When** the set is built, **Then** each form receives the argument meant for it, and the blank template form is distinguishable from a real one.
8. **Given** a declaration that decides its own display order, **When** the page renders, **Then** the forms appear in that order, and the order rows are validated and saved in is unchanged.
9. **Given** a set declaring a minimum number of rows, **When** a submission carries fewer, **Then** it is rejected.

---

### User Story 2 - Several row sets on one page (Priority: P1)

A developer lists two or more declaration classes on one view. The page shows the parent's form
followed by every set, each under its own heading. A submission carrying changes across several
sets saves all of them together, and a failure anywhere leaves nothing saved.

**Why this priority**: This is the gap the feature exists to close, and it is the reason the
declaration class was introduced. It is second only because it is expressed entirely in terms of
US1's surface and cannot be built before it.

**Independent Test**: Configure a view with two declaration classes against two different related
models, render the page, submit changes to rows in both sets at once, and confirm both sets
persist. Delivers the multi-set page.

**Acceptance Scenarios**:

1. **Given** a view listing two declaration classes, **When** the page is requested, **Then** both sets render, each under its own heading, in the order the view lists them.
2. **Given** the same page, **When** a submission adds a row to each set, **Then** both rows are saved and both belong to the parent record.
3. **Given** the same page, **When** the submission carries a row that fails validation in the second set, **Then** nothing is saved, including the first set's rows and the parent record.
4. **Given** a submission where two sets each carry a field of the same name, **When** it is read back, **Then** each set receives only its own rows' values.
5. **Given** two declaration classes that resolve to the same prefix, **When** the view is configured, **Then** the conflict is reported as a configuration error rather than the two sets silently sharing a submission.
6. **Given** two declaration classes naming the same related model through two different relations to the parent, **When** the page is built, **Then** both sets are built and their prefixes differ without either declaration setting one.
7. **Given** a page where several sets can carry uploads, **When** the page renders, **Then** the form is encoded for uploads if any set on the page needs it.
8. **Given** a page with two sets, each with its own row cap, **When** a submission is within one set's cap and above the other's, **Then** only the set over its cap is rejected and the other set's cap plays no part in the outcome.
9. **Given** a parent reachable from a related model by two foreign keys, **When** a declaration names which one it uses, **Then** the set is built against that relation and its rows are those the named relation reaches.

---

### User Story 3 - Every set reports its own errors (Priority: P1)

A developer submits a page whose first set has an invalid row. The page comes back showing that
error beside the row that caused it, and showing any errors the later sets have as well, rather
than reporting the first failure and rendering the rest as though they were fine.

**Why this priority**: A page that stops validating at the first failure is worse than the
single-set page it replaces, because it hides errors that exist. It is a correctness property of
the multi-set page rather than an addition to it, which is why it sits at P1 alongside US2 rather
than being folded into it: it is independently testable and independently able to regress.

**Independent Test**: Submit a page with two sets where both carry an invalid row, and confirm
both errors are shown on the redisplayed page. Delivers trustworthy error reporting across sets.

**Acceptance Scenarios**:

1. **Given** a page with two sets and an invalid row in each, **When** it is submitted, **Then** the redisplayed page shows an error against both rows.
2. **Given** a page whose parent form is invalid and whose sets are also invalid, **When** it is submitted, **Then** the parent's errors and every set's errors appear together.
3. **Given** a refused submission, **When** the page is redisplayed, **Then** every set shows the values that were submitted rather than the stored ones, and the page's own object-derived parts (title, breadcrumbs) show the stored record.

---

### User Story 4 - A page that edits only the related rows (Priority: P2)

A developer wants an update page that edits a record's related rows without exposing the record's
own fields — a page for an order's line items where the order's reference and customer are not
editable. They configure the same view with no parent fields, and the page renders the sets alone,
attached to the record the URL identifies.

**Why this priority**: This is the second half of what django-extra-views splits across two view
classes, folded into one here. It is genuinely valuable on its own and is the case a developer
currently has to write by hand, but it depends on the multi-set machinery being in place, and a
developer with US1 to US3 has a working feature without it.

**Independent Test**: Configure an update view with no parent fields and one declaration class,
request the page, and confirm no parent fields render and the set's rows are those of the record
the URL names. Delivers the rows-only page.

**Acceptance Scenarios**:

1. **Given** an update view whose parent fields are empty, **When** the page is requested, **Then** no parent fields render and every configured set renders against the record the URL identifies.
2. **Given** that page, **When** a valid submission is posted, **Then** the rows are saved against that record and the record's own field values are unchanged.
3. **Given** that page and a parent carrying a last-modified timestamp, **When** a valid submission is posted, **Then** the parent's timestamp reflects the change by default, and a developer who switches that off gets a parent the submission did not touch at all.
4. **Given** that page and a parent whose other fields were changed by someone else while the page was open, **When** a valid submission is posted, **Then** that other change survives.
5. **Given** that page, **When** a submission is refused, **Then** the page redisplays with the set's errors and still shows no parent fields.
6. **Given** a create view configured with no parent fields, **When** it is used, **Then** the misconfiguration is reported, because there would be nothing to create the parent record from.
7. **Given** an update view with no parent fields and no sets listed, **When** it is used, **Then** the misconfiguration is reported, because the page could edit nothing.

---

### User Story 5 - The migration is documented and demonstrated (Priority: P2)

A developer upgrading finds the `inline_*` attributes gone, and the changelog and documentation
tell them what replaces each one and how to rewrite a view. A developer arriving fresh finds the
documented path from two models to a page carrying both their row sets, and the demo application
has a page that does it.

**Why this priority**: The feature removes a public surface without a deprecation period, so the
note that explains the rewrite is part of shipping it rather than a follow-up. It is P2 because
the capability is usable before it is documented, and because the documentation is written against
whatever the earlier stories actually landed.

**Independent Test**: Read the changelog entry and the formsets guide against a view written on
the old attributes, and confirm the rewrite can be performed from them alone. Delivers a
migratable, discoverable feature.

**Acceptance Scenarios**:

1. **Given** the changelog for the release, **When** a developer reads it, **Then** the removal is stated as breaking and each removed attribute is mapped to its replacement.
2. **Given** the formsets guide, **When** a developer follows it, **Then** it walks from models to a page carrying more than one row set, and covers the rows-only page.
3. **Given** the demo application, **When** it is run, **Then** it has a page carrying more than one row set.
4. **Given** the package's own documentation and demo, **When** they are searched, **Then** no `inline_*` attribute remains described as a supported way to configure a page.
5. **Given** a project importing the packaged inline view classes, **When** it upgrades, **Then** the import still resolves and only the view's configuration has to be rewritten.
6. **Given** `CONTEXT.md`, **When** it is read, **Then** it carries the term for the declaration class alongside the row set and related row it already defines.

---

### Edge Cases

- Two declaration classes naming the same related model through the same relation. Their default
  prefixes are identical, so one must state a prefix or the page is a configuration error. This is
  the ordinary way the prefix conflict is met.
- A related model reachable from the parent by more than one relation. The default prefix already
  distinguishes the two, because it is derived from the relation rather than the model, but the
  declaration must still be able to name which relation it uses when the parent has more than one
  and Django cannot choose.
- A set whose row cap is reached, where the submission also removes rows. Removed rows must not
  count toward the cap, and a submission that is within the cap after removals must be accepted.
- A submission that arrives with a row count above what the page offered.
- An update page whose parent fields are empty and which lists no sets at all — a page that can
  edit nothing.
- A set configured with a custom form class that itself declares the fields.
- The rows-only page reached through a view that also allows the parent record to be deleted, so
  the page's other controls still resolve against the record.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A row set MUST be configurable as a declaration class naming the related model and carrying that set's own configuration, independently of any other set.
- **FR-002**: The declaration class MUST separate the parameters that shape the generated formset class from those that shape the formset instance, and MUST name its options after Django's own — the attributes `django.contrib.admin`'s inlines use and the parameters `inlineformset_factory` takes.
- **FR-003**: A view MUST accept an ordered list of declaration classes and build every one of them.
- **FR-004**: Each set's prefix MUST default to the one Django derives for that relation, and MUST be overridable per declaration.
- **FR-005**: Two sets resolving to the same prefix MUST raise a configuration error rather than being built.
- **FR-006**: A declaration class that does not name a related model MUST raise a configuration error.
- **FR-007**: The parent model MUST fall back to the one derived from the view's queryset when it is not stated explicitly, matching how Django's own model-form pages resolve it.
- **FR-008**: Every set MUST be validated on submission even after an earlier set has failed.
- **FR-009**: A submission MUST be saved only when the parent form and every set are valid, and the parent record and every set MUST be saved in one transaction.
- **FR-010**: A refused submission MUST redisplay every set carrying the submitted values and their errors, while the page's object-derived parts show the stored record.
- **FR-011**: Each set MUST render under its own heading, defaulting to the related model's plural name and overridable per declaration, with optional help text beneath it.
- **FR-012**: The page MUST be encoded for uploads when any set or the parent form requires it, decided from all of them together.
- **FR-013**: A row cap on a set MUST reject a submission that exceeds it, MUST NOT count rows the submission removes, and MUST NOT discard rows from a submission that is within the cap. Each set's cap is enforced independently of every other set on the page.
- **FR-014**: An update page MUST render no parent fields when the parent's fields are configured empty, and MUST still render every configured set against the record the URL identifies.
- **FR-015**: A page rendering no parent fields MUST NOT write the parent record's own field values, and MUST NOT lose a change another writer made to the record while the page was open.
- **FR-016**: A page rendering no parent fields MUST be able to record that its rows changed on the parent record's own last-modified timestamp, and a developer MUST be able to switch that off. Where the parent has no such timestamp there is nothing to record and the page does nothing.
- **FR-017**: A create page configured with no parent fields MUST raise a configuration error.
- **FR-018**: An update page configured with neither parent fields nor any set MUST raise a configuration error.
- **FR-019**: The declaration class MUST be able to name which relation to the parent it uses, for a related model reachable by more than one.
- **FR-020**: A developer MUST be able to supply a formset parameter the declaration class does not expose, by overriding the method that assembles that group of parameters rather than by the declaration growing an attribute for every parameter Django accepts.
- **FR-021**: A developer MUST be able to decide the keyword arguments passed to each individual form in a set, distinguishing one form from another, and not only the arguments shared by every form in it.
- **FR-022**: A developer MUST be able to decide the order a set's forms are displayed in, independently of the order they were loaded or added. This affects display only and MUST NOT change the order in which rows are validated or saved.
- **FR-023**: A set MUST be able to declare a minimum number of rows, and a submission below that minimum MUST be rejected.
- **FR-024**: The `inline_*` view attributes MUST be removed, with no configuration path left that depends on them. The names of the packaged view classes MUST NOT change.
- **FR-025**: The package's documentation, reference material, glossary and demo application MUST show the multi-set page and the rows-only page, MUST define the declaration class as a domain term, and MUST NOT describe the removed attributes as a supported configuration.
- **FR-026**: The release's changelog MUST record the removal as breaking and map each removed attribute to its replacement.

### Key Entities

- **Row set declaration**: One related model's configuration for one page, written once and reusable across views. It carries:

  - the related model, and which relation to the parent it uses
  - which of that model's fields to edit, or a form that decides
  - how many blank rows to offer, and whether rows can be removed
  - a cap on the number of rows, and any minimum
  - the prefix its rows submit under
  - the heading shown above the set, and any help text below it
  - what distinguishes one form in the set from another, and the order they are displayed in

  Its parameters are split into those that shape the generated formset class and those that shape the formset instance.
- **Parent record**: The record the page edits or creates, and the record every set's rows belong to. Its own fields may be absent from the page.
- **Page**: One parent record and an ordered list of row sets, submitted and saved as a unit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A view carrying two row sets is configured without writing a formset, a prefix, or a save by hand.
- **SC-002**: A submission that changes rows in more than one set on one page results in every change persisted, or, if any part is invalid, none of them.
- **SC-003**: A submission that is invalid in more than one set reports every one of those errors on a single redisplay, with no error hidden behind an earlier failure.
- **SC-004**: An update page can be configured to edit only a record's related rows, without the record's own fields appearing and without altering its field values, while still recording that something changed on the record's own timestamp when the developer wants that.
- **SC-005**: A page built on the previous `inline_*` attributes can be rewritten onto the new surface using only the changelog entry and the documentation.
- **SC-006**: Every configuration mistake this feature can make — a set with no related model, two sets sharing a prefix, a create page with no parent fields, an update page that can edit nothing — is reported when the page is built, not as a wrong page.
- **SC-007**: A set whose forms each need different arguments, or a set that must display its forms in a particular order, is configured on the declaration rather than by subclassing Django's formset machinery.

## Clarifications

*Recorded during the clarification scan. Each answer is integrated into the requirement, scenario
or edge case it affects. This section is the record, not the requirement. Longer rationale is in
`decisions.md`.*

### Session 2026-08-11 (plan gate)

- **Q**: Should the surface be named after django-extra-views, so a developer arriving from that package finds the names where they expect them?
  **A**: No. Take the ideas, name them ourselves, and where a name is already Django's, use Django's — which is what most new developers will recognise. `django.contrib.admin`'s inlines are the reference, so the declaration is an `InlineFormSet`. Sam's ruling. This also corrects a mistake in the research: the shorthand attributes were described as a divergence from django-extra-views needing justification, when they are in fact Django's own names for the same options, and that package is the one that removed them.
- **Q**: On the rows-only page, must the parent record be left entirely untouched?
  **A**: No. Not recording the change anywhere is the surprising outcome, because the rows and their parent are one connected record from a reader's point of view — a project whose description changed should show as having changed. The page records it on the parent's last-modified timestamp by default and a developer can switch that off, and where the parent carries no such timestamp there is nothing to record. Recorded as FR-016 and in US4.
- **Q**: Are a minimum row count and user-driven row ordering part of this feature?
  **A**: The minimum is; user-driven ordering is not, and is deferred until something asks for it. The two were bundled together in the plan and removed together, which was wrong — they are unrelated options that happened to be adjacent. Recorded as FR-023.
- **Q**: Is one set of keyword arguments per set enough, or must individual forms differ?
  **A**: Individual forms must be able to differ. A set that shows one form per permitted kind needs each form to know which kind it is, and a set that validates against its siblings needs each form to know what the others hold. Django already has the hook for this and it takes the form's position; the shared-dictionary shape is what makes it unreachable. Recorded as FR-021, with display order as FR-022.

### Session 2026-08-11 (Spec gate)

- **Q**: Do the `inline_*` view attributes keep working alongside the declaration class for a release?
  **A**: No. They are removed outright and the two surfaces never coexist. Confirmed by Sam at the Spec gate; already recorded as FR-020, restated here because a compatibility shim is the obvious thing to reach for and it is refused.
- **Q**: Must the new surface reproduce the removed attributes' behaviour?
  **A**: No. This feature is an overhaul of the previous one, not a port of it. The specification below is the whole of what the page must do, and a difference from what the removed attributes produced is not by itself a defect. Sam's ruling at the Spec gate. Recorded in US-1, SC-005 and Assumptions.

### Session 2026-08-11 (clarification scan)

- **Q**: What does a set's prefix default to, and when exactly do two sets collide?
  **A**: The prefix Django already derives for the relation, which is the reverse accessor name rather than the model name. Two sets on the same related model through *different* relations therefore differ without either declaration saying anything, and only two declarations on the *same* relation collide. Recorded as FR-004, US2 scenarios 5 and 6, and the first two Edge Cases.
- **Q**: Do the packaged view class names change, now that one view covers both the parent-and-rows page and the rows-only page?
  **A**: No. The feature changes how a page is configured, not what the view is. Renaming would widen a breaking change that already removes six attributes, for no gain to a reader — "inline" is the same word Django admin uses for the same idea. Recorded as FR-020.
- **Q**: Is the declaration class's attribute list the whole configuration surface?
  **A**: No, and it must not become one. It carries what the six `inline_*` attributes carried plus the prefix and the relation name, and anything else is reached by overriding the method that assembles that group of parameters — the super-and-extend pattern the current view already documents. Recorded as FR-019 and US1 scenario 6.
- **Q**: Which words does the spec use for these things, given the tracking issue and `CONTEXT.md` differ?
  **A**: `CONTEXT.md`'s, because the repository glossary is canonical: **row set** and **related row**. The issue's "related set" is the same concept. The declaration class has no term yet, so the glossary gains one. Recorded in Vocabulary above and as FR-021.
- **Q**: Does the row cap behave differently now that a page can carry several sets?
  **A**: No. Each set's cap is enforced on its own submission-shaped slice and never against the page's total, and the enforcement is the one FS-024 settled — reject above the cap, leave Django's absolute ceiling alone, so a submission within the cap after removals is accepted rather than silently truncated. Recorded as FR-013.

## Assumptions

- The package is pre-1.0, so removing the `inline_*` attributes in the same release that introduces their replacement is acceptable and needs a changelog note rather than a deprecation period. This is stated in the tracking issue and confirmed at the Spec gate. The two configuration surfaces never coexist, and no compatibility shim is written.
- This feature is an overhaul of the previous one rather than a port of it. Behavioural parity with the removed attributes is not a requirement, and a difference from what they produced is not by itself a defect. Where this specification is silent, the packaged single-form pages are the precedent, not the removed attributes. Sam's ruling at the Spec gate.
- FS-024 assumed one parent and one row set, and said the shape would be revisited when a case for it appeared. This feature is that revisit. FS-024's assumption and the intake clarification behind it are annotated in place on `specs/024-formset-pages/spec.md` rather than left to read as current.
- The branch `024-multi-inline-wip` is a sketch of the intended shape, not a candidate for merge, and carries no authority over the decisions this spec makes.
- The naming follows Django's own — `django.contrib.admin`'s inline attributes and `inlineformset_factory`'s parameters — because that is the vocabulary most Django developers already have. django-extra-views solved this problem first and its design is worth reading, but it is a source of ideas rather than a surface to reproduce. Why the view logic is written in this package rather than inherited from it is already recorded as R10 in `specs/024-formset-pages/research.md` and is not reopened here.
- Rendering, browser-side row adding and removing, and per-row error display already work for a single set and are reused rather than rebuilt. This feature is about how sets are configured, how several of them coexist on a page, and how the page saves.
- The rows-only page is an update-page capability only. Creating a parent record from a page that never shows its fields is out of scope and is a configuration error.
- Deriving a set's forms from a list of permitted kinds — one form per kind whether or not a row exists — is a thing a project builds on this surface, not a thing this feature packages. What this feature owes it is the per-form arguments and the display order; the rest is already reachable through the formset's own initial data.
- Rendering a set outside the packaged form components stays out of scope, as it was for the single-set page.
- No per-row permission surface is introduced, as FS-024 settled: the page behaves for a user as the packaged single-form pages behave.
