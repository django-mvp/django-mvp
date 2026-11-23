"""The prebuilt stylesheet styles every class django-mvp-forms writes.

django-mvp-forms writes classes in two places: its templates, and Python that
the widgets and the form pack join into a ``class`` attribute. The template set
is read from the templates, never by rendering a form. The Python set is read
from the tables and class attributes that hold those classes. The committed
stylesheet is read as text.
"""

from pathlib import Path

import mvp_forms
from mvp_forms import widgets
from mvp_forms.choices import Modifiers
from mvp_forms.templatetags.daisyui import FieldInput

import mvp
from tests.daisy_cotton_classes import component_classes, unstyled_classes

STYLESHEET = (
    Path(next(iter(mvp.__path__))).resolve() / "static" / "css" / "django-mvp.css"
)
MVP_FORMS_TEMPLATES = Path(next(iter(mvp_forms.__path__))).resolve() / "templates"
# Written in a template for django-mvp-forms to replace with a size class
# before the markup is returned, so it never reaches a page.
PLACEHOLDERS = {"daisyui-size"}
# The class attributes a django-mvp-forms widget joins into the markup it draws:
# a choice's input, the input that clears a choice, and a chosen card's edge.
WIDGET_CLASS_ATTRIBUTES = ("input_classes", "clearing_classes", "edge_classes")


def python_classes():
    """Return the classes django-mvp-forms builds in Python.

    These are the size, colour and variant classes of the form pack, the error
    and star classes of a drawn field, and the classes each widget class states
    for its inputs.

    Returns:
        The set of class names.
    """
    written = [
        modifier
        for table in Modifiers.tables.values()
        for modifiers in table.values()
        for modifier in modifiers.values()
    ]
    written += [
        *FieldInput.error_modifiers.values(),
        *FieldInput.star_classes,
        FieldInput.clearing_class,
    ]
    written += [
        getattr(widget, attribute, "")
        for widget in vars(widgets).values()
        if isinstance(widget, type)
        for attribute in WIDGET_CLASS_ATTRIBUTES
    ]
    return {name for classes in written for name in classes.split()}


class TestPrebuiltStylesheet:
    def test_every_mvp_forms_class_is_styled(self):
        classes = component_classes(MVP_FORMS_TEMPLATES) - PLACEHOLDERS

        missing = unstyled_classes(classes, STYLESHEET.read_text(encoding="utf-8"))

        assert classes
        assert not missing, (
            f"{len(missing)} classes django-mvp-forms' templates write have no "
            f"selector in {STYLESHEET}: {sorted(missing)}"
        )

    def test_every_class_mvp_forms_builds_in_python_is_styled(self):
        classes = python_classes()

        missing = unstyled_classes(classes, STYLESHEET.read_text(encoding="utf-8"))

        assert "has-checked:border-primary" in classes
        assert not missing, (
            f"{len(missing)} classes django-mvp-forms builds in Python have no "
            f"selector in {STYLESHEET}: {sorted(missing)}"
        )
