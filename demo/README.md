# Demo App - Layout Demonstrations & Dummy Data

This Demo App demonstrates the django-cotton-layouts system through two main features:

1. **Layout Demonstrations**: Interactive views showcasing different inner layout configurations
2. **Dummy Data Examples**: Comprehensive list/detail views with realistic content

## Layout Demonstrations

The demo views showcase how the inner layout system works with different sidebar configurations while maintaining a consistent outer layout (controlled by `PAGE_CONFIG`).

All demo views are accessible from the **Inner Layouts** menu in the site navigation.

### Available Demo Views

#### No Sidebars
- **URL**: http://localhost:8000/
- **Layout**: Full-width content area without sidebars
- **Use Case**: Landing pages, dashboards, content-focused pages
- **Demonstrates**: Clean, spacious layout maximizing content area

#### Primary Sidebar
- **URL**: http://localhost:8000/demo/primary-sidebar/
- **Layout**: Left sidebar + main content area
- **Use Case**: Applications with persistent navigation, admin panels
- **Demonstrates**: Primary navigation and menu systems

#### Secondary Sidebar
- **URL**: http://localhost:8000/demo/secondary-sidebar/
- **Layout**: Main content area + right sidebar
- **Use Case**: Content with contextual actions, document editors
- **Demonstrates**: Supplementary tools and information alongside main content

#### Both
- **URL**: http://localhost:8000/demo/dual-sidebars/
- **Layout**: Left sidebar + main content + right sidebar
- **Use Case**: Complex applications requiring both navigation and contextual tools
- **Demonstrates**: Rich, multi-panel layouts for power users

### Testing Outer Layout Configurations

The outer layout (sidebar vs navbar mode) is configured via `PAGE_CONFIG` in Django settings.

To test different configurations:

