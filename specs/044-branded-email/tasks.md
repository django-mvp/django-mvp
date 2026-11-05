# Tasks — 044 Branded HTML email layout

**Branch**: `044-branded-email` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md) · **Sketch**: [sketch.md](sketch.md)

Every task follows Article I's test-first cycle. The first dispatch resets the sketch's Python
(`mvp/email/*.py`, the `DEBUG` block in `mvp/urls.py`, `demo/apps.py`, `demo/emails.py`) to
origin/main, so those tests are written red. The approved templates stay on the branch. A test
written against a template that already passes is shown able to fail by a mutation recorded in the
task's evidence. A task is done when its tests pass, the tree is green, and the work is committed.
Documentation for a public name lands in the task that introduces it, in `docs/email.md`. Tests
mirror the source tree: `tests/test_email/test_brand.py`, `tests/test_email/test_previews.py`,
`tests/test_email/test_views.py`, `tests/test_templatetags/test_mvp_email.py`,
`tests/test_templates/test_email_base.py`, `tests/test_components/test_email_pieces.py`.

## Checklist

- [ ] T001 [US1] Reset the sketch's Python and add the dependencies
- [ ] T002 [US1] `EmailBrand` reads the configured themes from the static stylesheets
- [ ] T003 [US1] The site's address, name and `{% email_url %}`
- [ ] T004 [US1] `{% email_inline %}` and the base template
- [ ] T005 [US1] The email pieces
- [ ] T006 [US1] A third-party sender, unchanged, carries the brand
- [ ] T007 [US3] Fallbacks and the system check
- [ ] T008 [US3] Overriding the base template and pieces
- [ ] T009 [US3] PNG logos and their command
- [ ] T010 [US3] The stale-logo warning
- [ ] T011 [US2] Images, dark scheme and width
- [ ] T012 [US2] Contrast in the default themes
- [ ] T013 [US4] Preview registry and discovery
- [ ] T014 [US4] The preview page
- [ ] T015 [US4] Docs and changelog pass

## Order

US-1 (two groups) → US-3 → US-2 → US-4, in the feature worktree.

---

## Phase 1 — User Story 1: A developer gives an email the project's look (P1)

Delivers FR-001–FR-004, FR-010, FR-014–FR-016, SC-001, SC-003, SC-005.

### Group 1

#### T001 — Reset the sketch's Python and add the dependencies

**Files**: `mvp/email/__init__.py`, `mvp/email/brand.py`, `mvp/email/render.py`,
`mvp/email/views.py`, `mvp/urls.py`, `demo/apps.py`, `demo/emails.py`, `pyproject.toml`, `uv.lock`

Remove the sketch's Python modules and its `mvp/urls.py` and `demo/apps.py` hunks. Add
css-inline, tinycss2 and coloraide to the runtime dependencies with lower bounds at the measured
versions. `deptry` green.

#### T002 — `EmailBrand` reads the configured themes from the static stylesheets

**Files**: `mvp/email/__init__.py`, `mvp/email/brand.py`, `mvp/static/brand/email/logo.png`,
`mvp/static/brand/email/logo_dark.png`, `tests/test_email/test_brand.py`, `docs/email.md`

`EmailBrand.current()`, cached. Searches every `.css` file the static finders list that contains
`data-theme`, in finder order, with tinycss2, descending into `@layer`, for rules with a selector
that is the theme on its own. Descendant selectors never contribute, `var()` values are skipped,
first value per property wins. coloraide converts to fitted sRGB hex. Builds the palettes in
`plan.md`. The package's own email PNGs are committed here, and `EmailBrand` gives their URLs, the
dark one only when the file exists. Tests: a packaged daisyUI theme (oklch) reads to the expected
hex; a project stylesheet in `STATICFILES_DIRS` beats the packaged theme of the same name (AS 3.1,
3.2); a descendant rule such as `[data-theme=nord] .mvp-sidebar` placed before the theme is
ignored.

#### T003 — The site's address, name and `{% email_url %}`

**Files**: `mvp/templatetags/mvp_email.py`, `tests/test_templatetags/test_mvp_email.py`,
`docs/email.md`

The site's address from `context["request"]` when present, otherwise the current `Site` over
https, http while `DEBUG`. The no-request path raises `ImproperlyConfigured`, naming
`django.contrib.sites` and `SITE_ID`, when sites is not installed, when no `Site` matches
`SITE_ID`, and when the `Site`'s domain is empty. `{% email_url %}` takes a path, or a URL name
with arguments as `{% url %}` does, and returns absolute addresses unchanged.
`{% email_site_name %}`: `MVP_CONFIG["site_name"]`, otherwise the request's or `Site`'s name.
`{% email_brand as brand %}` gives the palettes and absolute logo URLs. Docs say the request path
relies on `ALLOWED_HOSTS`. Tests: AS 1.5 with and without a request, each of the three failures, a
configured `site_name`, an address on another site left as written.

### Group 2

#### T004 — `{% email_inline %}` and the base template

**Files**: `mvp/templatetags/mvp_email.py`, `mvp/templates/mvp/email/base.html`,
`tests/test_templatetags/test_mvp_email.py`, `tests/test_templates/test_email_base.py`,
`docs/email.md`

`{% email_inline %}` renders its contents and inlines them with
`CSSInliner(keep_at_rules=True, load_remote_stylesheets=False)`. The sketch's base template with its
styles moved into a `<style>` block as classes, spacing and colour for plain `h1`, `h2`, `p`,
`ul`, `li` and `a`, wrapped in `{% email_inline %}`, reading everything through the tag library.
Blocks `preheader`, `body`, `footer`. Tests: a child template's plain markup comes out with inline
styles (AS 1.2); the `@media` rules survive; the logo, site name and default footer surround the
body; a filled `footer` replaces the default (AS 1.4); a filled `preheader` appears; rendering with
an empty context and the sites framework works (FR-003).

