
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
