# Research: Django Tables2 Integration

**Phase**: 0 - Outline & Research
**Date**: January 20, 2026
**Feature**: [spec.md](spec.md)

## Purpose

Resolve technical unknowns and establish implementation patterns for integrating django-tables2 into django-mvp with fill mode support.

## Research Questions

### 1. django-tables2 Architecture & Patterns

**Question**: How does django-tables2.views.SingleTableView work and what are best practices for template customization?

**Findings**:

#### SingleTableView Core Features

- **Automatic Pagination**: When `table_class` is defined, pagination is handled automatically
- **Configurable via Attributes**:
  - `table_class`: The Table subclass to render
  - `table_data` or `get_table_data()`: Data source (QuerySet, list)
  - `context_table_name`: Template variable name (default: 'table')
  - `table_pagination` or `get_table_pagination()`: Pagination settings (set to `False` to disable)
  - `paginator_class`: Can use `LazyPaginator` for large datasets
- **Methods for Customization**:
  - `get_table()`: Returns configured table instance
  - `get_table_kwargs()`: Keyword arguments passed to Table constructor

**Code Example**:

```python
from django_tables2.views import SingleTableView

class DataTablesView(SingleTableView):
    table_class = ProductTable
    table_data = Product.objects.all()
    template_name = "demo/datatables_demo.html"
    paginator_class = LazyPaginator  # Optional: for performance with large datasets
```

#### Template Rendering

django-tables2 provides Bootstrap 5-specific templates:

- `django_tables2/bootstrap5.html` - Base Bootstrap 5 styling
- `django_tables2/bootstrap5-responsive.html` - Wrapped in `.table-responsive` div

**Template Usage**:

```django
{% load render_table from django_tables2 %}
{% render_table table "django_tables2/bootstrap5-responsive.html" %}
```

**Decision**: Use `SingleTableView` as the base class for the demo view, override templates in `mvp/templates/django_tables2/` for AdminLTE 4 styling.

---

### 2. Bootstrap 5 Responsive Tables & Fill Mode

**Question**: How can Bootstrap 5 utility classes (w-100, h-100) be used to implement fill mode for tables?

**Findings**:

#### Bootstrap 5 Responsive Tables

- `.table-responsive` wraps table in scrollable container
- `.table-responsive-{breakpoint}` for specific breakpoints
- Standard responsive behavior: horizontal scroll on narrow viewports

#### Fill Mode Implementation Strategy

**Standard Mode (Content Height)**:

```html
<div class="table-responsive">
    {% render_table table %}
</div>
```

- Page scrolls normally
- Table height determined by content
- Entire viewport scrolls

**Fill Mode (Viewport Height)**:

```html
<div class="d-flex flex-column h-100">
    <!-- Content header (if any) -->
    <div class="table-responsive flex-grow-1 overflow-auto">
        {% render_table table %}
    </div>
</div>
```

- Parent uses flexbox with `flex-column` and `h-100`
- Table container has `flex-grow-1` to fill available space
- `overflow-auto` enables independent scrolling
- Header/sidebar remain fixed

**CSS Consideration**: AdminLTE 4's `.app-main` uses CSS Grid. The table container needs to participate in the grid layout properly.

**Decision**:

- Use flexbox layout with Bootstrap 5 utility classes (`d-flex`, `flex-column`, `h-100`, `flex-grow-1`)
- Test with AdminLTE 4's grid system
- Alternative if needed: CSS Grid with `grid-template-rows: auto 1fr` pattern
- Responsive table wrapper uses `.table-responsive` for horizontal scrolling

---

### 3. Template Override Structure

**Question**: Where should django-tables2 template overrides be placed and what needs customization?

**Findings**:

#### Django Template Loading Order

Django searches for templates in this order:

1. App-specific templates (`APP_DIRS=True`)
2. Templates in `TEMPLATES` `DIRS` setting
3. django-tables2's bundled templates

#### Override Location

Per user requirement: "Any datatables2 template overrides should be placed in the mvp/templates/ dir"

**Structure**:

```
mvp/
└── templates/
    └── django_tables2/
        ├── table.html              # Main table template
        ├── bootstrap5.html         # Bootstrap 5 base (if needed)
        └── bootstrap5-responsive.html  # Responsive wrapper (if needed)
```

#### Customization Requirements

1. **AdminLTE 4 Table Styling**:
   - Apply AdminLTE-specific table classes
   - Ensure compatibility with Bootstrap 5 `.table` classes
   - Maintain semantic HTML structure

2. **ARIA Compliance** (FR-016, FR-017):
   - Add `role="table"` (if not present)
   - Ensure sortable column headers have `aria-sort` attributes
   - Add `aria-label` for pagination controls
   - Verify keyboard navigation (django-tables2 handles this by default)

