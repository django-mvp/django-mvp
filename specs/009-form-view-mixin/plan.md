# Implementation Plan: Form View Mixin for Consistent Form Layouts

**Branch**: `009-form-view-mixin` | **Date**: February 6, 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-form-view-mixin/spec.md`

## Summary

Create `MVPFormViewMixin` and three composed view classes (`MVPFormView`, `MVPCreateView`, `MVPUpdateView`) that automatically render Django forms within AdminLTE layouts with intelligent form library detection. The mixin detects and uses django-crispy-forms, django-formset, or standard Django rendering based on installed packages, providing a consistent card-based layout across all form views without requiring developers to build custom templates for each form.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Django 4.2+, django-cotton (AdminLTE components), django-crispy-forms (optional), django-formset (optional)
**Storage**: N/A (form rendering feature, no new models)
**Testing**: pytest + pytest-django (unit/integration), pytest-playwright (E2E)
**Target Platform**: Web server (Django application)
**Project Type**: Django reusable app (single project structure)
**Performance Goals**: Negligible overhead (< 5ms form rendering time increase)
**Constraints**: Must work with or without optional form libraries, graceful degradation required
**Scale/Scope**: 3 view classes (MVPFormView, MVPCreateView, MVPUpdateView) + 1 mixin + 1 template + demo views

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **PASSED** (Phase 0 - Pre-Research):

- ✅ Design-first approach is feasible and planned (implement mixin → implement views → visual verification → write tests)
- ✅ Visual verification approach is planned (chrome-devtools-mcp to verify form rendering with each library)
- ✅ Test types are identified (pytest unit tests for mixin logic, pytest-django for view integration, playwright for E2E form submission flows)
- ✅ Documentation updates are included (README examples, quickstart guide, API reference in data-model.md)
- ✅ Quality gates are understood (pytest + ruff check + ruff format + mypy)
- ✅ Documentation retrieval is planned (Context7 for django-crispy-forms, django-formset, Django FormView/CreateView/UpdateView APIs)
- ✅ End-to-end testing is planned (playwright tests for form submission success/failure paths with each renderer)

**Re-evaluation checkpoint**: After Phase 1 (data-model.md, contracts/, quickstart.md generation) - verify no new complexity introduced

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/                              # Main package
├── __init__.py                   # Package init (no changes)
├── views.py                      # NEW: MVPFormViewMixin, MVPFormView, MVPCreateView, MVPUpdateView
├── utils.py                      # EXISTING: app_is_installed() utility (no changes)
└── templates/
    └── mvp/
        └── form_view.html        # NEW: Card-based form template with renderer detection

demo/                          # Demo application
├── forms.py                      # NEW: ContactForm for MVPFormView demo
├── models.py                     # MODIFIED: Add Product model for create/update demos
├── views.py                      # MODIFIED: Add demo views (ContactFormView, ProductCreateView, ProductUpdateView)
├── urls.py                       # MODIFIED: Add routes for form demos
├── menus.py                      # MODIFIED: Add sidebar menu items for form demos
└── templates/
    └── demo/
        ├── contact_success.html  # NEW: Success page for contact form
        ├── product_list.html     # NEW: List view to demonstrate create/update links
        └── product_success.html  # NEW: Success page for product create/update

tests/
├── test_mvp_form_view_mixin.py   # NEW: Unit tests for mixin detection logic
├── test_mvp_form_views.py        # NEW: Integration tests for MVPFormView
├── test_mvp_create_view.py       # NEW: Integration tests for MVPCreateView
├── test_mvp_update_view.py       # NEW: Integration tests for MVPUpdateView
└── test_form_demos_e2e.py        # NEW: Playwright E2E tests for demo views
```

**Structure Decision**: Django reusable app with single-project layout. Core implementation in `mvp/views.py` and `mvp/templates/mvp/form_view.html`. Demonstration code in `demo/` app. Test suite covers unit (mixin logic), integration (view behavior), and E2E (browser-based form submission).

## Complexity Tracking

> **No violations**: All constitution checks passed. No complexity justifications required.

---

## Phase 0: Research & Discovery ✅

**Status**: COMPLETE (see [research.md](./research.md))

### Objectives

- Determine form library detection mechanism
- Identify rendering patterns for crispy-forms and django-formset
- Establish priority order for auto-detection
- Define template structure

### Outcomes

- ✅ Use `app_is_installed()` for runtime detection (established project pattern)
- ✅ Auto-detection priority: crispy-forms → django-formset → standard Django
- ✅ crispy-forms: `{% load crispy_forms_tags %}{% crispy form %}`
- ✅ django-formset: `{% load render_form %}{% render_form form "bootstrap" %}`
- ✅ AdminLTE card layout with header (title), body (fields), footer (buttons)
- ✅ Error display: Summary at top + inline per field for accessibility

