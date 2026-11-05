# Email

django-mvp gives an HTML email the look of your site. It ships a base template to extend, a few
pieces to write the message with and template tags for the parts that need the site's address.
It never renders or sends an email itself: whatever sends your email today keeps its own subject,
plain text and language.

This page covers the layout an email extends, the colours and the logo it is drawn in, and the
template tags it is written with. Nothing about the colours and the logo is set for email. They
come from what the site already uses.

## Write an email on the base template

Make your email template extend `mvp/email/base.html` and fill its blocks:

1. Start the template with `{% extends "mvp/email/base.html" %}`.
2. Write the message in `{% block body %}`, in plain `h1`, `h2`, `p`, `ul`, `li` and `a`. The
   base template gives them their spacing and colours.
3. Optionally write a one-line summary in `{% block preheader %}`. Mail clients show it after the
   subject in the inbox list.
4. Optionally replace the footer in `{% block footer %}`. Without it the footer reads "Sent by"
   and your site's name, linked to the site.

```django
{% extends "mvp/email/base.html" %}
{% load mvp_email %}
{% block preheader %}A new version is published.{% endblock %}
{% block body %}
  <h1>{{ version.title }}</h1>
  <p>Version {{ version.number }} is published.</p>
  <p><a href="{% email_url version.get_absolute_url %}">Read it</a></p>
{% endblock %}
```

The page around the message carries your site's logo, name and colours, and its dark-scheme and
phone-width rules. The template needs nothing in its context: it finds the site's address and name
with the tags described below, so it renders the same for a sender that passes only its own
variables. It never sets the subject or the plain-text part. Whatever sends the email keeps both.

## Write the message with the pieces

Five components cover what a message is usually made of. Each one is drawn in the site's colours
and written so it holds in every mail client. Use them inside the `body` block:

1. `<c-mvp.email.text>` writes a paragraph. Plain `<p>` works too and gets the same default
   spacing. Use the component when a paragraph needs other spacing. `mb` sets the space below it
   (`none`, `xs`, `sm`, `md` for the default, `lg`, `xl`), `size` the type (`sm`, `md`, `lg`) and
   `align` the alignment (`start` or `center`). A value that isn't on its list is the default.
2. `<c-mvp.email.button href="…" text="…" />` draws a link as a button.
3. `<c-mvp.email.note>` writes secondary text, such as what to do if the email was not expected.
4. `<c-mvp.email.divider />` draws a rule between parts of the message.
5. `<c-mvp.email.code code="…" />` sets a one-time code apart so it can be read and copied.

```django
{% extends "mvp/email/base.html" %}
{% block body %}
  <h1>Reset your password</h1>
  <c-mvp.email.text>Someone asked to reset the password for your account.</c-mvp.email.text>
  <c-mvp.email.text mb="lg" align="center">Choose a new one with the button below.</c-mvp.email.text>
  <c-mvp.email.button :href="reset_url" text="Choose a new password" />
  <c-mvp.email.divider />
  <c-mvp.email.note>If you didn't ask for this, you can ignore this email.</c-mvp.email.note>
  <c-mvp.email.code code="482913" />
{% endblock %}
```

