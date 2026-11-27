"""Render-smoke test: every packaged Cotton component template must render.

Renders each template under mvp/templates/cotton/ directly with a request
context and permissive (mostly-empty) variables. This catches missing
{% load %} tags, references to non-existent subcomponents, and broken template
syntax — the failure modes that silently break components until a page uses
them.

It does NOT validate component attribute APIs; it is a floor, not a spec.
"""

from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

import mvp

COTTON_DIR = Path(next(iter(mvp.__path__))).resolve() / "templates" / "cotton"

# Templates that need context this smoke test can't fake — each entry needs a
# reason and ideally a dedicated test elsewhere.
SKIP = {
    "mvp/addons/django_table.html": "requires a django-tables2 Table instance",
}

TEMPLATES = sorted(
    p.relative_to(COTTON_DIR).as_posix() for p in COTTON_DIR.rglob("*.html")
)
# The search components that reverse addresses the default URLconf does not mount.
SEARCH_TEMPLATES = ["mvp/actions/search.html", "mvp/search/dialog.html"]

# Those two are rendered by TestSearchComponentRenderSmoke instead.
TEMPLATES = [t for t in TEMPLATES if t not in SEARCH_TEMPLATES]


class TestComponentRenderSmoke:
    def test_inventory_is_nonempty(self):
        assert len(TEMPLATES) > 50, "cotton template discovery looks broken"

    @pytest.mark.django_db
    def test_every_component_template_renders_without_leaking_template_tags(self):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        failures = []
        for relpath in TEMPLATES:
            if relpath in SKIP:
                continue
            try:
                # `name` satisfies c-icon, the one component whose only attribute
                # is genuinely required. Everything else must survive an empty
                # context.
                html = render_to_string(
                    f"cotton/{relpath}", {"name": "home"}, request=request
                )
            except Exception as error:
                failures.append(f"{relpath}: {type(error).__name__}: {error}")
                continue
            # A default written as a template tag reaches the page as source when
            # its library is not loaded where the default is compiled.
            if "{%" in html:
                failures.append(f"{relpath}: output contains an unrendered tag")

        assert not failures, "\n".join(failures)


@pytest.mark.urls("tests.urls_search")
@pytest.mark.django_db
class TestSearchComponentRenderSmoke:
    """The search components render where the search's addresses are mounted."""

    @pytest.mark.parametrize("relpath", SEARCH_TEMPLATES)
    def test_component_template_renders(self, relpath):
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        html = render_to_string(f"cotton/{relpath}", {"name": "home"}, request=request)

        assert "{%" not in html
        assert 'id="mvp-search"' in html
