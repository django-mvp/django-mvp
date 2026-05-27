"""Context processors for django-mvp."""

import json
import logging

logger = logging.getLogger(__name__)


def mvp_config(request):
    """Provide MVP configuration to all templates.

    Returns:
        dict: Dictionary containing 'mvp' key with default configuration.
    """
    config = {
        "brand": {
            "text": "Django MVP",
            "logo": None,
            "icon": None,
        },
        "layout": {
            "fixed_sidebar": False,
            "sidebar_expand": "lg",
            "body_class": "sidebar-expand-lg",
        },
        "sidebar": {
            "visible": True,
            "width": "280px",
        },
        "footer": {
            "visible": True,
            "text": None,
        },
        "actions": [],
    }

    return {
        "mvp": json.dumps(config),
    }
