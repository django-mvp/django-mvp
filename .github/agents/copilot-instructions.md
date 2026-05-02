# django-cotton-layouts Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies
- Python 3.10-3.12 + Django 4.2-5.x, django-cotton =2.3.1, django-cotton-bs5 ^0.5.1, Bootstrap 5.3, django-compressor ^4.5.1, django-libsass ^0.9 (002-page-layout)
- N/A (component library) (002-page-layout)
- Python 3.11+ / Django 4.2+ + django-cotton (Cotton component system with c-vars and slots), AdminLTE 4 (CSS framework) (001-layout-components)
- N/A (template-only refactor) (001-layout-components)
- Python 3.11+ + Django 4.2+, django-cotton (Cotton component system with c-vars and slots) (001-layout-components)
- N/A (template-only feature) (001-layout-components)
- Python 3.11+, Django 4.2+ + django-cotton (template engine), Bootstrap 5.3, AdminLTE 4, Bootstrap Icons (003-default-widgets)
- N/A (template-only components) (003-default-widgets)
- Python 3.10-3.12 + Django 4.2-5.x, django-cotton >=2.3.1, AdminLTE 4 (CSS via CDN) (002-layout-configuration)
- N/A (no database changes - template/static files only) (002-layout-configuration)
- Python 3.10-3.12 (Django MVP supports 3.10, 3.11, 3.12) + Django 4.2-5.x, django-flex-menus ^0.4.1, django-cotton ^2.3.1, django-easy-icons ^0.4.0, django-cotton-bs5 ^0.5.1 (004-site-navigation)
- N/A (menu configuration is code-based, not database-backed) (004-site-navigation)
- Python 3.11, Django 5.1+ + django-cotton (template components), AdminLTE 4 (CSS framework) (002-layout-configuration)
- N/A (configuration-driven layout, no data persistence) (002-layout-configuration)
- [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION] + [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION] (006-page-layout)
- [if applicable, e.g., PostgreSQL, CoreData, files or N/A] (006-page-layout)
- Python 3.10+, Django 4.2-5.x + Django (>=4.2,<6.0), django-cotton (>=2.3.1), django-cotton-bs5 (^0.5.1), Bootstrap 5.3 (006-page-layout)
- N/A (UI components only, no data persistence) (006-page-layout)
- Python 3.11 (django-mvp requirement) + Django 5.1+, django-cotton (Cotton components), AdminLTE 4 (CSS/layout framework) (002-layout-configuration)
- N/A (configuration-only feature, no data persistence) (002-layout-configuration)
- Python 3.10+ (project supports 3.10, 3.11, 3.12) + Django 4.2-5.x, django-tables2 2.x, django-cotton 2.3.1+, django-cotton-bs5, Bootstrap 5, AdminLTE 4 (007-datatables-integration)
- SQLite (development), sample data via Django models or fixtures (007-datatables-integration)
- Python 3.11+ with Django 4.2+ + Django, django-cotton, django-filter (optional), crispy-forms (008-dash-list-view)
- N/A (works with any Django model) (008-dash-list-view)
- Python 3.11+ with Django 4.2+ + Django, django-cotton, django-crispy-forms (optional), django-formset (optional) (009-form-view-mixin)
- N/A (works with any Django model for ModelFormView) (009-form-view-mixin)
- Python 3.11+ / Django 4.2�5.x + django-cotton (>=2.3.1), django-cotton-bs5 (>=0.9.0), django-flex-menus (>=0.4.1), django-easy-icons (>=0.5), AdminLTE 4 (rc3, bundled locally), Bootstrap 5 (001-app-components)
- N/A (no database models � all state is declarative via template attributes) (001-app-components)
- Python 3.10+ + Django 4.2–5.x, pytest, pytest-django (003-base-mixin-classes)
- N/A (no database models) (003-base-mixin-classes)

- Python 3.11 (tests target) + Django, django-cotton, django-cotton-bs5, django-flex-menus, django-easy-icons, django-compressor, django-libsass, crispy-forms/bootstrap5 (001-outer-layout-config)

## Project Structure

```text
src/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11 (tests target): Follow standard conventions

## Recent Changes
- 003-base-mixin-classes: Added Python 3.10+ + Django 4.2–5.x, pytest, pytest-django
- 001-app-components: Added Python 3.11+ / Django 4.2�5.x + django-cotton (>=2.3.1), django-cotton-bs5 (>=0.9.0), django-flex-menus (>=0.4.1), django-easy-icons (>=0.5), AdminLTE 4 (rc3, bundled locally), Bootstrap 5
- 009-form-view-mixin: Added Python 3.11+ with Django 4.2+ + Django, django-cotton, django-crispy-forms (optional), django-formset (optional)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
