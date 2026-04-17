# Quickstart: AdminLTE Layout Components

**Feature**: 001-layout-components
**Date**: January 5, 2026

## Overview

This guide shows how to use the five AdminLTE layout Cotton components in your Django templates.

## Prerequisites

- Django project with django-mvp installed
- Django Cotton configured (`INSTALLED_APPS` includes `'cotton'`)
- AdminLTE 4 CSS loaded (provided by django-mvp)

## Component Architecture

The django-mvp package provides five separate Cotton components for AdminLTE layouts:

- **wrapper** (`<c-app>`) - Top-level grid container
- **header** (`<c-app.header>`) - Navigation bar
- **sidebar** (`<c-app.sidebar>`) - Side navigation menu
- **main** (`<c-app.main>`) - Main content area
- **footer** (`<c-app.footer>`) - Page footer

## Basic Usage with mvp/base.html

The recommended approach is to extend `mvp/base.html`, which includes all five components with predefined template blocks for customization.

### Example: Dashboard Template

See `demo/templates/demo/dashboard.html` for a complete working example.

```django
{% extends "mvp/base.html" %}
{% load cotton %}

{% block page_title %}
  Dashboard
{% endblock page_title %}

{% block breadcrumbs %}
  <ol class="breadcrumb float-sm-end">
    <li class="breadcrumb-item">
      <a href="/">Home</a>
    </li>
    <li class="breadcrumb-item active" aria-current="page">Dashboard</li>
  </ol>
{% endblock breadcrumbs %}

{% block sidebar_menu %}
  <li class="nav-item">
    <a href="/" class="nav-link active">
      <i class="nav-icon bi bi-speedometer2"></i>
      <p>Dashboard</p>
    </a>
  </li>
  <li class="nav-item">
    <a href="#" class="nav-link">
      <i class="nav-icon bi bi-box-seam"></i>
      <p>Products</p>
    </a>
  </li>
{% endblock sidebar_menu %}

{% block content %}
  <div class="container-fluid">
    <div class="row">
      <div class="col-lg-3 col-6">
        <c-adminlte.small-box
          number="150"
          text="New Orders"
          icon="cart"
          class="text-bg-primary"
          href="#" />
      </div>
      <!-- More content -->
    </div>
  </div>
{% endblock content %}
```

## Available Template Blocks

The `mvp/base.html` template provides these customizable blocks:

### Layout Blocks

- `app_header` - Override entire header component
- `app_sidebar` - Override entire sidebar component
- `app_footer` - Override entire footer component

### Content Blocks

- `page_title` - Page title in content header
- `breadcrumbs` - Breadcrumb navigation
- `content` - Main page content

### Navigation Blocks

- `navbar_left` - Left side of navbar
- `navbar_right` - Right side of navbar
- `sidebar_menu` - Sidebar menu items
- `footer_right` - Right side of footer

## Component Reference

### Wrapper Component

Location: `mvp/templates/cotton/app/wrapper.html`

The wrapper component is the top-level grid container for the AdminLTE layout.

**Component Variables (c-vars):**

- `body_class` (optional) - Additional CSS classes for wrapper
- `fixed_sidebar` (optional) - Enable fixed sidebar positioning (`"true"`)
- `sidebar_expand` (optional) - Responsive breakpoint for sidebar (`"sm"`, `"md"`, `"lg"`, `"xl"`, `"xxl"`)

**Slots:**

- `header` - Header component
- `sidebar` - Sidebar component
- `main` - Main content component
- `footer` - Footer component

### Header Component

Location: `mvp/templates/cotton/app/header/` (subdirectory)

- `index.html` - Main header orchestrator with integrated navbar
- `toggle.html` - Sidebar toggle button component

The header component renders the top navigation bar with sidebar toggle and navbar slots.

**Component Variables (c-vars):**

- `class` (optional) - Additional CSS classes for header
- `container_class` (optional) - Container CSS classes (default: `"container-fluid"`)

**Slots:**

- `left` - Left navbar content (before toggle button)
- `right` - Right navbar content

**Sub-components:**

- `<c-app.header.toggle>` - Sidebar toggle button (included automatically in header)

### Sidebar Component

Location: `mvp/templates/cotton/app/sidebar.html`

The sidebar component renders the side navigation menu.

**Component Variables (c-vars):**

- `brand_text` (required) - Application name
- `brand_logo` (optional) - Logo image URL
- `brand_url` (optional) - Brand link URL (default: `"/"`)
- `theme` (optional) - Sidebar theme
- `class` (optional) - Additional CSS classes

**Slots:**

- Default slot - Sidebar menu items

### Main Component

Location: `mvp/templates/cotton/app/main.html`

The main component renders the content area.

**Component Variables (c-vars):**

- `show_header` (optional) - Show content header section (`"true"`, `"false"`)
- `container_class` (optional) - Container CSS classes

**Slots:**

- `header` - Page title and breadcrumbs
- Default slot - Main content

### Footer Component

Location: `mvp/templates/cotton/app/footer.html`

The footer component renders the page footer.

**Component Variables (c-vars):**

- `text` (optional) - Footer text content
- `class` (optional) - Additional CSS classes

**Slots:**

- `right` - Right side footer content
- Default slot - Override all footer content

## Advanced: Direct Component Usage

For advanced use cases, you can use components directly without extending `mvp/base.html`:

```django
{% load cotton %}

<c-app fixed_sidebar="true" sidebar_expand="lg">
  <c-slot name="header">
    <c-app.header>
      <c-slot name="right">
        <li class="nav-item">
          <a class="nav-link" href="/profile">Profile</a>
        </li>
      </c-slot>
    </c-app.header>
  </c-slot>

  <c-slot name="sidebar">
    <c-app.sidebar brand_text="My Application">
      <li class="nav-item">
        <a href="/" class="nav-link">
          <i class="nav-icon bi bi-house"></i>
          <p>Dashboard</p>
        </a>
      </li>
    </c-app.sidebar>
  </c-slot>

  <c-slot name="main">
    <c-app.main show_header="true">
      <c-slot name="header">
        <div class="row">
          <div class="col-sm-6">
            <h3 class="mb-0">Dashboard</h3>
          </div>
        </div>
      </c-slot>

      <div class="container-fluid">
        <!-- Your content -->
      </div>
    </c-app.main>
  </c-slot>

  <c-slot name="footer">
    <c-app.footer text="© 2026 My Application" />
  </c-slot>
</c-app>
```

## Next Steps

- Review the component source files in `mvp/templates/cotton/app/`
- See `demo/templates/demo/dashboard.html` for a complete example
- Refer to [AdminLTE 4 documentation](https://adminlte.io/docs/4.0/) for CSS classes and JavaScript features
- Additional layout patterns will be documented in a separate specification
