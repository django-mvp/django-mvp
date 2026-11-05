# Planning notes: Branded HTML email layout

Notes for research and planning to answer by name. None of them is settled.

## From Sam

1. "I don't want too much additional config. If the email colours can be derived from the theme,
   that would be desirable. Only allow the addition of `MVP_CONFIG` options if there is no other
   alternative."

## From the request that opened this feature

2. Mail clients cannot read daisyUI's CSS variables, and many do not show SVG, which is what the
   brand logo is. Research how the theme's colours and the logo reach the email.
3. css-inline (0.23.1, October 2026, about 2.8M downloads a month) is a candidate for inlining
   CSS so mail clients render it. premailer is not: its last release was in 2021.
4. mjml-python is named in the research for a later community bundle. Measure it the same way
   (release date, downloads, licence) against css-inline and recommend one. Measured on
   2026-11-04: mjml-python 1.4.2 (September 2026, about 413k a month, MIT, a wrapper around the
   Rust `mrml`); the pure-Python `mjml` 1.0.0a1 (September 2026, about 306k a month, MIT).
5. `html2text`, the usual converter for a plain-text part, is GPL-3.0, which FR-018 rules out.
6. django-post-office is expected to be installed later as the email backend, so mail is queued
   and logged without changing the packages that send it. The design must not get in its way.
7. When sending from a background worker there is no request. Research where the site's address
   comes from without adding a setting (note 1).
