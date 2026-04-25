from django.conf import settings


def _get_or_default(name, default):
    return getattr(settings, name, default)


MVP_DEFAULT_VIEW_NAMES = _get_or_default(
    "MVP_DEFAULT_VIEW_NAMES",
    {
        "list": "{model_name}_list",
        "detail": "{model_name}_detail",
        "create": "{model_name}_create",
        "update": "{model_name}_edit",
        "delete": "{model_name}_delete",
    },
)
