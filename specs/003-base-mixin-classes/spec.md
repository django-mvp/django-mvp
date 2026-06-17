# Feature Specification: Document and Test Core View Mixins

**Feature Branch**: `003-base-mixin-classes`
**Created**: May 2, 2026
**Status**: Refined
**Refined**: 2026-05-27 — Added `breadcrumbs` class attribute to `PageMixin`; removed deprecated `page_icon` and `page_caption` references
**Input**: User description: "BaseTemplateMixin and PageMixin are two mixin classes that are inherited by essentially all other view classes. These need to be explicitly defined documented and tested."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New Django Developers Learn Mixin Architecture (Priority: P1)

A new developer joining the project reads the django-mvp codebase and needs to understand the architectural foundation of view composition. They discover that most view classes inherit from `BaseTemplateNameMixin` and `PageMixin`, but the purpose of these mixins is unclear without deep code reading.

**Why this priority**: Core architectural understanding is essential for any new contributor. Without clear documentation, developers must reverse-engineer the patterns through trial and error, leading to implementation mistakes and inconsistent view patterns.

**Independent Test**: Can be fully tested by (1) reading the mixin documentation in isolation, (2) understanding the purpose of each mixin, and (3) tracing how they integrate into real view classes (MVPListView, MVPDetailView, etc.). Delivers: Clear onboarding path for new developers.

**Acceptance Scenarios**:

1. **Given** a new developer reading `BaseTemplateNameMixin` documentation, **When** they examine the class docstring and method documentation, **Then** they understand what problem this mixin solves and how it extends Django's template resolution
2. **Given** a new developer reading `PageMixin` documentation, **When** they examine the class docstring and method documentation, **Then** they understand the page context structure and how to customize page title, subtitle, icon, and breadcrumbs
3. **Given** a developer implementing a new view, **When** they search for "PageMixin" or "BaseTemplateNameMixin" in the codebase, **Then** they find clear documentation with usage examples

---

### User Story 2 - Code Maintainers Verify Mixin Behavior with Tests (Priority: P1)

A code maintainer refactoring the view system needs confidence that changes to `BaseTemplateNameMixin` and `PageMixin` don't introduce regressions. Current test coverage for these core mixins is unclear or incomplete.

**Why this priority**: Without tests, any change to these foundational mixins risks breaking all view classes that depend on them. This is a critical safety concern for a core framework component.

**Independent Test**: Can be fully tested by (1) running a comprehensive test suite for each mixin, (2) verifying that all methods return expected values, and (3) testing integration with Django's generic views. Delivers: Confidence in refactoring safety.

**Acceptance Scenarios**:

1. **Given** a test for `BaseTemplateNameMixin.get_template_names()`, **When** the test runs with a view that has `base_template_name` set, **Then** the template name list includes both the view-specific template and the base template in correct priority order
2. **Given** a test for `PageMixin.get_page_context()`, **When** the test runs with all page attributes set, **Then** the context dict contains all expected keys (title, subtitle, icon, class, breadcrumbs, caption) with correct values
3. **Given** a test for `PageMixin` with unset attributes, **When** the test runs, **Then** the context dict contains sensible defaults (empty strings, None, empty lists as appropriate)

---

### User Story 3 - View Developers Understand Extension Points (Priority: P2)

A view developer needs to extend the page rendering behavior (e.g., add custom breadcrumbs, modify page class dynamically). They need to know which methods to override and what contract they must maintain.

**Why this priority**: Understanding the extension points ensures consistent behavior across all views that use these mixins. This reduces copy-paste mistakes and improves code maintainability.

**Independent Test**: Can be fully tested by (1) creating a custom mixin that extends PageMixin by overriding `get_page_title()` and `get_breadcrumbs()`, (2) verifying the custom behavior integrates correctly into a view, and (3) confirming that the parent mixin behavior is respected. Delivers: Clear extension patterns.

**Acceptance Scenarios**:

