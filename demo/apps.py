"""Demo app configuration."""

from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Demo app configuration.

    Automatically loads menu definitions on app startup to populate
    the navigation menu with demo items.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "demo"

    def ready(self):
        """Import the menu definitions and register the search kinds."""
        import contextlib

        from django.utils.translation import gettext_lazy as _

        from mvp.search import register, registered

        from .search import ArticleKind, ProductKind, find_components

        with contextlib.suppress(ImportError):
            from . import menus  # noqa: F401

        # Tests that reload the app registry run ready() again in one process.
        taken = {kind.name for kind in registered()}
        for kind in (ProductKind(), ArticleKind()):
            if kind.name not in taken:
                register(kind)
        if "components" not in taken:
            register(
                find_components,
                name="components",
                label=_("Components"),
                icon="grid",
                description=_("Documentation pages for the components"),
            )

    verbose_name = "Demo"
