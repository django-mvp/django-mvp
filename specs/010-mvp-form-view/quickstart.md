# Quickstart: MVPFormView — Non-Model Form View

**Branch**: `010-mvp-form-view`
**Date**: 2026-05-04

## What Was Built

Two method additions to the existing `MVPFormView` stub in `mvp/views/edit.py`:

1. `get_success_message(cleaned_data)` — safe `%(field)s` substitution without model dependency
2. `get_page_title()` — class-name fallback title using `camel_case_to_spaces()`

## Minimum Working Example

```python
# myapp/views.py
from myapp.forms import ContactForm
from mvp.views import MVPFormView

class ContactView(MVPFormView):
    form_class = ContactForm
    success_url = "/contact/thanks/"
    success_message = "Thanks, %(email)s! We'll be in touch."
    page_title = "Contact Us"
    page_subtitle = "Send us a message"
```

```python
# myapp/urls.py
from django.urls import path
from .views import ContactView

urlpatterns = [
    path("contact/", ContactView.as_view(), name="contact"),
]
```

That's it. No template required — the shared `form_view.html` layout is used automatically.

## What You Get for Free

| Feature | How |
|---------|-----|
| AdminLTE card layout | `MVPFormBase.base_template_name = "form_view.html"` |
| Standard form validation | `generic.FormView` lifecycle |
| Redirect after success | `success_url` or `?next=` parameter |
| Success message | `SuccessMessageMixin` + `get_success_message()` |
| Default page title | `"Contact View"` derived from `ContactView` class name |
| Page title / subtitle | `page_title`, `page_subtitle` attributes |
| Breadcrumbs | `breadcrumbs` list attribute |
| Open-redirect protection | `NextURLMixin.get_next_url()` |

## Advanced Usage

### Custom breadcrumbs

```python
class SettingsView(MVPFormView):
    form_class = SettingsForm
    success_url = "/settings/"
    page_title = "Account Settings"
    breadcrumbs = [
        {"text": "Dashboard", "href": "/"},
        {"text": "Account Settings"},
    ]
```

### Restrict to authenticated users

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class PrivateFormView(LoginRequiredMixin, MVPFormView):
    form_class = MyForm
    success_url = "/done/"
```

### Override redirect after success

```python
class SearchView(MVPFormView):
    form_class = SearchForm

    def form_valid(self, form):
        q = form.cleaned_data["query"]
        return redirect(f"/results/?q={q}")
```

## Distinctions from Model Form Views

| Concern | `MVPFormView` | `MVPCreateView` / `MVPUpdateView` |
|---------|--------------|-----------------------------------|
| `model` required | No | Yes |
| `%(verbose_name)s` in message | Renders as `""` (not injected) | Replaced with model verbose name |
| CRUD shorthand (`?next=list`) | Not supported | Supported via `resolve_crud_url()` |
| Default title source | Class name split | `page_title` class attribute |
| Fallback redirect | `success_url` or `ImproperlyConfigured` | `object.get_absolute_url()` |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ImproperlyConfigured: ... must define 'success_url'` | No `success_url` and no `?next=` | Add `success_url = "/path/"` to the class |
| `ImproperlyConfigured: ... get_form() called without form_class` | No `form_class` | Add `form_class = MyForm` |
