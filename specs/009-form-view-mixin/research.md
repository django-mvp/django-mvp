# Research: MVPFormViewMixin

## R1: Django Form Rendering Libraries — Detection and Usage

### Decision

Use `app_is_installed()` (wrapping `django.apps.apps.is_installed()`) for runtime detection of installed form rendering libraries. Auto-detection priority: crispy-forms → django-formset → standard Django.

### Rationale

- `app_is_installed()` already exists in `mvp/utils.py` and is the established pattern in this project
- Checking at class init / `get_context_data()` time is more reliable than import-time checks
- Priority order matches popularity and maturity: crispy-forms has broader adoption

### Alternatives Considered

- **Import-based detection** (`try: import crispy_forms`): Rejected — less reliable, doesn't account for app not being in `INSTALLED_APPS`
- **Settings-based flag**: Rejected — adds configuration burden; auto-detection is more ergonomic
- **Single library mandate**: Rejected — contradicts the spec requirement for flexibility

---

## R2: django-crispy-forms Rendering Pattern

### Decision

Use `{% load crispy_forms_tags %}{% crispy form %}` as the template tag for crispy-forms rendering.

### Rationale

- `{% crispy form %}` renders the complete form including `<form>` tag, CSRF, and submit button
- The `|crispy` filter only renders fields without the `<form>` wrapper
- Since the template wraps in a card layout, using `{% crispy form %}` inside the card body provides the most complete rendering
- App name for detection: `"crispy_forms"` (the Django app label)

### Key API Details (from Context7)

```python
# Template usage
{% load crispy_forms_tags %}
{% crispy form %}           # Full form with <form> tag
{{ form|crispy }}           # Fields only, no <form> tag

# Python helper (optional, for layout customization)
from crispy_forms.helper import FormHelper
helper = FormHelper()
helper.form_method = 'post'
```

### Alternatives Considered

- `{{ form|crispy }}` filter: Considered but provides less control — no `<form>` tag wrapper
- Custom `FormHelper`: Out of scope for MVP — users can add their own helpers to form classes

---

## R3: django-formset Rendering Pattern

### Decision

Use `{% load formsetify %}{% render_form form "bootstrap" %}` for django-formset rendering.

### Rationale

- `{% render_form %}` is the primary rendering tag in django-formset
- The `"bootstrap"` renderer provides Bootstrap 5 compatible output
- App name for detection: `"formset"` (the Django app label)

### Key API Details (from Context7)

```python
# Template usage
{% load formsetify %}
{% render_form form "bootstrap" %}   # Renders with Bootstrap styling

# Alternative renderers available: "default", "bootstrap", "bulma", "foundation", "tailwind"
```

### Alternatives Considered

- Other renderer strings (`"tailwind"`, `"bulma"`): Not relevant — AdminLTE uses Bootstrap 5
- Hardcoding renderer: Could be made configurable via mixin attribute, but "bootstrap" is correct default for AdminLTE

---

## R4: Django Generic CBV Form Patterns

### Decision

`MVPFormViewMixin` will work with Django's standard `FormView` and `CreateView` (via `ModelFormMixin`). The mixin injects context and provides template defaults without overriding form processing.

### Rationale

- Django's CBV hierarchy: `FormView` → `ProcessFormView` → handles `form_valid()` / `form_invalid()`
- `CreateView` → `ModelFormMixin` + `ProcessFormView` → handles model save in `form_valid()`
- The mixin should NOT override `form_valid()` or `form_invalid()` — only add rendering context
- This follows the same pattern as `MVPListViewMixin` which adds context without changing core list behavior

### Key CBV Attributes

```python
# FormView (for plain forms)
class MyFormView(FormView):
    template_name = "my_form.html"
    form_class = MyForm
    success_url = "/thanks/"

# CreateView (for model forms)
class MyCreateView(CreateView):
    model = MyModel
    fields = ["name", "email"]
    success_url = "/list/"
```

### Alternatives Considered

- Overriding `form_valid()` for flash messages: Out of scope — can be added by user
- Supporting `UpdateView` directly: Same mixin works since `UpdateView` shares `ModelFormMixin`

---

## R5: Error Display Strategy

### Decision

Both non-field error summary at top AND inline per-field errors. All three renderers must provide this.

### Rationale

- Crispy-forms and django-formset handle inline errors automatically
- For standard Django rendering, we must explicitly render `{{ form.non_field_errors }}` at the top
- This matches modern form UX best practices (summary for screen readers + inline for visual scanning)

### Implementation

```html
<!-- For "django" renderer -->
{% if form.non_field_errors %}
<div class="alert alert-danger">
  {{ form.non_field_errors }}
</div>
{% endif %}
{{ form.as_p }}
```

- For `"crispy"` and `"formset"`: Error display is handled by the library automatically
- Both libraries render inline errors and non-field errors by default

---

## R6: Template Layout Structure

### Decision

Use card component (header/body/footer) wrapped in a page component, matching `list_view.html` pattern.

### Rationale

- AdminLTE 4 uses card-based layouts for content sections
- `c-page` provides page title and breadcrumb support
- Card header for form title, body for the form, footer for submit/cancel actions
- Consistent with `list_view.html` which uses `c-page` + `c-row` pattern

### Layout Skeleton

```html
{% extends "mvp/base.html" %}
<c-page title="{{ page_title }}">
  <c-page.content>
    <c-card title="{{ page_title }}">
      <!-- conditional form rendering based on form_renderer -->
      <c-slot name="footer_end">
        <button type="submit">Save</button>
      </c-slot>
    </c-card>
  </c-page.content>
</c-page>
```

---

## R7: Invalid Renderer Fallback Behavior

### Decision

Log a warning via Python's `logging` module and fall back to `"django"` renderer.

### Rationale

- Silent failure would hide misconfiguration
- Raising an exception would break the page — too harsh for a rendering preference
- Warning + fallback provides visibility without disruption
- Standard Django pattern for non-critical configuration issues

### Implementation

```python
import logging

logger = logging.getLogger(__name__)

def get_form_renderer(self):
    if self.form_renderer and not self._is_renderer_available(self.form_renderer):
        logger.warning(
            "Form renderer '%s' specified but library not installed. "
            "Falling back to 'django' renderer.",
            self.form_renderer,
        )
        return "django"
    # ... auto-detection logic
```
