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