1. **Given** documentation on `PageMixin` methods, **When** a developer reads `get_page_title()`, `get_page_subtitle()`, and `get_breadcrumbs()`, **Then** they understand each method is a hook for customization and can be overridden safely
2. **Given** a custom view subclassing `PageMixin`, **When** the view overrides `get_breadcrumbs()` to return project-specific breadcrumbs, **Then** those breadcrumbs appear in the page context alongside other page attributes

---

### Edge Cases

- What happens when `base_template_name` is `None` (its default) → raises `ImproperlyConfigured`; subclasses must always set it (mirrors Django's `TemplateResponseMixin` behaviour)
- How does `get_page_context()` behave when parent classes don't implement `super().get_context_data()`? → Resolved: `PageMixin` is only used mixed with a Django generic view (`TemplateView`, `ListView`, etc.), all of which provide `get_context_data()`. Using `PageMixin` without a proper Django view base is not a supported use case.
- What if multiple views in an inheritance chain override `get_page_title()`? → Resolved: standard Python MRO applies; the most-derived class wins. No special handling is needed or planned.
- How does `PageMixin.get_page_class()` handle `None` values for `page_class`? → Resolved: `filter(None, ["mvp-page", None])` silently drops `None`; result is `"mvp-page"`. Covered by `test_get_page_class_with_none_page_class` (see T019).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide clear docstrings for `BaseTemplateNameMixin` explaining its purpose: extending Django's `get_template_names()` to support a fallback base template
- **FR-002**: System MUST provide clear docstrings for all public methods of `BaseTemplateNameMixin` (`get_template_names()`) documenting parameters, return type, and behavior
- **FR-003**: System MUST provide clear docstrings for `PageMixin` explaining its purpose: adding page-level context (title, subtitle, icon, CSS class, breadcrumbs) to template rendering
- **FR-004**: System MUST provide clear docstrings for all public methods of `PageMixin` (`get_context_data()`, `get_page_context()`, `get_page_title()`, `get_page_subtitle()`, `get_page_class()`, `get_breadcrumbs()`) documenting parameters, return types, and behavior
- **FR-005**: System MUST provide code examples in docstrings demonstrating how to use and extend each mixin; all docstrings MUST use **Google style** (`Args:`, `Returns:`, `Raises:`, `Example:` sections)
- **FR-006**: System MUST have automated tests for `BaseTemplateNameMixin` covering: normal template resolution, `ImproperlyConfigured` raised when `base_template_name` is `None`, template list priority order, and integration with Django generic views
- **FR-007**: System MUST have automated tests for `PageMixin` covering: context structure, all getter methods, attribute defaults (including `breadcrumbs = []`), the `breadcrumbs` class attribute being used by `get_breadcrumbs()`, and override patterns
- **FR-011** *(added during clarification — see § Session 2026-05-02; numbered out of sequence)*: System MUST add a `breadcrumbs = []` class attribute to `PageMixin` so breadcrumbs can be set declaratively (consistent with `page_title`, `page_subtitle`, `page_icon`, `page_class`); `get_breadcrumbs()` MUST return `self.breadcrumbs` by default
- **FR-012** *(added during refinement — see § Session 2026-05-27)*: System MUST add a `page_caption = ""` class attribute to `PageMixin` so a caption can be set declaratively, consistent with `page_title`, `page_subtitle`, `page_icon`, `page_class`; `get_page_caption()` MUST return `self.page_caption` by default; `get_page_context()` MUST include the result under the key `"caption"` so templates can reference it as `page.caption`
- **FR-008**: *(Format constraint on FR-001–FR-004)* Documentation MUST be available as inline docstrings (not external docs only) so IDE tooltips show the information
- **FR-009**: System MUST document the intended inheritance hierarchy in the class docstrings of both mixins — listing at minimum the primary known subclasses by name (e.g., `MVPDetailView`, `MVPListViewMixin`, `MVPFormBase`, `MVPDeleteView`, `MVPTableView` for `BaseTemplateNameMixin`; `MVPTemplateView`, `MVPDetailView`, `MVPListViewMixin`, `MVPFormBase` for `PageMixin`) as an illustrative list, not an exhaustive registry
- **FR-010**: System MUST provide guidance on when to override each method vs. setting class attributes

### Key Entities

- **BaseTemplateNameMixin**: A mixin class that extends Django's template resolution by appending a mandatory fallback base template name to the list of candidate templates. `base_template_name` defaults to `None`; subclasses **must** set it or `ImproperlyConfigured` is raised (mirrors Django's `TemplateResponseMixin` behaviour)
- **PageMixin**: A mixin class that injects page-rendering context (title, subtitle, caption, icon, CSS class, breadcrumbs) into the template context dict. Breadcrumb data can be set via the `breadcrumbs` class attribute (default `[]`) **or** by overriding `get_breadcrumbs()`. Caption can be set via `page_caption` (default `""`) **or** by overriding `get_page_caption()` — consistent with the `page_title`/`get_page_title()` pattern used by all other page attributes
- **View Class Hierarchy**: The structure of view classes (MVPListView, MVPDetailView, MVPFormBase, etc.) that inherit from these mixins

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All public methods in `BaseTemplateNameMixin` and `PageMixin` have Google-style docstrings (`Args:`, `Returns:`, `Raises:`, `Example:` sections) with parameter descriptions, return type annotations, and at least one usage example
- **SC-002**: Test coverage for both mixins reaches 100% line coverage and 100% branch coverage (as reported by coverage.py)
- **SC-003**: All tests pass on the first run after implementation (no flaky tests) and complete in under 2 seconds total
- **SC-004**: New developers can answer the question "When do I set `page_title` vs. override `get_page_title()`?" by reading the inline documentation
- **SC-005**: IDE tooltips (in VSCode, PyCharm, etc.) display meaningful help text for both mixins and their methods when hovering over class/method names
- **SC-006**: Documentation is discoverable: grep/search for "BaseTemplateNameMixin" or "PageMixin" in code finds comprehensive docstrings as the first result

