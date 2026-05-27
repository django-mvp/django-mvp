# Feature Specification: Vendored Theme Variable Overrides

**Feature Branch**: `018-vendor-adminlte-scss`
**Created**: 2026-05-26
**Status**: Refined
**Refined**: 2026-05-26 — UI verification tasks changed from Playwright MCP server to playwright-cli skill
**Refined**: 2026-05-27 — Renamed `_mvp_variables.scss` → `_bootstrap_variables.scss` and `_mvp_lte_variables.scss` → `_adminlte_variables.scss`; added second AdminLTE variable override hook (`_adminlte_variables.scss`) for vars that reference Bootstrap tokens; moved both override files from `mvp/static/scss/` to `mvp/static/` to enable include-path resolution for app-level overrides.
**Refined**: 2026-05-27 — Added User Story 4 and FR-013: the demo app must include a live demo page that shows downstream developers how to override SCSS variables in their own project.
**Refined**: 2026-05-27 — Demo page titled "Theme Customization"; registered as a top-level sidebar menu item; breadcrumbs are two levels: Home → Theme Customization.
**Input**: User description: "All apps are different and require their own themes, styles, colors, etc. The best way to do this is through customization of scss variables. To provide the simplest solution for downstream developers, we are going to simply vendor the adminlte scss stylesheets and allow users to provide their own variable overrides via a _mvp_variables.scss file."

## Clarifications

### Session 2026-05-26

- Q: How should AdminLTE dependency versioning behave during vendor refresh? -> A: Install the latest using npm and let the lockfile pin the version.
- Q: What refresh strategy should be used for vendored SCSS files? -> A: Delete existing vendored SCSS directory, then copy a fresh AdminLTE SCSS tree.
- Q: What variable load order should be enforced for overrides? -> A: Load `_bootstrap_variables.scss` before Bootstrap and AdminLTE defaults; load `_adminlte_variables.scss` after Bootstrap variables but before AdminLTE `_variables.scss`, so downstream apps can override both Bootstrap tokens and AdminLTE vars that reference those tokens.
- Q: What toolchain should compile the SCSS sources? -> A: Use django-compressor and django-libsass.

## User Scenarios & Testing *(mandatory)*

### User Story 1 [Developer] - Configure App Theme Quickly (Priority: P1)

**Audience**: Developer

A downstream developer can create and apply an app-specific visual theme by editing a single variables override file, without needing to edit core vendored style sources.

**Why this priority**: This is the core value of the feature: enabling fast, low-friction customization for different app brands and visual systems.

**Independent Test**: Can be fully tested by changing a set of color and spacing variables in the override file and confirming those theme changes appear across the app while vendor style files remain unchanged.

**Acceptance Scenarios**:

1. **Given** a project that uses the vendored base styles, **When** a developer defines custom theme variables in the override file, **Then** the generated styles reflect those overrides throughout the app UI.
2. **Given** a project with no variable overrides defined, **When** styles are built, **Then** the default vendored theme is applied consistently.

---

### User Story 2 [Developer] - Keep Upstream Style Updates Safe (Priority: P2)

**Audience**: Developer

A maintainer can update vendored base styles without manually reapplying local theme customizations.

**Why this priority**: Long-term maintainability depends on separating custom app branding from vendored source updates.

**Independent Test**: Can be tested by applying local overrides, performing a vendor stylesheet refresh, and confirming local overrides still apply without merge conflicts in customized files.

**Acceptance Scenarios**:

1. **Given** existing local variable overrides, **When** vendored base styles are updated, **Then** local override definitions are preserved and continue to drive app-specific theming.
2. **Given** a vendor update introduces new configurable variables, **When** the developer adds values for them in the override file, **Then** those new values apply without requiring edits to vendor files.

---

### User Story 3 [End User] - Onboard New Teams Faster (Priority: P3)

**Audience**: End User

A new downstream team can understand where and how to apply branding changes with minimal setup and reduced styling mistakes.

**Why this priority**: Documentation and predictable override behavior reduce support load and speed adoption.

**Independent Test**: Can be tested by giving a new team member the theming instructions and measuring whether they can make a branded style change in one pass using only the override workflow.

**Acceptance Scenarios**:

1. **Given** documented theming steps, **When** a new developer follows those steps, **Then** they can make a visible brand change using the override file without editing vendor sources.

---

### User Story 4 [Developer] - Demo Override Workflow In-App (Priority: P4)

**Audience**: Developer

A downstream developer can visit a demo page in the running application that shows, with live examples, how to set up SCSS variable overrides in their own project.

**Why this priority**: Static documentation alone is not enough — a live, interactive demo page lets developers see the actual effect of overrides in context and copy working code snippets directly from the app they are running.

**Independent Test**: Can be fully tested by opening the demo page in a browser and confirming it renders working code examples for both override entrypoints, displays the current active overrides, and links to the relevant documentation.

**Acceptance Scenarios**:

1. **Given** the demo app is running, **When** a developer navigates to the SCSS variables demo page, **Then** they see live code examples for `_bootstrap_variables.scss` and `_adminlte_variables.scss` showing how to override common variables.
2. **Given** the demo page is displayed, **When** the developer reads the page, **Then** they understand the INSTALLED_APPS ordering requirement for app-level overrides without needing to consult external documentation.
3. **Given** the demo page is displayed, **When** the developer views the active theme, **Then** the page renders using the currently active override values so they can see the effect of customization.

---

### Edge Cases that are used by the vendored theme? The system should fall back to default vendor-provided values without build failure

