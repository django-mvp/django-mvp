# Tasks — 044 Branded HTML email layout

**Branch**: `044-branded-email` · **Plan**: [plan.md](plan.md) · **Research**:
[research.md](research.md) · **Spec**: [spec.md](spec.md) · **Sketch**: [sketch.md](sketch.md)

Every task follows Article I's test-first cycle. The first dispatch resets the sketch's Python
(`mvp/email/*.py`, the `DEBUG` block in `mvp/urls.py`, `demo/apps.py`) to origin/main, so those
tests are written red. The approved templates stay on the branch. A test written against a
template that already passes is shown able to fail by a mutation recorded in the task's evidence.
A task is done when its tests pass, the tree is green, and the work is committed. Documentation
for a public name lands in the task that introduces it, in `docs/email.md`.

## Order

US-1 (two groups) → US-3 (two groups) → US-2 → US-4, in the feature worktree.

---

## Phase 1 — US-1: A package developer sends an email in the project's look (P1)

Delivers FR-001–FR-007, FR-014, FR-018, SC-001, SC-003, SC-005.

### Group 1

#### T001 [US1] — Reset the sketch's Python and add the dependencies

**Files**: `mvp/email/__init__.py`, `mvp/email/brand.py`, `mvp/email/render.py`,
`mvp/email/views.py`, `mvp/urls.py`, `demo/apps.py`, `pyproject.toml`, `uv.lock`

Remove the sketch's Python modules and its `mvp/urls.py` and `demo/apps.py` hunks. Add
css-inline, tinycss2, coloraide and inscriptis to the runtime dependencies with lower bounds at
the measured versions. `deptry` green.

#### T002 [US1] — `Email.render()`: subject, HTML and plain text from a template prefix

**Files**: `mvp/email/message.py`, `mvp/email/__init__.py`, `tests/test_email/test_message.py`, `docs/email.md`,
`docs/index.md`, `CHANGELOG.md`

`Email(prefix, context, *, language=None, request=None).render()` → `RenderedEmail`. Subject from
`_subject.txt`, joined to one line. HTML from `_message.html`. Text from `_message.txt` when it
exists, otherwise inscriptis over the HTML, with an `<a>` handler writing `text (address)`, or the
address alone when it is the text. Rendered inside `translation.override(language or
get_language())`. Tests: own text template used; generated text keeps body text and every link
address, in that format; multi-line subject joined; language passed is rendered and restored; with
a non-default language active and none passed, the active language is used (AS 1.3–1.5).

#### T003 [US1] — Absolute addresses, with and without a request

**Files**: `mvp/email/message.py`, `tests/test_email/test_message.py`, `docs/email.md`

Paths in `href="/` and `src="/` become absolute: from the request when given, otherwise the
current `Site` over https, http while `DEBUG`. The no-request path raises `ImproperlyConfigured`,
naming `django.contrib.sites` and `SITE_ID`, when sites is not installed, when no `Site` matches
`SITE_ID`, and when the `Site`'s domain is empty. Links to other sites and `//host` addresses
untouched. Context gains `site_url`, and `site_name`: `MVP_CONFIG["site_name"]`, otherwise the
request's or `Site`'s name. Docs say the request path relies on `ALLOWED_HOSTS`. Tests: AS 1.9,
each of the three failures, a configured `site_name` in the logo's alt text and the footer, the
edge case for other sites.

#### T004 [US1] — `Email.send()`

**Files**: `mvp/email/message.py`, `tests/test_email/test_message.py`, `docs/email.md`

One `EmailMultiAlternatives` with the HTML as an alternative, through `EMAIL_BACKEND`. Takes
`to`, `from_email`, `cc`, `bcc`, `reply_to`, `attachments`, `headers`. Empty `to` → nothing sent,
a warning logged, `0` returned. Tests with the in-memory backend (AS 1.1), and with a stand-in
backend class that records the message object it receives, to show it arrives unchanged (AS 1.6).
One test that `from_email`, `cc`, `bcc`, `reply_to`, `attachments` and `headers` reach the outbox
message.

### Group 2

#### T005 [US1] — `EmailBrand` reads the configured themes from the static stylesheets

**Files**: `mvp/email/brand.py`, `tests/test_email/test_brand.py`, `docs/email.md`

`EmailBrand.current()`, cached. Searches every `.css` file the static finders list that contains
`data-theme`, in finder order, with tinycss2, descending into `@layer`, for rules with a selector
that is the theme on its own (`[data-theme=<name>]`, quoted or not, optionally with `:root`).
Descendant selectors never contribute, and `var()` values are skipped. First value per `--color-*`
property wins. coloraide converts to fitted sRGB hex. Builds the light and dark palettes in
`plan.md`. Tests: a packaged daisyUI theme (oklch) reads to the expected hex; a project
stylesheet in `STATICFILES_DIRS` beats the packaged theme of the same name (AS 3.1, 3.2); a
descendant rule such as `[data-theme=nord] .mvp-sidebar` placed before the theme is ignored.
The package's committed `brand/email/logo.png` and `logo_dark.png` land here, and `EmailBrand`
gives their absolute URLs, the dark one only when the file exists.

#### T006 [US1] — The base layout, inlined

**Files**: `mvp/templates/mvp/email/base.html`, `mvp/email/__init__.py`,
`tests/test_email/test_layout.py`, `docs/email.md`

The sketch's layout with its styles moved into the `<style>` block as classes, spacing for plain
`h1`, `h2`, `p`, `ul` and `a` in the body. `render()` passes `email_brand` into the context and
inlines with `CSSInliner(keep_at_rules=True, load_remote_stylesheets=False)`. Blocks `preheader`, `body`, `footer`. Tests: the
sent HTML carries the logo, site name and default footer around the body (AS 1.2); plain body
elements carry inline styles; the `@media` rules survive; a filled `footer` block replaces the
default (AS 1.8); a filled `preheader` appears in the HTML; a body not extending the layout is
sent as written.

