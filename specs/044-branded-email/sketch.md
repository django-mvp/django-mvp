# Sketch: Branded HTML email layout

## What exists

- **Theme names**: `MVP_CONFIG["theme"]["default"]` and `["dark"]` name the site's light and dark
  themes. A theme is a `[data-theme="<name>"]` block of `--color-*` properties, in the package's
  `css/django-mvp.css` (prebuilt daisyUI themes, in `oklch()`) or in a project's own stylesheet
  (the demo's `css/themes.css`, in hex).
- **Brand logo**: `MVP_CONFIG["brand"]["logo_resolver"]`, `mvp.utils.logo_url`, returns
  `brand/logo.svg` and `brand/logo_dark.svg`. The shell draws both and lets the theme pick.
- **Site name**: `MVP_CONFIG["site_name"]`, else `mvp.utils.site_name(request)`.
- **Page shell**: `MVPTemplateView` with `page_view.html`, as the install page uses.
- **Planning notes applied**: note 1 (no new settings): the sketch reads colours from the themes
  and adds no setting. Note 2 (variables and SVG): the colours are read from the theme into plain
  hex, and the SVG logo is shown as it is, listed below as faked.

## What the screens need from the code

- The email's light colours come from the default theme, and its dark colours from the dark theme:
  page (`base-200`), card (`base-100`), border (`base-300`), text (`base-content`), button
  (`primary` and `primary-content`).
- Muted text is the theme's text colour laid at 70% over the card, as one solid colour, because
  mail clients don't apply opacity reliably.
- The logo needs an absolute address, and a dark version when the brand has one.
- Body markup carries no styling of its own: headings, paragraphs and lists need their spacing
  and type from the layout.
- The plain-text part keeps headings, list items, table rows and every link's address, and shows
  a link only once when its text is already the address.
- The preview page needs every declared preview with a label and a group, the rendered subject,
  HTML and plain text, and a render error for one email without breaking the list.
- The preview's dark and images-blocked views need the email as a client would show it.

## What the sketch faked

- **Colour reading**: a regex over two hard-coded stylesheet paths and a hand-written
  `oklch()` converter (`mvp/email/brand.py`).
- **Logo**: the SVG is linked as it is. Gmail and Outlook don't show SVG, so real mail needs
  another format.
- **Logo resolver**: the sketch calls `mvp.utils.logo_url` directly, not the configured resolver.
- **Inline styles**: hand-written inline in the layout, the pieces and the sample bodies. The
  sample bodies carry heading and paragraph margins they shouldn't need.
- **Plain text**: a hand-written HTML-to-text converter in `mvp/email/render.py`.
- **Site address**: taken from the request only.
- **Sending**: there is no helper that sends. The preview only renders.
- **Dark view**: the preview forces the email's dark rules on, rather than the browser's own
  scheme deciding.
- **Images blocked**: the preview empties every image address.
- **Preview declarations**: `mvp.email.render.preview()`, called from the demo's `demo/emails.py`
  at start-up.
- **Sample emails**: five in the demo (sign-in code, password reset, receipt, policy update,
  invitation) plus one that fails to render. None is a real package's email.
- **Language**: the preview renders in the active language, so the shell's language switcher
  changes it. There is no language choice on the page itself.

## What was ruled by eye

- One centred card, 600 px wide, on the page colour, with the logo at the top left and the footer
  outside the card in muted text.
- The footer's default is "Sent by <site name>", linked to the site.
- The button is the theme's primary colour, square-ish corners (4 px), 44 px tall.
- A one-time code sits in a sunk box in large monospace type with wide letter spacing.
- Links in body text are the text colour, underlined, never the brand colour.
- The preview page puts the list of emails beside the email at wide widths, with Part, Colour
  scheme, Images and Width as button groups above it.

## Review

Sam approved the first round as built, with no changes asked for: the layout, the pieces, the
five sample emails and the preview page.
