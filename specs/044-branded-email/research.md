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

**Adopted.** css-inline (MIT, 0.23.1 released 2026-10-27, about 2.8M a month). The layout is
written with a `<style>` block and classes. At send time `CSSInliner(keep_at_rules=True)` moves
every rule onto its elements and keeps the `@media` rules, which carry the dark scheme and the
phone width, in the head. Checked on 2026-11-05: with that option the dark-mode rule survives and
the plain rules are inlined. The sample emails' hand-written margins go away. premailer is not
used: nothing released since 2021.

### 4. mjml-python against css-inline: measure and recommend one.

**Not adopted.** mjml-python 1.4.2 (MIT, released 2026-09-01, about 413k a month, wraps the Rust
`mrml`). The pure-Python `mjml` is at 1.0.0a1. MJML would have every package write its emails in
a second template language with Django tags inside it. The layout here is one column written once
in this package, which is the part MJML's engine exists for. Packages that send mail write only a
body, in ordinary Django templates. css-inline does the one job left, inlining.

### 5. `html2text` is GPL-3.0, which FR-018 rules out.

**Adopted: inscriptis** (Apache-2.0, 2.7.6 released 2026-10-23, about 1.6M a month, Python 3.11+,
inside the package's 3.12 floor). It lays tables out as columns and lists as items. Its own link
option writes Markdown (`[text](url)`) and repeats an address that is already the link's text, so
a handler for `<a>`, through its `custom_html_tag_handler_mapping`, writes `text (address)` or
the address alone. It brings lxml (capped below 6.2) and requests into every consumer's install.
Weighed against a converter of our own over `html.parser`: the package stays, because a
maintained converter beats custom code and its size is no reason against it. markdownify (MIT) was the alternative: it
produces Markdown, so a plain-text reader sees `**` and `#`. html-text (MIT) drops link
addresses.

### 6. django-post-office will be the email backend later. The design must not get in its way.

**Adopted.** The helper builds one `EmailMultiAlternatives` and calls `send()`, which goes through
`EMAIL_BACKEND`. django-post-office's backend (3.12.0, MIT) accepts exactly that. No part of this
feature stores, queues or logs mail.

### 7. With no request, where does the site's address come from, without a setting?

**Adopted: the sites framework.** With a request, `request.build_absolute_uri("/")`. Without one,
`django.contrib.sites` `get_current_site(None)`, which reads `SITE_ID`. A `Site` holds a domain and
no scheme, so the scheme is `https`, or `http` while `DEBUG` is on. Every project that sends
account mail through allauth has the sites framework already, because allauth requires it. With
neither, the helper raises `ImproperlyConfigured` saying how to fix it.

## What the sketch needs and faked

| Sketch line | Met by |
|---|---|
| Light colours from the default theme, dark from the dark theme (page, card, border, text, button) | note 2, `mvp.email.brand` |
| Muted text as a solid colour, 70% text over the card | coloraide's `mix` |
| Absolute logo with a dark version | note 2 and note 7 |
| Body markup carries no styling | the layout's `<style>` block, inlined by css-inline (note 3) |
| Plain text keeps headings, items, rows and link addresses | inscriptis (note 5) |
| Preview list with labels and groups, error per email | `mvp.email.previews`, discovered from each app's `emails.py` |
| Dark and images-blocked views | preview-only transforms of the rendered HTML, tested |
| Faked: colour reading by regex and hand-written conversion | tinycss2 and coloraide |
| Faked: SVG logo | PNGs and `mvp_email_logos` |
| Faked: `logo_url` called directly | the email reads its own PNG paths. A configured `logo_resolver` returns SVG URLs a mail client cannot show, so the email does not call it |
| Faked: inline styles by hand | css-inline |
| Faked: plain-text converter | inscriptis |
| Faked: site address from the request only | note 7 |
| Faked: no sending helper | `mvp.email.send_email` |
| Faked: dark view forces the media query on | kept as the preview's own transform, now tested |
| Faked: images blocked empties every address | kept as the preview's own transform, now tested |
| Faked: `preview()` called from `demo/emails.py` in `DemoConfig.ready` | `autodiscover_modules("emails")` in `MvpConfig.ready`, Django's own mechanism, the one the admin uses |
| Faked: five sample emails in the demo | stay in the demo as the worked example, and become the preview fixtures in tests |
| Faked: language follows the shell switcher | a Language choice on the preview page when `LANGUAGES` has more than one entry |

## Template names

An email is a template prefix with three files: `<prefix>_subject.txt`, `<prefix>_message.html`
and optionally `<prefix>_message.txt`. This is allauth's own convention
(`DefaultAccountAdapter.render_mail`), so django-mvp-accounts adopts the layout by adding
`_message.html` files and changes nothing about how allauth finds them. The sketch's
`<name>/subject.txt` shape is dropped.

## What already exists

| New piece | Stopped at | Found |
|---|---|---|
| Base layout template | 7, new | none in the repo |
| Email pieces (button, note, divider, code) | 7, new Cotton components | daisy-cotton has a button, but its markup is classes a mail client drops |
| Theme colour reader | 6 | tinycss2 parses, coloraide converts. The glue that finds the rule is new, about 40 lines |
| Static file search | 4 | `django.contrib.staticfiles.finders.get_finders()` and each finder's `list()` |
| Contrast and mixing | 6 | coloraide `contrast()` and `mix()` |
| CSS inlining | 6 | css-inline |
| Plain text | 6 | inscriptis |
| Logo rendering | 2 and 6 | `mvp_pwa_icons`'s use of resvg-py. The new command shares its optional-import message |
| Site address | 4 | `request.build_absolute_uri`, `django.contrib.sites.shortcuts.get_current_site` |
| Site name | 2 | `mvp.utils.site_name` |
| Making paths absolute | 7, new | a regex over `href="/` and `src="/` in the rendered HTML. css-inline's `base_url` resolves stylesheets only |
| Sending | 4 | `EmailMultiAlternatives` |
| Language | 4 | `translation.override` |
| Preview discovery | 4 | `django.utils.module_loading.autodiscover_modules` |
| Preview page | 2 | `MVPTemplateView`, `page_view.html`, `UserPassesTestMixin` |
| Start-up warnings | 2 | the `mvp.checks` system checks |
| Absent in production | 2 | `mvp.urls` adds routes conditionally already (the installable-app routes) |

## Unknowns

- Desktop Outlook renders with Word. The layout is table-based and every colour is on a table
  cell, which is what Outlook honours. It still has to be checked by eye at the walkthrough by
  sending a real email. Nothing in the test suite can stand in for that.
