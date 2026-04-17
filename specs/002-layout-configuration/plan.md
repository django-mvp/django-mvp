# Implementation Plan: Fill Layout Configuration

**Branch**: `002-layout-configuration` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-layout-configuration/spec.md`

**Note**: This document extends the existing layout configuration system to document the `fill` layout mode that was developed in feature 006 (page-layout).

## Summary

The fill layout configuration is an all-in-one viewport-constrained layout mode where:

- App-wrapper is constrained to 100vh height with hidden scrollbars
- Scroll container changes from body/html to app-wrapper
- App-header and app-footer remain always visible (fixed)
- App-main scrolls independently between them
- Enables page-layout's internal toolbar-fixed/footer-fixed to work correctly

Primary use cases: Full-screen data-intensive UIs (tables, maps like maplibre, dashboards) requiring tight viewport fitting.

## Technical Context

**Language/Version**: Python 3.11 (django-mvp requirement)
**Primary Dependencies**: Django 5.1+, django-cotton (Cotton components), AdminLTE 4 (CSS/layout framework)
**Storage**: N/A (configuration-only feature, no data persistence)
**Testing**: pytest, pytest-django (component rendering), pytest-playwright (E2E UI verification)
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge) - server-side rendering with client-side CSS
**Project Type**: Django reusable app (single package with templates, static files, Demo App)
**Performance Goals**: <50ms page load impact from fill layout CSS, 60fps scrolling performance
**Constraints**: Must work with existing AdminLTE 4 CSS, no breaking changes to existing layout configurations
**Scale/Scope**: Single CSS variant (fill), 1 checkbox addition to demo form, documentation updates

**Current State**:

- Fill layout CSS already implemented in `mvp/static/scss/page-layout.scss` (lines 323-347)
- `<c-app>` component already accepts `fill` attribute in `mvp/templates/cotton/app/index.html`
- Layout demo page exists at `/layout/` but doesn't include fill checkbox yet
- Documentation doesn't mention fill layout

**What Needs Adding**:

- Fill checkbox in layout demo form template
- Documentation for fill layout (inline comments, public docs)
- E2E tests for fill layout behavior
- Update layout demo help text to explain fill mode

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ **Design-first approach is feasible and planned**: Fill layout CSS already exists; need to add UI controls and verify behavior
- ✅ **Visual verification approach is planned**: Will use chrome-devtools-mcp to verify fill checkbox appears and behavior changes correctly
- ✅ **Test types are identified**: pytest-playwright for E2E fill layout behavior (scroll container, viewport constraints, page-layout integration)
- ✅ **Documentation updates are included**: Will document fill attribute, use cases, and behavior changes
- ✅ **Quality gates are understood**: pytest + ruff lint + ruff format required before merge
- ✅ **Documentation retrieval is planned**: Using context7 for django-cotton and AdminLTE best practices
- ✅ **End-to-end testing is planned**: Playwright tests will verify full user workflow of enabling fill via demo form

**Status**: ✅ PASS - All gates satisfied. Feature is low-risk extension of existing layout system.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
mvp/                                    # Django reusable app (package)
├── static/
│   └── scss/
│       └── page-layout.scss            # EXISTING: Fill layout CSS (lines 323-347)
├── templates/
│   └── cotton/
│       └── app/
│           └── index.html              # EXISTING: <c-app> component with fill attribute
└── ...

demo/                                # Demo Django app
├── templates/
│   └── demo/
│       └── layout.html                 # MODIFY: Add fill checkbox to form
├── views.py                            # MODIFY: Handle fill query param
└── urls.py                             # EXISTING: /layout/ route

tests/
├── e2e/
│   └── test_fill_layout_e2e.py         # NEW: Playwright tests for fill behavior
└── integration/
    └── test_layout_demo.py             # MODIFY: Update assertions for fill checkbox

docs/
└── layout-configuration.md             # NEW or MODIFY: Document fill layout
```

**Structure Decision**: Django reusable app with Demo App for demo/testing. Fill layout is a CSS-driven feature requiring minimal template changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| N/A | N/A | N/A |

**Status**: No constitution violations. Feature follows established patterns.

