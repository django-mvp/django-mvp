# Data Model: Django Tables2 Integration

**Phase**: 1 - Design & Contracts
**Date**: January 20, 2026
**Feature**: [spec.md](spec.md)

## Purpose

Define the data structures required for the django-tables2 demo. This integration leverages the existing **Product model** from demo/models.py to showcase table capabilities without creating new models.

## Entities

### 1. Product (Existing Django Model)

**Purpose**: Demonstration model containing sufficient data to showcase horizontal and vertical scrolling in fill mode.

**Location**: `demo/models.py` (lines 34-80) - **ALREADY EXISTS**

#### Fields

| Field Name | Type | Constraints | Description |
|------------|------|-------------|-------------|
| id | AutoField | Primary Key | Unique identifier (auto-generated) |
| name | CharField(200) | Not Null | Product name |
| slug | SlugField(200) | Not Null, Unique | URL-friendly identifier |
| category | ForeignKey | Not Null, CASCADE | Reference to Category model |
| description | TextField | Nullable | Full product description |
| short_description | CharField(500) | Nullable | Brief product summary |
| price | DecimalField(10,2) | Not Null | Product price (dollars) |
| stock | IntegerField | Default=0 | Inventory quantity |
| rating | FloatField | Default=0.0 | Average rating (0.0-5.0) |
| status | CharField(20) | Not Null, Choices | Product status (draft/published/archived) |
| priority | CharField(20) | Not Null, Choices | Priority level (low/normal/high/urgent) |
| is_featured | BooleanField | Default=False | Featured product flag |
| is_available | BooleanField | Default=True | Availability flag |
| release_date | DateField | Nullable | Product release date |
| created_at | DateTimeField | Auto Now Add | Creation timestamp |
| updated_at | DateTimeField | Auto Now | Last modification timestamp |
| tags | CharField(200) | Nullable | Comma-separated tags |
| sku | CharField(100) | Unique, Nullable | Stock Keeping Unit |
| barcode | CharField(100) | Nullable | Product barcode |

#### Relationships

- `category`: ForeignKey to `Category` model (displays category name in table via `__str__`)

#### Choice Fields

```python
STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('normal', 'Normal'),
    ('high', 'High'),
    ('urgent', 'Urgent'),
]
```

#### Validation Rules

- `slug`: Must be unique across all products
- `sku`: Must be unique when provided
- `rating`: Should be between 0.0-5.0 (enforced in application logic)
- `stock`: Cannot be negative

#### Sample Data Characteristics

**Row Count**: 27 existing records (via `generate_dummy_data` command)

- Sufficient to demonstrate pagination (10-25 per page)
- **Note**: May increase to 50+ for better scrolling demo

**Column Count**: 18 fields (excluding id)

- Exceeds typical viewport widths (ensures horizontal scrolling)
- Demonstrates table responsiveness across device sizes
- Provides diverse data types for sorting/filtering tests

**Data Generation Strategy** (existing command):

- Names: Product names from predefined list (~27 items)
- Categories: Distributed across existing categories
- Prices: Random range $9.99 - $299.99
- Stock: Random 0-100
- Ratings: Random 3.5 - 5.0
- Status: 70% published, 20% draft, 10% archived
- Priority: Weighted toward "normal" and "high"
- SKUs: Generated format "SKU-{random 4-digit}"
- Barcodes: Generated format "{13 random digits}"
- Tags: Random selection from common tags
- Dates: Spread over past year

**Existing Management Command**: `poetry run python manage.py generate_dummy_data`

---

### 2. ProductTable (django-tables2 Table Class)

**Purpose**: Table definition specifying column configuration, styling, and behavior for rendering Product model data.

**Location**: `demo/tables.py` (NEW FILE)

#### Configuration

**Base Class**: `django_tables2.Table`

**Meta Options**:

- `model`: Product
- `template_name`: "django_tables2/bootstrap5-responsive.html"
- `attrs`: Table HTML attributes for styling and accessibility
- `fields`: Tuple of fields to include in table
- `sequence`: Optional field ordering (defaults to model field order)
- `empty_text`: Message when no records exist (FR-014)

**Table Attributes (attrs)**:

```python
{
    "class": "table table-striped table-hover table-bordered table-sm",
    "role": "table",
    "aria-label": "Product inventory table demonstrating django-tables2 integration"
}
```

**CSS Classes Rationale**:

- `table`: Bootstrap 5 base table class
- `table-striped`: Alternating row colors for readability
- `table-hover`: Row highlight on hover
- `table-bordered`: Cell borders for clearer data separation
- `table-sm`: Compact spacing (fits more data on screen)