3. **Empty State** (FR-014):
   - Override `{% block no-records %}` to display "No records available" message
   - Style consistently with AdminLTE 4

**django-tables2 Template Block Structure**:

```django
{% block table-wrapper %}
    {% block table %}
        <table {{ table.attrs.as_html }}>
            {% block table.thead %}
                {% block columns %} {# Column headers #} {% endblock %}
            {% endblock %}
            {% block table.tbody %}
                {% block rows %} {# Table rows #} {% endblock %}
            {% endblock %}
        </table>
    {% endblock %}
    {% block pagination %} {# Pagination controls #} {% endblock %}
{% endblock %}
```

**Decision**:

- Create custom `mvp/templates/django_tables2/bootstrap5-responsive.html` extending base Bootstrap 5 template
- Override blocks for AdminLTE 4 styling
- Add ARIA attributes in column header overrides
- Customize empty state message

---

### 4. Data Source: Existing Product Model

**Question**: What data structure satisfies the requirement for horizontal and vertical overflow in fill mode?

**Findings**:

#### Overflow Requirements (FR-012)

- **Horizontal**: Enough columns to exceed typical viewport widths (1920px, 1366px, 768px)
- **Vertical**: Enough rows to require scrolling in fill mode

#### Column Estimation

- Typical column width with data: 120-180px
- Viewport widths to consider:
  - Desktop (1920px): ~10-16 columns to overflow
  - Laptop (1366px): ~7-11 columns to overflow
  - Tablet (768px): ~4-6 columns to overflow

**Recommended**: 12-15 columns ensures overflow across all viewport sizes

#### Using Existing Product Model

**Location**: `demo/models.py` (lines 34-80)

**Field Count**: 18 displayable fields

1. ID (integer)
2. Name (string)
3. Slug (string)
4. Category (ForeignKey - displays category name)
5. Description (text - can truncate)
6. Short Description (string)
7. Price (decimal)
8. Stock (integer)
9. Rating (float)
10. Status (choice)
11. Priority (choice)
12. Is Featured (boolean)
13. Is Available (boolean)
14. Release Date (date)
15. Created At (datetime)
16. Updated At (datetime)
17. Tags (string)
18. SKU (string)
19. Barcode (string)

**Advantages**:

- Already exists (no migration needed)
- 18 fields exceed recommendation (ensures horizontal overflow)
- Diverse field types for demo (text, numbers, dates, choices, booleans, FK)
- Has ForeignKey relationship for advanced sorting demo
- Choice fields provide filtering opportunities

#### Row Count

**Existing Data**: 27 products (via `generate_dummy_data` command)

- Demonstrates pagination effectively (10-25 per page)
- **May increase to 50-100** for better vertical scrolling demo

**Decision**:

- Use existing `Product` model (18 fields) from `demo/models.py`
- Use existing `generate_dummy_data` management command
- Consider increasing product count in command for better scrolling demo

---

### 5. Menu Integration Pattern

**Question**: How to add the "Integrations" menu group before existing groups like "Tools & Utilities"?

**Findings**:

#### django-flex-menus Structure (from demo/menus.py)

```python
from flex_menu import MenuItem
from mvp.menus import AppMenu, MenuCollapse, MenuGroup

# Single items at top level
AppMenu.extend([...])

# Groups are created with
group = MenuCollapse(
    name="group_name",
    extra_context={"label": "Group Label", "icon": "icon-name", "component_type": "menu.collapse"},

)

# Items added to group
group.extend([MenuItem(...)])
```

#### Ordering Strategy

Menu items and groups are rendered in the order they're registered. To place "Integrations" before other groups:

**Option 1: Registration Order** (Simplest)

- Register Integrations group early in menus.py
- Existing groups registered after will appear after it

**Option 2: Priority/Weight System** (If flex-menus supports it)

- Check flex-menus documentation for priority attributes

**Decision**:

- Use registration order approach
- Add Integrations group early in demo/menus.py
- Keep existing single items at top (Dashboard, Layout Demo, etc.)
- Integrations group appears before Administration and other groups

**Code Pattern**:

```python
# Single items (unchanged)
AppMenu.extend([
    MenuItem(name="dashboard", ...),
    MenuItem(name="layout_demo", ...),
    # ... other single items
])

# NEW: Integrations group (registered first)
integrations_group = MenuCollapse(
    name="integrations",
    extra_context={
        "label": "Integrations",
        "icon": "puzzle-fill",  # Or appropriate icon
        "component_type": "menu.collapse"
    },

)

integrations_group.extend([
    MenuItem(
        name="datatables_demo",
        view_name="datatables_demo",
        extra_context={
            "label": "DataTables Demo",
            "icon": "table",
        }
    )
])

# Existing groups (Administration, etc.) - appear after
admin_group = MenuCollapse(...)
```

