# ADR 0041 — Email colours are read from the theme stylesheets

**Status:** accepted

## Decision

An email's light colours are the theme named in `MVP_CONFIG["theme"]["default"]`, and its dark colours the theme named in `MVP_CONFIG["theme"]["dark"]`. `mvp.email.brand.EmailBrand` reads them once per process from the static stylesheets that define them: every `.css` file the static file finders list, a project's own before the package's, parsed with tinycss2 and converted to hex with coloraide. Only a rule whose selector is the theme on its own (`[data-theme="name"]`) contributes, never a rule that styles something inside a theme. A missing or unreadable colour falls back to the packaged theme of the same name, then to the package's `light` or `dark`, and is reported by a system check. There is no setting for email colours.

## Why

Mail clients cannot read CSS custom properties or `oklch()`, so the email needs plain colours. A setting for them would have been a second copy of the theme, drifting from the site the first time the theme changed. The theme names are already configured and the themes already exist as CSS, so reading them keeps the email matching the site with nothing to configure. The selector rule exists because themes are often followed by rules for one part of the page, such as `[data-theme="nord"] .mvp-sidebar`, whose colours are not the theme's.

## Revisit if

Themes stop being plain CSS files the static finders can see, for example if they move into a database or a build step, or projects need email colours that differ from their site.
