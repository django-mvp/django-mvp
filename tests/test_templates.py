"""Tests for the package-qualified page/list template chain (#219).

`page_view.html` used to `{% extends "base.html" %}` — an unqualified name
that only resolves against a project's own template, since django-mvp ships
no top-level `base.html` of its own (`mvp/base.html` is a different name).
That made the packaged page/list/detail/form/delete/table chain reachable
only from a project, never from a reusable app: an app has no way to supply
a project-wide `base.html`, so `get_template("base.html")` — and everything
that extends it — raised `TemplateDoesNotExist`.

A package-qualified chain under `mvp/` fixes that: `mvp/page_view.html`
extends `mvp/base.html` directly, and `mvp/list_view.html`,
`mvp/detail_view.html`, `mvp/form_view.html`, `mvp/delete_view.html` and
`mvp/table_view.html` extend it (or each other) in the same shape as the
project-facing chain. The project-facing names now delegate to their
qualified equivalent, so nothing changes for a project while a reusable app
can extend the qualified name and inherit every later improvement.

These tests exercise raw `.html` template files under `mvp/templates/`,
which have no Python module behind them to mirror — declared in
`pyproject.toml` under `[tool.forge.conformance] non-mirror-paths`, the same
carve-out `tests/test_components/` uses for Cotton templates.
"""

from pathlib import Path

import pytest
from django.template.loader import get_template

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "mvp" / "templates"

# name -> the qualified parent it must extend
QUALIFIED_CHAIN = {
    "page_view.html": "mvp/base.html",
    "list_view.html": "mvp/page_view.html",
    "detail_view.html": "mvp/page_view.html",
    "form_view.html": "mvp/page_view.html",
    "delete_view.html": "mvp/form_view.html",
    "table_view.html": "mvp/list_view.html",
}


class TestPackageQualifiedTemplateChain:
    """`mvp/<name>` exists for every template a reusable app needs to
    extend, and each one extends its qualified parent rather than an
    unqualified name a reusable app cannot supply."""

    @pytest.mark.parametrize("name", QUALIFIED_CHAIN)
    def test_qualified_template_loads(self, name):
        """`mvp/<name>` resolves through the loader — the reported symptom
        was `TemplateDoesNotExist` on exactly this lookup."""
        get_template(f"mvp/{name}")

    @pytest.mark.parametrize("name,parent", QUALIFIED_CHAIN.items())
    def test_qualified_template_extends_its_qualified_parent(self, name, parent):
        content = (TEMPLATES_DIR / "mvp" / name).read_text(encoding="utf-8")
        assert f'{{% extends "{parent}" %}}' in content, (
            f"mvp/{name} must extend {parent!r} — extending an unqualified "
            "name here would reintroduce the reusable-app defect (#219)."
        )


class TestProjectFacingTemplatesDelegateToTheQualifiedChain:
    """The project-facing names (`page_view.html`, etc.) are unchanged from
    a project's point of view, but now delegate to the `mvp/`-qualified
    chain instead of pulling in an unqualified name directly."""

    @pytest.mark.parametrize("name", QUALIFIED_CHAIN)
    def test_project_facing_template_extends_its_qualified_equivalent(self, name):
        content = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
        assert f'{{% extends "mvp/{name}" %}}' in content, (
            f"{name} must extend 'mvp/{name}' so a project sees no change "
            "while a reusable app can extend the qualified name directly "
            "(#219)."
        )