#### T007 [US1] — The email pieces

**Files**: `mvp/templates/cotton/mvp/email/{button,note,divider,code}.html`,
`tests/test_components/test_email_pieces.py`, `docs/email.md`, `docs/components.md`

The sketch's four pieces, styled through the layout's classes so they inline. Tests per piece:
renders inside an email, colour comes from the palette, the button's colour is on its table cell
for clients that ignore `<a>` backgrounds (AS 1.7).

#### T008 [US1] — The demo's sample emails

**Files**: `demo/templates/demo/email/*`

Rename to `<name>_subject.txt`, `<name>_message.html`, `<name>_message.txt`. Drop the
hand-written inline margins the layout now supplies. The policy update keeps its own footer and
plain text.

---

## Phase 2 — US-3: A project developer's email takes on the project's theme and logo (P1)

Delivers FR-009–FR-011, FR-017, SC-002.

### Group 1

#### T009 [US3] — Fallbacks and the system check

**Files**: `mvp/email/brand.py`, `mvp/checks.py`, `mvp/apps.py`, `tests/test_email/test_brand.py`,
`tests/test_checks.py`, `docs/email.md`

Missing properties fall back to the packaged theme of the same name, then the package's
`light`/`dark`. An unreadable value falls back and is recorded. `EmailBrand.problems()` feeds
`check_email_brand`, a warning per theme no stylesheet defines and per unreadable colour. Email
still renders. Tests: AS 3.3 (changing `MVP_CONFIG["theme"]` after clearing the cache), AS 3.5,
the partial-theme and unknown-theme edge cases.

#### T010 [US3] — Overriding the layout

**Files**: `tests/test_email/test_layout.py`, `docs/email.md`

A project template at `mvp/email/base.html` and at a piece's path replaces the package's (AS 3.6,
FR-017). Documentation of the override paths.

### Group 2

#### T011 [US3] — PNG logos and their command

**Files**: `mvp/management/commands/mvp_email_logos.py`, `mvp/email/brand.py`,
`tests/test_management/test_mvp_email_logos.py`, `tests/test_email/test_brand.py`,
`docs/email.md`

The command renders `brand/logo.svg` and `brand/logo_dark.svg` to 64 px high PNGs in
`brand/email/`, into the first `STATICFILES_DIRS` entry or `--output-dir`, and stops naming
resvg-py when it is absent. Tests: AS 3.4 for a project's own logo; command output and the
missing-renderer message.

#### T012 [US3] — The stale-logo warning

**Files**: `mvp/email/brand.py`, `tests/test_checks.py`, `docs/email.md`

`problems()` warns when `brand/logo.svg` is found outside the package while
`brand/email/logo.png` is found only inside it, naming the command to run (AS 3.5 for logos).

---

## Phase 3 — US-2: A person reads a project's email in their mail client (P1)

Delivers FR-008, FR-010, FR-012, FR-013, SC-004.

#### T013 [US2] — Images, dark scheme and width

**Files**: `mvp/templates/mvp/email/base.html`, `tests/test_email/test_clients.py`

Tests on the sent HTML: the logo `img` has the site name as `alt` and nothing else needs an image
(AS 2.3); the dark rules use the dark palette and swap to the dark logo only when one exists
(AS 2.4); the narrow-width rule is present (AS 2.6); colours sit on table
cells (AS 2.1); the plain-text part carries the whole message (AS 2.2).

#### T014 [US2] — Contrast in the default themes

**Files**: `tests/test_email/test_clients.py`

With the package's default `light` and `dark`, text on page, text on surface, muted on surface,
muted on page and button text on button meet 4.5:1, measured with coloraide, and so does each pair
with both colours inverted (each sRGB channel 1 − x) (AS 2.5, FR-013, SC-004). Text is drawn only in those pairings.

---

## Phase 4 — US-4: A developer previews an email in the browser (P2)

Delivers FR-015, FR-016, SC-006.

#### T015 [US4] — Preview registry and discovery

**Files**: `mvp/email/previews.py`, `mvp/apps.py`, `demo/email_previews.py`, `tests/test_email/test_previews.py`,
`docs/email.md`

`register(prefix, label, context, *, group="")`, and `autodiscover_modules("email_previews")` in
`MvpConfig.ready` while `DEBUG` is on. `demo/emails.py` is renamed. Test with a test app's
`email_previews.py` (AS 4.1).

#### T016 [US4] — The preview page

**Files**: `mvp/email/views.py`, `mvp/urls.py`, `mvp/templates/mvp/email/preview.html`,
`demo/menus.py`, `tests/test_email/test_views.py`, `docs/email.md`

The sketch's page and frame view. Routes only while `DEBUG`. Staff only. Part, Colour scheme,
Images, Width, and Language when `LANGUAGES` has more than one. One failing email shows its error.
The frame view 404s for a prefix with no registered preview. Confirm every class is in the built
stylesheet, rebuild if not. Tests: AS 4.2–4.6 and the 404, through a URLconf loaded under
`override_settings(DEBUG=True)` with `mvp.urls` reloaded and `clear_url_caches()`.

---

## Phase 5 — Converge

#### T017 [US4] — Docs and changelog pass

**Files**: `docs/email.md`, `docs/index.md`, `README.md`, `CHANGELOG.md`

One page covering sending, templates, the pieces, colours and logos, previews and the command, with
a worked example drawn from the demo. Listed in the docs index. README features list. CHANGELOG
entry under Unreleased.
