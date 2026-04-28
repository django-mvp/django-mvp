from django.conf import settings


def _get_or_default(name, default):
    return getattr(settings, name, default)


MVP_DEFAULT_VIEW_NAMES = _get_or_default(
    "MVP_DEFAULT_VIEW_NAMES",
    {
        "list": "{model_name}-list",
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-edit",
        "delete": "{model_name}-delete",
    },
)
