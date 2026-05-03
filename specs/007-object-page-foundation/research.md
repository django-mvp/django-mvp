# Research: Object Page Foundation

**Branch**: `007-object-page-foundation` | **Date**: 2026-05-03
**Purpose**: Audit the current `PageObjectMixin` and `MVPDetailView` implementation in `mvp/views/detail.py` against every functional requirement in the spec. Identify all gaps; determine the full scope of work.

---

## Research Question 1: Does the current implementation satisfy FR-001 through FR-009?

**Task**: Line-by-line review of `PageObjectMixin` and `MVPDetailView` in `mvp/views/detail.py` against all nine functional requirements.

**Findings**:

| Requirement | Status | Notes |
|---|---|---|
| FR-001: `PageObjectMixin` merges model resolution, CRUD directory, page header/breadcrumbs | ✅ | `class PageObjectMixin(CRUDDirectoryMixin, PageMixin)` inherits both; model resolution comes through `CRUDDirectoryMixin → ModelInfoMixin` |
| FR-002: `list_view_title` controls breadcrumb back-link text; defaults to `verbose_name_plural.title()` | ✅ | `list_view_title = ""`; `get_list_title()` returns `self.list_view_title or self.model_meta.verbose_name_plural.title()` |
| FR-003: `get_list_url()` returns resolved list URL or empty string when suppressed | ✅ | `return self._resolve_directory_url("list") or ""` — routes through permission gating |
| FR-004: `get_breadcrumbs()` returns two-item trail: list link → current page (no link) | ✅ | `[{"text": self.get_list_title(), "href": self.get_list_url()}, {"text": self.get_page_title()}]` |
| FR-005: `PageObjectMixin.get_page_class()` appends model-name CSS class | ✅ | `" ".join(filter(None, [super().get_page_class(), self.model_meta.model_name + "-page"]))` |
| FR-006: `MVPDetailView` combines `PageObjectMixin` with Django's single-object retrieval | ✅ | `class MVPDetailView(BaseTemplateNameMixin, PageObjectMixin, generic.DetailView)` |
| FR-007: `MVPDetailView.get_page_title()` returns `str(self.object)` | ✅ | Implemented directly; single-line method |
| FR-008: Falls back to `detail_view.html` when no app-specific template exists | ✅ | `base_template_name = "detail_view.html"` + `BaseTemplateNameMixin` resolution |
| FR-009: `MVPDetailView` adds `mvp-detail-page`; model-name class comes from `PageObjectMixin` | ✅ | `page_class = "mvp-detail-page"` on `MVPDetailView`; `PageObjectMixin.get_page_class()` appends model-name class via `super()` chain. Effective classes: `mvp-page mvp-detail-page {model_name}-page` |

**Summary**: All 9 functional requirements are satisfied by the existing code. **No Python changes required.**

---

## Research Question 2: What is the CSS class order for a rendered MVPDetailView?

**Task**: Trace the `get_page_class()` MRO chain to confirm FR-005 and FR-009 are both satisfied with no duplication.

**MRO** (relevant portion):
`MVPDetailView → BaseTemplateNameMixin → PageObjectMixin → CRUDDirectoryMixin → ModelInfoMixin → PageMixin → generic.DetailView`

**Chain**:

1. `PageMixin.get_page_class()` → `" ".join(filter(None, ["mvp-page", self.page_class]))` = `"mvp-page mvp-detail-page"` (using `MVPDetailView.page_class = "mvp-detail-page"`)
2. `PageObjectMixin.get_page_class()` → `" ".join(filter(None, [super().get_page_class(), self.model_meta.model_name + "-page"]))` = `"mvp-page mvp-detail-page order-page"` (for an `Order` model)

**Decision**: No changes needed. The chain is correct and matches FR-005 and FR-009.

---

## Research Question 3: What is the test coverage gap?

**Task**: Search `tests/test_views/` for any existing tests covering `PageObjectMixin` or `MVPDetailView`.

**Findings**:

| Test file | Covers |
|---|---|
| `tests/test_views/test_base.py` | `BaseTemplateNameMixin`, `PageMixin`, `ModelInfoMixin` |
| `tests/test_views/test_base_e2e.py` | `MVPTemplateView` (PageView/HomeView) E2E |
| `tests/test_views/test_crud_directory_mixin.py` | `CRUDDirectoryMixin` |
| `tests/test_views/test_crud_directory_mixin_e2e.py` | `ProductDetailView` — CRUD directory buttons |
| `tests/test_views/test_delete_view.py` | `MVPDeleteView` |

**Gap**: `PageObjectMixin` and `MVPDetailView` have **zero unit test coverage**. The E2E test for `ProductDetailView` in `test_crud_directory_mixin_e2e.py` exercises the full stack but focuses on directory URL buttons — it does not assert page title, breadcrumb text, or CSS classes.

**Decision**: New test module `tests/test_views/test_detail_view.py` required for unit coverage of `PageObjectMixin` and `MVPDetailView`. The existing `test_crud_directory_mixin_e2e.py` needs additional assertions for US4 (heading text = `str(object)`, breadcrumb trail, CSS class).

---

## Research Question 4: Does the demo app have a suitable `ProductDetailView` for E2E?

**Findings**: `demo/views.py` already contains `ProductDetailView(MVPDetailView)` with `model = Product`, `directory = ["list", "detail", "update", "delete"]`, and permission gating. A URL and template for it exist and are used by the existing `test_crud_directory_mixin_e2e.py`.

**Decision**: No demo changes required. E2E tests for US4 are added to the existing E2E file.

---

## Research Question 5: Does `skills/django-mvp/SKILL.md` document `MVPDetailView`?

**Findings**: The skill file documents app shell integration steps (INSTALLED_APPS, EASY_ICONS, menus). `MVPDetailView` and `PageObjectMixin` are not referenced.

**Decision**: `skills/django-mvp/SKILL.md` update required to document `MVPDetailView` as the canonical detail view class and `PageObjectMixin` as the shared object-view base, with a minimal usage example.

---

## Decisions Summary

| Decision | Rationale |
|---|---|
| No changes to `mvp/views/detail.py` | All 9 FRs are satisfied by the existing implementation |
| New `tests/test_views/test_detail_view.py` | Zero unit test coverage is the primary gap; mirrors the source tree convention |
| Extend `test_crud_directory_mixin_e2e.py` | Adds US4 browser assertions without creating a new E2E module |
| Update `skills/django-mvp/SKILL.md` | Public API change: `MVPDetailView` and `PageObjectMixin` newly documented |
| No contracts/ directory | `PageObjectMixin` exposes no external interface beyond the Python API documented in `data-model.md` |