---

## Phase 1: Design & Contracts ✅

**Status**: COMPLETE

### Deliverables

- ✅ [data-model.md](./data-model.md) - Class hierarchy: MVPFormViewMixin + 3 composed views
- ✅ [quickstart.md](./quickstart.md) - Usage examples for MVPFormView, MVPCreateView, MVPUpdateView
- ✅ contracts/ - N/A (no API contracts needed for template-based feature)

### Design Decisions from data-model.md

- **MVPFormViewMixin**: Base mixin providing renderer detection and template context
  - Methods: `get_form_renderer()`, `get_mvp_form_context()`
  - Detection: Check `crispy_forms` → `django_formset` → return `"django"`
  - Override: `renderer = "crispy"` class attribute to force specific renderer

- **MVPFormView(MVPFormViewMixin, FormView)**: Plain form views (contact forms, search forms)
- **MVPCreateView(MVPFormViewMixin, CreateView)**: Model creation forms
- **MVPUpdateView(MVPFormViewMixin, UpdateView)**: Model editing forms

### Constitution Re-evaluation (Post-Design)

✅ **PASSED**: Design introduces no additional complexity. Single mixin with three composed views follows Django CBV patterns. Template uses standard Cotton components with conditional rendering blocks.

---

## Phase 2: Implementation

### Phase 2.1: Foundation (Mixin & Template)

**Files**:

- `mvp/views.py` - Create `MVPFormViewMixin` class
- `mvp/templates/mvp/form.html` - Create card-based form template

**Mixin Implementation**:

```python
# mvp/views.py
from mvp import app_is_installed

class MVPFormViewMixin:
    \"\"\"Mixin to render forms in AdminLTE layout with auto-detected renderer.\"\"\"
    template_name = "mvp/form_view.html"
    renderer = None  # Override to force specific renderer ("crispy", "formset", "django")

    def get_form_renderer(self):
        \"\"\"Detect and return form renderer to use.\"\"\"
        if self.renderer:
            # Explicit override - verify it's installed
            if self.renderer == "crispy" and not app_is_installed("crispy_forms"):
                # Log warning, fallback to django
                return "django"
            if self.renderer == "formset" and not app_is_installed("django_formset"):
                # Log warning, fallback to django
                return "django"
            return self.renderer

        # Auto-detection priority
        if app_is_installed("crispy_forms"):
            return "crispy"
        if app_is_installed("django_formset"):
            return "formset"
        return "django"

    def get_mvp_form_context(self):
        \"\"\"Additional context for MVP form template.\"\"\"
        return {
            "form_title": getattr(self, "form_title", "Form"),
            "submit_text": getattr(self, "submit_text", "Submit"),
            "cancel_url": getattr(self, "cancel_url", None),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_renderer"] = self.get_form_renderer()
        context.update(self.get_mvp_form_context())
        return context
```

**Template Structure** (`mvp/templates/mvp/form_view.html`):

```django
{% extends "mvp/base.html" %}
{% load cotton %}

{% block content %}
<c-card>
  <c-slot:header>
    <h3>{{ form_title }}</h3>
  </c-slot:header>

  <c-slot:body>
    {# Non-field errors summary #}
    {% if form.non_field_errors %}
      <div class="alert alert-danger">
        {{ form.non_field_errors }}
      </div>
    {% endif %}

    <form method="post">
      {% csrf_token %}

      {% if form_renderer == "crispy" %}
        {% load crispy_forms_tags %}
        {% crispy form %}
      {% elif form_renderer == "formset" %}
        {% load render_form %}
        {% render_form form "bootstrap" %}
      {% else %}
        {{ form.as_p }}
      {% endif %}
    </form>
  </c-slot:body>

  <c-slot:footer>
    <button type="submit" class="btn btn-primary">{{ submit_text }}</button>
    {% if cancel_url %}
      <a href="{{ cancel_url }}" class="btn btn-secondary">Cancel</a>
    {% endif %}
  </c-slot:footer>
</c-card>
{% endblock %}
```

**Verification**:

- Visual check with chrome-devtools-mcp: Form renders in card with header/body/footer
- Browser console: No JavaScript errors
- Manual toggle renderer: Verify all three rendering paths work

### Phase 2.2: View Classes

**Files**:

- `mvp/views.py` - Add `MVPFormView`, `MVPCreateView`, `MVPUpdateView`

**Implementation**:

