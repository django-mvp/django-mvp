# Implementation Plan: Installable app

**Branch**: `031-installable-app` | **Date**: 2026-09-24 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `/specs/031-installable-app/spec.md`

## Summary

A new `mvp/pwa/` package serves a web app manifest and a service worker from a URLconf the
project mounts at its root. `base.html` includes one overridable head template when
`MVP_CONFIG["pwa"]["enabled"]` is true. With it off, the page head is byte-identical to today's.
The manifest's name comes from the current site, and its colours come from the prebuilt daisyUI
themes' `base-100` colour, read from the committed stylesheet. Its images come from four PNGs
rendered by a new `mvp_pwa_icons` management command. The command uses an optional `resvg-py`
dependency. Two system checks warn when the feature is on but the root include or the images
are missing. Research R1–R9 records each choice.

## Technical Context

**Language/Version**: Python 3.12+ / Django 5.2+ (CI matrix 3.12/3.13 × 5.2/6.0).

**Primary Dependencies**: Django (`contrib.sites.shortcuts`, `contrib.staticfiles.finders`,
system checks). No new runtime dependency. `resvg-py` joins the **test** group and is imported
lazily by the command only (R5).

**Storage**: N/A. No model, no migration.

**Testing**: pytest + pytest-django. Rendered-markup assertions via BeautifulSoup as elsewhere.
PNG assertions read the image header for dimensions (Pillow is not needed: width and height are
bytes 16–24 of a PNG). No browser test, because nothing here is a claim about computed layout
(Article XIV).

**Target Platform**: The published package and its demo project.

**Constraints**: The page head is byte-identical with the feature off (SC-002). Nothing is
fetched from a third party (FR-018, Article XV). The runtime dependency set does not grow
(Article VII).

**Scale/Scope**: One new subpackage (config resolution, colours, two views, URLconf, checks). Two templates, one template tag, one management command, one docs page, a glossary
entry, and demo wiring.

## Constitution Check

| Article | How this plan satisfies it |
|---|---|
| I — Test-First | Every task names its failing test first. The golden-file test for the off state is written before `base.html` is touched. |
| II — Simplicity | One resolver function feeds both the manifest and the head. The worker is two event listeners. No settings hook beyond a URL string. |
| III — Anti-Abstraction | No base view class, no registry. Two function views. |
| IV — Integration-First | Tests mount `mvp.pwa.urls` at the root of a test URLconf, the same way a project does, and request real URLs through the test client. |
| V — Security | Every configured value reaches JSON through `JsonResponse` and reaches HTML through autoescape or `json_script`. A test feeds a name containing `</script>`, `"` and `&` through both. The worker caches nothing, so it cannot serve one user's response to another. |
| VI — Documentation | Each story documents what it introduces, in the same story (new page `docs/installable-app.md`, keys in `docs/configuration.md`, glossary in `CONTEXT.md`). |
| VII — Dependencies | `resvg-py` is test-group only and lazily imported. Its absence raises a message naming it. `deptry` stays clean with a reasoned `DEP001` entry. |
| VIII — i18n | Nothing a site visitor reads is hard-coded. The application name is project data. Command and check messages are developer-facing and follow the existing command's practice. |
| XI — Components are public API | No new component. The head template is an overridable template, not a component (ADR 0026). |
| XII — Configuration-driven layout | Everything is set through `MVP_CONFIG["pwa"]`. |
| XIII — Rendered markup is a contract | The head tags and the manifest keys are asserted exactly. |
| XV — Build artifacts | No new artifact. Theme colours are read from the committed stylesheet (research R4). |
| XVI — Compatibility | Off by default. No existing key or template path changes. |

## Project Structure

```text
mvp/
  apps.py                         # ready() imports mvp.pwa.checks
  config.py                       # new "pwa" defaults block
  pwa/
    __init__.py                   # resolve(request) → name, short_name, start_url, scope,
                                  #   display, theme_color, background_color, worker_url, icons
    colors.py                     # theme colours from the committed stylesheet (R4)
    urls.py                       # manifest.webmanifest, sw.js
    views.py                      # manifest(), service_worker()
    checks.py                     # mvp.W001, mvp.W002
  management/commands/mvp_pwa_icons.py
  templates/mvp/base.html         # one include, on an existing line (R8)
  templatetags/mvp.py             # the mvp_pwa simple tag (R8)
  templates/mvp/pwa/head.html
  templates/mvp/pwa/sw.js
demo/settings.py, demo/urls.py, demo/static/brand/pwa/*.png
docs/installable-app.md, docs/index.md, docs/configuration.md, CONTEXT.md, README.md, CHANGELOG.md
tests/test_pwa/  test_init.py test_colors.py test_views.py test_urls.py test_checks.py
tests/test_management/test_commands/test_mvp_pwa_icons.py   # mirrors the source path
tests/test_templates.py           # off-state golden file + on-state include
tests/fixtures/base_head_off.html # captured from main at 507c5a0
```

## Story order

Sequential: US-1, then US-2, then US-3, in one worktree. US-1 builds the resolver, views and
head that US-3 makes configurable, and US-2's image paths are the ones US-1's manifest and
checks name. Parallel worktrees would edit `mvp/pwa/__init__.py` and `head.html` three times
over.

## Complexity Tracking

None. No article is bent.
