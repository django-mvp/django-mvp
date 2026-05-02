# Public API Contract: Zero-Config Views

**Branch**: `004-zero-config-views` | **Date**: 2026-05-02
**Type**: Python class API (reusable Django package)

This document defines the public interface contract for the two zero-config views shipped by django-mvp. Implementors are bound by these contracts; consumers can rely on them across minor releases.

---

## Contract 1: PageView (MVPTemplateView)

### Import

```python
from mvp.views import PageView        # preferred public alias
from mvp.views import MVPTemplateView  # internal name, also exported
```

### Class Signature

```python
class PageView(TemplateView):
    template_name: str           # required — no default
    page_title: str = ""
    page_subtitle: str = ""
    page_icon: str | None = None
    page_class: str = ""
    breadcrumbs: list[dict] = []
```

### URL Wiring

```python
path("about/", PageView.as_view(template_name="myapp/about.html", page_title="About"))
```

### Template Context Contract

Any template rendered by `PageView` **MUST** receive:

| Variable | Type | Guarantee |
|----------|------|-----------|
| `page.title` | `str` | Always present; defaults to `""` |
| `page.subtitle` | `str` | Always present; defaults to `""` |
| `page.icon` | `str \| None` | Always present; defaults to `None` |
| `page.class` | `str` | Always present; always starts with `"mvp-page"` |
| `page.breadcrumbs` | `list[dict]` | Always present; defaults to `[]` |
| `request` | `HttpRequest` | Via Django's `RequestContext` |
| `request.user` | `User \| AnonymousUser` | Via `django.contrib.auth.context_processors.auth` |

### Behaviour Contract

| Scenario | Guaranteed Outcome |
|----------|-------------------|
| `template_name` set, template exists | `200 OK`, template rendered inside layout |
| `template_name` not set | Django raises `ImproperlyConfigured` |
| `template_name` set, template file missing | Django raises `TemplateDoesNotExist` |
| GET request | `200 OK` |
| POST / PUT / PATCH / DELETE request | `405 Method Not Allowed` |
| Anonymous request | `200 OK` (no login required) |
| Authenticated request | `200 OK` (no special handling) |

### Extension Contract

Developers MAY subclass `PageView` and:

- Override any `get_page_*()` method for dynamic values.
- Override `get_context_data()` to inject additional context (MUST call `super()`).
- Set `template_name`, `page_title`, etc. as class attributes.

Subclasses MUST NOT:

- Override `get()` in a way that bypasses template rendering.
- Remove the `page` context key.

---

## Contract 2: HomeView (MVPHomeView)

### Import

```python
from mvp.views import HomeView        # preferred public alias
from mvp.views import MVPHomeView      # internal name, also exported
```

### Class Signature

```python
class HomeView(MVPTemplateView):
    landing_template_name: str = "mvp/landing.html"
    dashboard_template_name: str = "mvp/dashboard.html"
    page_title: str = _("Home")
```

### URL Wiring

```python
path("", HomeView.as_view(), name="home")  # uses bundled defaults

# Or with project-specific templates:
path("", HomeView.as_view(
    landing_template_name="myapp/landing.html",
    dashboard_template_name="myapp/dashboard.html",
), name="home")
```

### Template Selection Contract

| Request State | Template Used | Condition |
|--------------|--------------|-----------|
| Anonymous user | `landing_template_name` | `request.user.is_authenticated is False` |
| Authenticated user | `dashboard_template_name` | `request.user.is_authenticated is True` |

**No redirect is issued under any condition.** The response is always `200 OK` for GET requests.

### Template Context Contract

**For anonymous requests** (landing template):

| Variable | Type | Guarantee |
|----------|------|-----------|
| `page` | `dict` | As per PageView contract above |
| `hero_content` | `dict` | Always present for anonymous requests; sourced from `MVP_LANDING_PAGE_HERO` Django setting |
| `hero_content.title` | `str` | Always present |
| `hero_content.subtitle` | `str` | Always present |
| `hero_content.lead` | `str` | Always present |
| `hero_content.image` | `str` | Always present (static file path) |
| `request.user` | `AnonymousUser` | Via auth context processor |

**For authenticated requests** (dashboard template):

| Variable | Type | Guarantee |
|----------|------|-----------|
| `page` | `dict` | As per PageView contract above |
| `request.user` | `User` | Via auth context processor |

### Error Contract

| Scenario | Raised Exception |
|----------|-----------------|
| `landing_template_name` is `None` and any request arrives | `django.core.exceptions.ImproperlyConfigured` with message containing class name and `landing_template_name` |
| `dashboard_template_name` is `None` and authenticated request arrives | `django.core.exceptions.ImproperlyConfigured` with message containing class name and `dashboard_template_name` |
| `landing_template_name` set but template file missing | `django.template.exceptions.TemplateDoesNotExist` |
| `dashboard_template_name` set but template file missing | `django.template.exceptions.TemplateDoesNotExist` |

**The landing template MUST NEVER be served to an authenticated user** under any fallback path. If `dashboard_template_name` is `None`, `ImproperlyConfigured` is raised rather than silently falling back.

### HTTP Method Contract

| Method | Response |
|--------|---------|
| GET | `200 OK` with rendered template |
| HEAD | `200 OK` with empty body |
| POST / PUT / PATCH / DELETE | `405 Method Not Allowed` |

### Extension Contract

Developers MAY subclass `HomeView` and:

- Override `landing_template_name` and/or `dashboard_template_name` as class attributes.
- Override `get_landing_context(context)` to add extra context for anonymous users (MUST call `super()` and return the modified `context` dict).
- Override `get_dashboard_context(context)` to add extra context for authenticated users (MUST call `super()` and return the modified `context` dict).
- Override `get_template_names()` for custom template selection logic (MUST preserve the anonymous/authenticated distinction).

Subclasses MUST NOT:

- Return a redirect response from `get()` based on authentication state.
- Make database queries in the default implementation (overrides may add queries, but the base class guarantees zero queries).

---

## Contract 3: Bundled Templates

### mvp/landing.html

**Purpose**: Default landing page. Provides a working starting point; replace or extend via Django's template override mechanism.

**Extends**: `page_view.html`

**Blocks exposed for override**:

| Block | Description |
|-------|-------------|
| `page.content` | Primary content area; contains default hero section. Override to replace content entirely. |

**Required context**: `hero_content` dict (injected by `MVPHomeView.get_landing_context()`).

### mvp/dashboard.html

**Purpose**: Default authenticated dashboard. Provides a working starting point.

**Extends**: `page_view.html`

**Blocks exposed for override**:

| Block | Description |
|-------|-------------|
| `page.content` | Primary content area; contains default user greeting. Override to add dashboard widgets. |

**Required context**: `request.user` (injected by auth context processor — no custom injection needed).

---

## Stability Guarantee

Both `PageView` and `HomeView` are **stable public API** from this release. The following are breaking changes that MUST be versioned:

- Removing or renaming `landing_template_name` or `dashboard_template_name` attributes.
- Changing the `page` context key structure.
- Changing when `ImproperlyConfigured` is raised (tightening is breaking; relaxing is not).
- Changing the HTTP method behaviour (currently GET/HEAD only; adding POST would be breaking for security posture).
- Removing `get_landing_context()` or `get_dashboard_context()` extension hooks.