---

### 6. pyproject.toml Optional Dependencies

**Question**: How to configure django-tables2 as an optional dependency with proper semantic versioning?

**Findings**:

#### Poetry Extras Syntax

```toml
[tool.poetry.dependencies]
# ... existing dependencies ...

[tool.poetry.extras]
datatables2 = ["django-tables2"]

[tool.poetry.group.dev.dependencies]
django-tables2 = ">=2.0.0,<3.0.0"  # Dev dependency for testing
```

#### Installation Patterns

- **Optional install**: `pip install django-mvp[datatables2]`
- **Dev install**: `poetry install` (includes dev dependencies)
- **Production without tables2**: `pip install django-mvp` (no django-tables2)

#### Version Constraint Rationale

- `>=2.0.0,<3.0.0`: Allows patch and minor updates (2.x.x)
- Prevents breaking changes from major version bump (3.0.0+)
- Current django-tables2 stable: 2.x series

**Decision**:

- Add `django-tables2 = ">=2.0.0,<3.0.0"` to dev dependencies
- Create `[tool.poetry.extras]` section with `datatables2 = ["django-tables2"]`
- Document both installation methods in quickstart

---

## Implementation Patterns Summary

### View Pattern

```python
# demo/views.py
from django_tables2.views import SingleTableView
from .tables import ProductTable
from .models import Product

class DataTablesView(SingleTableView):
    """Django Tables2 demo view showcasing fill mode and responsive design."""
    table_class = ProductTable
    template_name = "demo/datatables_demo.html"

    def get_queryset(self):
        return Product.objects.all()
```

### Table Definition Pattern

```python
# demo/tables.py (NEW FILE)
import django_tables2 as tables
from .models import Product

class ProductTable(tables.Table):
    """Table definition for Product model with sorting support."""

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap5-responsive.html"
        attrs = {
            "class": "table table-striped table-hover table-bordered",
            "role": "table"
        }
        fields = ("id", "name", "email", "department", "position", "status",
                  "hire_date", "manager", "office", "phone", "extension",
                  "project", "team_size", "updated_at")
```

### Template Pattern (Fill Mode)

```django
{# demo/templates/demo/datatables_demo.html #}
{% extends "mvp/base.html" %}
{% load render_table from django_tables2 %}

{% block page_title %}DataTables Demo{% endblock %}

{% block content %}
<div class="d-flex flex-column h-100">
    <div class="mb-3">
        <h3>Django Tables2 Integration</h3>
        <p class="text-muted">Demonstrating sorting, filtering, and pagination</p>
    </div>

    <div class="table-responsive flex-grow-1 overflow-auto">
        {% render_table table %}
    </div>
</div>
{% endblock %}
```

### Management Command Pattern

**Existing Command**: `generate_dummy_data` (already creates ~27 products)

```python
# demo/management/commands/generate_dummy_data.py (EXISTING)
# This command already generates Product instances with realistic data:
# - 27 product names from predefined list
# - Random prices ($9.99-$299.99), stock (0-100), ratings (3.5-5.0)
# - Status distribution (70% published, 20% draft, 10% archived)
# - SKUs, barcodes, tags, and category assignments

# Usage:
# poetry run python manage.py generate_dummy_data

# May be enhanced to create 50-100 products for better vertical scrolling demo
```

---

## Alternatives Considered

### Alternative 1: Use JavaScript DataTables Library

**Rejected Because**:

- Adds JavaScript dependency and complexity
- django-tables2 is more Django-idiomatic
- Server-side pagination/sorting is simpler to implement
- Better integration with Django's ORM and template system

### Alternative 2: Custom Table Implementation

**Rejected Because**:

- Reinventing functionality django-tables2 provides
- More maintenance burden
- Lost time on pagination, sorting, filtering logic
- django-tables2 has established patterns and community support

### Alternative 3: CSS Grid for Fill Mode

**Considered**: Using CSS Grid `grid-template-rows: auto 1fr` pattern
**Status**: Keep as backup if flexbox approach has issues with AdminLTE 4
**Reason**: Bootstrap 5 utility classes (flexbox) are simpler and more aligned with existing patterns

---

## Open Technical Questions

None remaining. All unknowns from Technical Context section have been resolved:

- ✅ django-tables2 usage patterns documented
- ✅ Fill mode implementation strategy defined
- ✅ Template override structure determined
- ✅ Existing Product model analyzed (18 fields, 27+ products)
- ✅ Menu integration pattern established
- ✅ Optional dependency configuration clarified

---

## Next Phase

**Ready for Phase 1**: Design & Contracts

- Generate data-model.md (Product model analysis, ProductTable definition)
- Create quickstart.md (django-tables2 usage guide)
- No API contracts needed (this is a UI-only feature)
