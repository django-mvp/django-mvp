# Implementation Plan: Dashboard List View Mixin

**Branch**: `008-dash-list-view` | **Date**: February 4, 2026 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-dash-list-view/spec.md`

## Summary

Implement a comprehensive MVPListViewMixin system that enables developers to create feature-rich list views with minimal configuration. The mixin architecture (SearchMixin → OrderMixin → SearchOrderMixin → ListItemTemplateMixin → MVPListViewMixin) is **already implemented**. This plan focuses on:

1. **Verifying existing implementation** against spec requirements
2. **Completing multi-word OR search** functionality (currently single-word only)
3. **Creating comprehensive demo views** demonstrating various configurations
4. **Writing tests** for all mixin functionality
5. **Documentation** for public API

## Technical Context

**Language/Version**: Python 3.11+ with Django 4.2+
**Primary Dependencies**: Django, django-cotton, django-filter (optional), crispy-forms
**Storage**: N/A (works with any Django model)
**Testing**: pytest, pytest-django, pytest-playwright
**Target Platform**: Web (Django templates with AdminLTE 4 layout)
**Project Type**: Django reusable app
**Performance Goals**: Search returns results in <500ms for 10,000 records
**Constraints**: Server-side rendering, no client-side filtering
**Scale/Scope**: Typical list views with <10,000 records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Design-first approach is feasible and planned (implementation before test writing)
- [x] Visual verification approach is planned (chrome-devtools-mcp for UI validation)
- [x] Test types are identified (pytest, pytest-django, pytest-playwright as needed) for post-implementation
- [x] Documentation updates are included for any public behavior change
- [x] Quality gates are understood (tests + lint + format)
- [x] Documentation retrieval is planned (context7 for up-to-date library docs)
- [x] End-to-end testing is planned (playwright for complete user workflows after implementation)

## Project Structure

### Documentation (this feature)

```text
specs/008-dash-list-view/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
mvp/
├── views.py                           # Mixin classes (EXISTING - needs enhancement)
├── templates/
│   └── mvp/
│       └── list_view.html             # Default list view template (EXISTING)
├── templates/cotton/
│   ├── grid.html                      # Grid component (EXISTING)
│   └── list/
│       ├── empty.html                 # Empty state component (EXISTING)
│       ├── search_widget.html         # Search widget (EXISTING)
│       └── order_widget.html          # Order dropdown widget (EXISTING)

demo/
├── views.py                           # Demo views (EXISTING - needs expansion)
├── urls.py                            # URL routing (EXISTING)
├── menus.py                           # Menu configuration (NEEDS UPDATE)
├── templates/
│   └── cards/
│       └── product_card.html          # Product list item template (EXISTING)

tests/
├── test_list_view_mixins.py           # Unit tests for mixins (NEW)
├── integration/
│   └── test_list_view_integration.py  # Integration tests (NEW)
└── e2e/
    └── test_list_view_e2e.py          # End-to-end tests (NEW)
