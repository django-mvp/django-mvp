# Feature Specification: Brand Logo & Icon Templatetags

**Feature Branch**: `019-brand-logo-templatetags`
**Created**: 2026-05-28
**Status**: Draft
**Input**: User description: "Properly displaying company branding is a first-class priority for most production apps. Logos and icons can come in all shapes, sizes and formats which we cannot predict, however, we can come up with a predictable set of rules and utilities that allow developers to place logos and be confident that things will just work. We will need to account for both light and dark theme logos, defaulting to light when only one is provided. The core of the functionality is provided by 2 templatetags: icon_url and logo_url. By default, these will return the results of a dynamic function declared in the users settings file (or using the default function). These functions receive the request object (useful for apps with 'seats' that require displaying different logos per user/company), height: the recommended max image height for the function to return (for use by thumbnailer apps if required by the end dev), and the theme specific requirements (typically light/dark but could be anything the user sets). We can't predict the exact needs of each end-developer so we keep the default function simple, returning static files as is based on theme. These functions should work relatively well for those providing .svg based brand logos. For those dealing with non-vector brand images, they will either need to accept placing a large image in places where it is not required, or, provide their own function to handle image cropping/thumbnailing."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic SVG Logo in Template (Priority: P1)

**Audience**: Developer

A developer wants to display their application's logo in a navbar. They have a single SVG logo file in static files. They use `logo_url` in their template and the logo appears correctly in both light and dark themes, falling back to the single provided logo when no theme-specific variant exists.

**Why this priority**: This is the most common use case — a developer placing a brand logo without needing any custom logic. It must work zero-config.

**Independent Test**: Can be tested by using `{% logo_url %}` in a template with only a light-theme logo configured. Delivers a working branded header with the correct logo URL in both themes.

**Acceptance Scenarios**:

1. **Given** only a light logo is configured in settings, **When** `{% logo_url %}` is called in any theme context, **Then** the light logo URL is returned for all themes.
2. **Given** both light and dark logos are configured, **When** `{% logo_url theme="dark" %}` is called, **Then** the dark logo URL is returned.
3. **Given** both light and dark logos are configured, **When** `{% logo_url theme="light" %}` is called, **Then** the light logo URL is returned.
4. **Given** no theme argument is supplied, **When** `{% logo_url %}` is called, **Then** the light (default) logo URL is returned.

---

### User Story 2 - Icon URL in Template (Priority: P1)

**Audience**: Developer

A developer wants to display a small application icon (e.g., favicon or sidebar icon) using the `icon_url` templatetag. They use it the same way as `logo_url` and receive an icon appropriate for the requested theme.

**Why this priority**: Icons and logos serve different visual roles (icon: compact, symbolic; logo: full brand mark). Both must be independently resolvable.

**Independent Test**: Can be tested by using `{% icon_url %}` in a template with an icon configured. Delivers the correct icon URL.

**Acceptance Scenarios**:

1. **Given** a light icon is configured, **When** `{% icon_url %}` is called, **Then** the icon URL is returned.
2. **Given** both light and dark icons are configured, **When** `{% icon_url theme="dark" %}` is called, **Then** the dark icon URL is returned.
3. **Given** no icon is configured, **When** `{% icon_url %}` is called, **Then** `None` or an empty string is returned without raising an error.

---

### User Story 3 - Per-User/Tenant Logo via Custom Resolver Function (Priority: P2)

**Audience**: Developer + End User

A developer building a multi-tenant SaaS app needs to display a different logo per logged-in company. They define a custom resolver function in their project settings that uses the `request` object to look up the current tenant's logo. The `logo_url` and `icon_url` templatetags call this function automatically, returning tenant-specific URLs.

**Why this priority**: Multi-tenant and white-label apps are a major use case for custom branding. The `request` parameter is the key enabler. Without it, the feature is incomplete for this audience.

**Independent Test**: Can be tested by configuring a custom resolver function in settings, logging in as different users with different logos, and calling `{% logo_url %}`. Each user sees their own logo.

**Acceptance Scenarios**:

1. **Given** a custom resolver function is registered in settings, **When** `{% logo_url %}` is called, **Then** the custom function is invoked with the request, height, and theme arguments.
2. **Given** the custom function returns a URL string, **When** rendered in a template, **Then** that URL is used as the logo source.
3. **Given** the custom function returns `None` or empty string, **When** rendered in a template, **Then** no error is raised; the output is empty or omitted.

---

### User Story 4 - Height Hint for Thumbnailing (Priority: P3)

**Audience**: Developer

