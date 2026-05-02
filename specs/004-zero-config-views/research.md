# Research: Zero-Config Ready-to-Use Views

**Branch**: `004-zero-config-views` | **Date**: 2026-05-02
**Purpose**: Resolve all unknowns identified in the Technical Context before Phase 1 design.

---

## Research Question 1: Current Implementation State

**Task**: Determine what already exists in `mvp/views/base.py` so the plan builds on rather than duplicates existing work.

**Findings**:

- `MVPTemplateView` = `PageMixin + django.views.generic.TemplateView` — already exists. Satisfies the spec's `PageView` concept completely. No new class needed; only a public alias is required.
- `MVPHomeView` = extends `MVPTemplateView` — already exists with:
  - `landing_template = "mvp/landing.html"` (attribute)
  - `dashboard_template = "mvp/dashboard.html"` (attribute)
  - `get_template_names()` that switches on `request.user.is_authenticated`
  - `get_landing_context()` / `get_dashboard_context()` extension hooks
- Both classes are exported from `mvp.views.__init__` via `__all__`.
- `PageMixin` is fully implemented: `page_title`, `page_subtitle`, `page_icon`, `page_class`, `breadcrumbs`, all with getter methods.

**Decision**: Do not rewrite — close the gaps only.

---

## Research Question 2: Attribute Naming Convention

**Task**: Decide whether to keep `landing_template` / `dashboard_template` or rename to `landing_template_name` / `dashboard_template_name` to match the spec and Django conventions.

**Findings**:

Django's own view classes use the `_name` suffix consistently: `template_name`, `success_url`, `login_url`. The spec's clarification session also chose `landing_template_name` / `dashboard_template_name`. The existing attribute names (`landing_template` / `dashboard_template`) do not follow this convention and may confuse developers familiar with Django's patterns.

The `BaseTemplateNameMixin` already uses `base_template_name`, reinforcing the `_name` pattern within this codebase.

**Decision**: Rename `landing_template` → `landing_template_name` and `dashboard_template` → `dashboard_template_name`. Since `MVPHomeView` is not yet documented or exposed via a public quickstart, there are no known consumer callsites outside `tests/test_views/test_base.py` which will be updated in the same PR.

**Alternatives considered**:

- Keep `landing_template` / `dashboard_template` — rejected; inconsistent with Django and the spec.
- Introduce a deprecation shim — rejected; these views have never been in a published release. Renaming is not a breaking change for this project at this stage.

---

## Research Question 3: ImproperlyConfigured Guard for Missing Dashboard Template

**Task**: Determine where and how to raise `ImproperlyConfigured` when `dashboard_template_name` is not set and an authenticated user requests `MVPHomeView`.

**Findings**:

The clarification session decided: *"Not having both templates declared is a configuration error."* This means `ImproperlyConfigured` must be raised, not a fallback to the landing template.

Django raises `ImproperlyConfigured` in `TemplateResponseMixin.get_template_names()` when `template_name` is not set. The same pattern already exists in `BaseTemplateNameMixin` for `base_template_name`. Raising it in `MVPHomeView.get_template_names()` when the selected template attribute is `None` is consistent with both Django and the existing codebase pattern.

`landing_template_name` is always required (FR requirement: anonymous requests must never expose dashboard content). If `landing_template_name` is also `None`, `ImproperlyConfigured` should be raised regardless of authentication state.

**Decision**: In `MVPHomeView.get_template_names()`:

1. If `landing_template_name` is `None` → raise `ImproperlyConfigured` with a clear message for any request.
2. If user is authenticated and `dashboard_template_name` is `None` → raise `ImproperlyConfigured` with a clear message.

**Alternatives considered**:

- Raise at class definition time via `__init_subclass__` — rejected; attributes can be set per-request or via `as_view()` kwargs, so class-time validation would produce false positives.
- Validate in `setup()` — possible, but `get_template_names()` is the canonical Django hook for this check and already used by `BaseTemplateNameMixin`.

---

## Research Question 4: Public Aliases (PageView, HomeView)

**Task**: Determine how to expose `PageView` and `HomeView` as the spec-described names without introducing a parallel class hierarchy.

**Findings**:

Python allows simple module-level aliases: `PageView = MVPTemplateView`. These are first-class references, not wrappers — `issubclass(PageView, MVPTemplateView)` is `True`, and subclassing `PageView` is identical to subclassing `MVPTemplateView`. Django's `as_view()` inherits correctly.

