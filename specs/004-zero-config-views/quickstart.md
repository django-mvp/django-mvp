# Quickstart: Zero-Config Ready-to-Use Views

**Branch**: `004-zero-config-views` | **Date**: 2026-05-02
**Estimated setup time**: under 5 minutes per view

This guide shows how to wire `PageView` and `HomeView` — the two zero-config views shipped by django-mvp. Neither view requires a model, form, or queryset. You only need to point a URL at the view and create a template.

---

## Prerequisites

- `mvp` app in `INSTALLED_APPS`
- `django.contrib.auth.context_processors.auth` in `TEMPLATES[...]["OPTIONS"]["context_processors"]` (Django default)
- The standard `mvp` layout configured (base template, Cotton components, static files)

---

## 1. PageView — Plain Layout-Aware Template

Use `PageView` for any informational page (About, FAQ, Terms, etc.) that should render inside the standard application layout.

### Step 1: Wire the URL

```python
# myapp/urls.py
from mvp.views import PageView

urlpatterns = [
    path("about/", PageView.as_view(
        template_name="myapp/about.html",
        page_title="About",
    ), name="about"),
]
```

### Step 2: Create the template

```html
{# myapp/templates/myapp/about.html #}
{% extends "page_view.html" %}

{% block page.content %}
  <p>Welcome to our about page.</p>
{% endblock page.content %}
```

That's it. Visit `/about/` — the page renders inside the full layout with a title in the header.

### Customising layout metadata

Set layout attributes directly on the URL entry or in a subclass:

```python
# Via as_view() — for one-off pages
path("about/", PageView.as_view(
    template_name="myapp/about.html",
    page_title="About Us",
    page_subtitle="Who we are",
    page_icon="person-circle",  # must be a name registered in EASY_ICONS
    breadcrumbs=[{"text": "Home", "href": "/"}, {"text": "About"}],
), name="about"),
```

```python
# Via subclass — for pages with dynamic values
from mvp.views import PageView

class AboutView(PageView):
    template_name = "myapp/about.html"
    page_title = "About Us"
    page_subtitle = "Who we are"
    page_icon = "person-circle"  # must be a name registered in EASY_ICONS
    breadcrumbs = [{"text": "Home", "href": "/"}, {"text": "About"}]
```

### Available context in the template

| Variable | Value |
|----------|-------|
| `{{ page.title }}` | Configured `page_title` |
| `{{ page.subtitle }}` | Configured `page_subtitle` |
| `{{ page.icon }}` | Configured `page_icon` or `None` |
| `{{ page.class }}` | `"mvp-page"` + any `page_class` |
| `{{ page.breadcrumbs }}` | List of breadcrumb dicts |
| `{{ request.user }}` | Current user (anonymous or authenticated) |

---

## 2. HomeView — Landing Page for Guests, Dashboard for Users

Use `HomeView` at your root URL (`/`) to serve a marketing landing page to anonymous visitors and an application dashboard to logged-in users — same URL, same view class, no redirect.

### Step 1: Wire the URL

```python
# myproject/urls.py (or myapp/urls.py)
from mvp.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(
        landing_template_name="myapp/landing.html",
        dashboard_template_name="myapp/dashboard.html",
    ), name="home"),
]
```

### Step 2: Create the landing template

```html
{# myapp/templates/myapp/landing.html #}
{% extends "mvp/landing.html" %}

{% block page.content %}
  <div class="container py-5">
    <h1>{{ hero_content.title }}</h1>
    <p class="lead">{{ hero_content.lead }}</p>
    <a href="{% url 'login' %}" class="btn btn-primary">Get Started</a>
  </div>
{% endblock page.content %}
```

### Step 3: Create the dashboard template

```html
{# myapp/templates/myapp/dashboard.html #}
{% extends "mvp/dashboard.html" %}

{% block page.content %}
  <div class="container py-4">
    <h2>Welcome back, {{ request.user.get_full_name|default:request.user.username }}!</h2>
    <p>Your dashboard is ready.</p>
  </div>
{% endblock page.content %}
```

### Step 4: Verify

1. Visit `/` without logging in → landing page is shown.
2. Log in → visit `/` again → dashboard is shown. URL stays at `/`.

### Using the bundled default templates

`HomeView` ships with built-in templates that work out of the box without any project-level template files. To use them, wire the URL without specifying templates:

```python
path("", HomeView.as_view(), name="home")  # uses mvp/landing.html and mvp/dashboard.html
```

The bundled `mvp/landing.html` uses `hero_content` from the `MVP_LANDING_PAGE_HERO` Django setting. Customise it in `settings.py`:

```python
MVP_LANDING_PAGE_HERO = {
    "title": "My App",
    "subtitle": "Built with django-mvp",
    "lead": "The fastest way to build your next Django application.",
    "image": "myapp/hero.png",  # path relative to STATIC_ROOT
}
```

### Subclassing HomeView

For dashboard-specific logic (e.g., fetching recent activity), override `get_dashboard_context()`:

```python
from mvp.views import HomeView

class AppHomeView(HomeView):
    landing_template_name = "myapp/landing.html"
    dashboard_template_name = "myapp/dashboard.html"

    def get_dashboard_context(self, context):
        context = super().get_dashboard_context(context)
        context["recent_items"] = []  # replace with actual queryset
        return context
```

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `ImproperlyConfigured: PageView requires template_name to be set` | `template_name` not provided | Set `template_name` as class attribute or `as_view()` kwarg |
| `ImproperlyConfigured: HomeView requires landing_template_name to be set` | `landing_template_name` is `None` | Set `landing_template_name` |
| `ImproperlyConfigured: HomeView requires dashboard_template_name to be set for authenticated users` | `dashboard_template_name` is `None` and user is logged in | Set `dashboard_template_name` |
| `TemplateDoesNotExist: myapp/about.html` | Template file not found | Create the template file in a `templates/` directory on `DIRS` or in an installed app |

---

## Summary

| View | Import | Required attributes | Optional attributes |
|------|--------|--------------------|--------------------|
| `PageView` | `from mvp.views import PageView` | `template_name` | `page_title`, `page_subtitle`, `page_icon`, `page_class`, `breadcrumbs` |
| `HomeView` | `from mvp.views import HomeView` | *(none — defaults to bundled templates)* | `landing_template_name`, `dashboard_template_name`, all `page_*` attributes |
