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
    "addons/django_table.html": "requires a django-tables2 Table instance",
}

TEMPLATES = sorted(
    p.relative_to(COTTON_DIR).as_posix()
    for p in COTTON_DIR.rglob("*.html")
)


def test_inventory_is_nonempty():
    assert len(TEMPLATES) > 50, "cotton template discovery looks broken"


@pytest.mark.django_db
@pytest.mark.parametrize("relpath", TEMPLATES)
def test_component_template_renders(relpath):
    if relpath in SKIP:
        pytest.skip(SKIP[relpath])

    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    # `name` satisfies c-icon, the one component whose only attribute is
    # genuinely required. Everything else must survive an empty context.
    render_to_string(f"cotton/{relpath}", {"name": "home"}, request=request)
