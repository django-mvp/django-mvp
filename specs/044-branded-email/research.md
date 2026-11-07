# Research: Branded HTML email layout

Done after the sketch was approved, against main of 2026-11-05. Packages measured on PyPI and
pypistats the same day.

## Planning notes

### 1. "I don't want too much additional config. If the email colours can be derived from the theme, that would be desirable. Only allow the addition of `MVP_CONFIG` options if there is no other alternative."

**Adopted.** The feature adds no `MVP_CONFIG` option. Each thing it needs comes from something
the project already has:

| Needs | Comes from |
|---|---|
| Light and dark colours | the themes named in `MVP_CONFIG["theme"]["default"]` and `["dark"]` |
| Logo | the brand logo files the shell already uses, rendered to PNG (note 2) |
| Site name | `MVP_CONFIG["site_name"]`, otherwise `mvp.utils.site_name` |
| Site address | the request when there is one, otherwise the sites framework (note 7) |

### 2. Mail clients cannot read daisyUI's CSS variables, and many do not show SVG.

**Adopted, in two parts.**

- **Colours.** A theme is a `[data-theme="<name>"]` rule of `--color-*` properties in a
  stylesheet. The package searches every `.css` file Django's static file finders can see, parses
  each with **tinycss2** (BSD, 1.5.1, about 91M downloads a month, already the CSS parser behind
  WeasyPrint), and takes the theme's colours. Values are converted to hex with **coloraide** (MIT,
  8.14 released 2026-11-02, about 586k a month), which reads `oklch()`, hex and every other CSS colour
  form, and maps out-of-gamut colours into sRGB. A project's own file
  wins over the package's because the finders return a project's `STATICFILES_DIRS` before app
  directories, which is the same precedence the page itself sees. The result is cached for the
  life of the process.
- **Logo.** The email shows PNG files at `brand/email/logo.png` and `brand/email/logo_dark.png`.
  A new management command, `mvp_email_logos`, renders them from `brand/logo.svg` and
  `brand/logo_dark.svg` with **resvg-py** (MIT, 0.5.0, about 3M a month). That is the renderer
  `mvp_pwa_icons` already uses, kept optional the same way. The package ships PNGs of its own
  default logo, so an untouched project's email matches its site. A system check warns when a
  project has its own `brand/logo.svg` but the PNG still comes from the package, which would put
  the package's logo on the project's email.

### 3. css-inline is a candidate for inlining CSS so mail clients render it. premailer is not.

**Adopted.** css-inline (MIT, 0.23.1 released 2026-10-27, about 2.8M a month). django-mvp never
sends an email (Sam, 2026-11-05), so the inlining cannot happen at send time. It happens while the
template renders: the base template wraps itself in a block tag, `{% email_inline %}`, which
renders its contents, the child template's blocks included, and passes the result through
`CSSInliner(keep_at_rules=True, load_remote_stylesheets=False)`. The `@media` rules for the dark
scheme and the phone width stay in the head. Checked on 2026-11-05: the dark rule survives, plain
rules are inlined, and a 7 KB email takes 0.4 ms. Any sender that renders the template, allauth
included, gets inlined HTML. premailer is not used: nothing released since 2021.

### 4. mjml-python against css-inline: measure and recommend one.

**Not adopted.** mjml-python 1.4.2 (MIT, released 2026-09-01, about 413k a month, wraps the Rust
`mrml`). The pure-Python `mjml` is at 1.0.0a1. MJML would have every package write its emails in
a second template language with Django tags inside it. The layout here is one column written once
in this package, which is the part MJML's engine exists for. Packages that send mail write only a
body, in ordinary Django templates. css-inline does the one job left, inlining.

### 5. `html2text` is GPL-3.0, which FR-014 rules out.

**Not needed.** The plain-text part belongs to whatever sends the email (Sam, 2026-11-05). allauth
renders its own `_message.txt` and attaches the HTML beside it
(`allauth/account/adapter.py`, `render_mail`), and django-mvp has no hook into that. No converter
is added. inscriptis, chosen while the plan still had a sending helper, is dropped with it.

### 6. django-post-office will be the email backend later. The design must not get in its way.

**Adopted, by doing nothing.** django-mvp does not send email, so a sender's mail keeps going
through `EMAIL_BACKEND` as it does today, and django-post-office's backend (3.12.0, MIT) receives it
unchanged. No part of this feature stores, queues or logs mail.

### 7. With no request, where does the site's address come from, without a setting?