A developer using a thumbnail/image processing library needs to serve optimally sized raster images. They implement a custom resolver function that uses the `height` parameter to return a URL to a resized image variant, rather than a full-resolution file.

**Why this priority**: This is a power-user extension point. It enables efficient image delivery but is not required for the feature to be usable.

**Independent Test**: Can be tested by writing a custom resolver that uses the `height` argument in the returned URL (e.g., a thumbnailing query parameter). Verifies the `height` value passed matches the value supplied in the template tag call.

**Acceptance Scenarios**:

1. **Given** `{% logo_url height=40 %}` is called, **When** the resolver function is invoked, **Then** it receives `height=40`.
2. **Given** `{% logo_url height=100 theme="dark" %}` is called, **When** the resolver is invoked, **Then** it receives `height=100` and `theme="dark"`.

---

### User Story 5 - Correct Branding for End Users in Multi-Tenant Apps (Priority: P2)

**Audience**: End User

A visitor to a white-label or multi-tenant application sees the correct brand identity — logo and icon matching their organisation's branding — without any additional action on their part.

**Why this priority**: This is the user-visible outcome that justifies the per-tenant resolver support in Story 3. Without it, the developer capability has no end-user value.

**Independent Test**: Can be tested by logging in as users from two different tenants in a browser and confirming that each sees their own organisation's logo in the page header.

**Acceptance Scenarios**:

1. **Given** two tenants (A and B) are configured with distinct logos, **When** a user from tenant A visits the application, **Then** tenant A's logo is displayed in the header.
2. **Given** two tenants (A and B) are configured with distinct logos, **When** a user from tenant B visits the application, **Then** tenant B's logo is displayed in the header.
3. **Given** a tenant has no logo configured, **When** a user from that tenant visits the application, **Then** a fallback logo is displayed without a broken image or rendering error.

---

### Edge Cases

- What happens when the resolver setting is absent? The built-in default resolver is used automatically with no error. What if the setting is present but the import path cannot be resolved? The system raises `ImproperlyConfigured` on first use.
- What happens when the resolver function raises an exception at runtime? The templatetag must not crash the page render; it returns an empty string silently. No logging is performed — custom resolvers are responsible for their own observability.
- What if an unrecognised `theme` value is passed (neither `"light"` nor `"dark"`)? The resolver receives it as-is; the default function falls back to the light logo.
- What if `request` is unavailable in the template context (e.g., RequestContext not used)? The templatetag must handle a `None` request gracefully and still attempt to return a URL using the default resolver.
- What if both `icon_url` and `logo_url` are called many times on a single page? The resolver function must be called each time (no implicit caching at the tag level) to support per-request tenant resolution; caching is the caller's responsibility.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide two templatetags, `logo_url` and `icon_url`, usable in Django templates without additional template configuration beyond loading the tag library.
- **FR-002**: Both templatetags MUST extract the `request` object automatically from the Django template context using `takes_context=True`. Template authors do NOT pass `request` explicitly; the tag reads it from the rendering context.
- **FR-003**: Both templatetags MUST accept an optional `theme` keyword argument (default: `"light"`).
- **FR-004**: Both templatetags MUST accept a required `height` keyword argument. Template authors MUST always supply a value (e.g., `{% logo_url height=40 %}`). There is no default; omitting `height` is a template error.
- **FR-005**: Both templatetags MUST delegate URL resolution to a callable resolver function.
- **FR-006**: The resolver function MUST be configurable via exactly two flat top-level settings keys: `MVP_LOGO_RESOLVER` and `MVP_ICON_RESOLVER`, each containing a dotted import path string to the callable (e.g., `"myapp.branding.get_logo_url"`).
- **FR-007**: When `MVP_LOGO_RESOLVER` or `MVP_ICON_RESOLVER` is absent from settings, the built-in default resolver MUST be used automatically with no error raised.
- **FR-008**: The default resolver MUST return a URL to a static file based on the requested theme.
- **FR-009**: The default resolver MUST fall back to the light-theme asset when only one asset is configured.
- **FR-010**: The default resolver MUST fall back to the light-theme asset for any unrecognised theme value.
- **FR-011**: All resolver functions — both built-in default and custom — MUST accept exactly the following arguments: `request`, `height`, and `theme`. This is a mandatory contract; custom functions that do not accept all three arguments are unsupported.
- **FR-012**: The templatetags MUST return an empty string (not raise an exception) when the resolver returns `None` or raises an exception. No logging is performed by the templatetag itself; custom resolver functions are responsible for their own error handling and observability.
- **FR-013**: The system MUST raise a clear, descriptive `ImproperlyConfigured` error when a setting is present but the dotted import path cannot be resolved — distinguishing this case from an absent setting, which silently uses the default resolver.
- **FR-014**: The default resolver functions handle theme selection internally; there are no additional project settings for individual light/dark static file paths. Developers who need different static assets configure them by supplying their own resolver function.
- **FR-015**: The feature MUST work without any additional required dependencies beyond Django itself for the default resolver path.
- **FR-016**: Both `logo_url` and `icon_url` MUST render the resolved URL as an inline string directly into the template output (e.g., `<img src="{% logo_url %}">`).
- **FR-017**: Both templatetags MUST return a plain string and rely on Django's standard auto-escaping. The tags MUST NOT call `mark_safe()` on the resolver's return value. An `as varname` form is explicitly out of scope for this iteration.

