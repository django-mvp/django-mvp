# Implementation Plan: Mount one django-mvp app inside another

**Branch**: `032-mounted-apps` | **Date**: 2026-09-25 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `/specs/032-mounted-apps/spec.md`

## Summary

A new module, `mvp/mounted.py`, holds one class, `MountedApp`, and a `mount(route, app,
main=False)` function the host calls in its `urls.py`. `mount()` returns a `URLResolver`
subclass whose `resolve()` marks the matched view with its app, and runs the app's check before
the view. The set of mounted apps is read back from the URL tree, not collected at import, and a
system check refuses a duplicate mount, a nested mount and a second main app. A template tag
resolves the current app once in `mvp/base.html`. The sidebar draws that app's menu under a
"Back to <site name>" link, and the title gains the app's name. `mvp.urls` mounts the Account
Center, and its layout loses the second navigation panel. A page an app's menu marks as current
also belongs to that app, which is how contributed Account Center pages join it unchanged.
Research R1–R10 records each choice.

## Technical Context

**Language/Version**: Python 3.12+ / Django 5.2+ (CI matrix 3.12/3.13 × 5.2/6.0).

**Primary Dependencies**: Django URL resolution (`URLResolver`, `ResolverMatch`), the checks
framework, `django-flex-menus` (already a dependency). No new dependency.

**Storage**: N/A. No model, no migration.

**Testing**: pytest + pytest-django. A test-only mounted app (`tests/testapp_mounted/`) with two
pages and its own menu, mounted through test URLconfs, the way a host does. Rendered-markup
assertions via BeautifulSoup. No browser test: nothing here is a claim about computed layout
(Article XIV).

**Target Platform**: The published package and its demo project.

**Constraints**: A project that mounts no app renders every page as before (FR-010, SC-004).
Existing `resolve(...).func.view_class` assertions keep passing (R3). No new runtime dependency.

**Scale/Scope**: One new module (`mvp/mounted.py`, ~200 lines), one template tag and one filter,
edits to three shell templates and the Account Center layout, `mvp.urls` mounting the Account
Center. One docs page, glossary entries, a skill routing row, a changelog entry, a demo app.

## Constitution Check

| Article | How this plan satisfies it |
|---|---|
| I — Test-First | Every task names its failing test first. The no-app title and sidebar are pinned before the templates change (T002). |
| II — Simplicity | One class, one function, one tag. The registry is derived from the URL tree rather than maintained. |
| III — Anti-Abstraction | `MountedAppResolver` exists because Django's `path()` cannot mark a match (R3). No base class for apps, no registry object. |
| IV — Integration-First | Tests mount a real test app through a test URLconf and request its pages through the client. |
| V — Security | The check refuses before the view runs, as Django's access mixins do (R6). The title filter `conditional_escape()`s the app name, because `{% filter %}` output is not autoescaped (SEC-002). Error pages carry no app name, so a refused person does not learn it from the title. |
| VI — Documentation | `docs/mounted-apps.md` lands with US-1 and each later story adds its section. Docstrings on every public name. |
| VIII — i18n | "Back to %(site_name)s" is translatable. The app's name is the package's own lazy string. |
| XI — Components are public API | `<c-app.sidebar>` keeps every attribute. `menu` loses its literal default, and an explicit value still wins (R5). |
| XIII — Rendered markup is a contract | The back link, the title and the sidebar menu are asserted exactly. |
| XV — Build artifacts | The stylesheet is rebuilt if the back link uses a class it lacks (FR-027). |
| XVI — Compatibility | Pre-1.0. The Account Center's layout change and `menu`'s default are changelog entries. |
| XVII — Cohesion | Declaration, menu entry, check and lookup share one subject and live on `MountedApp`. `mount()` is a thin wrapper. |
| XVIII — One corpus | `docs/mounted-apps.md` is the single page, and the skill's routing table points at it. `docs/account-center.md` and `docs/navigation.md` are corrected where they describe the panel. |

## Project Structure

```text
mvp/
  mounted.py                         # MountedApp, MountedAppResolver, mount(), the system check
  apps.py                            # import the check in ready()
  urls.py                            # mount("account/", account_center)
  views/account.py                   # account_center declaration
  menus.py                           # AccountCenterMenu docstring: now the app's sidebar menu
  templatetags/mvp.py                # {% mounted_app %}, the title filter
  templates/mvp/base.html            # resolve once, title filter
  templates/mvp/error_base.html      # title with no app segment
  templates/cotton/app/sidebar/index.html   # resolved menu, back link
  templates/cotton/app/sidebar/back.html    # the back link (new)
  templates/mvp/account/base.html    # a container around account.content
  templates/mvp/account/overview.html
demo/library/ (new), demo/urls.py, demo/menus.py, demo/settings.py
docs/mounted-apps.md (new), docs/index.md, docs/account-center.md, docs/navigation.md,
docs/layout.md, CONTEXT.md, CHANGELOG.md, skills/django-mvp/SKILL.md
tests/testapp_mounted/ (new: apps, urls, views, menus, mounted, templates)
tests/urls_mounted*.py (new test URLconfs)
tests/test_mounted.py                # mirrors mvp/mounted.py
tests/test_templatetags.py, tests/test_views/test_account.py, tests/test_components/…
```

## Story order

Sequential, one worktree: **US-1 → US-2 → US-3 → US-4.** Every story edits `mvp/mounted.py`, the
sidebar template and `docs/mounted-apps.md`. US-2 adds the menu-membership rule (R7), which US-3
must skip for the main app. US-4 fills in the wrapper's check, which exists from US-1.

## Complexity Tracking

| Addition | Why the simpler option fails |
|---|---|
| `MountedAppResolver` (a `URLResolver` subclass) | `path(route, include(...))` builds a plain resolver, and no other hook sees the matched view with a request in hand (R3). |
