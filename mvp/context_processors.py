"""Context processors for django-mvp."""

import json

from .config import MVP_CONFIG


def mvp_config(request):
    """Provide MVP configuration to all templates.

    Passes the merged MVP_CONFIG dict as JSON under the 'mvp' key.
    """

    return {
        "mvp": json.dumps(MVP_CONFIG),
    }