### Key Entities

- **Logo Resolver**: A callable (function) that receives `request`, `height`, and `theme`, and returns a URL string or `None`. Can be the built-in default or a developer-supplied custom function.
- **Icon Resolver**: Same contract as Logo Resolver but for icon assets.
- **Brand Asset Configuration**: A set of project settings keys that declare the static file paths for light/dark logo and icon variants, and optionally the resolver function import paths.
- **Theme**: A string value (typically `"light"` or `"dark"`) used to select the appropriate asset variant. The system treats it as an opaque value passed to the resolver, with `"light"` as the default.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can display a themed logo on a page by adding a single templatetag call — no custom Python code required for the SVG/static-file case.
- **SC-002**: Switching from a single-logo to a dual-theme (light/dark) setup requires only adding a new settings key and the additional asset — no template changes required.
- **SC-003**: A custom resolver function can be swapped in or out purely via a settings change — no template edits required.
- **SC-004**: A page using both `logo_url` and `icon_url` multiple times renders without errors when no custom resolver is configured and default assets are set.
- **SC-005**: A developer implementing a custom resolver for thumbnailing can receive and use the `height` argument within 1 hour of reading the documentation, based on a clearly defined function signature.
- **SC-006**: The templatetags produce no template rendering exceptions under any combination of valid inputs, including `None` request, missing assets, and unrecognised theme values.

---

## Assumptions

- Developers integrating this feature are using Django's standard template system with `RequestContext` (or equivalent) so the `request` object is available in templates via context processors.
- The default resolver handles only static file URL resolution and does not perform image manipulation; developers needing image resizing are expected to provide a custom resolver.
- "Light" is the canonical default theme; when only one asset is available, it is treated as the light variant.
- The feature does not manage or upload brand assets; it only resolves and returns their URLs.
- No caching layer is built into the templatetags themselves; resolver functions are called on every tag invocation.
- The `height` parameter is **required** in template calls — template authors must always supply it (e.g., `{% logo_url height=40 %}`). It is advisory from the resolver's perspective — the resolver receives it as a hint and may or may not use it (e.g., SVG resolvers typically ignore it; raster/thumbnailer resolvers use it to select a sized variant).
- A project will have at most one logo resolver and one icon resolver configured globally; per-template overrides are not a goal for this iteration.

## Clarifications

### Session 2026-05-28

- Q: How should the tag output the URL — inline string, `as varname`, or both? → A: Inline string only; `as varname` is out of scope for this iteration.
- Q: How should settings be structured — flat keys, single dict, or two dicts? → A: Exactly two flat top-level keys (`MVP_LOGO_RESOLVER`, `MVP_ICON_RESOLVER`); no separate light/dark path keys; custom functions MUST accept all three arguments (request, height, theme).
- Q: Should the templatetag log when a resolver raises an exception? → A: No logging; default resolver always succeeds (static files bundled in package); custom resolvers own their own observability.
- Q: Should the templatetag return `mark_safe()` or a plain string? → A: Plain string; Django auto-escaping applies as normal.
- Q: What happens when `MVP_LOGO_RESOLVER` / `MVP_ICON_RESOLVER` is not configured? → A: Built-in default resolver used silently; no error raised. Error only if a setting is present but the import path is invalid.
- Q: Should `request` be passed explicitly in the template or extracted from context? → A: Extracted automatically via `takes_context=True`; template authors write `{% logo_url %}` not `{% logo_url request %}`.
- The resolver function path in settings follows Django's standard dotted import string convention (e.g., `"myapp.branding.get_logo_url"`).
- Support for custom theme values beyond `"light"` and `"dark"` is a valid use case; the system passes the value through without validation.