#### Column Definitions

All columns use default django-tables2 rendering unless customization is needed.

**Sortable Columns** (default behavior):

- All columns sortable by default except description/tags
- Override with `orderable=False` for long text fields

**Column Customization Examples**:

```python
# Truncated text column for long descriptions
description = tables.Column(
    verbose_name="Description",
    attrs={"td": {"class": "text-truncate", "style": "max-width: 200px;"}},
    orderable=False
)

# Price formatting with currency
price = tables.Column(
    verbose_name="Price",
    attrs={"td": {"class": "text-end"}},
    orderable=True
)

# Status badge with color coding
status = tables.Column(
    verbose_name="Status",
    attrs={"td": {"class": "text-center"}},
    orderable=True
)

# Category with relationship traversal
category = tables.Column(
    verbose_name="Category",
    accessor="category__name",
    orderable=True
)

# Boolean as icon
is_featured = tables.BooleanColumn(
    verbose_name="Featured",
    yesno="✓,✗",
    attrs={"td": {"class": "text-center"}},
    orderable=True
)

# Date formatting
release_date = tables.DateColumn(
    verbose_name="Release Date",
    format="Y-m-d",
    orderable=True
)

# Centered numeric data
stock = tables.Column(
    verbose_name="Stock",
    attrs={"td": {"class": "text-center"}},
    orderable=True
)

# Rating with decimal formatting
rating = tables.Column(
    verbose_name="Rating",
    attrs={"td": {"class": "text-center"}},
    orderable=True
)
```

#### Empty State (FR-014)

**Meta.empty_text**: "No products available. Run 'poetry run python manage.py generate_dummy_data' to create sample data."

Displayed when queryset returns zero results. Styled by django-tables2 template.

#### Accessibility (FR-016, FR-017)

**ARIA Attributes**:

- Table: `role="table"`, `aria-label="..."`
- Column headers: Include `aria-sort` for sortable columns (handled by django-tables2)
- Pagination: Proper `aria-label` on navigation links (template override)

**Keyboard Navigation**:

- Sortable column headers are `<a>` elements (keyboard accessible)
- Pagination links are `<a>` elements (keyboard accessible)
- Tab order follows natural reading order

---

### 3. DataTablesView (Django View)

**Purpose**: View for rendering the Product table using django-tables2's SingleTableView.

**Location**: `demo/views.py`

**Base Class**: `django_tables2.SingleTableView`

#### Configuration

```python
class DataTablesView(SingleTableView):
    model = Product
    table_class = ProductTable
    template_name = "demo/datatables_demo.html"
    paginate_by = 25  # Items per page (FR-009)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Django Tables2 Demo'
        context['breadcrumbs'] = [
            {'text': 'Home', 'url': '/'},
            {'text': 'Integrations', 'url': None},
            {'text': 'DataTables Demo', 'url': None, 'active': True}
        ]
        return context
```

#### Attributes

- `model`: Product (source of table data)
- `table_class`: ProductTable (table configuration)
- `template_name`: Demo page template path
- `paginate_by`: 25 rows per page (configurable)

#### Methods

**get_queryset()**: (Optional override)

- Default: `Product.objects.all()`
- Can add filtering: `Product.objects.filter(status='published')`
- Can add prefetching: `Product.objects.select_related('category')`

**get_context_data()**: (Override)

- Adds page title for header block
- Adds breadcrumb navigation data
- Passes through table context from SingleTableView

---

## Database Schema

### Indexes (Existing)

Product model already has these database indexes:

1. **Primary Key**: `id` (auto-indexed)
2. **Unique Constraints**: `slug`, `sku` (auto-indexed)
3. **Foreign Keys**: `category_id` (auto-indexed)
4. **Manual Indexes**: None currently defined

### Performance Considerations

**Query Optimization**:

- Use `select_related('category')` to avoid N+1 queries
- Total data volume is small (27-50 products) - no pagination issues expected
- Sorting on indexed fields (slug, sku, category_id) will be fast

**Future Enhancements**:

- Add index on `status` if filtering by status becomes common
- Add index on `created_at` for "recent products" queries
- Consider composite index on `(status, priority)` for advanced filtering

---

## ARIA Compliance (FR-016)

All ARIA attributes will be applied in template layer:

### Table Element

```html
<table
    class="table table-striped table-hover"
    role="table"
    aria-label="Product inventory table with 18 columns">
```

### Column Headers

```html
<th role="columnheader"
    aria-sort="ascending"  <!-- when sorted -->
    scope="col">
    Product Name
</th>
```

### Sort Links

