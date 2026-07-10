"""Optional integrations with third-party packages.

Each subpackage integrates exactly one third-party package and is never
imported by django-mvp's core. The required package is therefore only needed
when a project explicitly imports from the integration, e.g.::

    from mvp.integrations.django_tables.views import MVPTableView

Importing an integration without its dependency installed raises
``ImproperlyConfigured`` with install instructions.
"""

from django.core.exceptions import ImproperlyConfigured


def missing_dependency(integration: str, pip_name: str) -> ImproperlyConfigured:
    """Return the error to raise when an integration's dependency is absent.

    Usage::

        try:
            from some_package import Something
        except ImportError as e:
            raise missing_dependency("some_integration", "some-package") from e
    """
    return ImproperlyConfigured(
        f"mvp.integrations.{integration} requires the '{pip_name}' package. "
        f"Install it with: pip install {pip_name}"
    )
