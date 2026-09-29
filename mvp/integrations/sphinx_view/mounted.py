"""Sphinx documentation as a mounted app.

The host creates an instance pointing at its JSON build and mounts it::

    # mounted.py
    from mvp.integrations.sphinx_view.mounted import DocumentationApp

    docs = DocumentationApp(json_build_dir=BASE_DIR / "docs/_build/json")

    # urls.py
    urlpatterns = [mount("docs/", docs)]

    # menus.py
    AppMenu.append(docs.menu_item())

On the documentation's pages the sidebar draws the docs' own contents under
the "Back to" link, built from the ``navigation.json`` that
``mvp.integrations.sphinx_view.navigation`` writes during the Sphinx build.
"""

from django.urls import path
from django.utils.translation import gettext_lazy as _

from mvp.mounted import MountedApp

from .menus import DocumentationMenu
from .views import MVPDocumentationView


class DocumentationApp(MountedApp):
    """A Sphinx JSON build, served inside the application shell.

    Attributes:
        json_build_dir: The directory ``sphinx-build -b json`` wrote to.
        namespace: The URL namespace the pages reverse under.
        view_class: The view that renders a page.
    """

    name = _("Documentation")
    icon = "documentation"
    namespace = "docs"
    landing = "docs:index"
    json_build_dir = None
    view_class = MVPDocumentationView

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        view = self.view_class.as_view(json_build_dir=self.json_build_dir)
        self.urls = (
            [
                path("", view, {"path": ""}, name="index"),
                path("<path:path>", view, name="page"),
            ],
            self.namespace,
        )
        self.landing = f"{self.namespace}:index"
        self.menu = DocumentationMenu(f"{self.namespace}-menu", app=self)
