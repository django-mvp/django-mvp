# Feature Specification: MVP Delete View

**Feature Branch**: `013-mvp-delete-view`
**Created**: 2026-05-05
**Status**: Draft
**Input**: User description: "The Django built-in delete view does one thing: confirm and delete. Real applications need more. This spec covers multiple scenarios. 1) A simple confirmation page (the default, requiring no configuration). 2) An opt-in mode that shows the user which related records will also be removed before they commit with the goal being to make informed deletion a one-line opt-in rather than a custom implementation. 3) When a record cannot be deleted because another record holds a protected foreign key to it, the view should detect that automatically, tell the user what is blocking deletion, and hide the Delete button — rather than raising an unhandled exception. 4) When a record is particularly sensitive and the developer wants to make accidental deletion very difficult, the view should support a type-to-confirm mode where the user must type a confirmation string (typically the record's name) before the delete proceeds."

## Clarifications

### Session 2026-05-05

- Q: Who is responsible for access control on the delete view? → A: Developer's responsibility; the view does not enforce authentication or permissions itself.
- Q: Is there a cap on how many related objects are displayed in the related-objects summary? → A: Yes — display up to a configurable maximum per group (default 25); show "… and N more" when truncated.
- Q: What is the default page title string? → A: `_("Delete %(verbose_name)s")` — e.g. "Delete Product", consistent with Create/Update view naming pattern.
- Q: What is the breadcrumb structure on the delete page? → A: List → Detail → Delete (three levels), mirroring MVPUpdateView.
- Q: What is the default success message string? → A: `_("%(verbose_name)s successfully deleted.")` — uses `verbose_name` (lowercase), consistent with Create/Update views.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Simple Confirmation (Priority: P1)

**Audience**: [Developer] · [End User]

A developer adds a delete view to their application. Without setting any extra options, the view presents the user with a warning message and two controls: a Go Back button and a Delete button. Pressing Delete permanently removes the record and redirects the user to a success destination. This is the entry-level experience — it should work with zero configuration beyond `model` and `success_url`.

**Why this priority**: Every other scenario builds on this baseline. It is also the most common real-world need — most records can be safely deleted without special ceremony.

**Independent Test**: Create a `MVPDeleteView` subclass with only `model` and `success_url` set. Confirm that a GET request renders a warning and a Delete button, and that a POST request deletes the record, emits a flash message, and redirects.

**Acceptance Scenarios**:

1. **Given** a delete view with no special configuration, **When** a user visits the page, **Then** they see a warning that the deletion is permanent and cannot be undone, plus a Go Back button and a Delete button.
2. **Given** a user on the confirmation page, **When** they press Delete, **Then** the record is removed, a success flash message appears, and they are redirected to the configured destination.
3. **Given** a user on the confirmation page, **When** they press Go Back, **Then** they return to the previous page without any record being deleted.

---

### User Story 2 — Related-Objects Summary (Priority: P2)

**Audience**: [Developer] · [End User]

A developer sets `show_related_objects = True` on their delete view. When a user visits the page, they see not only the warning but also a grouped list of all records that will be cascade-deleted along with the target record. No custom template or queryset code is required; the view derives this information automatically. The user can then make an informed decision before committing.

**Why this priority**: Cascade deletes silently remove child records in the default scenario. Showing them prevents data loss surprises and reduces support tickets. Because it is opt-in, existing views are unaffected.

**Independent Test**: Set `show_related_objects = True` on a view whose model has child records. Confirm that the confirmation page lists the related objects grouped by record type, and that the Delete button is still present and functional.

**Acceptance Scenarios**:

1. **Given** `show_related_objects = True` and the target record has related child records, **When** a user visits the confirmation page, **Then** they see a grouped list of all records that will also be deleted, labelled by record type.
2. **Given** `show_related_objects = True` and the target record has no related child records, **When** a user visits the confirmation page, **Then** no related-objects section is shown and the page is identical to the basic confirmation.
3. **Given** the related-objects summary is visible, **When** the user presses Delete, **Then** the target record and all listed related records are deleted together.

---

### User Story 3 — Protected-Record Detection (Priority: P2)

**Audience**: [Developer] · [End User]

When another record holds a `PROTECT` foreign key referencing the object the user is trying to delete, the view detects this automatically on page load, shows the user a message explaining which records are blocking the deletion, and hides the Delete button entirely. No unhandled exception reaches the browser. The developer does not need to write any guard code.

