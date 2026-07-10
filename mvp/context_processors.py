"""Context processors for django-mvp."""

from .config import MVP_CONFIG


def mvp_config(request):
    """Provide MVP configuration to all templates.

    Exposes the merged MVP_CONFIG dict as ``mvp_config`` so templates and
    Cotton components can read settings-driven configuration, e.g.
    ``{{ mvp_config.layout.sidebar.breakpoint }}``.
    """

    return {
        "mvp_config": MVP_CONFIG,
    }
