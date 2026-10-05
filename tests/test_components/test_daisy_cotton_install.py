"""The daisy-cotton install: the dependency package metadata declares, and which
package each Cotton component path resolves to when both are installed.

Component paths are worked out from the two installed template trees. No list of
names is copied here.
"""

from importlib import metadata
from pathlib import Path

import daisy_cotton
import pytest
from django import template
from django.apps import apps
from django.template.context import Context
from django.template.loader import get_template
from django_cotton.compiler_regex import CottonCompiler
from packaging.requirements import Requirement

import mvp

compiler = CottonCompiler()


class ComponentTrees:
    """The component paths each installed package ships, read from its templates."""

    mvp_templates = Path(next(iter(mvp.__path__))).resolve() / "templates"
    daisy_templates = Path(next(iter(daisy_cotton.__path__))).resolve() / "templates"

    @classmethod
    def paths(cls, templates_dir):
        """Component paths under a package's `cotton` directory.

        Args:
            templates_dir: The package's templates directory.

        Returns:
            The set of paths relative to `templates/cotton`, as POSIX strings.
        """
        root = templates_dir / "cotton"
        return {p.relative_to(root).as_posix() for p in root.rglob("*.html")}

    @classmethod
    def shared(cls):
        """Paths both packages ship."""
        return cls.paths(cls.mvp_templates) & cls.paths(cls.daisy_templates)

    @classmethod
    def daisy_only(cls):
        """Paths only daisy-cotton ships."""
        return cls.paths(cls.daisy_templates) - cls.paths(cls.mvp_templates)

    @classmethod
    def origin(cls, path):
        """The file Django's loaders return for a component path."""
        return Path(get_template(f"cotton/{path}").origin.name).resolve()

    @classmethod
    def tag(cls, path):
        """The Cotton tag name that calls the component at a path."""
        parts = path.removesuffix(".html").split("/")
        if parts[-1] == "index":
            parts.pop()
        return ".".join(part.replace("_", "-") for part in parts)


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


class TestSharedComponents:
    def test_the_two_packages_share_components(self):
        assert ComponentTrees.shared()

    @pytest.mark.parametrize("path", sorted(ComponentTrees.shared()))
    def test_a_shared_component_resolves_to_mvp(self, path):
        origin = ComponentTrees.origin(path)

        assert origin.is_relative_to(ComponentTrees.mvp_templates)


class TestDaisyCottonOnlyComponents:
    def test_daisy_cotton_ships_components_mvp_does_not(self):
        assert ComponentTrees.daisy_only()

    @pytest.mark.parametrize("path", sorted(ComponentTrees.daisy_only()))
    def test_a_daisy_cotton_only_component_resolves_to_daisy_cotton(self, path):
        origin = ComponentTrees.origin(path)

        assert origin.is_relative_to(ComponentTrees.daisy_templates)

    @pytest.mark.parametrize("path", sorted(ComponentTrees.daisy_only()))
    def test_a_daisy_cotton_only_component_renders_in_isolation(self, path):
        tag = ComponentTrees.tag(path)
        source = f"<c-{tag} only>x</c-{tag}>"

        html = template.Template(compiler.process(source)).render(Context())

        assert html