---

## Phase 0: Research & Dependencies

**Objective**: Resolve all "NEEDS CLARIFICATION" items from Technical Context. Generate `research.md` with decisions, rationale, and alternatives considered.

**Current Status**: ✅ COMPLETE - No research needed. Fill layout CSS already implemented and tested via DevTools inspection during spec clarification (Session 2026-01-20).

### Key Findings

1. **Fill Layout CSS Implementation** (VERIFIED)
   - **Location**: `mvp/static/scss/page-layout.scss` lines 323-347
   - **Behavior**: Sets `.app-wrapper.fill` to `height: 100vh`, `overflow: auto` with hidden scrollbars
   - **Effect**: Scroll container moves from body/html to app-wrapper
   - **Integration**: Makes `.app-main` scrollable while header/footer fixed

2. **Component Integration** (VERIFIED)
   - **Template**: `mvp/templates/cotton/app/index.html` already accepts `fill` attribute
   - **Usage**: `<c-app fill>` applies `.fill` class to `.app-wrapper`
   - **Compatibility**: Works alongside other layout attributes (though overrides their behavior)

3. **Layout Demo Page** (EXISTING)
   - **Route**: `/layout/` in Demo App
   - **View**: `demo/views.py` handles query params for layout configuration
   - **Template**: `demo/templates/demo/layout.html` contains configuration form
   - **Gap**: Form doesn't include fill checkbox yet

4. **Testing Approach** (PLANNED)
   - **E2E Tests**: Use playwright to verify scroll container change, viewport constraints
   - **Integration Tests**: Verify form includes fill checkbox and handles query param
   - **No Unit Tests Needed**: Pure CSS/template feature, no Python logic

### Dependencies

- **django-cotton**: ✅ Already in use for `<c-app>` component
- **AdminLTE 4 CSS**: ✅ Already integrated, fill layout extends existing CSS
- **pytest-playwright**: ✅ Already configured for E2E tests
- **No New Dependencies**: Feature uses existing stack

### research.md

Since no clarifications were needed and implementation already exists, `research.md` is minimal:

```markdown
# Research: Fill Layout Configuration

## Decision Summary

**Decision**: Document and add UI controls for the existing fill layout CSS implementation developed in feature 006 (page-layout).

**Rationale**: Fill layout CSS (`mvp/static/scss/page-layout.scss`) was created to support viewport-constrained scrolling for data-intensive interfaces like tables and maps. It's already functional and tested via manual DevTools inspection. This spec documents it and adds it to the layout demo page for easier testing and discovery.

**Alternatives Considered**:
1. **Create separate demo page** - Rejected: Goes against FR-019 (single consolidated demo page)
2. **Make fill exclusive radio option** - Rejected: Fill can technically combine with fixed attributes even though it overrides them
3. **Implement as Django setting** - Rejected: Should be per-page decision via template, not global config

## Implementation Notes

- CSS already complete and verified
- Only need to add checkbox to layout demo form
- E2E tests will verify the full user workflow
- Documentation will explain use cases and behavior
```

---

## Phase 1: Design & Contracts

**Objective**: Generate data models, API contracts, and quickstart guide for the feature.

### data-model.md

Since this is a UI/CSS feature with no data persistence, the data model is the configuration structure:

```markdown
# Data Model: Fill Layout Configuration

## Configuration Structure

Fill layout is controlled by a boolean attribute on the `<c-app>` Cotton component:

```django-html
<c-app fill>
  <!-- app content -->
</c-app>
```

### Attributes

| Attribute | Type | Default | Description |
| --- | --- | --- | --- |
| `fill` | boolean | `false` | Enables viewport-constrained layout mode |

### CSS Classes Applied

When `fill` is present:

```html
<div class="app-wrapper fill">
  <!-- layout structure -->
