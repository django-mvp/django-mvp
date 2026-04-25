---
name: django-cotton
description: Expert guide for working with Django Cotton, a component-based UI composition library. Use when creating, modifying, or testing Cotton components — covers component syntax, slots (default and named), attributes, c-vars, dynamic attributes with Python types, attribute proxying, template organization, naming conventions, and integration patterns. Essential for building reusable UI components in Django templates.
license: Complete terms in LICENSE.txt
---

# Django Cotton

Guide for working with Django Cotton, a component-based UI composition library for Django templates.

## When to Use This Skill

- Creating new Cotton components
- Modifying existing Cotton components
- Working with slots (default and named)
- Passing attributes and data to components
- Testing Cotton components
- Organizing component directory structure
- Integrating Cotton with Django forms, HTMX, or Alpine.js

## Core Concepts

### Component Syntax

Cotton uses an intuitive HTML-like syntax:

```html
<c-button>Click me</c-button>
<c-input name="email" />
<c-card.header>Title</c-card.header>
```

This syntax provides excellent IDE support including autocompletion, syntax highlighting, and auto-closing tags.

**🚨 CRITICAL: NEVER add `{% load cotton %}` to templates**

Cotton is auto-loaded via Django's `builtins` configuration. Adding `{% load cotton %}` is:

- Completely unnecessary
- Redundant
- Shows misunderstanding of the package

**Just use `<c-component>` tags directly. No loading required.**

### Component Naming Convention

**🚨 CRITICAL FILE NAMING:**

**Before creating component files, ALWAYS check the project's `COTTON_SNAKE_CASED_NAMES` setting:**

- If `COTTON_SNAKE_CASED_NAMES = True` (default): Use snake_case filenames → `my_component.html`
- If `COTTON_SNAKE_CASED_NAMES = False`: Use kebab-case filenames → `my-component.html`
- If setting not found: Default to snake_case filenames

**🚨 CRITICAL TEMPLATE USAGE:**

**ALWAYS use kebab-case in templates, regardless of filename format:**

- ✅ Correct: `<c-small-box />`, `<c-info-box />`, `<c-timeline-item />`
- ❌ Wrong: `<c-small_box />`, `<c-smallBox />`, `<c-SmallBox />`

**Example:**

```
Filename: small_box.html (snake_case)
Template: <c-small-box />  (kebab-case)
```

Kebab-case in templates looks clean and professional. Snake_case in templates looks terrible.

### Directory Structure

Components live in `templates/cotton/`:

```
templates/
├── cotton/              # Default component directory (configurable via COTTON_DIR)
│   ├── button.html     # <c-button />
│   ├── card.html       # <c-card />
│   └── card/
│       ├── index.html  # <c-card /> (default)
│       ├── header.html # <c-card.header />
│       └── body.html   # <c-card.body />
```

**Subfolders:** Use dot notation: `<c-sidebar.menu.link />` for `sidebar/menu/link.html`

**Index files:** `index.html` in a folder serves as the default component for that folder.

## Slots

### Default Slot

The `{{ slot }}` variable captures content between component tags:

```html
<!-- cotton/button.html -->
<a href="{{ url }}" class="btn">{{ slot }}</a>
```

```html
<!-- Usage -->
<c-button url="/home">Click me</c-button>
```

```html
<!-- Output -->
<a href="/home" class="btn">Click me</a>
```

### Named Slots

Named slots allow targeted content injection:

```html
<!-- cotton/card.html -->
<div class="card">
    <div class="card-header">{{ header }}</div>
    <div class="card-body">{{ slot }}</div>
    {% if footer %}
        <div class="card-footer">{{ footer }}</div>
    {% endif %}
</div>
```

```html
<!-- Usage -->
<c-card>
    <c-slot name="header">
        <h3>Card Title</h3>
    </c-slot>

    Main content here

    <c-slot name="footer">
        <button>Close</button>
    </c-slot>
</c-card>
```

**Slots can contain template expressions:**

```html
<c-slot name="icon">
    {% if mode == 'edit' %}
        <svg id="pencil">...</svg>
    {% else %}
        <svg id="disk">...</svg>
    {% endif %}
</c-slot>
```

## Attributes

### Basic Attributes

Pass attributes directly to components:

```html
<c-button url="/contact" theme="primary">Contact</c-button>
```

```html
<!-- cotton/button.html -->
<a href="{{ url }}" class="btn-{{ theme }}">{{ slot }}</a>
```

### The {{ attrs }} Variable

Use `{{ attrs }}` to spread all passed attributes as HTML attributes:

```html
<!-- cotton/input.html -->
<input type="text" class="form-control" {{ attrs }} />
```

```html
<!-- Usage -->
<c-input placeholder="Enter name" name="user_name" required />
```

```html
<!-- Output -->
<input type="text" class="form-control" placeholder="Enter name" name="user_name" required />
```

### <c-vars> Tag

Use `<c-vars>` to:

1. Define default attribute values
2. Declare component-internal variables (excluded from `{{ attrs }}`)

```html
<!-- cotton/button.html -->
<c-vars theme="primary" size="md" />

<a href="{{ url }}" class="btn btn-{{ theme }} btn-{{ size }}">
    {{ slot }}
</a>
```

```html
<!-- Usage -->
<c-button url="/home">Default button</c-button>
<c-button url="/save" theme="success">Save button</c-button>
```

**Preventing attributes from rendering as HTML:**

```html
<!-- cotton/input.html -->
<c-vars icon />  <!-- 'icon' won't appear in {{ attrs }} -->

{% if icon %}
    <img src="icons/{{ icon }}.png" />
{% endif %}

<input {{ attrs }} />
```

```html
<!-- Usage -->
<c-input type="password" id="pass" icon="padlock" />
```

```html
<!-- Output (note: 'icon' attribute is not in the <input>) -->
<img src="icons/padlock.png" />
<input type="password" id="pass" />
```

## Dynamic Attributes

### Passing Python Types

**Quoteless syntax** (simple values):

```html
<c-button enabled=True />
<c-input value=my_variable />
<c-counter start=42 />
```

**Colon prefix** (complex expressions with spaces/quotes):

```html
<c-select :options="['yes', 'no', 'maybe']" />
<c-card :config="{'open': True, 'theme': 'dark'}" />
<c-bio-card :user="user" />
```

**Template expressions in attributes:**

```html
<c-weather icon="fa-{{ icon }}"
           unit="{{ unit|default:'c' }}"
           condition="very {% get_intensity %}" />
```

### Attribute Proxying

Pass attributes from parent to child components using `:attrs`:

```html
<!-- cotton/outer_wrapper.html -->
<c-vars message />  <!-- Internal to outer_wrapper -->
<p>Message: {{ message }}</p>
<c-inner-component :attrs="attrs">{{ slot }}</c-inner-component>
```

```html
<!-- cotton/inner_component.html -->
<div class="inner {{ class }}">{{ slot }}</div>
```

```html
<!-- Usage -->
<c-outer-wrapper message="Hello" class="special">Content</c-outer-wrapper>
```

```html
<!-- Output -->
<p>Message: Hello</p>
<div class="inner special">Content</div>
```

**Pattern:** Use this to build higher-order components (e.g., form fields with labels and error handling).

## Dynamic Component Rendering

Render components dynamically based on variable names:

```html
<!-- Dynamic component name -->
<c-component :is="component_name" />
<c-component is="{{ component_name }}" />

<!-- With subfolder -->
<c-component is="form-fields.{{ field_type }}" />
```

```html
<!-- Example: Rendering form fields dynamically -->
{% for field in form_fields %}
    <c-component :is="field.type" :attrs="field.attrs" />
{% endfor %}
```

## Configuration

### Django Settings

```python
INSTALLED_APPS = [
    # Automatic configuration (recommended)
    'django_cotton',

    # OR manual configuration for custom loaders
    'django_cotton.apps.SimpleAppConfig',
]

# Optional settings
COTTON_DIR = 'cotton'           # Default component directory
COTTON_BASE_DIR = None          # Base dir for template search (defaults to BASE_DIR)
COTTON_SNAKE_CASED_NAMES = True # Use snake_case filenames (False = kebab-case)
```

### Manual Template Configuration

For custom loaders (e.g., with django-template-partials):

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django_cotton.cotton_loader.Loader',
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'builtins': [
                'django_cotton.templatetags.cotton',
            ],
        },
    },
]
```

## Discovering Available Components

**🚨 CRITICAL: Always discover available components before assuming they exist**

Users may have Cotton components from:

- Project-level `templates/cotton/` directory
- Third-party packages (e.g., `django-cotton-bs5`, `django-mvp`)
- App-level component directories

### Using the Discovery Script

This skill provides a script to discover all available components. Use it to get a complete list:

```bash
# From project root
poetry run python manage.py shell < .github/skills/django-cotton/scripts/discover_components.py
```

The script will:

1. Check the `COTTON_DIR` setting (defaults to `'cotton'`)
2. Use Django's template engine to find all template directories
3. Discover all `.html` files in the cotton directory
4. Convert filenames to component names (kebab-case)
5. Group components by namespace for easy viewing

Output example:

```
============================================================
Found 42 Cotton components:
============================================================

(root):
  <c-card />
  <c-button />

forms:
  <c-form.django />
  <c-form.bootstrap />

adminlte:
  <c-adminlte.small-box />
  <c-adminlte.info-box />
============================================================
```

### When to Use Component Discovery

- When user asks "what components are available?"
- Before suggesting a component, verify it exists
- When working with third-party packages (django-cotton-bs5, django-mvp, etc.)
- When debugging "component not found" errors
- When exploring a new project

## Integration Patterns

### With HTMX

Cotton components work seamlessly with HTMX for partial HTML responses:

```html
<!-- cotton/todo_item.html -->
<c-vars item />
<div class="todo-item" hx-delete="/todos/{{ item.id }}/" hx-target="this" hx-swap="outerHTML">
    <input type="checkbox" {% if item.done %}checked{% endif %} />
    <span>{{ item.text }}</span>