**Why this priority**: Without this, a `ProtectedError` propagates as an unhandled 500. This scenario is equally critical to the related-objects summary — both deal with relational data — but a crashing 500 is more urgent than a missing summary list.

**Independent Test**: Configure a delete view for a record that is referenced by a `PROTECT` foreign key. Confirm that the GET response shows the blocking record(s) by name, shows no Delete button, and that a crafted POST request is also rejected without crashing.

**Acceptance Scenarios**:

1. **Given** the target record is referenced by one or more protected foreign keys, **When** a user visits the confirmation page, **Then** they see a message that the record cannot be deleted and a list of the records preventing deletion.
2. **Given** the protected-record state, **When** the page is rendered, **Then** the Delete button is not present.
3. **Given** the protected-record state, **When** a POST request is submitted (e.g. by a user with browser tools), **Then** the view does not crash; it re-renders the page with the protection message.

---

### User Story 4 — Type-to-Confirm (Priority: P3)

**Audience**: [Developer] · [End User]

A developer marks a sensitive delete view with `require_confirmation = True`. When a user visits the page, they see an input field alongside the warning, labelled with a clear prompt and showing the exact string they must type (typically the record's string representation). The Delete button remains visible so the intended flow is clear, but submitting the form with an incorrect or empty value re-renders the page with a validation error and does not delete the record.

**Why this priority**: This is an additional safety layer for records that are costly to lose (configuration objects, customer accounts, etc.). Because it is opt-in it has no impact on other views.

**Independent Test**: Set `require_confirmation = True`. Confirm that the GET page shows the input and the expected confirmation string. Submit the form with an incorrect value and confirm the record is not deleted and an error message is shown. Submit with the correct value and confirm deletion proceeds.

**Acceptance Scenarios**:

1. **Given** `require_confirmation = True`, **When** a user visits the confirmation page, **Then** they see an input field and a prompt showing the exact string they must type before deletion is allowed.
2. **Given** the type-to-confirm input is shown, **When** the user submits the form with a value that does not match, **Then** the record is not deleted and an inline error message explains the mismatch.
3. **Given** the type-to-confirm input is shown, **When** the user submits the form with the exact expected value, **Then** deletion proceeds normally.
4. **Given** the type-to-confirm input is shown, **When** the user submits an empty value, **Then** the record is not deleted (empty string does not match a non-empty confirmation string).

---

### Edge Cases

- What happens when the record is both protected and has cascade children? Protected state takes precedence — the Delete button is hidden and protection details are shown.
- What happens when `show_related_objects = True` but protection is also detected? Protection message shown; related-objects list is suppressed (there is nothing to cascade-delete if the object is blocked).
- What happens when `require_confirmation = True` and the record is protected? The type-to-confirm input is not shown — a protected record cannot be deleted regardless of the confirmation string.
- What happens when the confirmation string contains special characters or whitespace? The match is exact; leading/trailing whitespace submitted by the user is stripped before comparison to account for accidental spaces.
- What destination does the view redirect to after deletion? First, a validated `?next=` parameter; second, the configured `success_url`; third, the list view URL from the CRUD directory. The object's own URL is never used as a fallback (it would 404 after deletion).
- What happens when no Go Back or redirect destination can be determined? The view degrades gracefully — an `ImproperlyConfigured` error is raised at development time, not in production silently redirecting to a wrong URL.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The view MUST render a confirmation page on GET with a permanent-deletion warning, a Go Back button, and a Delete button when the record is safe to delete and no special mode is active.
- **FR-002**: On a confirmed POST (all validation passed), the view MUST delete the record, emit a flash success message, and redirect to the resolved destination URL. The default success message MUST be `_("%(verbose_name)s successfully deleted.")`, where `%(verbose_name)s` is substituted with the model's `verbose_name` (e.g. "product"). Developers MAY override `success_message` on the class.
- **FR-003**: When `show_related_objects = True`, the view MUST inspect cascade relations and display a grouped list of all records that will also be deleted, labelled by record type, before the user commits. Each group MUST be capped at a configurable maximum (default 25 items); when the group exceeds this limit the view MUST show a "… and N more" truncation note rather than listing every record.
- **FR-004**: The view MUST automatically detect when a `PROTECT` constraint blocks deletion (without requiring any developer configuration) and render a blocking message listing the protecting records by name.
- **FR-005**: When a protected state is detected, the view MUST NOT render a Delete button, whether on GET or in response to a POST.
- **FR-006**: When `require_confirmation = True`, the view MUST render a text input field on the confirmation page displaying the expected confirmation string in the prompt.
- **FR-007**: When `require_confirmation = True` and the submitted value does not match the expected confirmation string, the view MUST re-render the confirmation page with an error message and MUST NOT delete the record.
- **FR-008**: The confirmation string MUST default to the string representation of the object being deleted. Developers MUST be able to override this via `get_confirmation_value()`.
- **FR-009**: The confirmation label and prompt text MUST be internationalisation-ready (translatable).
- **FR-010**: Post-deletion redirect destination MUST follow the priority chain: validated `?next=` parameter → `success_url` → list view URL from CRUD directory.
- **FR-011**: The Go Back button destination MUST be resolved from a validated `?back=` query parameter, falling back to the list URL.
- **FR-012**: All four scenarios MUST integrate with the AdminLTE layout (page title, breadcrumbs, page icon) through zero additional configuration.
- **FR-013**: The page title MUST be configurable via a `page_title` class attribute and MUST default to `_("Delete %(verbose_name)s")`, producing e.g. "Delete Product" or "Delete Order Line" from the model's `verbose_name`. This pattern is consistent with `MVPCreateView` and `MVPUpdateView`.
- **FR-014**: The view MUST render a three-level breadcrumb trail: List → Detail → Delete. The List and Detail links MUST be gated by their respective CRUD-directory permissions (rendered as plain text when the permission is absent, consistent with the update view breadcrumb behaviour).

### Key Entities

- **DeleteView**: The configurable Django class-based view that orchestrates all four deletion scenarios. Carries boolean flags (`show_related_objects`, `require_confirmation`) and a label string (`confirmation_label`) as class-level attributes.
- **Target Object**: The model instance to be deleted. The view derives the confirmation string and cascade/protection data from this instance.
- **Related Objects**: The set of records that would be cascade-deleted alongside the target. Grouped by record type for display. Present only when `show_related_objects = True` and no protection is detected. Display is capped per group (default 25); groups exceeding the cap show a "… and N more" note.
- **Protected Objects**: The set of records holding a `PROTECT` foreign key reference to the target. Derived automatically; their presence suppresses the Delete button.
- **Confirmation Value**: The string the user must reproduce in type-to-confirm mode. Defaults to `str(object)`; overridable by the developer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can add a working delete view to their application by writing a subclass with only `model` and `success_url` — no extra methods or templates required.
- **SC-002**: Enabling the related-objects summary requires a single line of configuration (`show_related_objects = True`) and no additional queryset or template code. The display cap and truncation note are applied automatically with a sensible default (25 per group) and are overridable via a class attribute.
- **SC-003**: Protected-record detection requires zero developer configuration; a view that would previously crash with an unhandled error renders a user-friendly blocking message instead.
- **SC-004**: Enabling type-to-confirm requires a single line of configuration (`require_confirmation = True`); the confirmation string and input label are derived automatically.
- **SC-005**: All four scenarios are visually consistent within the AdminLTE layout with no custom template work.
- **SC-006**: An incorrect confirmation string never results in a deleted record, regardless of how the POST request is constructed.
- **SC-007**: A protected record cannot be deleted through the view, regardless of how the POST request is constructed.

## Assumptions

- The target project uses Django's built-in ORM and `on_delete=PROTECT` / cascade semantics are expressed through Django model `ForeignKey` options.
- The AdminLTE layout, CRUD directory mixin, and `MVPModelFormBase` infrastructure from earlier features are in place and stable.
- The developer has registered the delete view in the project's URL configuration; the view itself does not handle URL routing.
- **Access control is the developer's responsibility.** The view does not enforce authentication or permissions; developers apply `LoginRequiredMixin`, `PermissionRequiredMixin`, or other standard Django mechanisms as needed.
- Deleting a record via this view always requires a two-step confirmation (GET then POST); direct single-request deletion is out of scope.
- Mobile support is in scope to the extent that the AdminLTE layout is responsive; no mobile-specific delete UX is required.
- The view does not implement soft-delete or archive workflows; all deletions are permanent and irreversible through this view.
