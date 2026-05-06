# Implementation Plan: List Search and Ordering Mixins

**Branch**: `014-list-search-ordering` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/014-list-search-ordering/spec.md`

## Summary

`SearchMixin`, `OrderMixin`, and `SearchOrderMixin` already exist in `mvp/views/list.py` with basic implementations. This feature formalises, refines, and correctly implements those classes to satisfy all spec requirements. The primary code changes are:

1. **Breaking API change**: `OrderMixin.order_by` entries migrate from two-tuples `(orm_expression, label)` to three-tuples `(public_key, label, orm_expression)` — separating the URL-visible key from the private ORM field name (FR-006a).
2. **Context always-injected sentinels**: `SearchMixin` already always injects `is_searchable` and `search_query`; the docstring must be updated to document this guarantee.
3. **Comprehensive Constitution-XII-compliant docstrings** for all three mixins and `MVPListViewMixin`.
4. **New test module**: `tests/test_views/test_list_view.py` covering all FR requirements.
5. **Demo update**: `demo/views.py` `order_by` declarations migrated to three-tuple format.
6. **`skills/django-mvp/SKILL.md` update** to document the new `order_by` format.

No new Django models, migrations, or template files are needed. The existing MRO `SearchOrderMixin(SearchMixin, OrderMixin)` already satisfies the evaluation-order requirement (ordering-first, search+distinct-last).

## Technical Context

**Language/Version**: Python 3.12, Django 5.x  
**Primary Dependencies**: django-mvp (internal), `django-filter` (optional dev dependency, used in `MVPFilteredListView`)  
**Storage**: N/A — no new models or migrations  
**Testing**: pytest, pytest-django, factory-boy; pytest-playwright for E2E  
**Target Platform**: Django web application (server-rendered), reusable library  
**Project Type**: Reusable Django library  
**Performance Goals**: No queryset overhead when mixins are unconfigured — `search_fields = None` and `order_by = None` must be proven no-ops in tests.  
**Constraints**: The `?o=` parameter value must never be passed directly to the ORM. The security whitelist must be the only code path that produces an ORM field name for `order_by()`.  
**Scale/Scope**: Three mixin classes in one file; one new test module; one quickstart update.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Status | Notes |
|---|---|---|---|
| I. Design-First, Verify Implementation | Tests written for verified implementation; `python manage.py check` after each story phase | ✅ PASS | Test file to be created; all story phases include explicit validation tasks |
| I. Story-Level Validation | Tasks grouped by user story; `manage.py check` + pytest validation required per phase | ✅ PASS | Required in tasks.md generation |
| II. Documentation-First | Public API documented; quickstart included | ✅ PASS | [quickstart.md](quickstart.md), [contracts/view-api.md](contracts/view-api.md), `skills/django-mvp/SKILL.md` update required |
| III. Component Quality & Accessibility | No new templates or Cotton components | ✅ PASS | This feature modifies only Python view mixins |
| IV. Config-Driven Design | All configuration is via class attributes; no Python-level CSS/layout config | ✅ PASS | `search_fields` and `order_by` are class attributes |
| V. Tooling & Consistency | Ruff + djlint must pass | ✅ PASS | Python-only changes; no template files added |
| VI. UI Verification (playwright-mcp) | No new HTML/CSS/templates; existing list view template behaviour is unchanged | ✅ PASS | No UI changes; playwright-mcp not required for this PR |
| VIII. End-to-End Testing (pytest-playwright) | E2E tests required if user-visible behaviour changes | ⚠️ WARN | The existing search/ordering UI is unchanged in this PR; E2E tests for the ordering UI can be added alongside the demo view update. E2E test file `test_list_view_e2e.py` is planned but low-risk if deferred to a follow-up. |
| IX. Template Component Reuse | No new templates | ✅ PASS | No template changes in this PR |
| X. django-mvp Skill Currency | `skills/django-mvp/SKILL.md` update required for `order_by` format change | ✅ PASS | Listed as required file change |
| XI. Dual-Audience User Stories | Developer stories (class attribute config) and end-user stories (search/filter UI) both present | ✅ PASS | All user stories cover both audiences |
| XII. View Class Docstring Completeness | `SearchMixin`, `OrderMixin`, `SearchOrderMixin`, `MVPListViewMixin` all need Constitution-XII-compliant docstrings | ✅ PASS | Listed as required file change; existing docstrings exist but are non-compliant |

**Constitution Check result**: PASS (one informational warning on Principle VIII — E2E test file is planned; not a blocker).

## Project Structure

### Documentation (this feature)

```text
specs/014-list-search-ordering/
├── plan.md              ← this file
├── research.md          ← Phase 0 decisions
├── data-model.md        ← OrderEntry three-tuple definition and context variable schema
├── quickstart.md        ← Developer quickstart
├── contracts/
│   └── view-api.md      ← Public API contract for all three mixins
└── tasks.md             ← Phase 2 output (/speckit.tasks command)
```

### Source Code

```text
mvp/
└── views/
    └── list.py          ← SearchMixin, OrderMixin, SearchOrderMixin, MVPListViewMixin (modify)

demo/
└── views.py             ← Migrate order_by declarations to three-tuple format (modify)

