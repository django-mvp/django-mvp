# Quickstart: Validating Formset Pages

**Feature**: `024-formset-pages` | **Date**: 2026-08-05

How to prove the feature works, end to end. Each scenario maps to the user story it validates
and to the success criteria it settles. This is a validation guide, not an implementation guide
— the shapes live in `contracts/` and the steps in `tasks.md`.

## Prerequisites

```bash
cd /home/sam/projects/django-mvp/django-mvp
poetry install
```

The full machine check for any stage exit:

```bash
poetry run pytest
poetry run ruff check . && poetry run ruff format --check .
poetry run mypy mvp
poetry run deptry .
```

## Scenario 1 — The clean install (US1, SC-001)

Proves the packaged form rendering no longer depends on a package nobody was told to install.

```bash
poetry run deptry .
poetry run pytest tests/test_views/test_edit.py -k render
```

Expected: deptry reports nothing missing and nothing transitively relied upon, and
`[project].dependencies` in `pyproject.toml` names both `django-crispy-forms` and
`crispy-tailwind`. `README.md` and `docs/getting-started.md` list `crispy_forms` and
`crispy_tailwind` in the required `INSTALLED_APPS` alongside `CRISPY_TEMPLATE_PACK`, because
installing the distributions alone does not make their template tag libraries loadable.

## Scenario 2 — A formset renders with the packaged look (US2, SC-008)

```bash
poetry run pytest tests/test_components/test_form_formset.py
```

Expected: a formset with several rows renders one row per form; each row's fields carry the
same control, label and help-text markup a single form's fields carry; the management form is
present; blank extra rows are indistinguishable from populated ones. Also confirm the floor test
still passes, since both new components are enrolled in it automatically:

```bash
poetry run pytest tests/test_components/test_render_all.py
```

Expected: green with no `SKIP` entry added for either new template.

## Scenario 3 — A record and its rows on one page (US3, SC-002, SC-006)

```bash
poetry run pytest tests/test_views/test_inline.py
```

Expected: configuring `model` plus `inline_model` and `inline_fields` produces a page carrying
the parent form and one row per related record; a valid submission persists both and redirects
by the same rule the single-form pages use; a failure part-way through saving persists neither;
an invalid parent with valid rows persists nothing and re-renders with every submitted value
still present; a create page attaches new rows to the newly-created parent.

To see it in a browser:

```bash
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open the demo product's order-lines page linked from the product detail page.

## Scenario 4 — Errors appear where the problem is (US4, SC-003)

```bash
poetry run pytest tests/test_views/test_inline.py -k error
poetry run pytest tests/test_components/test_form_formset.py -k error
```

Expected: a row-level error renders inside that row and in no other row; a set-level error
renders above the set and is distinguishable from a row's; errors on several rows each render in
their own row; no error renders only as a single page-level message; submitted values survive
the re-render.

## Scenario 5 — Rows in the browser (US5, SC-004, SC-005)

Most of this is provable without a browser and is tested that way, per Article XIV:

```bash
poetry run pytest tests/test_components/test_form_formset.py -k "add or remove or empty_form"
poetry run pytest tests/test_views/test_inline.py -k delete
```

Expected from the markup: the empty-form template is present exactly once and carries
`__prefix__`; the add control is absent or disabled at `max_num`; no remove control is rendered
when the formset forbids deletion; each row's `DELETE` field is hidden rather than a visible
checkbox.

Expected from the view: a submission whose row carries `DELETE` deletes that record; a submission
whose *added* row carries `DELETE` creates nothing; a record whose row was removed on the page
but never submitted is unchanged.

Also expected from the view: a submission whose `TOTAL_FORMS` exceeds the configured
`inline_max_num` is rejected with a set-level error and persists nothing. The add control is
presentation; this is the cap.

The interaction itself needs a real browser and is the one exception Article XIV allows. It lives
beside the components it exercises, as a class with the marker at class level:

```bash
poetry run pytest tests/test_components/test_form_formset.py -m e2e
```

Expected: adding a row inserts a blank row without a reload and increments `TOTAL_FORMS`;
removing a pre-rendered row hides it without a request; **removing the row that was just added**
hides it and sets its `DELETE`, which is the case no server-side test can reach because cloned
markup is inert until Alpine initialises it; and submitting afterwards matches the database to
what the page showed.

## Scenario 6 — The documented path (US6, SC-007)

Manual, and the point is that it is manual: follow `docs/formsets.md` from an empty app to a
rendered parent-and-rows page **without opening the package source**. Anything that forces you
into the source is a defect in the document, not in the reader.

```bash
poetry run pytest tests/test_components/test_render_all.py
```

Then confirm `CONTEXT.md` defines the vocabulary this feature introduces, and `CHANGELOG.md`'s
Unreleased section records the new public surface with an "On upgrade:" note covering the
`INSTALLED_APPS` change.

## Stylesheet

Article XV, and CI cannot check it:

```bash
poetry run invoke build-stylesheet
git status --short mvp/static/css/
```

Expected: `mvp/static/css/django-mvp.css` and its brotli sibling are rebuilt and committed on
this branch.
