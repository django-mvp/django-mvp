"""The daisy-cotton install: the dependency package metadata declares, and which
package each Cotton component path resolves to when both are installed.

Component paths are worked out from the two installed template trees. No list of
names is copied here.
"""

from importlib import metadata

from django.apps import apps
from packaging.requirements import Requirement


class TestDeclaredDependency:
    def declared_requirement(self):
        requirements = [
            Requirement(line) for line in metadata.requires("django-mvp") or []
        ]
        return next((r for r in requirements if r.name == "daisy-cotton"), None)

    def test_metadata_requires_daisy_cotton_unconditionally(self):
        requirement = self.declared_requirement()

        assert requirement is not None
        assert requirement.marker is None
        assert not requirement.extras

    def test_installed_daisy_cotton_satisfies_the_declared_specifier(self):
        requirement = self.declared_requirement()

        assert requirement is not None
        assert metadata.version("daisy-cotton") in requirement.specifier

    def test_daisy_cotton_is_an_installed_app(self):
        assert apps.is_installed("daisy_cotton")
