# Implementation Plan: Branded HTML email layout

**Branch**: `044-branded-email` · **Spec**: [spec.md](spec.md) · **Research**:
[research.md](research.md) · **Sketch**: [sketch.md](sketch.md)

## Summary

django-mvp ships a base email template, four email pieces and a small template tag library.
Whoever owns an HTML email template, a django-mvp package or a project overriding a third-party
package's template, extends the base template and writes the message. Nothing in this feature
renders or sends email: the package that sends an email today keeps sending it, with its own
subject, plain text and language. The email's colours are read from the project's light and dark
themes, its logo is a PNG rendered from the brand logo, and a staff-only preview page exists
while `DEBUG` is on. The approved sketch's layout, pieces, sample emails and preview page are kept
as Sam saw them. The code behind them is rewritten test-first.

## Technical context

Python 3.12+, Django 5.2–6.1, django-cotton 2.8. New runtime dependencies, each justified in
`research.md` (Article VII): css-inline, tinycss2, coloraide. resvg-py stays optional and is used
only by the new management command, imported inside it the way `mvp_pwa_icons` does. Tests are
pytest with rendered-template assertions, plus one test that sends a third-party-style email
through Django's in-memory backend. No browser test (Article XIV).

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every task writes its tests first. The sketch's Python is reset to origin/main before the first dispatch so those tests start red |
| II Simplicity, III Anti-abstraction | Templates, Cotton components and template tags. No class for sending, no setting |
| IV Integration-first | The first acceptance test is a third-party-style sender, unchanged, whose overridden template extends the base template |
| V Security | Every value reaches the email through Django's template layer. The preview page is absent with `DEBUG` off and staff-only with it on |
| VI, XVII Documentation | `docs/email.md` is written in the task that introduces each name, and listed in the docs index |
| VII Dependencies | Three runtime additions, each with its reason in `research.md`. `deptry` stays green |
| VIII Internationalization | Every string in the layout, pieces and preview page is translatable. The language is the sender's |
| X Cohesion | `EmailBrand` holds the colours and logos. The template tags are thin readers of it |
| XI Components are the public API | The pieces are Cotton components, `c-mvp.email.text`, `.button`, `.note`, `.divider`, `.code` |
| XIII Rendered markup is a contract | Each piece and the base template have rendered-markup tests |
| G10 | Third-party senders are not extended or replaced. Only their templates are overridden |

## Design

### The base template: `mvp/email/base.html`

```django
{# mvp_compliance/email/version_published_message.html #}
{% extends "mvp/email/base.html" %}
{% block preheader %}A new version is published.{% endblock %}
{% block body %}
  <h1>{{ version.title }}</h1>
  <c-mvp.email.text>…</c-mvp.email.text>
  <c-mvp.email.text mb="lg">…</c-mvp.email.text>
  <c-mvp.email.button href="{% email_url version.get_absolute_url %}" text="Read it" />
{% endblock %}
```

- The sketch's markup, with its styles moved into a `<style>` block as classes. Blocks:
  `preheader`, `body`, `footer`. Plain `h1`, `h2`, `p`, `ul`, `li` and `a` in the body get their
  spacing and colour from the block, so an author writes plain markup.
- The whole template is wrapped in `{% email_inline %}…{% endemail_inline %}`, a block tag that
  renders its contents, child blocks included, and passes the result through css-inline
  (`keep_at_rules=True`, `load_remote_stylesheets=False`). The `@media` rules for the dark scheme
  and the phone width stay in the head. This is how the styling becomes inline without the sender
  doing anything: it happens while the template renders.
- The template reads everything through `{% load mvp_email %}` tags, so it needs nothing in its
  context that a third-party sender would not pass (FR-003).

### Template tags: `mvp/templatetags/mvp_email.py`

- `{% email_brand as brand %}`: the light and dark palettes and the absolute logo URLs.
- `{% email_url path %}`: an absolute address on the site for a path or a URL name with arguments,
  the same way `{% url %}` takes them. Addresses already absolute are returned unchanged.
- `{% email_site_name %}`: `MVP_CONFIG["site_name"]`, otherwise the request's or the current
  `Site`'s name, as the shell names the site.
- `{% email_inline %}`: above.
- The site's address: `context["request"].build_absolute_uri("/")` when the context has a request
  (allauth passes one), otherwise the current `Site` over `https`, `http` while `DEBUG`. With no
  request, the no-request path raises `ImproperlyConfigured`, naming `django.contrib.sites` and
  `SITE_ID`, when the sites framework is not installed, when no `Site` matches `SITE_ID`, and when
  the `Site`'s domain is empty.

