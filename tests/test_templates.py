"""The default ``base.html`` django-mvp ships for hosts that do not write one.

``page_view.html`` and everything under it extend the unqualified ``base.html``.
That name is the project's to own, so a project template always wins — but a
reusable app cannot ask its host to write one, and without a fallback the whole
packaged chain raises ``TemplateDoesNotExist``. The package therefore ships a
``base.html`` that forwards to ``mvp/base.html`` and defines nothing of its own.

The first three tests run against a package-only engine, because the test
project (``demo``) ships its own ``base.html`` and shadows the packaged one in
the configured engine — which is what the last test asserts.
"""

from pathlib import Path

import pytest
from django.apps import apps
from django.conf import settings
from django.template import Engine, engines
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode

MVP_TEMPLATES = Path(apps.get_app_config("mvp").path) / "templates"


@pytest.fixture
def package_only_engine():
    """An engine that can see django-mvp's templates and nothing else.

    Stands in for a host that installed django-mvp and wrote no template of
    its own — the case the issue reported.
    """
    configured = engines["django"].engine
    return Engine(
        dirs=[str(MVP_TEMPLATES)],
        app_dirs=False,
        libraries=configured.libraries,
        builtins=configured.builtins,
    )


class TestDefaultBaseTemplate:
    def test_the_package_ships_one(self, package_only_engine):
        assert package_only_engine.get_template("base.html") is not None

    def test_it_forwards_to_the_packaged_shell(self, package_only_engine):
        template = package_only_engine.get_template("base.html")

        extends = [n for n in template.nodelist if isinstance(n, ExtendsNode)]

        assert len(extends) == 1
        assert extends[0].parent_name.var == "mvp/base.html"

    def test_it_defines_nothing_of_its_own(self, package_only_engine):
        """Forwarding only. A block here would silently override the shell's."""
        template = package_only_engine.get_template("base.html")
        extends = next(n for n in template.nodelist if isinstance(n, ExtendsNode))

        assert list(extends.blocks) == []
        assert extends.nodelist.get_nodes_by_type(BlockNode) == []

    def test_the_packaged_page_chain_resolves_without_a_project_template(
        self, package_only_engine
    ):
        """The reported symptom: ``page_view.html`` could not find its parent."""
        for name in (
            "page_view.html",
            "list_view.html",
            "detail_view.html",
            "form_view.html",
            "delete_view.html",
            "table_view.html",
        ):
            template = package_only_engine.get_template(name)
            extends = next(n for n in template.nodelist if isinstance(n, ExtendsNode))

            assert package_only_engine.get_template(extends.parent_name.var)

    def test_an_app_listed_above_mvp_still_wins(self):
        """The override rule getting-started documents, exercised for real.

        ``demo`` ships its own ``base.html`` and sits above ``mvp`` in
        ``INSTALLED_APPS``, so the app template loader reaches it first.
        """
        installed = settings.INSTALLED_APPS
        assert installed.index("demo") < installed.index("mvp")

        origin = get_template("base.html").origin.name

        assert MVP_TEMPLATES not in Path(origin).parents
        assert Path(origin).parts[-3:] == ("demo", "templates", "base.html")