**Adopted: the sites framework.** With a request, `request.build_absolute_uri("/")`. Without one,
`django.contrib.sites` `get_current_site(None)`, which reads `SITE_ID`. A `Site` holds a domain and
no scheme, so the scheme is `https`, or `http` while `DEBUG` is on. Every project that sends
account mail through allauth has the sites framework already, because allauth requires it, and
allauth passes the request into its email templates' context. The template tags read the request
from the context when it is there. With neither, they raise `ImproperlyConfigured` naming
`django.contrib.sites` and `SITE_ID`.

## What the sketch needs and faked

| Sketch line | Met by |
|---|---|
| Light colours from the default theme, dark from the dark theme (page, card, border, text, button) | note 2, `mvp.email.brand` |
| Muted text as a solid colour, 70% text over the card | coloraide's `mix` |
| Absolute logo with a dark version | note 2 and note 7 |
| Body markup carries no styling | the base template's `<style>` block, inlined by `{% email_inline %}` (note 3) |
| Plain text keeps headings, items, rows and link addresses | the sender's own plain-text template (note 5). The preview shows it when the email has one |
| Preview list with labels and groups, error per email | `mvp.email.previews`, discovered from each app's `email_previews.py` |
| Dark and images-blocked views | preview-only transforms of the rendered HTML, tested |
| Faked: colour reading by regex and hand-written conversion | tinycss2 and coloraide |
| Faked: SVG logo | PNGs and `mvp_email_logos` |
| Faked: `logo_url` called directly | the email reads its own PNG paths. A configured `logo_resolver` returns SVG URLs a mail client cannot show, so the email does not call it |
| Faked: inline styles by hand | `{% email_inline %}` and css-inline |
| Faked: plain-text converter | dropped: the sender's own template (note 5) |
| Faked: site address from the request only | note 7 |
| Faked: no sending helper | none is built: django-mvp does not send email (FR-016) |
| Faked: dark view forces the media query on | kept as the preview's own transform, now tested |
| Faked: images blocked empties every address | kept as the preview's own transform, now tested |
| Faked: `preview()` called from `demo/emails.py` in `DemoConfig.ready` | `autodiscover_modules("email_previews")` in `MvpConfig.ready` while `DEBUG` is on, Django's own mechanism, the one the admin uses |
| Faked: five sample emails in the demo | stay in the demo as the worked example, and become the preview fixtures in tests |
| Faked: language follows the shell switcher | a Language choice on the preview page when `LANGUAGES` has more than one entry |

## Template names

Every sender names its own templates, so django-mvp imposes no naming. allauth's are
`<prefix>_subject.txt`, `<prefix>_message.txt` and `<prefix>_message.html`, and django-mvp-accounts
adopts the layout by overriding the `_message.html` files to extend the base template. A preview
names its templates in full.

## What already exists

| New piece | Stopped at | Found |
|---|---|---|
| Base layout template | 7, new | none in the repo |
| Email pieces (button, note, divider, code) | 7, new Cotton components | daisy-cotton has a button, but its markup is classes a mail client drops |
| Theme colour reader | 6 | tinycss2 parses, coloraide converts. The glue that finds the rule is new, about 40 lines |
| Static file search | 4 | `django.contrib.staticfiles.finders.get_finders()` and each finder's `list()` |
| Contrast and mixing | 6 | coloraide `contrast()` and `mix()` |
| CSS inlining | 6 | css-inline |
| Logo rendering | 2 and 6 | `mvp_pwa_icons`'s use of resvg-py. The new command shares its optional-import message |
| Site address | 4 | `request.build_absolute_uri`, `django.contrib.sites.shortcuts.get_current_site` |
| Site name | 2 | `mvp.utils.site_name` |
| Absolute addresses in a body | 4 and 7 | `{% email_url %}`, a thin tag over Django's `reverse` and the site's address |
| Sending, subject, plain text, language | 1 | not built: they are the sender's |
| Inlining at render time | 7, new | `{% email_inline %}`, a block tag of a few lines over css-inline |
| Preview discovery | 4 | `django.utils.module_loading.autodiscover_modules` |
| Preview page | 2 | `MVPTemplateView`, `page_view.html`, `UserPassesTestMixin` |
| Start-up warnings | 2 | the `mvp.checks` system checks |
| Absent in production | 2 | `mvp.urls` adds routes conditionally already (the installable-app routes) |

## Unknowns

- Desktop Outlook renders with Word. The layout is table-based and every colour is on a table
  cell, which is what Outlook honours. It still has to be checked by eye at the walkthrough by
  sending a real email. Nothing in the test suite can stand in for that.