#### T005 — The email pieces

**Files**: `mvp/templates/cotton/mvp/email/{button,note,divider,code}.html`,
`tests/test_components/test_email_pieces.py`, `docs/email.md`, `docs/components.md`

The sketch's four pieces, styled through the base template's classes. Tests per piece: renders
inside an email, colour from the palette, the button's colour on its table cell (AS 1.3).

#### T006 — A third-party sender, unchanged, carries the brand

**Files**: `tests/test_templates/test_email_base.py`, `tests/testapp_email/`, `demo/templates/demo/email/*`,
`docs/email.md`

A test app that sends mail the way allauth's adapter does (`render_to_string` of `_subject.txt`,
`_message.txt` and `_message.html`, `EmailMultiAlternatives`), with a project override of its HTML
template extending the base template. Through the in-memory backend: the HTML part carries the
brand, the plain-text part is the app's own template, unchanged (AS 1.1, 1.6, SC-003, FR-015). The
demo's sample emails are renamed to that naming and lose the hand-written margins the base template
now supplies. Docs: a worked example of overriding a third-party template.

---

## Phase 2 — User Story 3: A project developer's email takes on the project's theme and logo (P1)

Delivers FR-005–FR-007, FR-011, SC-002.

#### T007 — Fallbacks and the system check

**Files**: `mvp/email/brand.py`, `mvp/checks.py`, `mvp/apps.py`, `tests/test_email/test_brand.py`,
`tests/test_checks.py`, `docs/email.md`

Missing properties fall back to the packaged theme of the same name, then the package's
`light`/`dark`. An unreadable value falls back and is recorded. `EmailBrand.problems()` feeds
`check_email_brand`, a warning per theme no stylesheet defines and per unreadable colour. Email
still renders. Tests: AS 3.3 (changing `MVP_CONFIG["theme"]` after clearing the cache), AS 3.5.

#### T008 — Overriding the base template and pieces

**Files**: `tests/test_templates/test_email_base.py`, `docs/email.md`

A project template at `mvp/email/base.html` and at a piece's path replaces the package's (AS 3.6,
FR-011).

#### T009 — PNG logos and their command

**Files**: `mvp/management/commands/mvp_email_logos.py`, `tests/test_management/test_mvp_email_logos.py`,
`docs/email.md`

Renders `brand/logo.svg` and `brand/logo_dark.svg` to 64 px high PNGs in `brand/email/`, into the
first `STATICFILES_DIRS` entry or `--output-dir`, and stops naming resvg-py when it is absent.
Tests: AS 3.4 for a project's own logo; command output and the missing-renderer message.

#### T010 — The stale-logo warning

**Files**: `mvp/email/brand.py`, `tests/test_checks.py`, `docs/email.md`

`problems()` warns when `brand/logo.svg` is found outside the package while
`brand/email/logo.png` is found only inside it, naming the command to run.

---

## Phase 3 — User Story 2: A person reads a project's email in their mail client (P1)

Delivers FR-002, FR-006, FR-008, FR-009, SC-004.

#### T011 — Images, dark scheme and width

**Files**: `mvp/templates/mvp/email/base.html`, `tests/test_templates/test_email_base.py`

Tests on the rendered HTML: the logo `img` has the site name as `alt` and nothing in the layout
needs an image (AS 2.2); the dark rules use the dark palette and swap to the dark logo only when
one exists (AS 2.3); the narrow-width rule is present (AS 2.5); colours sit on table cells (AS 2.1).

#### T012 — Contrast in the default themes

**Files**: `tests/test_email/test_brand.py`

With the package's default `light` and `dark`: text on page, text on surface, muted on surface,
muted on page and button text on button meet 4.5:1, measured with coloraide, and so does each pair
with both colours inverted (each sRGB channel 1 − x) (AS 2.4, FR-009, SC-004).

---

## Phase 4 — User Story 4: A developer previews an email in the browser (P2)

Delivers FR-012, FR-013, SC-006.

#### T013 — Preview registry and discovery

**Files**: `mvp/email/previews.py`, `mvp/apps.py`, `demo/email_previews.py`,
`tests/test_email/test_previews.py`, `docs/email.md`

`register(template, label, context, *, subject=None, text=None, group="")`, and
`autodiscover_modules("email_previews")` in `MvpConfig.ready` while `DEBUG` is on. Test with a test
app's `email_previews.py` (AS 4.1).

#### T014 — The preview page

**Files**: `mvp/email/views.py`, `mvp/urls.py`, `mvp/templates/mvp/email/preview.html`,
`demo/menus.py`, `tests/test_email/test_views.py`, `docs/email.md`

The sketch's page and frame view, rendering the declared templates with `render_to_string`. Routes
only while `DEBUG`. Staff only. Part (plain text only when the email has a text template), Colour
scheme, Images, Width, and Language when `LANGUAGES` has more than one. One failing email shows its
error. The frame view 404s for a template with no registered preview. Confirm every class is in the
built stylesheet, rebuild if not. Tests: AS 4.2–4.6 and the 404, through a URLconf loaded under
`override_settings(DEBUG=True)` with `mvp.urls` reloaded and `clear_url_caches()`.

#### T015 — Docs and changelog pass

**Files**: `docs/email.md`, `docs/index.md`, `README.md`, `CHANGELOG.md`

One page: extending the base template, overriding a third-party package's email template, the
pieces, the tags, colours and logos, previews and the command. Listed in the docs index. README
features list. CHANGELOG entry under Unreleased.