**Decision**: Add `PageView = MVPTemplateView` and `HomeView = MVPHomeView` to `mvp/views/__init__.py` and include them in `__all__`. Document `PageView` and `HomeView` as the primary names in quickstart and the SKILL.md.

**Alternatives considered**:

- Rename the classes directly — rejected; `MVPTemplateView` and `MVPHomeView` follow the project's existing naming convention (`MVP*`) and are used internally. Renaming would be a larger change.
- Introduce subclasses — rejected; unnecessary indirection with no behaviour difference.

---

## Research Question 5: Bundled Templates (mvp/landing.html, mvp/dashboard.html)

**Task**: Determine what the bundled base templates should contain and how they should hook into the layout.

**Findings**:

`mvp/templates/page_view.html` already provides the full layout shell (navbar, sidebar, content wrapper) using Cotton components. It defines `{% block page.content %}` for custom content. The bundled landing and dashboard templates should extend `page_view.html` and provide meaningful defaults in `{% block page.content %}`.

The `mvp/landing.html` template already has `get_landing_context()` injecting `hero_content` from `MVP_LANDING_PAGE_HERO`. The template should use this context to render a hero section using available django-cotton-bs5 components.

The `mvp/dashboard.html` template should provide a minimal authenticated-user greeting. Since no model data is fetched by default, it should use `{{ request.user }}` (available via the standard auth context processor) for a personalised welcome.

**Decision**:

- `mvp/landing.html` extends `page_view.html`, renders a hero block using `{{ hero_content }}` dict fields.
- `mvp/dashboard.html` extends `page_view.html`, renders a minimal greeting using `{{ request.user.get_full_name|default:request.user.username }}`.
- Both use existing Cotton components from `django-cotton-bs5` where applicable.

---

## Research Question 6: GET-Only HTTP Method Behaviour

**Task**: Confirm Django's TemplateView already handles FR-011 (GET only, 405 for all other methods).

**Findings**:

`django.views.generic.TemplateView` inherits from `View`. `View.http_method_not_allowed()` returns a `405 Method Not Allowed` response for any method not listed in `http_method_names` that has a corresponding handler. `TemplateView` defines only `get()`. POST, PUT, PATCH, DELETE, etc., return `405` by default.

**Decision**: No additional code needed. FR-011 is already satisfied by the Django base class. Document the behaviour in the contract and quickstart.

---

## Research Question 7: Demo App Integration

**Task**: Determine how to wire both views in the demo app for end-to-end validation.

**Findings**:

`demo/urls.py` already has `path("", MVPDemoView.as_view(template_name="demo/home.html"), name="home")`. The demo's home URL uses a plain `TemplateView` subclass. For this feature, the demo's home URL should be updated to use `HomeView` (via `MVPHomeView`) to demonstrate the dual landing/dashboard pattern. A separate URL (e.g., `/about/`) can demonstrate `PageView`.

**Decision**:

- Update demo home URL (`""`) to use `MVPHomeView` with demo-specific `landing_template_name` and `dashboard_template_name`.
- Add a `path("about/", ...)` URL using `MVPTemplateView` (i.e., `PageView`) with `template_name = "demo/about.html"` and `page_title = "About"`.
- Create minimal `demo/templates/demo/landing.html` and `demo/templates/demo/dashboard.html` templates that extend the bundled `mvp/landing.html` and `mvp/dashboard.html` respectively, overriding `{% block page.content %}` with demo-specific content.

---

## Summary: All NEEDS CLARIFICATION Resolved

| # | Question | Decision |
|---|----------|----------|
| 1 | Current implementation state | Both views exist; close gaps only |
| 2 | Attribute naming | Rename to `_name` suffix: `landing_template_name`, `dashboard_template_name` |
| 3 | ImproperlyConfigured guard | Raise in `get_template_names()` when selected template attribute is `None` |
| 4 | Public aliases | `PageView = MVPTemplateView`, `HomeView = MVPHomeView` in `__init__.py` |
| 5 | Bundled templates | Extend `page_view.html`; use `hero_content` for landing, `request.user` for dashboard |
| 6 | HTTP method constraint | Already handled by Django's TemplateView base; no new code needed |
| 7 | Demo app integration | Update demo home URL; add `/about/`; create demo-specific template overrides |
