# Feature Specification: Model Resolution Mixin

**Feature Branch**: `005-model-resolution-mixin`
**Created**: 2026-05-03
**Status**: Draft
**Input**: User description: "Any view that renders or manipulates a model record needs to know what model it is dealing with. Django gives developers several ways to express this — a model attribute, a queryset, a form class, an already-resolved object — and in practice all of these appear in real projects. This spec defines a single, consistent resolution mechanism that works regardless of which style a downstream view uses. Views that build on this should never need to ask 'which configuration style was used?' — the answer should always just be available. This spec refers specifically to the ModelInfoMixin currently in mvp.views.detail"

## Clarifications

### Session 2026-05-03

- Q: Does this spec describe the current implementation or prescribe a future target state? → A: Prescriptive — spec defines the target; planner evaluates whether current code needs changes or additions.
- Q: Where should `ModelInfoMixin` live? → A: Move to `mvp.views.base`, alongside `BaseTemplateNameMixin` and `PageMixin`.
- Q: What should the template context key for model metadata be named? → A: `model_info`.
- Q: Should the `model_info` dict expose the resolved model class itself? → A: No — metadata fields only; model class is accessible in Python via `get_model_class()`, not in the template context.
- Q: Should the spec require caching of the resolved model class? → A: No — caching is an implementation detail; the spec makes no requirement about it.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use Any Configuration Style Transparently (Priority: P1) [Developer]

As a developer building views with django-mvp, I can express my model using whichever Django style fits my code — a direct model reference, a queryset, a ModelForm class, or a pre-fetched object — and the framework will always identify the correct model without requiring me to adapt or add extra code to accommodate the resolution process.

**Audience**: Developer (integrator)
**Why this priority**: This is the core contract of the mixin. Every downstream feature that builds on model-aware views depends on resolution working correctly across all four styles. Without it, developers would need to maintain separate paths for each style, defeating the purpose of the abstraction.
**Independent Test**: Four minimal view classes — each configured with exactly one of the four supported styles — are pointed at the same model. All four views must produce identical model metadata context without any view-specific resolution code.

**Acceptance Scenarios**:

1. **Given** a view sets only a `model` attribute, **When** the view renders, **Then** the model's metadata is available in the template context and matches the configured model.
2. **Given** a view declares only a `queryset` attribute (with no explicit `model`), **When** the view renders, **Then** the model's metadata resolves from the queryset's associated model and is available in the template context.
3. **Given** a view specifies only a ModelForm `form_class` (with no explicit `model` or `queryset`), **When** the view renders, **Then** the model's metadata resolves from the form's declared model and is available in the template context.
4. **Given** a view has no static model configuration but receives a pre-fetched model instance as `object` at runtime, **When** the view renders, **Then** the model's metadata resolves from the instance's class and is available in the template context.

---

### User Story 2 - Extend Resolution With a Custom Strategy (Priority: P2) [Developer]

As a developer whose view cannot express its model through any of the four standard styles, I can override a single, named method to supply my own resolution logic so I can still use all model-aware view features without forking the base class.

**Audience**: Developer (integrator)
**Why this priority**: Edge cases exist (dynamic model selection, multi-tenancy, proxy model switching) where no standard style is sufficient. A clean override point prevents developers from abandoning the mixin entirely when their situation is unusual.
**Independent Test**: A view subclass that overrides the resolution method and returns a model class not reachable via any standard style correctly makes that model's metadata available in context, with all downstream consumers (page title, breadcrumbs, directory) working correctly.

**Acceptance Scenarios**:

1. **Given** a developer overrides the resolution method to return a dynamically chosen model, **When** the view renders, **Then** all model-derived context values reflect the dynamically chosen model.
2. **Given** a developer overrides the resolution method and their logic raises an unhandled exception, **When** the view renders, **Then** the exception propagates normally without being swallowed by the resolution mechanism.

---

### User Story 3 - Receive a Diagnostic Error for Misconfigured Views (Priority: P2) [Developer]

As a developer who forgets to provide any resolvable model configuration, I receive a clear error message that names the offending view and lists the configuration options available to me so I can fix the problem without guessing.

**Audience**: Developer (integrator)
**Why this priority**: Silent failures or opaque stack traces waste debugging time. A clear, actionable error message with the view class name and configuration options available reduces time-to-fix significantly.
**Independent Test**: A view that inherits the mixin but supplies no model, queryset, form class, or object triggers a configuration error whose message identifies the view class by name and describes the available resolution options.

**Acceptance Scenarios**:

1. **Given** a view inherits the mixin and provides no model-identifying configuration, **When** a request is handled, **Then** an error is raised that identifies the view class by name and describes the supported configuration options.
2. **Given** a view provides a queryset with no associated model information and no other configuration, **When** a request is handled, **Then** the same clear configuration error is raised.

---

### User Story 4 - See Correct Model Labels in Rendered Views (Priority: P1) [End User]

As an end user viewing any model-driven page — a detail page, a form, a confirmation prompt — I see labels, headings, and titles that correctly name the data type I am working with, regardless of how the developer configured the underlying view.