```html
<a href="?sort=name"
   aria-label="Sort by product name ascending">
    Product Name
    <span class="visually-hidden">Sort ascending</span>
</a>
```

### Pagination

```html
<nav aria-label="Product table pagination">
    <ul class="pagination">
        <li class="page-item">
            <a class="page-link"
               href="?page=1"
               aria-label="Go to page 1">1</a>
        </li>
    </ul>
</nav>
```

### Empty State

```html
<tr role="row">
    <td colspan="18"
        role="cell"
        class="text-center text-muted">
        No products available.
    </td>
</tr>
```

---

## API Contracts

While this feature doesn't introduce REST APIs, the django-tables2 integration provides these implicit contracts:

### URL Query Parameters

**Sorting** (FR-004, FR-005):

- `?sort=name` - Sort by name ascending
- `?sort=-name` - Sort by name descending
- `?sort=price,-rating` - Multi-column sort (price asc, rating desc)

**Pagination** (FR-009):

- `?page=1` - First page
- `?page=2` - Second page
- `per_page=25` - Items per page (if configurable)

**Filter** (FR-010 - future):

- `?status=published` - Filter by status
- `?category=electronics` - Filter by category slug

### Template Context

Views must provide this context for templates:

```python
{
    'table': ProductTable(queryset),  # django-tables2 table instance
    'page_title': str,                # For app-content-header
    'breadcrumbs': List[dict],        # For breadcrumb nav
}
```

### Template Blocks Expected

Demo template extends `mvp/base.html` and uses these blocks:

- `{% block page_title %}` - Header text
- `{% block breadcrumbs %}` - Breadcrumb items
- `{% block content %}` - Main content area

---

## Data Management

### Existing Management Command

**Command**: `generate_dummy_data`

**Location**: `demo/management/commands/generate_dummy_data.py` - **ALREADY EXISTS**

**Usage**:

```bash
poetry run python manage.py generate_dummy_data
```

**Current Behavior**:

- Creates ~27 Product instances
- Generates realistic product data (names, prices, stock, ratings, etc.)
- Distributes across existing categories
- Creates varied status/priority distributions

**Potential Enhancement**: May increase product count to 50+ for better vertical scrolling demonstration.

---

## Relationships to Other Components

### Dependencies

**Consumed By**:

- `ProductTable` (demo/tables.py) - Defines table structure
- `DataTablesView` (demo/views.py) - Provides queryset to view
- Templates (demo/templates/demo/datatables_demo.html) - Renders table

**Depends On**:

- Django ORM
- Existing Product and Category models
- Existing generate_dummy_data command

### Integration Points

1. **View Layer**: `DataTablesView.get_queryset()` returns `Product.objects.all()`
2. **Template Layer**: `{% render_table table %}` tag receives table instance with Product queryset
3. **Admin**: Product already registered with Django admin

---

## Testing Considerations

### Unit Tests (pytest-django)

**Model Tests**:

- No new model - uses existing Product model
- Verify Product model has expected fields for table display

**Table Tests**:

- Column configuration
- Empty state message display
- ARIA attributes presence
- CSS classes applied correctly

### Integration Tests

**View Tests**:

- View returns 200 status
- Context contains 'table' variable
- Template rendering succeeds
- Pagination works correctly

### E2E Tests (pytest-playwright)

**Data Interaction**:

- Sorting columns changes order
- Pagination navigates pages
- Empty state displays when no data
- Table renders correctly across viewport sizes

---

## Summary

**No New Models Required**: Uses existing Product model (18 fields, 27+ records)

**New Components**:

1. `ProductTable` class in `demo/tables.py`
2. `DataTablesView` class in `demo/views.py`
3. Demo template in `demo/templates/demo/datatables_demo.html`

**Data Source**: Existing `generate_dummy_data` management command

**Field Count**: 18 displayable fields (exceeds viewport for horizontal scroll demo)

**Row Count**: 27 existing products (may increase to 50+ for better vertical scroll)

**Performance**: Small dataset, no optimization needed for initial release

**Accessibility**: Full ARIA compliance via template attributes (FR-016)

---

## Next Steps

1. Implement `ProductTable` class with column customizations
2. Implement `DataTablesView` with pagination config
3. Create demo page template with fill mode layout
4. Override django-tables2 templates in `mvp/templates/django_tables2/`
5. Write tests for table rendering and sorting behavior

**Consumed By**:

- `ProductTable` (demo/tables.py) - Defines table structure
- `DataTablesView` (demo/views.py) - Provides queryset to view
- Templates (demo/templates/demo/datatables_demo.html) - Renders table

**Depends On**:

- Django ORM
- Existing Product and Category models
- Existing generate_dummy_data command
