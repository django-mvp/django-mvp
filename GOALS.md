# Goals

These are the standing directions `django-mvp` works toward. Each one is a capability or
quality to steer by, not a task that gets ticked off. Whether any goal has been served well enough
is decided in the roadmap, the feature specs, and review, never by the goal itself.

This file carries no version numbers or release plan; that lives in the roadmap. For what the
package is, what it stays out of, and the principles that settle a close call, read the
*Scope & philosophy* section of the [README](README.md).

Importance is a tag on each goal, not a ranking:

- **Essential** — not worth adopting without it.
- **Expected** — a complete, dependable version is expected to have it.
- **Aspirational** — a genuine want whose absence never makes the package incomplete.

| ID | Goal | Importance | Status | Notes |
|----|------|------------|--------|-------|
| G1 | A complete, responsive application shell that a project configures rather than builds | Essential | | |
| G2 | A component library covering what a data-centric web application needs, with small attribute APIs and deliberately limited variation | Essential | | |
| G3 | A short path from a Django model to a working set of pages, configured declaratively rather than written by hand | Essential | | |
| G4 | A usable front end for the Django features that ship backend machinery without one | Essential | | |
| G5 | A polished, modern look and feel out of the box | Essential | | |
| G6 | No front-end build tooling required to use the package | Essential | | |
| G7 | Customization that never dead-ends, from view configuration through component override to a project's own CSS | Essential | | |
| G8 | Theming and branding without forking templates | Expected | | |
| G9 | Documentation and a demo application that show every component in use | Expected | | |
| G10 | A consistent UI around the third-party packages projects already rely on, without extending or replacing them | Expected | | |
| G11 | A recorded, predictable public surface that becomes safe to depend on across releases | Expected | | |
| G12 | A hosted demo where the components can be browsed and copied without installing anything | Aspirational | | |
| G13 | Integrations beyond the packages currently relied on, as projects or adopters need them | Aspirational | | |

_Written 2026-08-03. Revise as the goals change._
