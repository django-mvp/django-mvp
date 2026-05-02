# Research: Document and Test Core View Mixins

**Branch**: `003-base-mixin-classes` | **Date**: 2026-05-02

## Decision Log

---

### 1. `base_template_name` default value and guard behaviour

**Decision**: Change `base_template_name = ""` → `base_template_name = None`. Raise `django.core.exceptions.ImproperlyConfigured` in `get_template_names()` when the attribute is still `None`.

**Rationale**: Mirrors the established Django convention in `TemplateResponseMixin.get_template_names()`, which raises `ImproperlyConfigured` when `template_name` is not set. Every concrete subclass in the project already sets a non-empty value (`"detail_view.html"`, `"list_view.html"`, etc.), so this is a safe tightening with no breaking impact on existing consumers.

**Alternatives considered**:
- Empty string default + silently skip append: permissive but confusing — callers would get incomplete template lists without any indication of misconfiguration.
- Keep empty string + always append: current behaviour; would cause `TemplateDoesNotExist` at render time for any class that forgets to set the attribute, giving a poor developer experience.

---

### 2. `breadcrumbs` class attribute on `PageMixin`

**Decision**: Add `breadcrumbs: list = []` class attribute to `PageMixin` and change `get_breadcrumbs()` to return `self.breadcrumbs`.

**Rationale**: All other page-level data (`page_title`, `page_subtitle`, `page_icon`, `page_class`) follow a dual pattern: a class attribute for declarative configuration + a `get_*()` method as an override hook. Breadcrumbs previously only had the method, creating an asymmetry. Adding the attribute makes the API consistent and gives developers a one-liner way to set static breadcrumbs without subclassing.

**Alternatives considered**:
- Method-only (status quo): works but is inconsistent and forces a subclass just to set a static list.
- Attribute-only (no method): would remove the override hook, making dynamic breadcrumbs impossible without deep subclassing.

**Risk**: `breadcrumbs = []` is a mutable class attribute. Python shares the default list across all instances. However, `get_breadcrumbs()` returns it by reference and callers only *read* it (they don't mutate it in place), so this is safe. The docstring will note that subclasses wishing to return a computed list should override `get_breadcrumbs()`, not mutate the class attribute.

---

### 3. Docstring format

**Decision**: Google style throughout (`Args:`, `Returns:`, `Raises:`, `Example:` sections).

**Rationale**: The codebase already uses Google-style `Returns:` sections (visible in existing partial docstrings). Google style is the most readable inline and is natively understood by Pylance/Pyright, producing useful IDE tooltips without additional configuration. Sphinx / reStructuredText is heavier and typically requires a docs build pipeline.

**Alternatives considered**:
- NumPy style: verbose with dashed separators; suited for scientific libraries, not web frameworks.
- reStructuredText: better for generated docs sites but poor inline readability.

---

### 4. Test file location and naming

**Decision**: `tests/test_views/test_base.py` — new file, mirrors `mvp/views/base.py`.

**Rationale**: The constitution mandates that test structure mirrors the `mvp/` source tree. Existing pattern: `mvp/views/` → `tests/test_views/`. The file `test_base.py` directly mirrors `base.py`.

**Alternatives considered**:
- `tests/test_base_mixins.py` (top-level): doesn't mirror source tree; inconsistent.
- `tests/test_views/test_mixins.py`: acceptable but `test_base.py` is more precise.

---

### 5. Test approach for mixins (no concrete Django view required)

**Decision**: Use lightweight concrete view stubs in tests — minimal `View` subclasses that mix in `BaseTemplateNameMixin` / `PageMixin` alongside `django.views.generic.TemplateView`. Use `RequestFactory` (not `Client`) to avoid URL routing overhead.

**Rationale**: Mixins have no standalone callable interface; they must be mixed with a concrete Django view. Creating minimal test stubs keeps tests fast, explicit, and isolated from URL configuration. `RequestFactory` produces proper request objects without needing URL routing.

**Alternatives considered**:
- Full `Client` + URL routing: heavier, requires demo URL configuration; unnecessary for unit-testing mixin methods.
- Calling mixin methods directly without a request: not possible for `get_context_data()` which calls `super()` up the MRO.

---

### 6. `skills/django-mvp/SKILL.md` update scope

**Decision**: Update the skill to document the `breadcrumbs` class attribute on `PageMixin`.

**Rationale**: This is a public API addition (new class attribute on a public mixin). Principle X mandates a skill update in the same PR for any public API change.

**Alternatives considered**:
- Skip: violates Principle X; not acceptable.
- Full docstring rewrite in the skill: over-engineering; the skill only needs to reflect the new attribute.

---

## Summary Table

| # | Decision | Status |
|---|----------|--------|
| 1 | `base_template_name = None` + `ImproperlyConfigured` guard | Resolved |
| 2 | Add `breadcrumbs: list = []` attr; `get_breadcrumbs()` returns `self.breadcrumbs` | Resolved |
| 3 | Google-style docstrings | Resolved |
| 4 | Tests in `tests/test_views/test_base.py` | Resolved |
| 5 | Lightweight view stubs + `RequestFactory` | Resolved |
| 6 | Update `skills/django-mvp/SKILL.md` for breadcrumbs attr | Resolved |
