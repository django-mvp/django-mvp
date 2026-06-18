# Django MVP — Domain Model

## Core Concepts

### Component

A reusable, override-able UI building block implemented as a Cotton template. Components define the **public API** of django-mvp. They are named after their domain role, not their implementation or any external design system.

**Examples:** `c-app`, `c-page`, `c-card`, `c-grid`

### Component Attribute

A configurable property declared via `<c-vars>` that controls a component's appearance or behavior. Attributes are the **only** way to customize components — raw CSS classes must not appear in templates that demonstrate components.

**Valid attributes:** `title`, `icon`, `variant`, `size`, `gap`, `cols` (on `c-grid`)
**Invalid:** `class="flex grid-cols-3"` — use component attributes instead.

### Override

The mechanism by which a consumer replaces a package component with their own implementation. Drop a template at the same path in your project's template directory and it replaces the package version. This is the **primary extension point**.

### Core Component

A component that is part of django-mvp's stable vocabulary. These are the only components consumers should use when building reusable templates. Everything else is an implementation detail.

**Core components:** `c-app`, `c-page`, `c-card`, `c-grid`, `c-section`, `c-button`, `c-avatar`

### Mixin

A Python class that provides cross-cutting behavior for Django views. Consumers compose their own view from exported mixins rather than using factory functions or pre-built concrete classes. This follows Django's standard pattern.

**Exported mixins:** `PageMixin`, `BaseTemplateNameMixin`, `SearchMixin`, `OrderMixin`, `CRUDDirectoryMixin`
**Concrete views:** `MVPListView`, `MVPCreateView`, `MVPDetailView`, `MVPUpdateView`, `MVPDeleteView`

### Config

A single merged dictionary, built at module import time by deep-merging package defaults with user overrides from ``settings.MVP_CONFIG``. Consumers import it directly::

    from mvp.config import MVP_CONFIG

**Structure:**

```python
# settings.py — optional overrides
MVP_CONFIG = {
    "view_names": {"list": "{model_name}_list"},
}
```

## Terminology

### Cotton Component vs. DaisyUI Component

Django MVP's components are **not** DaisyUI components. They borrow DaisyUI classes as an implementation detail today, but their names and API are independent of any external design system. The component vocabulary belongs to django-mvp.

### Layout vs. Page

- **Layout** (`c-app`): The outermost wrapper that defines the application chrome (sidebar, header, footer). One per page.
- **Page** (`c-page`): The content container within a layout. Defines the page structure (header, body, footer sections).

### View vs. Template

- **View**: A Python class (usually a Django CBV composed from mixins) that handles request/response logic.
- **Template**: A Cotton component or HTML template that renders the visual output. Views and templates are separate concerns.

## Constraints

1. Demo templates must never use raw Tailwind classes — only Cotton component attributes.
2. Components must not declare ghost attributes (declared in `<c-vars>` but never used).
3. Mixin composition is the extension path — no factory functions, no pre-built concrete views for consumers.
4. Config uses deep merge — consumers override individual keys, not the entire dict.