```

**Structure Decision**: Follows existing Django app structure. Core mixins in `mvp/views.py`, templates in `mvp/templates/`, demo views in `demo/`.

## Existing Implementation Analysis

### What Already Exists

| Component | Status | Notes |
|-----------|--------|-------|
| `SearchMixin` | ✅ Complete | Provides `search_fields`, `get_search_fields()`, `_apply_search()`, context: `search_query`, `is_searchable` |
| `OrderMixin` | ✅ Complete | Provides `order_by`, `get_order_by_choices()`, `_apply_ordering()`, context: `order_by_choices`, `current_ordering` |
| `SearchOrderMixin` | ✅ Complete | Combines SearchMixin + OrderMixin |
| `ListItemTemplateMixin` | ✅ Complete | Provides `list_item_template`, `get_list_item_template()`, auto-generates template path |
| `MVPListViewMixin` | ✅ Complete | Combines SearchOrderMixin + ListItemTemplateMixin, adds `grid`, `page_title`, `get_grid_config()`, `get_page_title()` |
| `list_view.html` | ✅ Complete | Template with page header, grid, pagination footer, filter sidebar |
| `c-grid` | ✅ Complete | Grid component with responsive breakpoints |
| `c-list.search-widget` | ✅ Complete | Search input widget |
| `c-list.order-widget` | ✅ Complete | Order dropdown menu |
| `c-list.empty` | ✅ Complete | Empty state component |
| `c-sidebar.filter` | ✅ Complete | Filter sidebar for django-filter |
| `c-page.footer.pagination` | ⚠️ Partial | Exists but uses `table` context (DataTables), needs to work with `page_obj` |
| `ListViewDemo` | ✅ Complete | Demo with FilterView, search, ordering, grid |
| Product model | ✅ Complete | Demo model with various fields |
| URL routing | ✅ Complete | `/list-view/` route configured |

### What Needs Work

| Component              | Status     | Required Work                                                     |
| ---------------------- | ---------- | ----------------------------------------------------------------- |
| Multi-word OR search   | ❌ Missing | FR-020: Currently single-word, need to split and OR match         |
| Pagination footer      | ⚠️ Partial | Works with `page_obj` but page_info shows DataTable variables     |
| Demo: Basic ListView   | ❌ Missing | ListView without django-filter (search + order only)              |
| Demo: Minimal ListView | ❌ Missing | ListView with only list_item_template (no search/order)           |
| Demo: Grid variations  | ❌ Missing | Multiple grid configurations (1-col, 2-col, 3-col, responsive)    |
| Unit tests             | ❌ Missing | Tests for all mixin functionality                                 |
| Integration tests      | ❌ Missing | Tests for views with templates                                    |
| E2E tests              | ❌ Missing | Browser tests for user workflows                                  |
| Documentation          | ❌ Missing | Quickstart guide, API docs                                        |

## Implementation Phases

### Phase 1: Fix Multi-Word OR Search (FR-020)

**Current behavior**: Single search term applied to all fields.

**Required behavior**: Split search term by whitespace, apply OR matching across all words and all fields.

**File**: `mvp/views.py` - `SearchMixin._apply_search()`

**Change**:

```python
# Current (simplified)
for field in self.get_search_fields():
    search_query |= Q(**{f"{field}__icontains": search_term})

# Required
words = search_term.split()
for word in words:
    for field in self.get_search_fields():
        search_query |= Q(**{f"{field}__icontains": word})
```

### Phase 2: Fix Pagination Footer

**Current behavior**: `c-page.footer.pagination` uses `table.page.start_index` (DataTables context).

**Required behavior**: Should work with standard Django pagination `page_obj`.

**File**: `mvp/templates/cotton/page/footer/pagination.html`

**Change**: Update to use `page_obj.start_index()`, `page_obj.end_index()`, `page_obj.paginator.count`

### Phase 3: Create Additional Demo Views

Create demo views in `demo/views.py` and register in `demo/urls.py` and `demo/menus.py`:

1. **BasicListViewDemo** - ListView (no django-filter) with search + ordering
2. **MinimalListViewDemo** - ListView with only list_item_template (no search/order)
3. **GridDemo1Col** - Single column grid layout
4. **GridDemo2Col** - Two column responsive grid
5. **GridDemo3Col** - Three column responsive grid
6. **GridDemoResponsive** - Full responsive grid (1→2→3→4 cols)

### Phase 4: Write Unit Tests

**File**: `tests/test_list_view_mixins.py`

Test coverage:

- `SearchMixin`: search_fields, get_search_fields(),_apply_search(), single-word, multi-word OR
- `OrderMixin`: order_by, get_order_by_choices(), _apply_ordering(), invalid ordering
- `SearchOrderMixin`: combined functionality
- `ListItemTemplateMixin`: list_item_template, get_list_item_template(), auto-generation
- `MVPListViewMixin`: grid, page_title, get_grid_config(), get_page_title()
- Override methods: all get_* methods can override class attributes

### Phase 5: Write Integration Tests

**File**: `tests/integration/test_list_view_integration.py`

Test coverage:

- View renders with correct template
- Context contains expected variables
- Search filtering works end-to-end
- Ordering works end-to-end
- Pagination preserves search/order state
- Empty state displays correctly
- Grid configuration passed correctly

### Phase 6: Write E2E Tests

**File**: `tests/e2e/test_list_view_e2e.py`

Test coverage:

- Page loads with correct title
- Search bar appears when search_fields defined
- Search filters results
- Order dropdown appears when order_by defined
- Ordering changes result order
- Filter sidebar opens/closes (with django-filter)
- Pagination works with state preservation
- Grid layouts display correctly on different screen sizes

### Phase 7: Documentation

**File**: `specs/008-dash-list-view/quickstart.md`

Contents:

- Minimal example (10 lines of code)
- Search configuration
- Ordering configuration
- Grid configuration
- Filter integration
- Customization (overriding methods)

## Demo Views Design

### 1. BasicListViewDemo (No django-filter)

```python
class BasicListViewDemo(LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, ListView):
    """Demo showing search and ordering without django-filter."""
    model = Product
    template_name = "mvp/list_view.html"
    list_item_template = "cards/product_card.html"
    paginate_by = 12
    search_fields = ["name", "description"]
    order_by = [
        ("name", "Name (A-Z)"),
        ("-name", "Name (Z-A)"),
        ("price", "Price (Low to High)"),
        ("-price", "Price (High to Low)"),
    ]
