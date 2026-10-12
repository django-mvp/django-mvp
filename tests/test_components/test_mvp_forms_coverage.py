"""The prebuilt stylesheet styles every class django-mvp-forms' templates write.

The class set is read from django-mvp-forms' templates, never by rendering a
form, and the committed stylesheet is read as text.
"""

from pathlib import Path

import mvp_forms

import mvp
from tests.daisy_cotton_classes import component_classes, unstyled_classes

STYLESHEET = (
    Path(next(iter(mvp.__path__))).resolve() / "static" / "css" / "django-mvp.css"
)
MVP_FORMS_TEMPLATES = Path(next(iter(mvp_forms.__path__))).resolve() / "templates"
# Written in a template for django-mvp-forms to replace with a size class
# before the markup is returned, so it never reaches a page.
PLACEHOLDERS = {"daisyui-size"}


class TestPrebuiltStylesheet:
    def test_every_mvp_forms_class_is_styled(self):
        classes = component_classes(MVP_FORMS_TEMPLATES) - PLACEHOLDERS

        missing = unstyled_classes(classes, STYLESHEET.read_text(encoding="utf-8"))

        assert classes
        assert not missing, (
            f"{len(missing)} classes django-mvp-forms' templates write have no "
            f"selector in {STYLESHEET}: {sorted(missing)}"
        )
