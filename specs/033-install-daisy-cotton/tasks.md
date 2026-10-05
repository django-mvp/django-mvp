# Tasks — 033 Install daisy-cotton alongside the package

**Branch**: `033-install-daisy-cotton` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md) · **Spec**: [spec.md](spec.md)

Every task follows the red-green-refactor cycle of Article I. A task is done when its tests pass,
the tree is green, and the work is committed. Documentation for a public name lands in the story
that introduces it.

Rules for every task:

- No name starts with an underscore: no function, helper, constant, fixture or file.
- Lines are at most 88 characters.
- No test asserts wording, layout or appearance.
- No template under `mvp/templates/` is edited. Nothing under `.github/` is edited.
- No existing test is edited, with the one exception named in T008.
- No version bump. Changelog entries go under `## [Unreleased]`.

## Order

**US-1 → US-2 → US-3 → US-4 → US-5, one at a time, in one worktree.** US-2 and US-3 share the
preset, the helper module and `docs/styling.md`, and every story adds to `CHANGELOG.md`.

---

## US-1 — A project gets daisy-cotton with the package and no page changes (P1)

Issue: #456. Delivers FR-001–FR-005, FR-011, FR-020, and US-1's parts of FR-017 and FR-019.

### T001 — The dependency and the app order

**Files**: `pyproject.toml`, `uv.lock`, `demo/settings.py`,
`tests/test_components/test_daisy_cotton_install.py`

Test first, in `TestDeclaredDependency`:

- `importlib.metadata.requires("django-mvp")` has a requirement named `daisy-cotton`, with no
  extra and no marker (parse with `packaging.requirements.Requirement`). Do not compare the
  specifier with a literal range: that test could only fail when someone moves the range on
  purpose;
- the installed `daisy-cotton` version satisfies the declared specifier;
- `apps.is_installed("daisy_cotton")` under the test settings.

Then: `uv add "daisy-cotton>=0.1.2,<0.2"` (never edit `uv.lock` by hand; keep the entry in the
bracketed style of its neighbours). Add `"daisy-cotton"` to the `DEP002` list in
`[tool.deptry.per_rule_ignores]` and name it in the comment beneath that explains the
`INSTALLED_APPS` packages. Add `"daisy_cotton"` to `demo/settings.py` directly below `"mvp"`.
`django-cotton` stays pinned at `2.6.1`.

Covers US-1 scenario 1, FR-001, FR-002 (demo and test project), SC-001.

### T002 — Which package each component comes from

**Files**: `tests/test_components/test_daisy_cotton_install.py`

Work the component paths out by walking the two installed trees, `mvp/templates/cotton` and
`daisy_cotton/templates/cotton`. Copy no list of names into the repository.

- `TestSharedComponents`: for every path present in both trees,
  `get_template("cotton/<path>").origin.name` is inside this package's templates directory. Assert
  the shared set is not empty, so the test cannot pass by finding nothing.
- `TestDaisyCottonOnlyComponents`: for every path present only in daisy-cotton's tree, the origin
  is inside daisy-cotton's templates directory, and the component renders without raising when
  called in isolation with slot content (`<c-name only>x</c-name>`, compiled through
  `django_cotton.compiler_regex.CottonCompiler` as `test_responsive_safelist.py` does).

These pass as soon as T001 lands. That is expected: they pin behaviour the later features rely on.
Show each fails for the right reason, once, with a scratch settings override that is not
committed, and say so in the progress entry: `TestSharedComponents` with `daisy_cotton` moved
above `mvp`; `TestDaisyCottonOnlyComponents` with `daisy_cotton` left out of `INSTALLED_APPS`,
where each lookup raises `TemplateDoesNotExist`.

Covers US-1 scenarios 2 and 4, FR-003, FR-005, FR-011. US-1 scenario 3 (FR-004, SC-002) is proved
by the existing suite passing with no test edited.

### T003 — The app list in the documentation, the decision record and the changelog

**Files**: `docs/getting-started.md`, `README.md`, `skills/django-mvp/SKILL.md`,
`docs/adr/0030-daisy-cotton-is-a-runtime-dependency.md`, `CHANGELOG.md`

- All three app lists gain `"daisy_cotton"` on the line below `"mvp"`. The getting-started guide's
  *Why the order matters* says why: both packages ship components under the same names, the first
  app listed wins, and `mvp` must come first.
- Say what is true after this feature and no more: daisy-cotton is installed with the package and
  its components are found. Do not present them as replacing this package's components.
- ADR 0030, in the shape of `docs/adr/0029-forms-are-drawn-by-django-mvp-forms.md`: why the
  package depends on daisy-cotton (Article VII), why the range is `>=0.1.2,<0.2`, why the project
  lists the app itself, why `mvp` stays above it.