</div>
```

### Behavior Changes

| Aspect | Without Fill | With Fill |
| --- | --- | --- |
| App Wrapper Height | Auto (content-driven) | `100vh` (viewport-constrained) |
| Scroll Container | `<html>` / `<body>` | `.app-wrapper` |
| Scrollbar Visibility | Default browser scrollbars | Hidden (scrollbar-width: none) |
| App Header | Scrolls with content | Fixed at top (always visible) |
| App Footer | Scrolls with content | Fixed at bottom (always visible) |
| App Main | No independent scroll | Scrolls between header/footer |

### Query Parameter Format (Demo Page)

Layout demo form uses GET request with query params:

```
/layout/?fill=on&fixed_header=on&...
```

Parameters:

- `fill`: "on" (present) or absent (not checked)
- Combines with: `fixed_header`, `fixed_sidebar`, `fixed_footer`, `sidebar_breakpoint`

## Integration Points

1. **Cotton Component**: `<c-app>` component in `mvp/templates/cotton/app/index.html`
2. **CSS**: `.app-wrapper.fill` selector in `mvp/static/scss/page-layout.scss`
3. **Demo View**: `demo/views.py` layout demo view handles `fill` query param
4. **Demo Template**: `demo/templates/demo/layout.html` renders fill checkbox

## Validation Rules

- Fill is a boolean attribute (present or absent, no value)
- Fill can be combined with other layout attributes but takes precedence
- Fill requires viewport height to work (doesn't make sense in print media)

## State Diagram

```
┌─────────────┐
│ Default     │
│ Layout      │
│ (no fill)   │
└──────┬──────┘
       │ User adds fill attribute
       ▼
┌─────────────┐
│ Fill Layout │ ◄─┐
│ (fill=true) │   │ User toggles checkbox
└──────┬──────┘   │
       │          │
       └──────────┘
```

No persistent state - configuration is per-request via template/query params.

```

### contracts/

No API contracts needed - this is a template-driven feature with no backend API.

### quickstart.md