### Colours and logos: `mvp/email/brand.py`, `EmailBrand`

- `EmailBrand.current()` is cached for the process. It reads the themes named in
  `MVP_CONFIG["theme"]["default"]` and `["dark"]`.
- Reading a theme: every `.css` file listed by the static file finders that contains
  `data-theme`, in finder order, parsed with tinycss2, descending into `@layer` blocks. A rule
  contributes its `--color-*` declarations only when one of its comma-separated selectors is the
  theme on its own: `[data-theme=<name>]`, quoted or not, optionally with `:root` in the same
  compound. A selector naming the theme and then a descendant (`[data-theme=nord] .mvp-sidebar`)
  never contributes. A `var()` value is skipped silently. The first value found for each property
  wins, so a project's own stylesheet beats the package's. Missing properties fall back to the
  package's theme of the same name, then to the package's `light` or `dark`.
- Each value is converted with coloraide to sRGB hex, fitted into gamut. A value coloraide cannot
  read takes the fallback and is recorded as a problem.
- The palette: `page` (`base-200`), `surface` (`base-100`), `border` (`base-300`), `text`
  (`base-content`), `muted` (`base-content` mixed 70% over `base-100`), `primary`,
  `primary_content`.
- Logos: `brand/email/logo.png` and, when present, `brand/email/logo_dark.png`, found with the
  static file finders. The package ships both, rendered from its own SVGs.
- `EmailBrand.problems()` feeds a system check: a theme no stylesheet defines, a colour that could
  not be read, a project `brand/logo.svg` whose email PNG still comes from the package.

### Pieces

Cotton components under `cotton/mvp/email/`: `text` (slot, `mb`, `size`, `align`), `button`
(`href`, `text`), `note` (slot), `divider`, `code` (`code`).

`c-mvp.email.text` renders `<p>` with its options written straight into `style`, so the spacing
holds even where nothing is inlined. `mb` takes `none`, `xs`, `sm`, `md` (the default), `lg` and
`xl`, for 0, 4, 8, 12, 16 and 24 px below. `size` takes `sm`, `md` (the default) and `lg`, for 14,
16 and 18 px type. `align` takes `start` (the default) and `center`. The scale lives in the
component's `<c-vars>` and a `{% with %}` lookup, with no Python. Plain `<p>` in a body still gets
the base template's default spacing. The sketch's markup, styled through the base template's classes so
they inline. The button's colour sits on its table cell, which Outlook honours.

### Previews

- `mvp.email.previews.register(template, label, context, *, subject=None, text=None, group="")`
  records an `EmailPreview`: the HTML template, and the subject and plain-text templates when the
  email has them. Template names are given in full, because each sender names its own.
- While `DEBUG` is on, `MvpConfig.ready` calls `autodiscover_modules("email_previews")`, so a
  package declares its previews in its own `email_previews.py`.
- `mvp.urls` adds `emails/` and `emails/frame/<path:template>` only while `DEBUG` is on, the way
  it already adds the installable-app routes only while `pwa` is set.
- The page and frame views render the declared templates with `render_to_string`, refuse anyone
  but a signed-in staff member, and show one email's render error in its place. Controls: Part
  (HTML, or plain text when the email has it), Colour scheme, Images, Width, as approved, plus
  Language when `LANGUAGES` has more than one entry. Dark and Images blocked are preview-only
  transforms of the rendered HTML.

### Management command: `mvp_email_logos`

Renders `brand/logo.svg` and `brand/logo_dark.svg`, as the static finders find them, to PNG at
64 px high into `brand/email/` under the first `STATICFILES_DIRS` entry or `--output-dir`.
Without resvg-py it stops and names the package, with the same wording as `mvp_pwa_icons`.

### Demo

The five approved sample emails stay under `demo/templates/demo/email/`, written with
`c-mvp.email.text` and with no translation markup (django-mvp's demo carries none, per
https://github.com/django-mvp/django-mvp/issues/648), renamed to allauth's naming as an example of overriding a third party's templates, and are declared in
`demo/email_previews.py`. The broken preview and the menu entry stay.

## Story order and dispatch

US-1 → US-3 → US-2 → US-4, one feature worktree, five dispatches (`tasks.md`).

## Risks

- `{% email_inline %}` runs css-inline on every render. On a ten-kilobyte email it takes well under
  a millisecond.
- The theme search reads every static `.css` file containing `data-theme` once per process.
- Desktop Outlook is checked by eye at the walkthrough, by sending a real email.