```

### 2. MinimalListViewDemo (Bare minimum)

```python
class MinimalListViewDemo(LayoutConfigMixin, PageModifierMixin, MVPListViewMixin, ListView):
    """Demo showing minimal configuration - just model and template."""
    model = Product
    template_name = "mvp/list_view.html"
    list_item_template = "cards/product_card.html"
    paginate_by = 12
```

### 3. Grid Variation Demos

```python
class GridDemo1Col(MinimalListViewDemo):
    """Single column grid layout."""
    grid = {"cols": 1}

class GridDemo2Col(MinimalListViewDemo):
    """Two column responsive grid."""
    grid = {"cols": 1, "md": 2}

class GridDemo3Col(MinimalListViewDemo):
    """Three column responsive grid."""
    grid = {"cols": 1, "md": 2, "lg": 3}

class GridDemoResponsive(MinimalListViewDemo):
    """Fully responsive grid (1→2→3→4 columns)."""
    grid = {"cols": 1, "sm": 2, "md": 3, "xl": 4, "gap": 3}
```

## Menu Structure

Add to `demo/menus.py`:

```python
MenuGroup(
    "list_views_group",
    items=[
        MenuItem(name="list_view_demo", view_name="list_view_demo",
                 extra_context={"label": "Full Demo (FilterView)", "icon": "list"}),
        MenuItem(name="basic_list_demo", view_name="basic_list_demo",
                 extra_context={"label": "Basic (ListView)", "icon": "list-ul"}),
        MenuItem(name="minimal_list_demo", view_name="minimal_list_demo",
                 extra_context={"label": "Minimal", "icon": "list-task"}),
    ],
    extra_context={
        "label": "List Views",
        "icon": "collection",
    },
),
MenuGroup(
    "grid_demos_group",
    items=[
        MenuItem(name="grid_1col", view_name="grid_1col_demo",
                 extra_context={"label": "1 Column", "icon": "grid-1x2"}),
        MenuItem(name="grid_2col", view_name="grid_2col_demo",
                 extra_context={"label": "2 Columns", "icon": "grid"}),
        MenuItem(name="grid_3col", view_name="grid_3col_demo",
                 extra_context={"label": "3 Columns", "icon": "grid-3x3"}),
        MenuItem(name="grid_responsive", view_name="grid_responsive_demo",
                 extra_context={"label": "Responsive", "icon": "aspect-ratio"}),
    ],
    extra_context={
        "label": "Grid Layouts",
        "icon": "grid-fill",
    },
),
```

## Dependency Verification

| Dependency | Required | Status | Notes |
|------------|----------|--------|-------|
| django-cotton | Yes | ✅ Installed | Grid, widgets, page components |
| django-filter | Optional | ✅ Installed | FilterView integration |
| crispy-forms | Optional | ✅ Installed | Filter form rendering |
| Bootstrap 5 | Yes | ✅ Configured | Responsive grid classes |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Multi-word search performance | Low | Medium | Add index recommendations to docs |
| Pagination context mismatch | Low | Low | Already identified issue, straightforward fix |
| Grid component edge cases | Low | Low | Well-tested component, add specific tests |
| Filter sidebar state | Medium | Medium | Test state preservation through pagination |

## Success Criteria Mapping

| Success Criteria | Implementation | Verification |
|------------------|----------------|--------------|
| SC-001: <10 lines of code | MinimalListViewDemo | Count lines in demo |
| SC-002: <500ms for 10k records | Multi-word OR search | Performance test |
| SC-003: Discoverable UI | Existing widgets | E2E visual tests |
| SC-004: Responsive 320px-1920px | Grid component | E2E responsive tests |
| SC-005: <2s render time | Full demo view | Performance test |
| SC-006: 60% time reduction | Documentation | Quickstart demo |
| SC-007: 375px width | Page header widgets | E2E mobile tests |
| SC-008: State persistence | URL params | E2E pagination tests |

## Next Steps

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement Phase 1 (multi-word OR search)
3. Verify with visual inspection
4. Implement remaining phases
5. Write comprehensive tests
6. Update documentation
