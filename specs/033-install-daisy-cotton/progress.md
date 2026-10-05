
## 2026-10-05T14:43:49Z · Forge · plan

Did: research against daisy-cotton 0.1.2 as installed, then plan.md and tasks.md (14 tasks, five stories).
Verified: trial builds with @tailwindcss/cli 4.3.2 and daisyUI 5.6.18 and 5.7.0; all 60 daisy-cotton-only components rendered under django-cotton 2.6.1.
Next: design review, then US-1.
Watch: daisyUI moves to 5.7.0 for menu-paged; the fixtures in T005 and T009 are written from origin/main, not from the working tree.

## 2026-10-05T15:00:21Z · Implementer US1 · T001

Did: wrote TestDeclaredDependency (three tests) first and saw all three fail (no daisy-cotton requirement in the installed metadata; daisy_cotton not an installed app). Ran `uv add "daisy-cotton>=0.1.2,<0.2"`, then put the pyproject entry in the parenthesised style of its neighbours and ran `uv lock`. Added "daisy-cotton" to the DEP002 list and its comment, and "daisy_cotton" below "mvp" in demo/settings.py.
Verified: `uv run pytest tests/test_components/test_daisy_cotton_install.py::TestDeclaredDependency` 3 passed; `uv run deptry .` no issues; `uv lock --check` clean; `uv run pre-commit run --all-files` all hooks passed. The full suite has not been run yet; it runs once at the end of the story.
Next: T002, the resolution tests.
Watch: uv resolved daisy-cotton 0.1.3, not 0.1.2, which is inside the range. uv 0.11.19 here writes `revision = 3` in uv.lock where the committed file said 5; I left the tool's output as written.

## 2026-10-05T15:01:17Z · Implementer US1 · T002

Did: added ComponentTrees, TestSharedComponents and TestDaisyCottonOnlyComponents to tests/test_components/test_daisy_cotton_install.py. Paths come from walking mvp/templates/cotton and daisy_cotton/templates/cotton; nothing is listed by hand. The shared set (22 paths) and the daisy-cotton-only set (60 paths) are each asserted non-empty. Only-daisy components are called as `<c-tag only>x</c-tag>` through CottonCompiler.
Verified: both classes passed on first run once T001 was in (they pin existing behaviour, as the task says), so I broke each on purpose with a scratch settings module in /tmp, passed with `--ds`, never added to the repository. TestSharedComponents with daisy_cotton listed above mvp: 22 failed, 1 passed (the non-empty check); every shared path resolved into daisy_cotton/templates, so the failure is the resolution it guards. TestDaisyCottonOnlyComponents with daisy_cotton removed from INSTALLED_APPS: 120 failed, 1 passed; each lookup and each render raised TemplateDoesNotExist. Scratch files deleted. Real settings: `uv run pytest tests/test_components/test_daisy_cotton_install.py` 147 passed; ruff check and ruff format --check clean on the file; pre-commit all hooks passed.
Next: T003, documentation, ADR 0030 and changelog.
Watch: the two non-empty checks are the only tests that pass under the breaking overrides, as intended.

## 2026-10-05T15:01:55Z · Implementer US1 · T003

Did: added "daisy_cotton" directly below "mvp" in the app lists in docs/getting-started.md, README.md and skills/django-mvp/SKILL.md. The guide's "Why the order matters" now says both packages ship components under the same names, the first app listed wins, `mvp` must come first, and that some daisy-cotton components draw a button or menu item inside themselves and get mvp's copy. Wrote docs/adr/0030-daisy-cotton-is-a-runtime-dependency.md in the shape of ADR 0029. Added a breaking `### Changed` entry under `## [Unreleased]` in CHANGELOG.md with the one INSTALLED_APPS line. The docs say daisy-cotton is installed and found, and do not present its components as replacing mvp's.
Verified: `uv run pre-commit run --all-files` all hooks passed on the staged tree. Docs are prose and a settings list; I did not run a page against them beyond the test settings, which inherit the same list from demo/settings.py. US-1 scenario 5's test belongs to T012 and is not written.
Next: full suite once, then the ledger and the report.
Watch: the ADR title keeps the em dash that ADR 0029's title has; the prose has none.

## 2026-10-05T15:08:01Z · Implementer US2 · T004

Did: Added tests/daisy_cotton_classes.py (component_classes, unstyled_classes, safelisted_classes) and TestClassDerivation, TestUnstyledClasses, TestSafelistedClasses in tests/test_components/test_daisy_cotton_coverage.py. Tests written first; the first run failed with ModuleNotFoundError for the helper. Comments, {% comment %} blocks and annotations are stripped before reading; a variation or responsive tag not written with quoted literals raises.
Verified: uv run pytest tests/test_components/test_daisy_cotton_coverage.py -q -> 22 passed. uv run ruff check and ruff format on both files clean. A one-off run against the installed daisy-cotton 0.1.3 and the committed stylesheet gave 649 classes and 91 unstyled, matching research R2 (nothing hard-coded in the tests).
Next: T005, the 0.26.0 fixture and TestPrebuiltStylesheet.
Watch: unstyled_classes searches the stylesheet once per class (about 1.4s for 649 classes on a 450 KB file); the T005 fixture is larger, so watch the test time.

