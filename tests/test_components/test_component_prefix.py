"""Tests that every component the package keeps sits under the ``mvp`` prefix.

The package's components live under ``mvp/templates/cotton/mvp/`` and are reached
as ``<c-mvp.…>``. The exceptions are the icon and the basic components that
daisy-cotton also ships, which keep their bare names until they are removed.

Source: mvp/templates/cotton/
"""

import importlib.util
from pathlib import Path

import pytest
from django.template import TemplateDoesNotExist

import mvp

COTTON_DIR = Path(next(iter(mvp.__path__))).resolve() / "templates" / "cotton"

PREFIX_EXCEPTIONS = frozenset(
    {
        "alert.html",
        "avatar/group.html",
        "badge.html",
        "breadcrumbs/index.html",
        "breadcrumbs/item.html",
        "button.html",
        "divider.html",
        "dock/index.html",
        "dock/item.html",
        "icon.html",
        "link.html",
        "menu/index.html",
        "mockup/browser.html",
        "mockup/code/index.html",
        "mockup/code/line.html",
        "mockup/phone.html",
        "mockup/window.html",
    }
)


def template_paths(directory):
    """Return every component template under ``directory``, relative to it."""
    return {p.relative_to(directory).as_posix() for p in directory.rglob("*.html")}


class TestComponentPrefix:
    def test_every_template_is_under_the_prefix_or_an_exception(self):
        outside = {
            path
            for path in template_paths(COTTON_DIR)
            if not path.startswith("mvp/") and path not in PREFIX_EXCEPTIONS
        }

        assert not outside, f"templates outside cotton/mvp/: {sorted(outside)}"

    def test_every_exception_exists(self):
        missing = PREFIX_EXCEPTIONS - template_paths(COTTON_DIR)

        assert not missing, f"exceptions with no template: {sorted(missing)}"

    @pytest.mark.parametrize("name", ["page", "toolbar", "data-field"])
    def test_a_moved_components_old_bare_name_does_not_resolve(
        self, cotton_render_string, name
    ):
        with pytest.raises(TemplateDoesNotExist):
            cotton_render_string(f"<c-{name}></c-{name}>")


@pytest.mark.skipif(
    importlib.util.find_spec("daisy_cotton") is None,
    reason="daisy_cotton is not installed",
)
class TestNamesSharedWithDaisyCotton:
    def test_the_shared_template_paths_are_exactly_the_exceptions(self):
        import daisy_cotton

        theirs = template_paths(
            Path(next(iter(daisy_cotton.__path__))) / "templates" / "cotton"
        )

        shared = template_paths(COTTON_DIR) & theirs

        assert shared == PREFIX_EXCEPTIONS