## Assumptions

- The project supports Python 3.10+ (as declared in `pyproject.toml`); type annotations and test code must be compatible with Python 3.10 and above
- Django's class-based views and mixin patterns are well-understood by the target audience (existing developers and contributors)
- The existing view implementations (MVPListView, MVPDetailView, MVPFormBase, etc.) are the canonical examples of correct mixin usage
- Testing follows pytest + django conventions already established in the django-mvp project (as evidenced by existing test structure)
- Behaviour changes are limited to those explicitly agreed in Clarifications (§ Session 2026-05-02): (1) `base_template_name` defaults to `None` and raises `ImproperlyConfigured` when unset; (2) `breadcrumbs = []` attribute is added to `PageMixin` with `get_breadcrumbs()` returning `self.breadcrumbs`. No other behaviour changes are in scope
- External documentation (README, guides) is out of scope; this feature focuses on inline code documentation and tests

## Clarifications

### Session 2026-05-27

- Q: Should `PageMixin` support a caption? → A: Yes, in scope. Add `page_caption = ""` class attribute and `get_page_caption()` method returning `self.page_caption`. `get_page_context()` MUST expose it as the `"caption"` key so templates access it as `page.caption`. Follows the same declarative/override pattern as `page_title`/`get_page_title()`.

### Session 2026-05-02

- Q: Which docstring format should be used for new/updated method docstrings? → A: Google style (`Args:`, `Returns:`, `Raises:`, `Example:` sections)
- Q: Should a `breadcrumbs` class attribute be added to `PageMixin`? → A: Yes, in scope. Add `breadcrumbs = []` so breadcrumbs can be set declaratively, matching the `page_title`/`get_page_title()` pattern. `get_breadcrumbs()` must return `self.breadcrumbs`.
- Q: What Python version should tests and annotations target? → A: Python 3.10+ per `pyproject.toml`; spec incorrectly stated 3.13+.
- Q: What should happen when `base_template_name` is not set? → A: Default changed to `None`; `get_template_names()` raises `ImproperlyConfigured` if it is still `None`. Subclasses must always set it. Mirrors Django's `TemplateResponseMixin` behaviour.