1. Open `tests/settings.py` (or your project's settings file)
2. Modify the `PAGE_CONFIG` dictionary:

```python
# Sidebar mode (navigation in collapsible sidebar)
PAGE_CONFIG = {
    "brand": {"text": "Demo"},
    "sidebar": {"show_at": "lg", "collapsible": True},
    "navbar": {"fixed": False},
    "actions": [],
}

# Navbar mode (navigation in top navbar)
PAGE_CONFIG = {
    "brand": {"text": "Demo"},
    "sidebar": {"show_at": False},
    "navbar": {"fixed": True, "breakpoint": "md"},
    "actions": [],
}
```

3. Restart the development server
4. Navigate between demo views to see how inner layouts adapt

**Key Concept**: The outer layout is global (affects all pages), while inner layouts are per-page (each view configures its own sidebar content).

---

## Dummy Data Examples

This app also provides comprehensive dummy content to demonstrate various list view and detail view setups.

## Quick Start

### 1. Generate Dummy Data

To populate the database with example data:

```bash
poetry run python manage.py generate_dummy_data
```

To clear existing data and regenerate:

```bash
poetry run python manage.py generate_dummy_data --clear
```

### 2. Run the Development Server

```bash
poetry run python manage.py runserver
```

### 3. Access the Examples

Navigate to:
- **Products List**: http://localhost:8000/products/
- **Categories**: http://localhost:8000/categories/
- **Articles**: http://localhost:8000/articles/
- **Tasks**: http://localhost:8000/tasks/

## What's Included

### Models

#### Product
- **Purpose**: Demonstrates e-commerce/catalog views
- **Features**:
  - Multiple view modes (grid, list, table)
  - Filtering by category, status, availability
  - Search functionality
  - Stock tracking, pricing, ratings
  - Featured products
  - Related products
- **Sample Data**: 32 products across 5 categories

#### Category
- **Purpose**: Shows hierarchical organization
- **Features**:
  - Icon and color customization
  - Product grouping
  - Category-specific product listings
- **Sample Data**: 8 categories with icons and color variants

#### Article
- **Purpose**: Blog/content management demonstrations
- **Features**:
  - Author attribution
  - Read time estimates
  - View counts
  - Publishing workflow (draft, review, published)
  - Tags and categorization
  - Related content suggestions
- **Sample Data**: 20 articles with various statuses

#### Task
- **Purpose**: Project management/task tracking views
- **Features**:
  - Status workflow (todo, in progress, review, done)
  - Priority levels (low, medium, high, urgent)
  - Assignee tracking
  - Due dates with overdue detection
  - Time estimation vs actual tracking
  - Statistics dashboard
- **Sample Data**: 25 tasks with varying priorities and statuses

### View Templates

Each model includes:

#### List Views
- **Filtering**: Dynamic filters for common fields
- **Multiple Display Modes**: Grid, list, and table views where applicable
- **Pagination**: Configurable page sizes
- **Statistics**: Dashboard cards showing key metrics
- **Search**: Text-based search functionality

#### Detail Views
- **Comprehensive Display**: All model fields beautifully presented
- **Related Content**: Links to associated objects
- **Action Buttons**: Common actions (edit, delete, etc.)
- **Metadata**: Timestamps, status indicators, badges
- **Responsive Layout**: 2-column layout with sidebar

### View Modes Demonstrated

#### Products (All 3 modes)
1. **Grid View**: Card-based layout, perfect for visual browsing
2. **List View**: Compact list items with key information
3. **Table View**: Data-dense tabular display

#### Articles (Card Grid)
- Featured image placeholders
- Excerpt previews
- Author and date information
- Category badges

#### Tasks (Table View)
- Status and priority indicators
- Overdue highlighting
- Assignee filtering
- Statistics cards

#### Categories (Icon Grid)
- Large icons with brand colors
- Product counts
- Description previews

## Customization Examples

### Add More Products

```python
from demo.models import Product, Category

electronics = Category.objects.get(slug="electronics")
product = Product.objects.create(
    name="New Product",
    slug="new-product",
    category=electronics,
    description="Product description here",
    price=99.99,
    stock=50,
    status="published",
)
```

### Modify View Modes

In `product_list.html`, the view mode is controlled by the `view` query parameter:
- `?view=grid` - Grid layout (default)
- `?view=list` - List layout
- `?view=table` - Table layout

### Custom Filtering

Each list view supports filtering via query parameters:

**Products:**
- `?category=electronics` - Filter by category slug
- `?status=published` - Filter by status
- `?available=1` - Show only available products
- `?search=wireless` - Search in product names

**Articles:**
- `?category=technology` - Filter by category
- `?status=published` - Filter by status

**Tasks:**
- `?status=in_progress` - Filter by status
- `?priority=high` - Filter by priority
- `?assignee=John` - Filter by assignee name

## Template Structure

All templates extend `layouts/standard.html` and use these blocks:

```django
{% extends "layouts/standard.html" %}

{% block title %}Page Title{% endblock %}
{% block page_title %}Display Title{% endblock %}
{% block page_description %}Description{% endblock %}
{% block content %}
  {# Your content here #}
{% endblock %}
```

## Bootstrap Components Used

- **Cards**: Product/article/category displays
- **Badges**: Status indicators, tags, priority levels
- **Tables**: Task lists, product tables
- **Forms**: Filter controls, search inputs
- **Pagination**: Multi-page navigation
- **Grid System**: Responsive layouts
- **Buttons**: Actions, view mode toggles
- **Alerts**: Empty states, notifications

## Icons

Uses Bootstrap Icons throughout:
- `bi-box-seam` - Products
- `bi-folder` - Categories
- `bi-newspaper` - Articles
- `bi-check2-square` - Tasks
- `bi-person` - Assignees
- `bi-calendar-event` - Dates
- Many more...

## Testing Different Scenarios

### High Stock Products
Products with stock > 10 show green badge

### Low Stock Products
Products with stock 1-10 show yellow badge

### Out of Stock
Products with stock = 0 show red badge

### Overdue Tasks
Tasks with due_date in the past and status != "done" are highlighted in red

### Featured Products
25% of products are marked as featured

### Published vs Draft
75% of content is published, rest in draft/review

## Next Steps

1. **Customize Templates**: Modify the templates in `demo/templates/demo/` to match your design
2. **Add Filtering**: Extend the QuerySet filtering in views for more options
3. **Implement Forms**: Add create/edit forms for CRUD operations
4. **Add HTMX**: Enhance with dynamic loading and inline editing
5. **Style Customization**: Override Bootstrap variables or add custom CSS
6. **Add Sorting**: Implement table column sorting
7. **Export Features**: Add CSV/PDF export functionality

## Tips

- Use `{% load humanize %}` for better date/number formatting
- Leverage Bootstrap's utility classes for quick styling
- The dummy data uses realistic variety to test edge cases
- All models use slugs for SEO-friendly URLs
- Timestamps use `auto_now` and `auto_now_add` for automatic tracking