- `CHANGELOG.md`, under `## [Unreleased]`, a `### Changed` entry marked breaking: the new
  dependency, and the one line a project adds to `INSTALLED_APPS` on upgrade, shown as a code
  block.

Covers US-1 scenario 5 (with T012's test), FR-002, FR-017, FR-019, FR-020.

---

## US-2 — The prebuilt stylesheet styles every daisy-cotton component (P1)

Issue: #457. Delivers FR-006, FR-007, FR-010 (prebuilt half), and US-2's part of FR-017.

### T004 — Work out the classes daisy-cotton can render

**Files**: `tests/daisy_cotton_classes.py`,
`tests/test_components/test_daisy_cotton_coverage.py`

`tests/daisy_cotton_classes.py`, three public functions (plan, *The derivation*; research R1):

- `component_classes(templates_dir)`: the set of classes the templates under a directory can
  render. Literal classes inside any attribute whose name is or ends in `class`, read after
  comments, `{% … %}` tags and `{{ … }}` variables are taken out; every
  `{% variation var "base" "a,b" %}` as `base-a`, `base-b`; every `{% responsive var "name" %}` as
  `name` and `bp:name` for each breakpoint in `daisy_cotton.templatetags.daisy_cotton.BREAKPOINTS`.
  A literal joined to a variable (`mask-half-{{ item.half }}`) is looked up in a module-level
  table of stems to values, holding `mask-half-` → `1`, `2`; a stem that is not in the table
  raises an error naming the stem and the file.
- `unstyled_classes(classes, stylesheet)`: the classes with no selector in the stylesheet text. A
  selector is the class name with every character outside `[A-Za-z0-9_-]` backslash-escaped,
  preceded by `.`, and not followed by another name character or a backslash. A name whose first
  character is a digit is matched the way CSS writes it, with a code-point escape: backslash, `3`,
  the digit, one space, then the rest escaped as above (`2xl:drawer-open` is
  `.\32 xl\:drawer-open`).
- `safelisted_classes(preset)`: every class declared by an `@source inline("…")` entry in the
  preset text, brace groups expanded.

`TestClassDerivation`, test first, against template files written under `tmp_path`:

- a literal class, a `variation` class and a `responsive` class at every breakpoint are returned;
- a caller-supplied `{{ class }}` adds nothing;
- an unknown interpolated stem raises, and the error names it;
- `unstyled_classes` returns a made-up class by name and does not return one that has a selector,
  including one whose name needs escaping (`md:example`, `group/item`, `2xl:example`);
- `safelisted_classes` expands nested brace groups.

Covers US-2 scenario 4 and the mechanism of FR-010.

### T005 — Pin what the 0.26.0 stylesheet styles

**Files**: `tests/fixtures/stylesheet_classes_0_26_0.txt`,
`tests/test_components/test_daisy_cotton_coverage.py`

Before any build input changes, write every class selector in
`git show origin/main:mvp/static/css/django-mvp.css` to the fixture, unescaped, one per line,
sorted. A class selector is a `.` followed by a name that starts with a letter, `-`, `_` or a
backslash escape, never a bare digit: the minified stylesheet is full of numbers such as `.25rem`
that are not classes. Undo the leading-digit escape when writing (`\32 xl\:drawer-open` becomes
`2xl:drawer-open`). `TestPrebuiltStylesheet::test_no_class_from_the_previous_release_is_lost` asserts
`unstyled_classes(fixture, committed stylesheet)` is empty, with the missing names in the failure
message. The fixture's first line is a `#` comment saying what it is, which commit it was taken from, and
that a class removed on purpose has its line deleted.

Covers US-2 scenario 3, FR-007, SC-005.

### T006 — Cover every class in the prebuilt stylesheet

**Files**: `tests/test_components/test_daisy_cotton_coverage.py`, `mvp/tailwind/base.css`,
`assets/tailwind.css`, `package.json`, `package-lock.json`, `mvp/static/css/django-mvp.css`,
`mvp/static/css/django-mvp.css.br`

Test first: `TestPrebuiltStylesheet::test_every_daisy_cotton_class_is_styled` asserts
`unstyled_classes(component_classes(<installed daisy-cotton templates>), committed stylesheet)`
is empty, listing the missing names. It fails, naming 91 classes (research R2).

Then:

1. `mvp/tailwind/base.css`: a new block headed as daisy-cotton's, after the existing safelist
   entries, with one `@source inline()` entry carrying every `responsive` class at every
   breakpoint, `{sm,md,lg,xl,2xl}:{…}`. Leave every existing entry as it is.
2. `npm install -D -E daisyui@5.7.0` (changes `package.json` and `package-lock.json` only).
3. `assets/tailwind.css`: under a comment naming daisy-cotton, `@source inline()` entries for the
   eight plain utilities its templates write literally: `end-2`, `top-2`,
   `focus-visible:outline-2`, `focus-visible:-outline-offset-2`, `group/item`,
   `group-first/item:hidden`, `group-last/item:hidden`, `max-sm:megamenu-vertical`. `tasks.py` and
   the `npm` scripts are not changed, and the build does not scan daisy-cotton's templates
   (research R3).
4. `uv run invoke build-stylesheet`, and commit the rebuilt `.css` and `.css.br`.
5. Look at the rebuilt stylesheet on the running demo: the home page, a list page, a detail page,
   a form page and the sign-in page. Nothing should have moved. Name the pages looked at in the
   progress entry. If something has, stop and report it as a concern; do not adjust styles.

Both `TestPrebuiltStylesheet` tests are green afterwards.

Covers US-2 scenarios 1 and 2, FR-006, FR-007, FR-010, SC-003.

### T007 — Say what the prebuilt stylesheet covers

**Files**: `docs/styling.md`, `CHANGELOG.md`

- `docs/styling.md`, Tier 1: the prebuilt stylesheet styles every class daisy-cotton's components
  can render.
- `CHANGELOG.md`, under `## [Unreleased]`: the coverage, and that the stylesheet is now built with
  daisyUI 5.7.0.

Covers FR-017.

---

## US-3 — A project that builds its own stylesheet gets the same coverage (P2)

Issue: #458. Delivers FR-008, FR-009, FR-010 (generated-entry half), FR-016, and US-3's parts of
FR-017 and FR-019.

### T008 — The generator finds daisy-cotton's templates

**Files**: `mvp/management/commands/mvp_tailwind.py`,
`tests/test_components/test_mvp_tailwind_command.py`

Test first, added to `TestMVPTailwindCommand`:

- `--paths` prints four lines; the fourth is absolute, exists, is a directory, uses forward
  slashes and equals `Path(daisy_cotton.__file__).resolve().parent / "templates"`;
- the first three lines are what they were (preset file, this package's templates, the form pack);
- the generated entry has `@source "<fourth path>";`.

`test_entry_paths_exist_and_are_absolute` unpacks exactly three lines and so breaks when a fourth
is printed. Change its unpacking to take the first three (`lines[:3]`) and change nothing else in
it. **This is the only existing test this feature edits**, and FR-016 is the reason.

Then: a module constant `DAISY_COTTON_TEMPLATES_DIR`, resolved as `FORMS_DIR` is; an `@source`
line for it in `ENTRY_TEMPLATE` after the form pack's, under a one-line comment; a fourth
`self.stdout.write` under `--paths`. Update the module docstring, the command's `help` and the
`--paths` help text to name it.

Covers US-3 scenarios 1 and 3, FR-008, FR-016.

### T009 — Cover every class from the generated entry

**Files**: `tests/fixtures/preset_safelist_0_26_0.txt`,
`tests/test_components/test_daisy_cotton_coverage.py`, `mvp/tailwind/base.css`,
`mvp/static/css/django-mvp.css`, `mvp/static/css/django-mvp.css.br`

Test first, in `TestGeneratedEntry`, reading the preset from the first line of `--paths` and the
scanned directory from the fourth:

- `test_every_daisy_cotton_class_is_covered`: every class from `component_classes` is either
  written literally in a file under the scanned directory, or returned by `safelisted_classes`.
  "Written literally" means the class appears as a whole token when the file's text is split on
  whitespace, quotes, commas and the characters `<>{}%=;()`. The failure message lists the missing
  names. It fails on the `variation` classes.
- `test_no_class_from_the_previous_release_is_lost`: every class in the fixture is still returned
  by `safelisted_classes`. Write the fixture from
  `safelisted_classes(git show origin/main:mvp/tailwind/base.css)`, sorted, one per line, under
  the same kind of `#` comment as T005's.

Then, in the daisy-cotton block of `mvp/tailwind/base.css`: one `@source inline()` entry per
option list, `{base,base,…}-{option,option,…}`, covering every `variation` call in the installed
daisy-cotton. Rebuild the stylesheet with `uv run invoke build-stylesheet`
and commit it, because the preset is one of its inputs.

Covers US-3 scenarios 2 and 4, FR-009, FR-010, SC-004.

### T010 — Document the generated entry

**Files**: `docs/styling.md`, `README.md` (only if it describes the entry's contents or `--paths`),
`CHANGELOG.md`

- `docs/styling.md`, Tier 2: the generated entry scans daisy-cotton's templates; `--paths` prints
  four paths, daisy-cotton's last; a project's own build needs daisyUI 5.7 or later for every
  class to exist; re-run the generator after upgrading.
- `CHANGELOG.md`, under `## [Unreleased]`: the generator's new line and fourth path, and that a
  project building its own stylesheet re-runs it.

Covers FR-017, FR-019.

---

## US-4 — A project is told when its app list is wrong (P2)

Issue: #459. Delivers FR-012, FR-013, FR-014, and US-4's part of FR-017.

### T011 — The start-up check

**Files**: `mvp/checks.py`, `mvp/apps.py`, `tests/test_checks.py`

Test first, in `TestDaisyCottonAppMessages` and `TestDaisyCottonAppCheck`:

- `daisy_cotton_app_messages(["mvp"])` returns one `Error` with id `mvp.E002`;
- `daisy_cotton_app_messages(["daisy_cotton", "mvp"])` returns one `Warning` with id `mvp.W001`;
- `daisy_cotton_app_messages(["mvp", "x", "daisy_cotton"])` returns nothing;
- each message has a non-empty `hint`. Assert identifiers, levels and that the message names the
  apps (`"daisy_cotton" in message.msg`), never the sentence;
- under the repository's own settings, `check_daisy_cotton_app(None)` returns nothing;
- with `INSTALLED_APPS` overridden to leave `daisy_cotton` out, `call_command("check")` raises
  `SystemCheckError` naming `mvp.E002`, and does not once `SILENCED_SYSTEM_CHECKS` lists it; the
  same pair for `mvp.W001` with the two apps the other way round, reading the warning from the
  command's `stderr`.

Then `mvp/checks.py` as the plan's *The start-up check* describes, registered in
`MvpConfig.ready()` beside the existing check, and the docstring of `ready()` updated.

Covers US-4 scenarios 1 to 4, FR-012, FR-013, FR-014, SC-006.

### T012 — The guide's app list passes the check, and the check is documented

**Files**: `tests/test_checks.py`, `docs/troubleshooting.md`, `docs/getting-started.md`,
`CHANGELOG.md`

- `TestGettingStartedAppList`: read the first fenced `python` block in `docs/getting-started.md`
  that assigns `INSTALLED_APPS`, take the quoted names in order, and assert
  `daisy_cotton_app_messages` returns nothing for them.
- `docs/troubleshooting.md`: an entry for each identifier, what causes it and the fix.
- `docs/getting-started.md`: one sentence after the order explanation saying the project is told
  at start-up when the line is missing or misplaced, with the two identifiers.
- `CHANGELOG.md`, under `## [Unreleased]`: the check and its two identifiers.

Covers US-1 scenario 5, SC-007, FR-017.

---

## US-5 — A page's variables stay out of a daisy-cotton component (P3)

Issue: #460. Delivers FR-015, FR-018.

### T013 — Prove isolation

**Files**: `tests/test_components/test_daisy_cotton_isolation.py`

`TestIsolatedCall`, each test rendering a compiled Cotton source with a page context (research
R6):

- `<c-menu.title only />` with a page variable `text`: the value is not in the output;
- the same call without `only`: the value is in the output. This is the hazard the rule exists
  for, and it shows the first test is not passing by accident;
- `<c-menu.title only>{{ page_value }}</c-menu.title>`: the page's value is in the output;
- `<c-stat only><c-slot name="title">{{ page_value }}</c-slot></c-stat>`: the page's value is in
  the output, inside the element with class `stat-title`;
- `<c-menu.title text="given" only />` with a page variable `text`: the passed value is in the
  output and the page's is not.

Use values that cannot occur in markup by chance. Find elements by class or role with
BeautifulSoup, never by surrounding text.

Covers US-5 scenarios 1 to 4, FR-015, SC-008.

### T014 — Write the rule down

**Files**: `CONTRIBUTING.md`

Under *Component Development*: every call this package's templates make to a daisy-cotton
component passes `only`. Why: a daisy-cotton component that declares an attribute with no default
reads a page variable of the same name when the caller does not pass it. What still works: content
between the tags, and content in named slots, renders with the page's variables. One short
example.

Covers US-5 scenario 5, FR-018.

---

## After the code review

The review approved the build with three low points. Each was taken.

### T015 — Match Tailwind's boundaries when deciding a class is written literally (US-3)

**Files**: `tests/test_components/test_daisy_cotton_coverage.py`,
`tests/test_components/test_mvp_tailwind_command.py`

Tailwind does not extract a class that sits next to a comma, `=`, `;` or a parenthesis, so
`written_literally` no longer splits on them. The assertion that `--paths` prints exactly four
lines is removed: the test still reads the fourth line, and a count would break on the next path
added.

### T016 — Do not pin that the check has no tag (US-4)

**Files**: `tests/test_checks.py`

The behaviour is read by the tests that run `check`. Whether the check carries a tag is not a
requirement.

### T017 — Say truthfully how daisy-cotton is reached (US-1)

**Files**: `pyproject.toml`, `docs/adr/0030-daisy-cotton-is-a-runtime-dependency.md`

The generator imports `daisy_cotton`, so it is no longer listed among the packages reached only
through `INSTALLED_APPS`, and the ADR no longer says so.
