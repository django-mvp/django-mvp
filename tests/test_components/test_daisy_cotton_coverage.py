"""The prebuilt stylesheet styles every class daisy-cotton's components can render.

The class set is read from daisy-cotton's templates, never by rendering a
component, and the committed stylesheet is read as text.
"""

import re
from io import StringIO
from pathlib import Path

import daisy_cotton
import pytest
from django.core.management import call_command

import mvp
from tests.daisy_cotton_classes import (
    component_classes,
    safelisted_classes,
    unstyled_classes,
)

STYLESHEET = (
    Path(next(iter(mvp.__path__))).resolve() / "static" / "css" / "django-mvp.css"
)
DAISY_COTTON_TEMPLATES = Path(next(iter(daisy_cotton.__path__))).resolve() / "templates"
LITERAL_SEPARATORS = re.compile(r"[\s\"'<>{}%]+")


def written_literally(directory):
    """Return the class names written whole in any file under a directory.

    A name is written whole when it is a token of the file's text split on
    whitespace, quotes and the characters ``< > { } %``. Tailwind does not pick
    a class out next to a comma, ``=``, ``;`` or a parenthesis, so neither does
    this.

    Args:
        directory: The directory to read, recursively.

    Returns:
        The set of tokens.
    """
    tokens = set()
    for path in Path(directory).rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            tokens |= set(LITERAL_SEPARATORS.split(text))
    return tokens


class TestPrebuiltStylesheet:
    def test_every_daisy_cotton_class_is_styled(self):
        classes = component_classes(DAISY_COTTON_TEMPLATES)

        missing = unstyled_classes(classes, STYLESHEET.read_text(encoding="utf-8"))

        assert classes
        assert not missing, (
            f"{len(missing)} classes daisy-cotton's components can render have no "
            f"selector in {STYLESHEET}: {sorted(missing)}"
        )


class TestGeneratedEntry:
    @pytest.fixture
    def entry_paths(self):
        """The preset's text and the directory the generated entry scans."""
        out = StringIO()
        call_command("mvp_tailwind", "--paths", stdout=out)
        lines = out.getvalue().strip().splitlines()
        return Path(lines[0]).read_text(encoding="utf-8"), Path(lines[3])

    def test_every_daisy_cotton_class_is_covered(self, entry_paths):
        preset, scanned = entry_paths
        classes = component_classes(DAISY_COTTON_TEMPLATES)

        missing = classes - written_literally(scanned) - safelisted_classes(preset)

        assert classes
        assert not missing, (
            f"{len(missing)} classes daisy-cotton's components can render are "
            f"neither written in a file under {scanned} nor declared by the "
            f"preset: {sorted(missing)}"
        )