The component reference lists them with the other components in [Components](components.md#email).

## Override a third-party package's email

A package that sends HTML email from a template can be given your site's look without touching its
code. The package renders its templates by name, so a template of yours with the same name is
rendered instead. This works with any package that renders an HTML part from a template, such as
django-allauth.

1. Find the template names. A package usually has a prefix and three templates under it:
   `<prefix>_subject.txt`, `<prefix>_message.txt` and `<prefix>_message.html`. For allauth's
   confirmation email the prefix is `account/email/email_confirmation`.
2. Create `<prefix>_message.html` in your project's template directory, at the same path.
   Django searches `DIRS` before the packages' own template directories, so yours wins.
3. Make it extend `mvp/email/base.html` and write the message in the `body` block. Use the
   variables the package passes to its own template.
4. Leave `<prefix>_subject.txt` and `<prefix>_message.txt` alone. The subject and the plain-text
   part stay exactly as the package wrote them. Only the HTML part changes.

```django
{# templates/account/email/email_confirmation_message.html #}
{% extends "mvp/email/base.html" %}
{% load mvp_email %}
{% block preheader %}Confirm your email address to finish signing up.{% endblock %}
{% block body %}
  <h1>Confirm your email address</h1>
  <c-mvp.email.text>Confirm your address to finish signing up to {% email_site_name %}.</c-mvp.email.text>
  <c-mvp.email.button :href="activate_url" text="Confirm your email address" />
  <c-mvp.email.note>If you didn't sign up, you can ignore this email.</c-mvp.email.note>
{% endblock %}
```

The logo and the site's name come from your site, and the styles are inlined while the template
renders, so the package needs to do nothing more. When the package passes a `request` to its
templates, as allauth does, links and the logo use that request's host. Otherwise they use the
current `Site`.

The demo's sample emails under `demo/templates/demo/email/` follow this naming, each with a
`_subject.txt` and a `_message.html`.

## Replace the base template or a piece

The base template and each piece are ordinary templates, so a project replaces one by writing a
template at the same path. Django searches your `DIRS` before the packages' template directories,
so yours is rendered in its place, for every email built on it.

1. Put a directory in the `DIRS` of your `TEMPLATES` setting, if you haven't one.
2. To replace the base template, create `mvp/email/base.html` in it. Emails that extend
   `mvp/email/base.html` now extend yours. Keep the `preheader`, `body` and `footer` blocks, or
   the emails written for them lose their content.
3. To replace a piece, create its file at the same path in your directory:
   `cotton/mvp/email/text.html`, `button.html`, `note.html`, `divider.html` or `code.html`. Keep
   the component's `<c-vars>` line so emails using it still pass the same attributes.

Start from a copy of the package's file and change what you need. Emails you haven't replaced a
piece for keep using the package's.

## Inline your own styles

Gmail and Outlook drop or ignore most of a `<style>` element, so the base template writes its
rules onto the markup they match while it renders. `{% email_inline %}` does the same for markup
of your own:

```django
{% load mvp_email %}
{% email_inline %}
  <style>.total { font-weight: 700; }</style>
  <p class="total">{{ total }}</p>
{% endemail_inline %}
```

Everything between the tags is rendered first, then each rule in a `<style>` block is written into
the `style` attribute of the elements it matches, and the rule leaves the block. Rules that can't
be written inline, such as `@media`, stay in the block. Linked stylesheets are never fetched.

## Give the email your theme's colours

An email uses the two themes `MVP_CONFIG["theme"]` names: `default` for the light scheme and
`dark` for the dark scheme. Change those two names, or write your own theme, as
[Theming](theming.md) describes, and the email follows.

The colours are read from the stylesheets your static file finders list, once per process:

1. Every `.css` file the finders list that mentions `data-theme` is read, in finder order. Your
   project's own files come before the package's, so a theme you define wins over the packaged
   theme of the same name.
2. A rule contributes only when one of its comma-separated selectors is the theme on its own,
   such as `[data-theme=brand]`, `[data-theme="brand"]` or `:root[data-theme=brand]`. A selector
   that goes on to name something inside the theme, such as `[data-theme=brand] .mvp-sidebar`,
   is ignored. Rules inside `@layer` blocks are read.
3. The first value found for each property wins. A value that refers to another property with
   `var()` is skipped.
4. Each colour is converted to a hex value with its out-of-range parts fitted into sRGB, so a
   theme written in `oklch()` works.

5. A colour the stylesheets don't give comes from the package's theme of the same name, and
   failing that from the package's `light` theme for the light scheme or `dark` theme for the dark
   scheme. A project theme that sets only `--color-primary` gets every other colour from there.
   A value that isn't a colour is treated the same way.

These theme colours make up the palette:

| Palette colour | Theme colour |
| --- | --- |
| `page` | `--color-base-200` |
| `surface` | `--color-base-100` |
| `border` | `--color-base-300` |
| `text` | `--color-base-content` |
| `muted` | `--color-base-content`, 70% of it over `--color-base-100` |
| `primary` | `--color-primary` |
| `primary_content` | `--color-primary-content` |

## Find out which colours the email can't use

An email always renders, whatever the theme. When a colour can't be used, the project's system
checks say so when it starts, as warnings that never stop anything:

- `mvp.W002` names a theme in `MVP_CONFIG["theme"]` that no stylesheet defines. The email uses the
  package's own `light` or `dark` colours in its place.
- `mvp.W003` names a theme and a property whose value isn't a colour. The email takes that colour
  from the package.
- `mvp.W005` says the brand couldn't be read at all, as when a static file manifest hasn't been
  built yet.

Run `python manage.py check` to see them. After fixing a stylesheet or `MVP_CONFIG["theme"]` in a
running process, call `EmailBrand.current.cache_clear()`. A new process reads them afresh.

## Show your logo in the email

Mail clients don't draw SVG, so the email shows PNG files: `brand/email/logo.png` and, for the
dark scheme, `brand/email/logo_dark.png`. The package ships both, rendered from its own logo at 64
pixels high. The dark logo is used only when the file is found.

To show your own logo instead, render your SVG logo to those two files:

1. Put your logo at `brand/logo.svg` in a static directory of your project, and, for the dark
   scheme, `brand/logo_dark.svg`.
2. Install the renderer with `pip install resvg-py`. django-mvp doesn't depend on it, so the
   command stops and names the package when it is missing.
3. Run `python manage.py mvp_email_logos`. It writes `brand/email/logo.png` and, when a dark
   logo is found, `brand/email/logo_dark.png`, each 64 pixels high, into the first
   `STATICFILES_DIRS` entry that has no prefix. Pass `--output-dir` to write into another static
   directory.
4. Run it again whenever the logo changes, and before `collectstatic`.

Your PNG files come before the package's in the static file finders, so the email shows yours. The
command says so when a logo it drew from is the package's own.

## Give a link an absolute address

A link or an image in an email is opened far from your site, so it needs a full address.
Load the tags and use `{% email_url %}`:

1. Put `{% load mvp_email %}` at the top of the template.
2. Write `{% email_url '/accounts/confirm/abc/' %}` for a path, or
   `{% email_url version.get_absolute_url %}` for one from your data.
3. Write `{% email_url 'item' pk=7 %}` for a URL name. It takes arguments the way `{% url %}`
   does and fails the same way when the name does not reverse.
4. Add `as link` to keep the result in a variable.

An address that already names a host, such as `https://other.example/x`, is returned unchanged.

The site's address comes from one of two places:

- **The request.** When the template context has a `request`, as allauth's email templates do,
  the address is that request's scheme and host. `HttpRequest.get_host()` checks the host against
  `ALLOWED_HOSTS`, so the address is only as trustworthy as that setting. Keep `ALLOWED_HOSTS` to
  your own hosts.
- **The current site.** With no request, the address is the domain of the `Site` that `SITE_ID`
  names, over `https`, or over `http` while `DEBUG` is on.

Without a request, rendering fails with `ImproperlyConfigured`, naming `django.contrib.sites` and
`SITE_ID`, when `django.contrib.sites` is not installed, when no `Site` matches `SITE_ID`, and
when that `Site`'s domain is empty. The fix is to install the app, set `SITE_ID` and give the
`Site` its domain, or to render the email with a request.

## Name the site in an email

`{% email_site_name %}` gives the site's name: `MVP_CONFIG["site_name"]` when it is set,
otherwise the name of the request's site or, with no request, of the current `Site`. The text is
escaped like any other variable. It fails like `{% email_url %}` when it needs the `Site` and
cannot find it.

## Read the brand in a template

`{% email_brand as brand %}` puts the brand in the context: `brand.light` and `brand.dark`, each
with `page`, `surface`, `border`, `text`, `muted`, `primary` and `primary_content`, and
`brand.logo` and `brand.logo_dark` as absolute addresses. `brand.logo_dark` is `None` when no dark
logo file is found.

## Read the brand from Python

`mvp.email.brand.EmailBrand.current()` returns the brand: `light` and `dark` palettes, `logo` and
`logo_dark` as static URLs. It is cached for the process. After changing `MVP_CONFIG["theme"]` or
a stylesheet, call `EmailBrand.current.cache_clear()`.
