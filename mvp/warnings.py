"""Warning categories raised by django-mvp."""


class MVPDeprecationWarning(DeprecationWarning):
    """Raised where django-mvp still accepts something it intends to remove.

    A dedicated category so a project can surface this package's deprecations
    without unmasking every other dependency's. Python ignores
    ``DeprecationWarning`` by default, so opt in explicitly::

        # pyproject.toml
        [tool.pytest.ini_options]
        filterwarnings = ["error::mvp.warnings.MVPDeprecationWarning"]

    or at runtime::

        warnings.simplefilter("always", MVPDeprecationWarning)
    """


MENU_DRIVEN_DOCK = (
    "The menu-driven dock (MobileFooterMenu, MobileFooterNavRenderer and the menu "
    "path of cotton/app/dock.html) is deprecated. Declare the dock in a template "
    "with <c-dock> and <c-mvp.dock.item> by overriding cotton/app/dock.html; see "
    "the mobile dock in docs/navigation.md."
)
