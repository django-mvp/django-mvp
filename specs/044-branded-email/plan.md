# Implementation Plan: Branded HTML email layout

**Branch**: `044-branded-email` · **Spec**: [spec.md](spec.md) · **Research**:
[research.md](research.md) · **Sketch**: [sketch.md](sketch.md)

## Summary

`mvp.email` gives a package one class to render and send a branded email, a base layout with four
email pieces, a colour reader that takes the email's colours from the project's light and dark
themes, PNG logos with a command that renders them, and a staff-only preview page that exists
while `DEBUG` is on. The approved sketch's layout, pieces, sample emails and preview page are kept
as Sam saw them. The code behind them is rewritten test-first, and everything the sketch faked is
replaced (research, "What the sketch needs and faked").

## Technical context

Python 3.12+, Django 5.2–6.1, django-cotton 2.8. New runtime dependencies, each justified in
`research.md` (Article VII): css-inline, tinycss2, coloraide, inscriptis (which brings lxml and
requests). resvg-py stays optional
and is used only by the new management command, imported inside it the way `mvp_pwa_icons` does.
Tests are pytest with Django's in-memory email backend and assertions on the rendered HTML and
text. No browser test: nothing here needs a browser to observe (Article XIV).

## Constitution check

| Article | How the plan meets it |
|---|---|
| I Testing | Every task writes its tests first. The sketch's Python is reset to origin/main before the first dispatch so those tests start red |
| II Simplicity, III Anti-abstraction | One class for an email, one for the brand. No base class, no backend of our own, no setting |
| V Security | Every value reaches the email through Django's template layer. The preview page is absent with `DEBUG` off and staff-only with it on |
| VI, XVII Documentation | `docs/email.md` is written in the story that introduces each name, and listed in the docs index |
| VII Dependencies | Four runtime additions, each with its reason in `research.md`. `deptry` stays green |
| VIII Internationalization | Every string in the layout, pieces and preview page is translatable. The email renders in the language it is given |
| X Cohesion | `Email` holds rendering and sending, `EmailBrand` holds colours and logos. The preview registry is a module dict with one `register` function, the shape Django's own `autodiscover_modules` callers use |
| XI Components are the public API | The pieces are Cotton components, `c-mvp.email.button`, `.note`, `.divider`, `.code` |
| XIII Rendered markup is a contract | Each piece and the layout have rendered-markup tests |
| XV Build artifacts | The preview page uses classes already in the built stylesheet. The task that adds it confirms that and rebuilds if any is missing |
| XVI Compatibility | Additive only. No existing name changes |

## Design

### Sending: `mvp.email.Email`

```python
from mvp.email import Email

Email("mvp_compliance/email/version_published", {"version": version}).send(
    to=[user.email], language=user.language, request=request,
)
```

- `Email` lives in `mvp/email/message.py` and is re-exported from `mvp.email`.
  `Email(prefix, context, *, language=None, request=None)`. `render()` returns a `RenderedEmail`
  with `subject`, `html` and `text`. `send(to, *, from_email=None, cc=None, bcc=None,
  reply_to=None, attachments=None, headers=None)` builds one `EmailMultiAlternatives` and calls
  `send()`, returning what Django returns. An empty `to` sends nothing, logs a warning and returns
  `0`.
- Templates follow allauth's naming: `<prefix>_subject.txt`, `<prefix>_message.html`, and
  optionally `<prefix>_message.txt`. The subject is joined to one line.
- Rendering runs inside `translation.override(language or translation.get_language())`, so an
  email sent without a language uses the active one, and the previous language is restored.
  `override(None)` would switch translation off, so it is never called with `None`.
- The context the templates see is the caller's, plus `email_brand` (light and dark colours, logo
  URLs), `site_name` and `site_url`. `site_name` is `MVP_CONFIG["site_name"]` when set, otherwise
  the request's or the current `Site`'s name, so the email names the site the way the shell does. The caller's keys win.
- After rendering: paths in `href="/…"` and `src="/…"` become absolute against the site's address,
  then css-inline inlines the `<style>` block with `keep_at_rules=True` and
  `load_remote_stylesheets=False`. The plain-text part is the `_message.txt` template when it
  exists, otherwise inscriptis over the final HTML, with a handler for `<a>` that writes
  `text (address)`, or the address alone when the text already is the address.