```markdown
# Quickstart: Fill Layout

## Overview

Fill layout constrains your Django MVP application to viewport height (100vh) with hidden scrollbars, moving the scroll container from the browser body to the app-wrapper. This is ideal for data-intensive interfaces like tables, maps, and dashboards.

## Basic Usage

### 1. Add fill attribute to base template

```django-html
{# templates/base.html #}
{% extends "mvp/base.html" %}

{% block app %}
  <c-app fill>
    {% block app_header %}
      {# Your header content #}
    {% endblock %}

    {% block app_main %}
      {# Your scrollable content here #}
    {% endblock %}

    {% block app_footer %}
      {# Your footer content #}
    {% endblock %}
  </c-app>
{% endblock %}
```

### 2. Your content will now fill viewport height

- Header stays fixed at top
- Footer stays fixed at bottom
- Main content scrolls between them
- No body-level scrolling

## Use Cases

### Data Tables

```django-html
<c-app fill>
  {% block app_main %}
    <table class="table">
      {# Large dataset that needs viewport-constrained scrolling #}
    </table>
  {% endblock %}
</c-app>
```

### Interactive Maps

```django-html
<c-app fill>
  {% block app_main %}
    <div id="map" style="height: 100%;"></div>
    <script>
      // maplibre or other map library
      // Map will fill available space between header/footer
    </script>
  {% endblock %}
</c-app>
```

### With Page Layout Grid

Fill enables page-layout's internal fixed positioning:

```django-html
<c-app fill>
  {% block app_main %}
    <c-page.index toolbar_fixed footer_fixed>
      <c-page.toolbar>
        {# This toolbar stays fixed during page-content scroll #}
      </c-page.toolbar>

      <c-page.content>
        {# Scrollable content #}
      </c-page.content>

      <c-page.footer>
        {# This footer stays fixed during page-content scroll #}
      </c-page.footer>
    </c-page.index>
  {% endblock %}
</c-app>
```

## Testing Fill Layout

Visit the layout demo page to interactively test fill:

```
http://localhost:8000/layout/?fill=on
```

Toggle the "Fill Layout" checkbox and scroll to see the behavior change.

## Technical Details

**CSS Applied**:

```css
.app-wrapper.fill {
  height: 100vh;
  overflow: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

.app-wrapper.fill::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.app-wrapper.fill .app-main {
  min-height: 0;
  overflow: auto;
}
```

**Browser Compatibility**: Works in all modern browsers (Chrome, Firefox, Safari, Edge).

## Relationship to Fixed Attributes

Fill can be combined with `fixed_header`, `fixed_sidebar`, `fixed_footer`, but fill's behavior takes precedence:

```django-html
{# These are equivalent when fill is present #}
<c-app fill>
<c-app fill fixed_header fixed_footer>
```

When fill is enabled:

- App-header is always fixed at top
- App-footer is always fixed at bottom
- Individual fixed attributes don't change this behavior

## When NOT to Use Fill

❌ **Don't use fill for**:

- Blog posts or documentation pages (natural content flow is better)
- Forms with variable content length (body scrolling works fine)
- Print layouts (100vh doesn't translate to print)

✅ **DO use fill for**:

- Dashboards with fixed chrome
- Data tables with many rows
- Interactive maps or visualizations
- Split-pane interfaces
- Any UI that benefits from viewport-constrained scrolling

```

### Agent Context Update

Agent context has been updated successfully:

```

✓ Updated existing GitHub Copilot context file

- Added language: Python 3.11 (django-mvp requirement)
- Added framework: Django 5.1+, django-cotton, AdminLTE 4
- Added database: N/A (configuration-only feature)

```

---

## Phase 2: Task Breakdown

**Status**: NOT STARTED - Run `/speckit.tasks` to generate tasks.md

Phase 2 task breakdown will include:

1. **Template Changes**:
   - Add fill checkbox to layout demo form
   - Update form submission to include fill parameter
   - Update help text to explain fill mode

2. **View Logic**:
   - Handle fill query parameter in layout demo view
   - Pass fill boolean to template context

3. **E2E Tests**:
   - Test fill checkbox interaction
   - Verify scroll container changes
   - Test viewport constraint behavior
   - Test combination with fixed attributes
   - Test page-layout integration

4. **Documentation**:
   - Add fill layout section to docs
   - Document use cases (tables, maps, dashboards)
   - Explain relationship to fixed attributes
   - Add code examples

5. **Verification**:
   - Cross-browser testing
   - Responsive behavior verification
   - Performance testing (60fps scroll)

**Next Command**: `/speckit.tasks` to generate detailed task breakdown with acceptance criteria.

---

## Summary & Status

**Branch**: `002-layout-configuration`

**Feature**: Fill Layout Configuration Documentation

**Current Phase**: ✅ Phase 1 COMPLETE (Design & Contracts)

**Generated Artifacts**:

- ✅ plan.md - This file (implementation plan)
- ✅ research.md - Already exists (from previous planning)
- ✅ data-model.md - Already exists (from previous planning)
- ✅ quickstart.md - Already exists (from previous planning)
- ⏳ tasks.md - Generate with `/speckit.tasks`

**Constitution Check**: ✅ PASS (re-verified post-design)

- ✅ Design-first workflow followed (CSS already exists, adding UI controls)
- ✅ Visual verification planned (chrome-devtools-mcp for form/behavior)
- ✅ Test types identified (playwright for E2E)
- ✅ Documentation updates scoped
- ✅ Quality gates understood
- ✅ Context7 used for dependency docs
- ✅ End-to-end testing planned

**Key Technical Decisions**:

1. ✅ Extend existing layout demo form (not separate page) - follows FR-019
2. ✅ Add fill as checkbox (not radio) - allows showing override behavior
3. ✅ Use query parameters for state - keeps demo bookmarkable
4. ✅ Playwright for E2E testing - verifies full user workflow
5. ✅ Document fill as all-in-one layout mode - clarifies relationship to fixed attrs

**Risks & Mitigation**:

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Fill behavior unclear to users | Medium | Medium | Comprehensive documentation + help text in demo |
| Combination with fixed attrs confusing | Medium | Low | Document that fill overrides, show in demo |
| Cross-browser scrollbar inconsistencies | Low | Low | Already handled by CSS (-webkit, -moz, -ms) |
| Performance issues with nested scroll | Low | Medium | E2E tests verify 60fps requirement (SC-006) |

**Ready for Implementation**: ✅ YES

All design and planning complete. Ready to generate tasks and begin implementation.
