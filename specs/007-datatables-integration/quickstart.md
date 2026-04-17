# Quickstart: Django Tables2 Integration with MVP Layouts

**Phase**: 1 - Design & Contracts
**Date**: January 20, 2026
**Feature**: [spec.md](spec.md)

## Overview

This guide shows how to integrate django-tables2 with django-mvp layouts, supporting both fill mode (viewport-height tables with independent scrolling) and standard mode (content-based height with normal page scrolling).

---

## Installation

### Option 1: Optional Dependency (Recommended for Production)

```bash
pip install django-mvp[datatables2]
```

This installs both django-mvp and django-tables2.

### Option 2: Development Installation

```bash
git clone https://github.com/SamuelJennings/django-mvp.git
cd django-mvp
poetry install  # Includes django-tables2 as dev dependency
```

---

## Quick Start (5 Minutes)

### Step 1: Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'django_tables2',
    'mvp',
    # ... your apps
]
```

### Step 2: Create a Model (or Use Existing)

```python
# myapp/models.py
from django.db import models

class Employee(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    hire_date = models.DateField()

    def __str__(self):
        return self.name
```

### Step 3: Define a Table

```python
# myapp/tables.py
import django_tables2 as tables
from .models import Employee

class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        template_name = "django_tables2/bootstrap5-responsive.html"
        attrs = {
            "class": "table table-striped table-hover table-bordered",
            "role": "table"
        }
```

### Step 4: Create a View

```python
# myapp/views.py
from django_tables2.views import SingleTableView
from .models import Employee
from .tables import EmployeeTable

class EmployeeListView(SingleTableView):
    model = Employee
    table_class = EmployeeTable
    template_name = "myapp/employee_list.html"
    paginate_by = 25  # Optional: items per page
```

### Step 5: Add URL Pattern

```python
# myapp/urls.py
from django.urls import path
from .views import EmployeeListView

urlpatterns = [
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
]
```

### Step 6: Create Template

**Standard Mode Template** (content-based height):

```django
{# myapp/templates/myapp/employee_list.html #}
{% extends "mvp/base.html" %}
{% load render_table from django_tables2 %}

{% block page_title %}Employees{% endblock %}

{% block content %}
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">Employee Directory</h3>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                {% render_table table %}
            </div>
        </div>
    </div>
{% endblock %}
```

**Fill Mode Template** (viewport-height with independent scrolling):

```django
{# myapp/templates/myapp/employee_list.html #}
{% extends "mvp/base.html" %}
{% load render_table from django_tables2 %}

{% block page_title %}Employees{% endblock %}

{% block content %}
    <div class="d-flex flex-column h-100">
        {# Optional: Header section (fixed) #}
        <div class="mb-3">
            <h3>Employee Directory</h3>
            <p class="text-muted">Showing {{ table.paginator.count }} employees</p>
        </div>

        {# Table section (fills remaining space, scrolls independently) #}
        <div class="table-responsive flex-grow-1 overflow-auto">
            {% render_table table %}
        </div>
    </div>
{% endblock %}
```

---

## Fill Mode vs Standard Mode

### When to Use Fill Mode

**Use fill mode when:**

- Building data-heavy admin interfaces
- Displaying tables as primary page content
- Users need to scan large datasets efficiently
- Header/sidebar should remain visible while scrolling table

**Layout Requirements:**

```django
<div class="d-flex flex-column h-100">
    <div><!-- Fixed content (optional) --></div>
    <div class="flex-grow-1 overflow-auto">
        <!-- Scrollable table -->
    </div>
</div>
```

**Key CSS Classes:**

- `d-flex flex-column`: Flexbox column layout
- `h-100`: Full height (100% of parent)
- `flex-grow-1`: Table container grows to fill available space
- `overflow-auto`: Enables independent scrolling

### When to Use Standard Mode

**Use standard mode when:**

- Table is one of multiple page sections
- Content height is more important than viewport fill
- Traditional page scrolling behavior is expected
- Table is part of a longer form or multi-section page

**Layout:**

```django
<div class="table-responsive">
    {% render_table table %}
</div>
```

**Behavior:**

- Table height determined by content
- Entire page scrolls normally
- No independent table scrolling

---

## Configuration Options

### Pagination

**Enable Pagination** (default):

```python
class EmployeeListView(SingleTableView):
    table_class = EmployeeTable
    paginate_by = 25  # Rows per page
```

**Disable Pagination**:

```python
class EmployeeListView(SingleTableView):
    table_class = EmployeeTable
    table_pagination = False
```

**Lazy Pagination** (for large datasets):

```python
from django_tables2.paginators import LazyPaginator

class EmployeeListView(SingleTableView):
    table_class = EmployeeTable
    paginator_class = LazyPaginator
    paginate_by = 25
```

### Sorting

**Enable Sorting** (default):

```python
class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        # All columns sortable by default
```

**Disable Sorting for Specific Columns**:

```python
class EmployeeTable(tables.Table):
    name = tables.Column(orderable=True)
    notes = tables.Column(orderable=False)  # Not sortable

    class Meta:
        model = Employee
```

### Filtering (with django-filter)

**Install**:

```bash
pip install django-filter
```

**Create FilterSet**:

```python
# myapp/filters.py
import django_filters
from .models import Employee

class EmployeeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    department = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Employee
        fields = ['name', 'department', 'hire_date']
```

**Update View**:

```python
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

class EmployeeListView(SingleTableMixin, FilterView):
    table_class = EmployeeTable
    model = Employee
    template_name = "myapp/employee_list.html"
    filterset_class = EmployeeFilter
```

**Template**:

```django
{% block content %}
<div class="d-flex flex-column h-100">
    {# Filter form #}
    <div class="mb-3">
        <form method="get" class="row g-3">
            {{ filter.form.as_p }}
            <button type="submit" class="btn btn-primary">Filter</button>
        </form>
    </div>

    {# Table #}
    <div class="table-responsive flex-grow-1 overflow-auto">
        {% render_table table %}
    </div>
</div>
{% endblock %}
```

---

## Styling & Customization

### Table CSS Classes

**AdminLTE 4 + Bootstrap 5 Recommended Classes**:

```python
class EmployeeTable(tables.Table):
    class Meta:
        attrs = {
            "class": "table table-striped table-hover table-bordered table-sm",
            "role": "table"
        }
```

**Class Reference**:

- `table`: Base Bootstrap table class (required)
- `table-striped`: Alternating row colors
- `table-hover`: Highlight on hover
- `table-bordered`: Cell borders
- `table-sm`: Compact spacing
- `table-dark`: Dark theme
- `table-responsive`: Horizontal scrolling (applied to wrapper div)

### Column Styling

**Center-align column**:

```python
status = tables.Column(attrs={"td": {"class": "text-center"}})
```

**Custom header**:

```python
hire_date = tables.DateColumn(verbose_name="Date Hired")
```

**Link column to detail page**:

```python
name = tables.Column(linkify=True)  # Links to get_absolute_url()
```

**Conditional formatting**:

```python
class EmployeeTable(tables.Table):
    status = tables.Column()

    def render_status(self, value):
        if value == "Active":
            return format_html('<span class="badge bg-success">{}</span>', value)
        return format_html('<span class="badge bg-secondary">{}</span>', value)
```

### Empty State Customization

```python
class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        empty_text = "No employees found matching your criteria."
```

---

## Accessibility Features

### Built-in Accessibility (django-tables2)

**Provided Automatically**:

- `<th>` elements for column headers
- `aria-sort` attributes on sortable columns
- Keyboard-accessible links for sorting/pagination
- Semantic HTML table structure

### Custom ARIA Labels

```python
class EmployeeTable(tables.Table):
    class Meta:
        attrs = {
            "class": "table table-striped",
            "role": "table",
            "aria-label": "Employee directory with sortable columns"
        }
```

### Template Overrides for Accessibility

Create `myapp/templates/django_tables2/bootstrap5-responsive.html`:

```django
{% extends 'django_tables2/bootstrap5.html' %}

{% block table-wrapper %}
<div class="table-responsive" role="region" aria-label="Data table">
    {% block table %}{{ block.super }}{% endblock %}
    {% block pagination %}{{ block.super }}{% endblock %}
</div>
{% endblock %}
```

---

## Advanced Patterns

### Custom QuerySet

```python
class EmployeeListView(SingleTableView):
    table_class = EmployeeTable

    def get_queryset(self):
        # Only show active employees
        return Employee.objects.filter(status='Active').select_related('department')
```

### Multiple Tables Per Page

```python
from django_tables2 import RequestConfig

def dashboard(request):
    recent_employees = EmployeeTable(Employee.objects.order_by('-hire_date')[:5])
    RequestConfig(request, paginate=False).configure(recent_employees)

    all_departments = DepartmentTable(Department.objects.all())
    RequestConfig(request, paginate={"per_page": 10}).configure(all_departments)

    return render(request, 'dashboard.html', {
        'recent_employees': recent_employees,
        'all_departments': all_departments
    })
```

### Custom Table Template

```python
class EmployeeTable(tables.Table):
    class Meta:
        template_name = "myapp/custom_table.html"  # Your custom template
```

---

## Responsive Design

### Mobile-First Approach

**Template Pattern**:

```django
<div class="table-responsive">
    {# Horizontal scroll on mobile, full width on desktop #}
    {% render_table table %}
</div>
```

**Breakpoint-Specific Responsive**:

```django
<div class="table-responsive-lg">
    {# Scrollable below 'lg' breakpoint, full width above #}
    {% render_table table %}
</div>
```

### Column Visibility

**Hide columns on small screens**:

```python
class EmployeeTable(tables.Table):
    name = tables.Column()
    email = tables.Column(attrs={"td": {"class": "d-none d-md-table-cell"}})
    phone = tables.Column(attrs={"td": {"class": "d-none d-lg-table-cell"}})
```

---

## Performance Tips

### 1. Use select_related() and prefetch_related()

```python
def get_queryset(self):
    return Employee.objects.select_related('department', 'manager').all()
```

### 2. Use LazyPaginator for Large Datasets

```python
from django_tables2.paginators import LazyPaginator

class EmployeeListView(SingleTableView):
    paginator_class = LazyPaginator
```

### 3. Limit Column Count

Only include necessary columns:

```python
class EmployeeTable(tables.Table):
    class Meta:
        model = Employee
        fields = ('name', 'email', 'department')  # Limit columns
```

### 4. Add Database Indexes

```python
class Employee(models.Model):
    name = models.CharField(max_length=200, db_index=True)  # For sorting
```

---

## Demo Page

**Explore the Full Demo**:
Navigate to `/datatables-demo/` to see:

- Fill mode with independent scrolling
- Sorting on all columns
- Pagination with configurable page size
- Responsive design across viewport sizes
- ARIA-compliant markup for screen readers

**Demo Source Code**:

- View: `demo/views.py` → `DataTablesView`
- Table: `demo/tables.py` → `SampleDataTable`
- Model: `demo/models.py` → `SampleData`
- Template: `demo/templates/demo/datatables_demo.html`

---

## Troubleshooting

### Table Not Rendering

**Check**:

1. `django_tables2` in `INSTALLED_APPS`
2. `{% load render_table from django_tables2 %}` in template
3. View passes `table` to context (SingleTableView does this automatically)

### Styling Issues

**Ensure**:

1. Bootstrap 5 CSS is loaded (django-mvp includes this)
2. Table `attrs` include Bootstrap classes
3. Template uses `django_tables2/bootstrap5-responsive.html` or `bootstrap5.html`

### Fill Mode Not Working

**Verify**:

1. Parent container has `h-100` class
2. MVP layout configured for fill mode
3. Table wrapper has `flex-grow-1 overflow-auto`
4. `.app-content` block is not overriding height

### Sorting Not Working

**Check**:

1. Columns are `orderable=True` (default)
2. `RequestConfig` applied to table (SingleTableView does this)
3. URL querystring includes `?sort=column_name`

---

## Further Reading

- [django-tables2 Official Docs](https://django-tables2.readthedocs.io/)
- [Bootstrap 5 Tables](https://getbootstrap.com/docs/5.0/content/tables/)
- [AdminLTE 4 Documentation](https://adminlte.io/docs/)
- [django-mvp Layouts Guide](../../docs/layout-configuration.md)

---

## Next Steps

1. ✅ Quickstart guide complete
2. → Update agent context with django-tables2
3. → Re-evaluate constitution check
4. → Proceed to Phase 2: Implementation Tasks
