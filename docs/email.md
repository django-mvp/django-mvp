# Email

django-mvp gives an HTML email the look of your site. It ships a base template to extend, a few
pieces to write the message with and template tags for the parts that need the site's address.
It never renders or sends an email itself: whatever sends your email today keeps its own subject,
plain text and language.

This page covers the colours and the logo an email is drawn in. Nothing about them is set for
email. They come from what the site already uses.

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

## Show your logo in the email

Mail clients don't draw SVG, so the email shows PNG files: `brand/email/logo.png` and, for the
dark scheme, `brand/email/logo_dark.png`. The package ships both, rendered from its own logo at 64
pixels high. The dark logo is used only when the file is found.

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