tests/
└── test_views/
    ├── test_list_view.py     ← NEW: unit tests for all three mixins
    └── test_list_view_e2e.py ← NEW: playwright E2E for search/order UI in demo

skills/
└── django-mvp/
    └── SKILL.md         ← Document new order_by three-tuple format (modify)
```

## Design Decisions

### D1: Three-Tuple OrderEntry Format

```python
order_by = [
    ("public_key", "Display Label", "orm_expression"),
]
```

- `public_key`: matched against `?o=`; never passed to ORM
- `label`: display string for templates
- `orm_expression`: passed to `queryset.order_by()`; never URL-exposed

This is a **breaking change** from the existing two-tuple format. All existing usages in `demo/views.py` must be migrated in the same PR. Backward compatibility shim is deliberately omitted (alpha package; adds complexity; obscures security guarantee).

### D2: MRO Invariant

`SearchOrderMixin(SearchMixin, OrderMixin)` is fixed. This guarantees:

- Ordering applied first (innermost `super()` call)
- Search + `distinct()` applied last (outermost)

This avoids the PostgreSQL `SELECT DISTINCT` + `ORDER BY` on JOIN columns error.

### D3: `FilterView` Composition

No code changes are needed. The MRO convention `class MyView(SearchOrderMixin, FilterView)` is documented in docstrings and quickstart. Tests verify this composition pattern.

### D4: SearchMixin Context Sentinels

`is_searchable` and `search_query` are always injected (existing behaviour is correct). Docstring must be updated to document this as a guarantee.

### D5: OrderMixin Context — No Sentinels When Unconfigured

`order_by_choices` and `current_ordering` are only injected when `order_by` is configured. Templates guard with `{% if order_by_choices %}`. No `is_orderable` sentinel is needed per the spec.

## Implementation Phases

### Phase 1 — Core: OrderMixin Three-Tuple Migration (Story 2)

**Files modified**: `mvp/views/list.py`, `demo/views.py`

Changes:

1. Change `_apply_ordering` to read `choice[0]` as the public_key and `choice[2]` as the orm_expression.
2. Change `get_context_data` to pass `order_by_choices` as the raw three-tuple list (templates destructure it as `(key, label, _)`).
3. Update `OrderMixin` docstring to Constitution XII format (Config, Override hooks, example).
4. Update `SearchMixin` docstring to Constitution XII format.
5. Update `SearchOrderMixin` docstring to Constitution XII format.
6. Update `MVPListViewMixin` docstring to Constitution XII format.
7. Migrate `demo/views.py` `order_by` declarations to three-tuple format.

Validation: `python manage.py check` + `pytest tests/test_views/` after completion.

### Phase 2 — Tests: SearchMixin (Story 1)

**Files created/modified**: `tests/test_views/test_list_view.py`

Test cases:

- `test_search_no_query_returns_all`
- `test_search_single_word_filters`
- `test_search_multi_word_or_semantics`
- `test_search_case_insensitive`
- `test_search_whitespace_only_query_no_filter`
- `test_search_no_fields_configured_is_noop`
- `test_search_related_field_traversal`
- `test_search_context_always_injected`
- `test_search_is_searchable_false_when_unconfigured`
- `test_search_distinct_deduplicates`

Validation: `pytest tests/test_views/test_list_view.py` after completion.

### Phase 3 — Tests: OrderMixin (Story 2)

**Files modified**: `tests/test_views/test_list_view.py`

Test cases:

- `test_order_valid_key_applies_orm_expression`
- `test_order_invalid_key_ignored`
- `test_order_absent_parameter_no_override`
- `test_order_no_config_is_noop`
- `test_order_public_key_not_exposed_as_orm_field`
- `test_order_context_choices_and_current`
- `test_order_context_not_injected_when_unconfigured`

Validation: `pytest tests/test_views/test_list_view.py` after completion.

### Phase 4 — Tests: SearchOrderMixin + django_filters (Stories 3 & 4)

**Files modified**: `tests/test_views/test_list_view.py`

Test cases:

- `test_combined_search_and_ordering`
- `test_combined_search_only`
- `test_combined_ordering_only`
- `test_django_filters_composition_search_on_top`
- `test_django_filters_composition_ordering_on_top`
- `test_django_filters_no_search_fields_is_noop`

Validation: `pytest tests/test_views/test_list_view.py` after completion.

### Phase 5 — E2E: Demo View Playwright Tests

**Files created**: `tests/test_views/test_list_view_e2e.py`

Playwright tests via the demo `ProductListView`:

- Verify search input pre-populated with `?q=` value
- Verify filtered results shown on search submit
- Verify ordering dropdown shows selected state for `?o=` value
- Verify combined `?q=&o=` produces correct filtered+ordered output

Validation: `pytest tests/test_views/test_list_view_e2e.py` after completion.

### Phase 6 — Docs: SKILL.md Update

**Files modified**: `skills/django-mvp/SKILL.md`

- Update `OrderMixin` / `order_by` section to document three-tuple format.
- Add `django_filters` composition pattern.

Validation: Read-only; no automated check. Human review.

## Complexity Tracking

No constitution violations. No complexity exceptions required.
