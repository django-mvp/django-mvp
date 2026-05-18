from django.conf import settings


def _get_or_default(name, default):
    return getattr(settings, name, default)


MVP_DEFAULT_VIEW_NAMES = _get_or_default(
    "MVP_DEFAULT_VIEW_NAMES",
    {
        "list": "{model_name}-list",
        "detail": "{model_name}-detail",
        "create": "{model_name}-create",
        "update": "{model_name}-update",
        "delete": "{model_name}-delete",
    },
)


MVP_LANDING_PAGE_HERO = _get_or_default(
    "MVP_LANDING_PAGE_HERO",
    {
        "subtitle": "Your new website",
        "title": "Django MVP",
        "lead": "A Django app to jumpstart your next project with a clean, modular architecture and modern design.",
        "image": "mvp/landing_hero.png",
    },
)

MVP_AVATAR_URL_FUNCTION = _get_or_default(
    "MVP_AVATAR_URL_FUNCTION", "mvp.utils.avatar_url"
)