- How does the system handle invalid override values (for example malformed color or unit values)? The build should fail with actionable diagnostics that identify the invalid variable.
- What happens when two apps in the same organization require significantly different themes? Each app should be able to provide its own override file values without cross-app leakage.
- How does the system behave when a vendor update removes or renames variables that an app still overrides? The mismatch should be detectable so maintainers can reconcile deprecated overrides.
- What happens when upstream removes or renames SCSS files between AdminLTE releases? The refresh process should remove previously vendored files before copying new sources so stale files are not retained.
- What happens when SCSS compilation fails inside django-compressor or django-libsass? The build should surface actionable diagnostics so maintainers can fix the source or override value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include vendored base stylesheet sources so app themes do not depend on runtime access to upstream external style repositories.
- **FR-002**: System MUST support app-level variable overrides through two dedicated files: `_bootstrap_variables.scss` (for Bootstrap tokens and plain AdminLTE variables) and `_adminlte_variables.scss` (for AdminLTE variables that reference Bootstrap tokens).
- **FR-003**: System MUST produce final compiled theme output that applies downstream override values without requiring edits to vendored source files.
- **FR-004**: System MUST preserve the separation between vendored base styles and app-specific overrides, allowing developers to customize themes without modifying vendored files.
- **FR-005**: System MUST allow builds to succeed when no custom override file values are provided, using default vendored values.
- **FR-006**: System MUST provide clear failure feedback when override variable values are invalid.
- **FR-007**: System MUST allow vendored style source updates without overwriting or removing downstream app override definitions.
- **FR-008**: System MUST provide guidance that identifies the intended customization entry point and warns against editing vendored files directly.
- **FR-009**: Delivery plan MUST include a repeatable vendor refresh task that installs the latest AdminLTE 4 package via npm, relies on the committed lockfile to pin the resolved version, and copies the SCSS source files into `mvp/static/adminlte/scss` as the canonical vendored source location.
- **FR-010**: Vendor refresh MUST replace the full vendored SCSS source directory (delete then copy) to prevent stale upstream files from persisting across updates.
- **FR-011**: Build ordering MUST load `_bootstrap_variables.scss` before Bootstrap and AdminLTE `!default` declarations, and MUST load `_adminlte_variables.scss` after Bootstrap variables are resolved but before AdminLTE's own `_variables.scss`, so downstream apps can override both Bootstrap design tokens and AdminLTE variables that reference those tokens.
- **FR-012**: SCSS compilation MUST use django-compressor and django-libsass so the vendored AdminLTE sources, `_bootstrap_variables.scss`, and `_adminlte_variables.scss` are processed through the project build pipeline.
- **FR-013**: The demo app MUST include a dedicated demo page titled "Theme Customization" that provides live, in-app guidance on how downstream developers can override SCSS variables in their own project, covering both `_bootstrap_variables.scss` and `_adminlte_variables.scss` entrypoints and the INSTALLED_APPS ordering convention. The page MUST be registered as a top-level sidebar menu item and MUST display two-level breadcrumb navigation (Home → Theme Customization).

### Key Entities *(include if feature involves data)*

- **Vendored Base Styles**: The imported upstream stylesheet source set that provides default visual tokens and component styling.
- **Bootstrap Override File**: The downstream app-owned `_bootstrap_variables.scss` input (at `mvp/static/`) where developers define Bootstrap design token overrides and plain AdminLTE variable values. Resolved via Sass include paths so app-level overrides shadow the default by INSTALLED_APPS order.
- **AdminLTE Override File**: The downstream app-owned `_adminlte_variables.scss` input (at `mvp/static/`) where developers define AdminLTE variables that reference Bootstrap tokens (e.g. `$lte-sidebar-color: $gray-800`). Injected into `adminlte.scss` after Bootstrap vars are resolved but before AdminLTE defaults fire.
- **Effective Theme Output**: The final resolved style output produced by combining vendored defaults with downstream overrides.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of tested downstream apps can change primary brand colors and typography scale by editing only the override file.
- **SC-002**: At least 90% of first-time downstream developers can complete a requested theme change in under 15 minutes using documented instructions.
- **SC-003**: Vendor stylesheet refreshes require zero manual reapplication of app-specific theme changes in at least 95% of update attempts.
- **SC-004**: Theme build failures caused by invalid override values provide diagnostics that identify the problematic variable in 100% of sampled failures.

## Assumptions

- Downstream applications already use the existing project style build process and can include two app-owned override variable files: `_bootstrap_variables.scss` and `_adminlte_variables.scss`.
- Two override files per downstream app cover all override scenarios for the initial release: Bootstrap tokens and AdminLTE variables that reference those tokens.
- Override files are placed at the app's static root (not a subdirectory) so Sass include-path resolution can find them when that app is listed before `mvp` in INSTALLED_APPS.
- Teams prefer stable defaults and only override the subset of variables needed for branding.
- The demo app will include a dedicated page for SCSS variable override guidance so downstream developers can learn the workflow from the running application.
- Planning and implementation will include an explicit task to refresh vendored styles by installing the latest AdminLTE 4 npm package, relying on the lockfile to pin the resolved version, and copying SCSS sources into `mvp/static/adminlte/scss`.
- Vendor refresh patches the vendored `adminlte.scss` to inject the `_adminlte_variables` override hook before AdminLTE's own `_variables.scss` import.
- Vendor refresh is a full replacement operation of the vendored SCSS directory, not an in-place merge.
- AdminLTE SCSS token defaults are compatible with pre-import variable overrides from `_bootstrap_variables.scss` and post-Bootstrap-resolution overrides from `_adminlte_variables.scss`.
- The project build pipeline will compile SCSS through django-compressor and django-libsass.