</div>
```

### With Alpine.js

Components can contain Alpine.js directives:

```html
<!-- cotton/dropdown.html -->
<div x-data="{ open: false }">
    <button @click="open = !open">{{ label }}</button>
    <div x-show="open" @click.away="open = false">
        {{ slot }}
    </div>
</div>
```

### With Django Forms

Wrap form widgets in Cotton components:

```html
<!-- cotton/form_field.html -->
<c-vars field label help_text />

<div class="form-group">
    {% if label %}
        <label for="{{ field.id_for_label }}">{{ label }}</label>
    {% endif %}

    {{ field }}

    {% if field.errors %}
        <div class="errors">{{ field.errors }}</div>
    {% endif %}

    {% if help_text %}
        <small class="help">{{ help_text }}</small>
    {% endif %}
</div>
```

```html
<!-- Usage -->
<c-form-field :field="form.email" label="Email Address" />
```

## Best Practices

### Component Organization

1. **Keep components focused** — One responsibility per component
2. **Use subfolders** for related components (`card/index.html`, `card/header.html`)
3. **Leverage index.html** for default folder components
4. **Name descriptively** — `todo_item.html`, not `item.html`

### Attribute Design

1. **Use `<c-vars>` for defaults** — Provide sensible defaults, allow overrides
2. **Use `{{ attrs }}`** for flexibility — Let users pass arbitrary HTML attributes
3. **Keep internal state in `<c-vars>`** — Don't leak implementation details to `{{ attrs }}`
4. **Document expected attributes** — Comment at top of component file

### Slot Design

1. **Always provide `{{ slot }}`** for main content
2. **Use named slots for structured content** (headers, footers, actions)
3. **Make optional slots truly optional** — Use `{% if slot_name %}` checks
4. **Default to semantic HTML** — Slots should enhance structure, not replace it

### Testing

Use pytest fixtures from `django-cotton-bs5` (or create similar fixtures):

```python
def test_button_renders(cotton_render):
    """Test basic button component rendering"""
    html = cotton_render('button', {'url': '/home', 'slot': 'Click me'})
    assert 'href="/home"' in html
    assert 'Click me' in html

def test_card_with_slots(cotton_render_soup):
    """Test card with named slots"""
    soup = cotton_render_soup('card', {
        'slot': 'Main content',
        'header': '<h2>Title</h2>',
        'footer': '<button>Close</button>'
    })

    assert soup.select_one('.card-header h2').text == 'Title'
    assert soup.select_one('.card-body').text.strip() == 'Main content'
    assert soup.select_one('.card-footer button').text == 'Close'

def test_component_attrs(cotton_render_soup):
    """Test attribute spreading"""
    soup = cotton_render_soup('input', {
        'attrs': {'name': 'email', 'placeholder': 'Enter email', 'required': True}
    })

    input_tag = soup.find('input')
    assert input_tag['name'] == 'email'
    assert input_tag['placeholder'] == 'Enter email'
    assert input_tag.has_attr('required')
```

### Common Patterns

**Wrapper components:**

```html
<!-- cotton/panel.html -->
<c-vars title variant="default" />
<div class="panel panel-{{ variant }}">
    {% if title %}
        <div class="panel-header">{{ title }}</div>
    {% endif %}
    <div class="panel-body">{{ slot }}</div>
</div>
```

**Icon components:**

```html
<!-- cotton/icon.html -->
<c-vars name size="md" />
<i class="icon icon-{{ name }} icon-{{ size }}"></i>
```

**List components:**

```html
<!-- cotton/list.html -->
<c-vars items />
<ul>
    {% for item in items %}
        <li>{{ item }}</li>
    {% endfor %}
</ul>
```

## Common Pitfalls

1. **Using camelCase/PascalCase** — Always use snake_case or kebab-case
2. **Using `|default` filter for defaults** — Use `<c-vars>` with default values instead
3. **Not using `<c-vars>`** for internal attributes — Results in unwanted HTML attributes
4. **Overcomplicating components** — Keep them simple and composable
5. **Not checking optional slots** — Always wrap optional slots in `{% if slot_name %}`

## Troubleshooting

**Component not found:**

- Check filename matches usage: `<c-my-button />` → `my_button.html`
- Verify component is in `templates/cotton/` (or your `COTTON_DIR`)
- Check `COTTON_SNAKE_CASED_NAMES` setting matches your naming convention

**Attributes not rendering:**

- Ensure you're using `{{ attrs }}` in the component
- Check if attribute is declared in `<c-vars>` (which excludes it from `{{ attrs }}`)

**Slot content not appearing:**

- Verify `{{ slot }}` or `{{ slot_name }}` is in the component template
- For named slots, check spelling matches: `<c-slot name="header">` → `{{ header }}`