## 2026-10-05T15:09:22Z · Implementer US2 · T005

Did: Wrote tests/fixtures/stylesheet_classes_0_26_0.txt from `git show origin/main:mvp/static/css/django-mvp.css` (origin/main bd63880, version 0.26.0): 2349 class selectors, unescaped, sorted, with a # header line. Only text in a rule prelude was read, so `w3` and `org` from an SVG URL inside the stylesheet are not in it. Added TestPrebuiltStylesheet::test_no_class_from_the_previous_release_is_lost. Also committed a second T004 commit: unstyled_classes now finds a selector by substring search, because the regex version took 16s on the fixture; the T004 tests were the net and are unchanged.
Verified: uv run pytest tests/test_components/test_daisy_cotton_coverage.py -q -> 23 passed in 0.54s. Probe: renaming `.btn-ghost` to `.btn-gone` in the committed stylesheet made the new test fail naming ['btn-ghost']; the file was restored with git checkout.
Next: T006. The test goes in first and has to fail naming about 91 classes.
Watch: the test is green on the current stylesheet by design (nothing is lost yet). It only has teeth after the rebuild in T006.

## 2026-10-05T15:10:50Z · Implementer US2 · T006

Did: Added TestPrebuiltStylesheet::test_every_daisy_cotton_class_is_styled first; it failed naming 91 classes. Then: a daisy-cotton block in mvp/tailwind/base.css with one @source inline() entry for the 19 responsive classes at every breakpoint; `npm install -D -E daisyui@5.7.0` (npm rewrote the lockfile's top-level name to the worktree directory name, which I set back to django-mvp, so only daisyui changed); eight @source inline() entries in assets/tailwind.css; `uv run invoke build-stylesheet`, committed with its .br. tasks.py is unchanged.
Verified: uv run pytest tests/test_components/test_daisy_cotton_coverage.py -q -> 24 passed; tests/test_components/test_responsive_safelist.py still passes. Compared class selectors in the rebuilt stylesheet with origin/main's: 2349 before, 2440 after, none lost, 91 gained. Rebuilt .br decompresses to exactly the .css.
Pages: ran the demo on port 8002 (nothing was listening; stopped it afterwards). Migrated the git-ignored db.sqlite3 and ran generate_dummy_data first, because the worktree had no tables. With curl, the home page /, the list page /products/, the detail page /products/1/, the form page /products/create/ and the sign-in page /account/login/ each returned 200 and linked css/django-mvp.css, and the served file was the rebuilt size (492996 bytes). Nobody has looked at these pages by eye: this is a curl check, not a visual one.
Next: T007, docs/styling.md and the changelog.
Watch: daisyUI moved from 5.6.18 to 5.7.0 and no test judges appearance, so rule bodies were not compared. The visual check named in the plan's Risks still has to be done by a person.

## 2026-10-05T15:11:09Z · Implementer US2 · T007

Did: docs/styling.md, Tier 1: a paragraph saying the prebuilt stylesheet styles every class daisy-cotton's components can render (breakpoint forms included), that it is built with daisyUI 5.7.0, and that caller-supplied classes are outside it. CHANGELOG.md, under [Unreleased] > Changed: an entry for the coverage and daisyUI 5.7.0. The 82 in the entry is research R2's count of missing breakpoint forms; I measured 91 missing in all (82 + 8 utilities + menu-paged).
Verified: uv run pytest tests/test_components/test_daisy_cotton_coverage.py -q -> 24 passed. No test asserts the wording of either file.
Next: full verify once, then the ledger and the report.
Watch: nothing else under docs/ describes the stylesheet's coverage; docs/utility-classes.md covers the project utility pack and is unchanged.

## 2026-10-05T15:15:54Z · Implementer US3 · T008

Did: mvp_tailwind resolves DAISY_COTTON_TEMPLATES_DIR, prints it as the fourth --paths line and adds an @source line after the form pack's in the entry. Docstring, command help, --paths help and the entry header (daisyUI 5.7 or later) updated. Added two tests to TestMVPTailwindCommand; changed test_entry_paths_exist_and_are_absolute to unpack lines[:3] only.
Verified: both new tests failed first (3 lines printed, no fourth). `uv run pytest tests/test_components/test_mvp_tailwind_command.py -q`: 7 passed. ruff check and format --check on the touched files clean.
Next: T009, the generated-entry coverage test and the preset's variation entries.
Watch: the file's older tests use an underscore helper (_run); left untouched, new tests reuse it.

## 2026-10-05T15:17:35Z · Implementer US3 · T009

Did: added TestGeneratedEntry (every class covered, previous release's preset classes kept) and TestWrittenLiterally with the public helper written_literally; wrote tests/fixtures/preset_safelist_0_26_0.txt from origin/main's base.css (185 classes); added 17 @source inline() entries to the preset, one per variation option list. Rebuilt the stylesheet with `uv run invoke build-stylesheet`: the .css and .css.br came out byte for byte the same, so nothing to commit there.
Verified: test_every_daisy_cotton_class_is_covered failed first, naming 253 variation classes. Probe: deleting the md:max-w preset line made test_no_class_from_the_previous_release_is_lost fail; restored. `uv run pytest` on test_daisy_cotton_coverage.py, test_mvp_tailwind_command.py and test_responsive_safelist.py: 46 passed. `uv run pre-commit run --all-files`: all hooks passed.
Next: T010, docs and changelog.
Watch: mypy needed `# type: ignore[import-untyped]` on the daisy_cotton import in mvp_tailwind.py (pyproject's mypy overrides, outside this story's scope, would be the cleaner place).

## 2026-10-05T15:18:04Z · Implementer US3 · T010

Did: docs/styling.md Tier 2 now says the entry scans daisy-cotton's templates, --paths prints four paths with daisy-cotton's last, the build needs daisyUI 5.7 or later, and the generator is re-run after upgrading django-mvp or daisy-cotton. README's entry description and install line updated to match. CHANGELOG Unreleased records the new line and fourth path.
Verified: `uv run pre-commit run --all-files`: all hooks passed. No test for prose, by the testing standard.
Next: flip T008-T010 in feature-state.json, run the full suite once, write the report.
Watch: skills/django-mvp/SKILL.md has no mention of --paths or the entry's contents, so it is untouched.

## 2026-10-05T15:25:18Z · Implementer US4 · T011

Did: added mvp/checks.py with daisy_cotton_app_messages (Error mvp.E002 when daisy_cotton is missing, Warning mvp.W001 when listed above mvp) and check_daisy_cotton_app, registered with no tag in MvpConfig.ready(). Tests in tests/test_checks.py (TestDaisyCottonAppMessages, TestDaisyCottonAppCheck).
Verified: new module import failed first (red). `uv run pytest tests/test_checks.py` 12 passed. Probe: with the checks.register line removed, 3 tests failed (registration, E002 command, W001 stderr); restored. `uv run mypy mvp` clean, `uv run pre-commit run --all-files` all passed.
Next: T012, the guide's app list test and the docs.
Watch: tests override INSTALLED_APPS through the settings fixture and call `check`; nothing else broke in that scope.

## 2026-10-05T15:26:01Z · Implementer US4 · T012

Did: added TestGettingStartedAppList (parses the first python block assigning INSTALLED_APPS in docs/getting-started.md, comments stripped, and asserts mvp and daisy_cotton are present and the check returns nothing). Added a Start-up checks section to docs/troubleshooting.md with mvp.E002 and mvp.W001, one sentence naming both in docs/getting-started.md, and an Added entry under Unreleased in CHANGELOG.md. skills/django-mvp/SKILL.md only links the troubleshooting page, so it is unchanged.
Verified: `uv run pytest tests/test_checks.py` 13 passed. The guide test passed on its first run because the US1 guide edit already satisfied it, so I probed it: swapping the two lines in the guide failed it, and deleting the daisy_cotton line failed it; guide restored. `uv run pre-commit run --all-files` all passed.
Next: the full suite once, then the report.
Watch: the test reads the guide's list with a regex, so a second INSTALLED_APPS block placed before the first would be the one tested.

## 2026-10-05T15:27:26Z · Implementer US4 · T012

Did: the full suite showed three of my command-level tests failing in the whole run but not alone: a model left registered by tests/test_views/test_base.py (_CustomVerboseModel, models.E023) made `check` raise an unrelated error. The command tests now run `check mvp`, so only the mvp app's models are inspected; nothing is silenced.
Verified: `uv run pytest -n auto --dist loadscope` 2637 passed, 1 skipped, exit 0. `uv run pytest tests/test_checks.py` 13 passed. pre-commit all passed. `uv build` exit 0.
Next: flip T011 and T012 in the ledger and report.
Watch: tests/test_views/test_base.py:217 defines a model with a leading underscore at module level, which stays in the app registry for the rest of a worker's run.

## 2026-10-05T15:30:45Z · Implementer US5 · T013

Did: added tests/test_components/test_daisy_cotton_isolation.py with TestIsolatedCall, five tests over menu.title and stat (leak with only absent, hazard control without only, default slot, named slot, passed attribute).
Verified: `uv run pytest tests/test_components/test_daisy_cotton_isolation.py` 5 passed. Probe: removing `only` from the sources made the isolation test and the default-slot test fail (2 failed, 3 passed). ruff check and ruff format clean.
Next: T014, the rule in CONTRIBUTING.md.
Watch: the test passes on first run because Cotton already behaves this way; the probe above is the red evidence.

## 2026-10-05T15:30:56Z · Implementer US5 · T014

Did: added a "Calling daisy-cotton components" subsection under Component Development in CONTRIBUTING.md: the rule (pass `only`), the reason, what still works, one example.
Verified: `uv run pre-commit run --files CONTRIBUTING.md` passed. No test applies to prose.
Next: ledger flip, full suite, report.
Watch: none.