- The site's address: `request.build_absolute_uri("/")` (so it relies on `ALLOWED_HOSTS`, as every
  request does), otherwise the current `Site` over `https` (`http` while `DEBUG`). The no-request
  path raises `ImproperlyConfigured`, naming `django.contrib.sites` and `SITE_ID`, in every way it
  can fail: the sites framework not installed, no `Site` matching `SITE_ID`, or a `Site` with an
  empty domain.

### Colours and logos: `mvp.email.brand.EmailBrand`

- `EmailBrand.current()` is cached for the process. It reads the themes named in
  `MVP_CONFIG["theme"]["default"]` and `["dark"]`.
- Reading a theme: every `.css` file listed by the static file finders that contains
  `data-theme`, in finder order, parsed with tinycss2, descending into `@layer` blocks. A rule
  contributes its `--color-*` declarations only when one of its comma-separated selectors is the
  theme on its own: `[data-theme=<name>]`, quoted or not, optionally with `:root` in the same
  compound. A selector naming the theme and then a descendant (`[data-theme=nord] .mvp-sidebar`)
  never contributes. A `var()` value is skipped silently, as a reference and not a colour. The first value found for each property wins, so a project's own
  stylesheet beats the package's, which is what the page sees. Missing properties fall back to the
  package's theme of the same name, then to the package's `light` or `dark`.
- Each value is converted with coloraide to sRGB hex, fitted into gamut. A value coloraide cannot
  read takes the fallback and is recorded as a problem.
- The palette the layout uses: `page` (`base-200`), `surface` (`base-100`), `border`
  (`base-300`), `text` (`base-content`), `muted` (`base-content` mixed 70% over `base-100`),
  `primary`, `primary_content`.
- Logos: `brand/email/logo.png` and, when present, `brand/email/logo_dark.png`, found with the
  static file finders and served through `static()`. The package ships both, rendered from its own
  SVGs.
- `EmailBrand.problems()` lists what the system check reports: a theme no stylesheet defines, a
  colour that could not be read, a project `brand/logo.svg` whose email PNG still comes from the
  package.

### The layout and pieces

- `mvp/email/base.html`: the approved sketch's markup with its inline styles moved into the
  `<style>` block as classes, so css-inline puts them back. Blocks: `preheader`, `body`, `footer`.
  The `@media (prefers-color-scheme: dark)` rules use the dark palette and swap the logo. The
  `@media (max-width: 620px)` rule is kept. Headings, paragraphs and lists in the body get their
  spacing from the block, so a sender writes plain markup.
- Pieces as Cotton components under `cotton/mvp/email/`: `button` (`href`, `text`), `note`
  (slot), `divider`, `code` (`code`). Their markup is the sketch's.

### Previews

- `mvp.email.previews.register(prefix, label, context, *, group="")` adds an `EmailPreview` to a
  module dict. While `DEBUG` is on, `MvpConfig.ready` calls `autodiscover_modules("email_previews")`,
  so a package declares its previews in its own `email_previews.py`. The name avoids the
  `emails.py` modules packages already have for sending.
- `mvp.urls` adds `emails/` and `emails/frame/<path:prefix>` only while `DEBUG` is on, the way it
  already adds the installable-app routes only while `pwa` is set.
- `EmailPreviewView` and `EmailPreviewFrameView` refuse anyone but a signed-in staff member. The
  page is the sketch's. One email failing to render shows its error in place of the email.
- The preview's controls: Part, Colour scheme, Images and Width, as approved, plus Language when
  `LANGUAGES` has more than one entry. Dark shows the email with its dark rules applied
  unconditionally, and Images blocked removes every image address. Both are preview-only
  transforms of the rendered HTML.

### Management command: `mvp_email_logos`

Renders `brand/logo.svg` and `brand/logo_dark.svg`, as the static finders find them, to PNG at
64 px high (twice the 32 px the layout draws), into `brand/email/` under the first
`STATICFILES_DIRS` entry or `--output-dir`. Without resvg-py it stops and names the package, with
the same wording as `mvp_pwa_icons`.

### Demo

The five approved sample emails move to the allauth naming under `demo/templates/demo/email/`
and are declared in `demo/emails.py`. The deliberately broken preview stays. The menu entry stays.

## Story order and dispatch

US-1 → US-3 → US-2 → US-4, one feature worktree, six dispatches (one per group) (`tasks.md`). US-3 comes before
US-2 because the dark colours US-2 checks come from the theme reader US-3 completes.

## Risks

- The theme search reads every static `.css` file once per process: 22 files, about 800 KB, on
  the demo. Files without `data-theme` are skipped before parsing.
- Desktop Outlook is checked by eye at the walkthrough, by sending a real email. No test stands in
  for it.