```python
# mvp/views.py (continued)
from django.views.generic import FormView, CreateView, UpdateView

class MVPFormView(MVPFormViewMixin, FormView):
    \"\"\"FormView with AdminLTE layout and auto-detected form rendering.\"\"\"
    pass  # Inherits all behavior from mixin + FormView

class MVPCreateView(MVPFormViewMixin, CreateView):
    \"\"\"CreateView with AdminLTE layout and auto-detected form rendering.\"\"\"
    pass  # Inherits all behavior from mixin + CreateView

class MVPUpdateView(MVPFormViewMixin, UpdateView):
    \"\"\"UpdateView with AdminLTE layout and auto-detected form rendering.\"\"\"
    pass  # Inherits all behavior from mixin + UpdateView
```

**Verification**:

- Import check: Verify all three classes importable from `mvp.views`
- Type check: Run `mypy mvp/views.py` (should pass with no errors)

### Phase 2.3: Demonstration Views

**Files**:

- `demo/forms.py` - Create `ContactForm`
- `demo/models.py` - Add `Product` model
- `demo/views.py` - Add demo views
- `demo/urls.py` - Wire up demo routes
- `demo/menus.py` - Add sidebar menu items
- `demo/templates/demo/` - Success page templates, product list

**Demo Views** (see tasks.md for detailed breakdown):

1. **ContactFormView** (MVPFormView) - Plain form with name/email/message fields
2. **ProductCreateView** (MVPCreateView) - Create new Product instances
3. **ProductUpdateView** (MVPUpdateView) - Edit existing Product instances
4. **CrispyContactFormView** (MVPFormView) - Forced crispy renderer
5. **FormsetContactFormView** (MVPFormView) - Forced formset renderer
6. **DjangoContactFormView** (MVPFormView) - Forced django renderer

**Verification**:

- Visual check each demo with chrome-devtools-mcp
- Submit test data, verify success redirects work
- Check database for created/updated Product records

---

## Phase 3: Testing

### Test Coverage Requirements

**Unit Tests** (`tests/test_mvp_form_view_mixin.py`):

- `test_get_form_renderer_auto_crispy` - Detects crispy-forms when installed
- `test_get_form_renderer_auto_formset` - Detects django-formset when installed (crispy not installed)
- `test_get_form_renderer_auto_django` - Falls back to django when no libraries installed
- `test_get_form_renderer_explicit_override` - Respects `renderer` class attribute
- `test_get_form_renderer_invalid_override_fallback` - Falls back when override library not installed
- `test_get_mvp_form_context_defaults` - Provides default form_title/submit_text/cancel_url

**Integration Tests** (3 files):

- `tests/test_mvp_form_views.py` - MVPFormView tests (GET, POST success, POST validation errors)
- `tests/test_mvp_create_view.py` - MVPCreateView tests (GET, POST creates record, validation)
- `tests/test_mvp_update_view.py` - MVPUpdateView tests (GET with pk, POST updates record, validation)

**E2E Tests** (`tests/test_form_demos_e2e.py`):

- Playwright tests for form submission workflows
- Test all three renderers (crispy, formset, django)
- Verify error messages display correctly
- Verify success redirects work

---

## Phase 4: Documentation & Polish

### Documentation Updates

- **README.md**: Add quickstart example for form views
- **API Reference**: Document MVPFormViewMixin, MVPFormView, MVPCreateView, MVPUpdateView
- **Docstrings**: Ensure all classes/methods have docstrings

### Quality Checks

- Run full test suite: `poetry run pytest`
- Run linting: `poetry run ruff check .`
- Run formatting: `poetry run ruff format .`
- Run type checking: `poetry run mypy mvp`
- Coverage check: Ensure >95% coverage for new code

---

## Risk Mitigation

1. **Optional dependencies testing**: Add django-formset and django-crispy-forms as dev dependencies in Phase 1 to enable testing all renderer paths without requiring users to install them
2. **Visual verification early**: Use chrome-devtools-mcp during Phase 2.1 (foundation) to catch layout issues before writing tests
3. **Template complexity**: Keep conditional rendering simple (single if/elif/else block) to reduce maintenance burden
4. **Configuration errors**: Log warnings when `renderer` override specifies uninstalled library, then gracefully degrade to standard Django rendering

---

## Implementation Order

1. ✅ **Phase 0**: Research (COMPLETE)
2. ✅ **Phase 1**: Design & Contracts (COMPLETE)
3. **Phase 2.1**: Foundation (Mixin + Template) - CRITICAL PATH
4. **Phase 2.2**: View Classes - Depends on 2.1
5. **Phase 2.3**: Demos - Depends on 2.2
6. **Phase 3**: Testing - Depends on 2.3 (visual verification complete)
7. **Phase 4**: Documentation & Polish - Depends on 3 (tests passing)

**MVP Delivery**: Phase 2.1 + Phase 2.2 = MVPFormView, MVPCreateView, MVPUpdateView functional
**Full Feature**: All phases complete = Production-ready with demos, tests, and documentation