**Audience**: End User
**Why this priority**: Model-derived labels (verbose names, plural names, breadcrumb text) directly shape the readability and usability of every model-driven page. Incorrect or missing labels immediately degrade user trust.
**Independent Test**: Four views configured with each of the four resolution styles, all targeting the same model, render pages whose headings and titles display the expected human-readable model name. No page shows a raw identifier, empty string, or wrong model name.

**Acceptance Scenarios**:

1. **Given** a developer has used any supported configuration style, **When** an end user opens the corresponding page, **Then** the page title and any heading labels correctly name the model in human-readable form.
2. **Given** a model has a custom verbose name defined, **When** an end user opens a page for that model, **Then** the custom name appears in headings rather than the internal model identifier.

---

### Edge Cases

- A view has both `model` and `queryset` configured with different models — the resolution priority order must be applied consistently and predictably.
- A view's `get_queryset()` raises an exception — resolution must not surface an unrelated error; it must proceed to the next strategy.
- A view has a `form_class` that is a plain `Form` (not a `ModelForm`) with no `_meta.model` — the form strategy must be skipped silently and resolution must continue.
- `self.object` is present but set to `None` — the object strategy must be skipped, not treated as a resolution result.
- `get_form_class()` raises an exception — resolution must not surface an unrelated error; it must proceed to the next strategy.
- A view uses a proxy model — resolution must return the proxy model class, not the concrete parent.
- All four strategies are present simultaneously — priority order must be applied deterministically.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The mechanism MUST resolve the model class when the view declares a `model` attribute directly.
- **FR-002**: The mechanism MUST resolve the model class from an associated queryset when no `model` attribute is set.
- **FR-003**: The mechanism MUST resolve the model class from a ModelForm `form_class` when neither `model` nor a model-bearing queryset is available.
- **FR-004**: The mechanism MUST resolve the model class from a pre-fetched model instance bound to the view when no earlier strategy succeeds.
- **FR-005**: Resolution MUST follow a fixed priority order: direct model attribute → queryset → form class → object instance.
- **FR-006**: The mechanism MUST raise a clear configuration error when none of the four strategies can identify a model class. The error MUST name the offending view class and describe the available configuration options.
- **FR-007**: The mechanism MUST provide a single, named override point that developers can use to supply custom resolution logic without modifying the base class.
- **FR-008**: The mechanism MUST expose the resolved model's human-readable name, plural name, application label, and internal model name to the template context under the key `model_info`. This key MUST remain stable across all view types that use the mixin. The `model_info` dict MUST NOT include the model class itself; Python consumers that require the class MUST call `get_model_class()` directly.
- **FR-009**: When a queryset-based strategy or a form-class strategy raises an internal exception during resolution, the mechanism MUST silently skip that strategy and attempt the next one rather than surfacing an unrelated error.
- **FR-010**: The mechanism MUST treat a `None`-valued `object` as an absent configuration, not as a valid resolution result.
- **FR-011**: All downstream view features that depend on model identity (page titles, breadcrumbs, CRUD directory URLs, CSS class injection) MUST consume the resolved model class through the same single mechanism; no downstream feature may implement its own independent model resolution.
- ~~**FR-012**~~ *(removed during clarification — caching of the resolved model class is an implementation detail, not a spec requirement)*
- **FR-013**: The mixin MUST be defined in `mvp.views.base`, co-located with other shared view mixins (`BaseTemplateNameMixin`, `PageMixin`). The class definition MUST be removed from `mvp.views.detail`; `mvp.views.detail` MUST retain a backward-compatible re-export (`from .base import ModelInfoMixin`) so existing callers of `mvp.views.detail.ModelInfoMixin` are NOT required to update their imports.

### Assumptions

- This specification is prescriptive: it defines the desired target behavior. The plan phase is responsible for evaluating whether the current `ModelInfoMixin` implementation fully satisfies all requirements and for generating tasks to close any gaps.
- Developers using the mixin are building standard Django views that work with a single model type per request.
- Proxy models are valid configuration targets and must be treated as distinct from their concrete parents.
- The four supported configuration styles (direct model, queryset, form class, object instance) cover all common Django view patterns used within this project.
- Template context consumers are responsible for rendering the metadata values; this mechanism is only responsible for supplying them correctly.
- Resolution correctness is defined entirely within a single request/response cycle; cross-request state is not a concern.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of acceptance scenarios for all four configuration styles pass in automated testing with no view-specific workarounds required.
- **SC-002**: A developer can add the mixin to an existing view using any of the four configuration styles and have model metadata available in context without writing any resolution code.
- **SC-003**: When no model can be resolved, the resulting error message identifies the view class by name in 100% of cases, enabling a developer to locate and fix the misconfiguration without additional diagnostic tools.
- **SC-004**: Zero downstream view features contain independent model resolution logic; all rely exclusively on the single shared mechanism.
- **SC-005**: Model metadata context values (human-readable name, plural name, application label, internal name) are correct for 100% of tested model configurations, including models with custom verbose names and proxy models.
