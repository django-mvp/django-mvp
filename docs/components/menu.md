# Menu Components

**Components**: `<c-app.sidebar.menu>`, `<c-app.sidebar.menu-item>`, `<c-app.sidebar.menu-collapse>`, `<c-app.sidebar.menu-group>`
**Location**: `mvp/templates/cotton/app/sidebar/`
**Status**: ✅ Implemented

## Overview

Menu components provide template-level control for building AdminLTE 4 sidebar navigation. These Cotton components render semantic HTML with proper AdminLTE CSS classes and JavaScript behaviors.

**Use Cotton components when:**

- Building page-specific navigation
- Prototyping layouts
- Menu structure requires complex template logic
- You need custom HTML output

**For production apps with centralized menus**, use [AppMenu](../navigation.md#appmenu-django-flex-menus) instead.

## Component Hierarchy

```django
<c-app.sidebar.menu>                        {# Container #}
    <c-app.sidebar.menu-item />             {# Single item (leaf) #}
    <c-app.sidebar.menu-collapse>           {# Expandable dropdown #}
        <c-app.sidebar.menu-item />         {# Nested items #}
    </c-app.sidebar.menu-collapse>
    <c-app.sidebar.menu-group>              {# Section header #}
        <c-app.sidebar.menu-item />         {# Grouped items #}
    </c-app.sidebar.menu-group>
</c-app.sidebar.menu>
```

## Menu Container

### `<c-app.sidebar.menu>`

**File**: `mvp/templates/cotton/app/sidebar/menu.html`

Wraps the navigation menu list. Provides the `<ul>` container with AdminLTE classes.

### Basic Usage

```django
<c-app.sidebar.menu>
    <c-app.sidebar.menu-item label="Dashboard" href="/" icon="house" />
    <c-app.sidebar.menu-item label="Profile" href="/profile" icon="person" />
</c-app.sidebar.menu>
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | str | `"Main Navigation"` | ARIA label for accessibility |
| `id` | str | `"navigation"` | HTML id attribute |

### Generated HTML

```html
<ul id="navigation"
    class="nav sidebar-menu flex-column"
    aria-label="Main Navigation"
    role="navigation"
    data-lte-toggle="treeview"
    data-accordion="false">
    <!-- Menu items here -->
</ul>
```

### Custom Label

```django
<c-app.sidebar.menu label="Admin Menu">
    <!-- Items -->
</c-app.sidebar.menu>
```

## Menu Item

### `<c-app.sidebar.menu-item>`

**File**: `mvp/templates/cotton/app/sidebar/menu_item.html`

Renders a single menu item or parent item with children. Handles both leaf nodes (clickable links) and parent nodes (expandable dropdowns).

### Single Item (Leaf)

```django
<c-app.sidebar.menu-item
    label="Dashboard"
    href="/"
    icon="house" />
```

**Generated HTML:**

```html
<li class="nav-item">
    <a href="/" class="nav-link">
        <i class="bi bi-house nav-icon"></i>
        <p>Dashboard</p>
    </a>
</li>
```

### Parent Item (with children)

```django
<c-app.sidebar.menu-item label="Products" icon="box-seam">
    <c-app.sidebar.menu-item label="All Products" href="/products" />
    <c-app.sidebar.menu-item label="Add Product" href="/products/add" />
</c-app.sidebar.menu-item>
```

**Generated HTML:**

```html
<li class="nav-item">
    <a href="#" class="nav-link">
        <i class="bi bi-box-seam nav-icon"></i>
        <p>
            Products
            <i class="bi bi-chevron-right nav-arrow"></i>
        </p>
    </a>
    <ul class="nav nav-treeview" role="navigation" aria-label="Products">
        <li class="nav-item">
            <a href="/products" class="nav-link">
                <i class="bi bi-circle nav-icon"></i>
                <p>All Products</p>
            </a>
        </li>
        <!-- More items -->
    </ul>
</li>
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | str | Required | Display text |
| `href` | str | `"#"` | Link URL (use `#` for parent items) |
| `icon` | str | `"circle"` | Icon name (django-easy-icons) |
| `active` | bool | `false` | Whether item is active/current |

### Active State

Highlight the current page:

```django
<c-app.sidebar.menu-item
    label="Dashboard"
    href="/"
    icon="house"
    active />
```

**Effect:**

- Adds `.active` class to link
- For parent items: adds `.menu-open` class and inline `style="display: block;"` to expand children

### Icons

Icons use [django-easy-icons](https://github.com/SamuelJennings/django-easy-icons) with Bootstrap Icons by default:

```django
{# Common icons #}
<c-app.sidebar.menu-item label="Home" icon="house" href="/" />
<c-app.sidebar.menu-item label="Users" icon="people" href="/users" />
<c-app.sidebar.menu-item label="Settings" icon="gear" href="/settings" />
<c-app.sidebar.menu-item label="Reports" icon="graph-up" href="/reports" />
```

**Available icon sets:**

- `bi` - Bootstrap Icons (default)
- `fa` - Font Awesome
- `material` - Material Icons
- Custom icon sets via django-easy-icons configuration

### Nested Items

Create hierarchical menus by nesting items:

```django
<c-app.sidebar.menu-item label="Catalog" icon="folder">
    <c-app.sidebar.menu-item label="Products" href="/products" />
    <c-app.sidebar.menu-item label="Categories" icon="folder-open">
        <c-app.sidebar.menu-item label="Electronics" href="/cat/electronics" />
        <c-app.sidebar.menu-item label="Clothing" href="/cat/clothing" />
    </c-app.sidebar.menu-item>
</c-app.sidebar.menu-item>
```

**Best practices:**

- Limit to 2-3 nesting levels
- Use consistent icons at each level
- Keep labels concise

## Menu Collapse

### `<c-app.sidebar.menu-collapse>`

**File**: `mvp/templates/cotton/app/sidebar/menu-collapse.html`

Specialized component for expandable dropdown menus. Similar to `menu-item` with children but with explicit AdminLTE treeview attributes.

### Usage

```django
<c-app.sidebar.menu-collapse label="Reports" icon="graph-up">
    <c-app.sidebar.menu-item label="Sales" href="/reports/sales" />
    <c-app.sidebar.menu-item label="Inventory" href="/reports/inventory" />
    <c-app.sidebar.menu-item label="Customers" href="/reports/customers" />
</c-app.sidebar.menu-collapse>
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | str | Required | Display text |
| `icon` | str | `"circle"` | Icon name |
| `active` | bool | `false` | Whether dropdown is active (expanded) |

### Active State

Expand dropdown by default:

```django
<c-app.sidebar.menu-collapse label="Reports" icon="graph-up" active>
    <c-app.sidebar.menu-item label="Sales" href="/reports/sales" active />
    <c-app.sidebar.menu-item label="Inventory" href="/reports/inventory" />
</c-app.sidebar.menu-collapse>
```

**Effect:**

- Adds `.menu-open` class to parent
- Adds inline `style="display: block;"` to show children
- Rotates chevron icon to indicate open state

### Generated HTML

```html
<li class="nav-item menu-open">
    <a href="#" data-lte-toggle="treeview" class="nav-link active">
        <i class="bi bi-graph-up nav-icon"></i>
        <p>
            Reports
            <i class="bi bi-chevron-right nav-arrow"></i>
        </p>
    </a>
    <ul class="nav nav-treeview"
        style="display: block;"
        role="navigation"
        aria-label="Reports">
        <!-- Children -->
    </ul>
</li>
```

**JavaScript Behavior:**

- Click parent link to toggle expand/collapse
- Chevron rotates on state change
- Smooth height transition animation
- Only one dropdown open at a time (accordion mode)

### Difference from menu-item

| Feature | menu-item | menu-collapse |
|---------|-----------|---------------|
| **Purpose** | Generic item | Explicit dropdown |
| **Children detection** | Automatic (via slot) | Explicit component |
| **data-lte-toggle** | Auto-added if slot | Always present |
| **Use case** | General purpose | Clear intent for dropdowns |

**Recommendation:** Use `menu-collapse` for better code clarity when building static templates. Both produce identical output when used with children.

## Menu Group

### `<c-app.sidebar.menu-group>`

**File**: `mvp/templates/cotton/app/sidebar/menu-group.html`

Section header component for grouping related menu items. Renders as non-clickable uppercase header.

### Usage

```django
<c-app.sidebar.menu-group label="ADMINISTRATION">
    <c-app.sidebar.menu-item label="Users" href="/admin/users" icon="person-badge" />
    <c-app.sidebar.menu-item label="Roles" href="/admin/roles" icon="shield-check" />
    <c-app.sidebar.menu-item label="Settings" href="/admin/settings" icon="gear" />
</c-app.sidebar.menu-group>
```

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | str | Required | Section header text (uppercase recommended) |

### Generated HTML

```html
<li class="nav-header text-uppercase">ADMINISTRATION</li>
<!-- Menu items rendered here -->
```

### Styling

Headers automatically receive:

- `.nav-header` class (AdminLTE styling)
- `.text-uppercase` class (uppercase text)
- Lighter text color
- Additional top padding for visual separation

### Mixed Content

Combine regular items and dropdowns within groups:

```django
<c-app.sidebar.menu-group label="CONTENT">
    <c-app.sidebar.menu-item label="Pages" href="/content/pages" icon="file-text" />
    <c-app.sidebar.menu-item label="Media" href="/content/media" icon="images" />

    <c-app.sidebar.menu-collapse label="Blog" icon="newspaper">
        <c-app.sidebar.menu-item label="All Posts" href="/blog/posts" />
        <c-app.sidebar.menu-item label="Categories" href="/blog/categories" />
    </c-app.sidebar.menu-collapse>
</c-app.sidebar.menu-group>
```

## Complete Example

### E-commerce Application Menu

```django
<c-app.sidebar>
    <c-app.sidebar.menu label="E-commerce Menu">
        {# Dashboard #}
        <c-app.sidebar.menu-item
            label="Dashboard"
            href="{% url 'dashboard' %}"
            icon="house"
            active />

        {# Products dropdown #}
        <c-app.sidebar.menu-collapse label="Products" icon="box-seam">
            <c-app.sidebar.menu-item
                label="All Products"
                href="{% url 'products:list' %}"
                icon="list" />
            <c-app.sidebar.menu-item
                label="Add Product"
                href="{% url 'products:create' %}"
                icon="plus-circle" />
            <c-app.sidebar.menu-item
                label="Categories"
                href="{% url 'products:categories' %}"
                icon="folder" />
        </c-app.sidebar.menu-collapse>

        {# Orders dropdown #}
        <c-app.sidebar.menu-collapse label="Orders" icon="cart">
            <c-app.sidebar.menu-item
                label="All Orders"
                href="{% url 'orders:list' %}" />
            <c-app.sidebar.menu-item
                label="Pending"
                href="{% url 'orders:pending' %}" />
            <c-app.sidebar.menu-item
                label="Shipped"
                href="{% url 'orders:shipped' %}" />
        </c-app.sidebar.menu-collapse>

        {# Reports section #}
        <c-app.sidebar.menu-group label="REPORTS">
            <c-app.sidebar.menu-item
                label="Sales"
                href="{% url 'reports:sales' %}"
                icon="graph-up" />
            <c-app.sidebar.menu-item
                label="Inventory"
                href="{% url 'reports:inventory' %}"
                icon="boxes" />
            <c-app.sidebar.menu-item
                label="Customers"
                href="{% url 'reports:customers' %}"
                icon="people" />
        </c-app.sidebar.menu-group>

        {# Admin section #}
        <c-app.sidebar.menu-group label="ADMINISTRATION">
            <c-app.sidebar.menu-item
                label="Users"
                href="{% url 'admin:users' %}"
                icon="person-badge" />
            <c-app.sidebar.menu-item
                label="Settings"
                href="{% url 'admin:settings' %}"
                icon="gear" />
        </c-app.sidebar.menu-group>
    </c-app.sidebar.menu>
</c-app.sidebar>
```

## Dynamic Menus

### Conditional Items

Show/hide items based on permissions:

```django
<c-app.sidebar.menu>
    <c-app.sidebar.menu-item label="Dashboard" href="/" icon="house" />

    {% if user.is_staff %}
        <c-app.sidebar.menu-group label="ADMIN">
            <c-app.sidebar.menu-item
                label="User Management"
                href="{% url 'admin:users' %}"
                icon="people" />
        </c-app.sidebar.menu-group>
    {% endif %}

    {% if user.has_perm('products.view_product') %}
        <c-app.sidebar.menu-item
            label="Products"
            href="{% url 'products:list' %}"
            icon="box" />
    {% endif %}
</c-app.sidebar.menu>
```

### Loop Through Items

Generate menu from data:

```django
<c-app.sidebar.menu-collapse label="Categories" icon="folder">
    {% for category in categories %}
        <c-app.sidebar.menu-item
            label="{{ category.name }}"
            href="{% url 'category_detail' category.slug %}" />
    {% endfor %}
</c-app.sidebar.menu-collapse>
```

### Active State from Request

Highlight current section:

```django
<c-app.sidebar.menu-item
    label="Products"
    href="{% url 'products:list' %}"
    icon="box"
    {% if request.resolver_match.url_name == 'products:list' %}active{% endif %} />
```

Or use a template tag:

```django
{% load menu_tags %}

<c-app.sidebar.menu-item
    label="Products"
    href="{% url 'products:list' %}"
    icon="box"
    {% archived 'products:*' %}active{% endarchived %} />
```

## Accessibility

All menu components are ARIA-compliant:

- **Semantic HTML**: Proper `<nav>`, `<ul>`, `<li>` structure
- **ARIA labels**: Navigation regions labeled for screen readers
- **Keyboard navigation**: Full keyboard support (Tab, Enter, Arrow keys)
- **Focus management**: Visible focus indicators
- **Screen reader support**: Expandable state announced

### Example ARIA Structure

```html
<ul role="navigation" aria-label="Main Navigation">
    <li class="nav-item">
        <a href="/" class="nav-link">Dashboard</a>
    </li>
    <li class="nav-item">
        <a href="#" class="nav-link" data-lte-toggle="treeview">
            Products
        </a>
        <ul class="nav nav-treeview"
            role="navigation"
            aria-label="Products">
            <!-- Nested items -->
        </ul>
    </li>
</ul>
```

## Best Practices

### 1. Keep Labels Concise

```django
<!-- ✅ Good -->
<c-app.sidebar.menu-item label="Products" href="/products" />

<!-- ❌ Avoid -->
<c-app.sidebar.menu-item label="View All Products in Catalog" href="/products" />
```

### 2. Use Consistent Icons

```django
<!-- ✅ Good: Consistent folder icons -->
<c-app.sidebar.menu-collapse label="Catalog" icon="folder">
    <c-app.sidebar.menu-collapse label="Products" icon="folder">
        <!-- Items -->
    </c-app.sidebar.menu-collapse>
</c-app.sidebar.menu-collapse>

<!-- ❌ Avoid: Mixing icon styles -->
<c-app.sidebar.menu-collapse label="Catalog" icon="folder">
    <c-app.sidebar.menu-collapse label="Products" icon="box-seam">
        <!-- Items -->
    </c-app.sidebar.menu-collapse>
</c-app.sidebar.menu-collapse>
```

### 3. Limit Nesting Depth

```django
<!-- ✅ Good: 2 levels -->
<c-app.sidebar.menu-collapse label="Products" icon="box">
    <c-app.sidebar.menu-collapse label="Categories" icon="folder">
        <c-app.sidebar.menu-item label="Electronics" href="/cat/electronics" />
    </c-app.sidebar.menu-collapse>
</c-app.sidebar.menu-collapse>

<!-- ⚠️ Avoid: 3+ levels (hard to use) -->
<c-app.sidebar.menu-collapse label="Products">
    <c-app.sidebar.menu-collapse label="Categories">
        <c-app.sidebar.menu-collapse label="Electronics">
            <c-app.sidebar.menu-item label="Computers" href="/cat/computers" />
        </c-app.sidebar.menu-collapse>
    </c-app.sidebar.menu-collapse>
</c-app.sidebar.menu-collapse>
```

### 4. Use Groups for Organization

```django
<!-- ✅ Good: Grouped by purpose -->
<c-app.sidebar.menu>
    <c-app.sidebar.menu-item label="Dashboard" href="/" />

    <c-app.sidebar.menu-group label="CONTENT">
        <c-app.sidebar.menu-item label="Pages" href="/pages" />
        <c-app.sidebar.menu-item label="Posts" href="/posts" />
    </c-app.sidebar.menu-group>

    <c-app.sidebar.menu-group label="SETTINGS">
        <c-app.sidebar.menu-item label="Account" href="/account" />
        <c-app.sidebar.menu-item label="Privacy" href="/privacy" />
    </c-app.sidebar.menu-group>
</c-app.sidebar.menu>
```

### 5. Uppercase Section Headers

```django
<!-- ✅ Good: Uppercase for visual distinction -->
<c-app.sidebar.menu-group label="ADMINISTRATION">

<!-- ❌ Avoid: Mixed case -->
<c-app.sidebar.menu-group label="Administration">
```

## See Also

- **[Navigation System Overview](../navigation.md)** - AppMenu vs Cotton Components
- **[App Component](app.md)** - Sidebar configuration
- **[django-easy-icons](https://github.com/SamuelJennings/django-easy-icons)** - Icon system
