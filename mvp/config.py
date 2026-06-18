"""Package configuration for django-mvp.

MVP_CONFIG is the single source of truth for all package settings. It is built by
deep-merging package defaults with user overrides from ``settings.MVP_CONFIG``.
Consumers import it directly::

    from mvp.config import MVP_CONFIG

"""

from django.conf import settings
from mergedeep import merge  # type: ignore[import-untyped]

MVP_CONFIG = {
    "view_names": {
        "list": "{model_name}-list",
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    },
    "brand": {
        "avatar_resolver": "mvp.utils.avatar_url",
        "logo_resolver": "mvp.utils.logo_url",
        "icon_resolver": "mvp.utils.icon_url",
    },
}

merge(MVP_CONFIG, getattr(settings, "MVP_CONFIG", {}))
