"""System checks for how a project lists django-mvp and daisy-cotton, names its title layouts and themes its email."""

from collections.abc import Sequence
from typing import Any

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.core.checks import CheckMessage
from django.core.exceptions import ImproperlyConfigured

from .config import MVP_CONFIG
from .email.brand import EmailBrand
from .utils import title_layout_component

HINT = 'List "daisy_cotton" in INSTALLED_APPS directly below "mvp".'

AUTHENTICATION_MIDDLEWARE = "django.contrib.auth.middleware.AuthenticationMiddleware"
PREFERENCES_MIDDLEWARE = "mvp.middleware.PreferencesMiddleware"


def daisy_cotton_app_messages(app_names: Sequence[str]) -> list[CheckMessage]:
    """Judge where ``daisy_cotton`` sits among the installed apps.

    Args:
        app_names: The names of the installed apps, in the order they are listed.

    Returns:
        An error when ``daisy_cotton`` is missing, a warning when it is listed
        before ``mvp``, and nothing otherwise.
    """
    if "daisy_cotton" not in app_names:
        return [
            checks.Error(
                'The app "daisy_cotton" is not in INSTALLED_APPS.',
                hint=HINT,
                id="mvp.E002",
            )
        ]
    if "mvp" in app_names and app_names.index("daisy_cotton") < app_names.index("mvp"):
        return [
            checks.Warning(
                'The app "daisy_cotton" is listed above "mvp" in INSTALLED_APPS.',
                hint=HINT,
                id="mvp.W001",
            )
        ]
    return []


def check_daisy_cotton_app(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project when ``daisy_cotton`` is missing or listed above ``mvp``.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        The messages from :func:`daisy_cotton_app_messages` for the installed apps.
    """
    return daisy_cotton_app_messages([config.name for config in apps.get_app_configs()])


def page_title_layout_messages(layout: str | dict[str, str]) -> list[CheckMessage]:
    """Judge the names in the page title layout setting.

    Args:
        layout: The value of ``MVP_CONFIG["page_title"]["layout"]``: one layout name
            for every page, or a dict of layout names by page type.

    Returns:
        One error for each name that is neither a shipped layout nor a Cotton
        component the project provides, and nothing when every name resolves.
    """
    names = layout.values() if isinstance(layout, dict) else [layout]
    messages: list[CheckMessage] = []
    for name in names:
        try:
            title_layout_component(name)
        except ImproperlyConfigured as error:
            messages.append(
                checks.Error(
                    str(error),
                    hint='Fix MVP_CONFIG["page_title"]["layout"].',
                    id="mvp.E003",
                )
            )
    return messages


def check_page_title_layout(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project when the page title layout setting names a layout it lacks.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        The messages from :func:`page_title_layout_messages` for the merged setting.
    """
    return page_title_layout_messages(MVP_CONFIG["page_title"]["layout"])  # type: ignore[index]


def check_email_brand(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project which theme colours and logos its email cannot use.

    Nothing here stops an email rendering: each problem is a warning, and the
    email takes the package's colour or logo in its place.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        One warning for each problem in :meth:`EmailBrand.problems`, or a single
        warning when the brand cannot be read at all, as when a static file
        manifest does not exist yet.
    """
    try:
        problems = EmailBrand.problems()
    except ValueError as error:
        return [
            checks.Warning(f"The email brand could not be read: {error}", id="mvp.W005")
        ]
    return [
        checks.Warning(problem.message, hint=problem.hint, id=problem.id)
        for problem in problems
    ]


def object_preferences_app_messages(app_names: Sequence[str]) -> list[CheckMessage]:
    """Judge whether ``object_preferences`` is among the installed apps.

    Args:
        app_names: The names of the installed apps.

    Returns:
        An error when ``object_preferences`` is missing, and nothing otherwise.
    """
    if "object_preferences" in app_names:
        return []
    return [
        checks.Error(
            'The app "object_preferences" is not in INSTALLED_APPS.',
            hint=(
                'List "object_preferences" in INSTALLED_APPS, and add '
                "mvp.models.PreferencesMixin to your user model."
            ),
            id="mvp.E004",
        )
    ]


def check_object_preferences_app(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project when ``object_preferences`` is not installed.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        The messages from :func:`object_preferences_app_messages` for the installed apps.
    """
    return object_preferences_app_messages(
        [config.name for config in apps.get_app_configs()]
    )


def preferences_middleware_messages(middleware: Sequence[str]) -> list[CheckMessage]:
    """Judge where the preferences middleware sits in ``MIDDLEWARE``.

    Args:
        middleware: The dotted paths in ``MIDDLEWARE``, in order.

    Returns:
        A warning when the preferences middleware is missing or listed before
        the authentication middleware, and nothing otherwise.
    """
    if PREFERENCES_MIDDLEWARE in middleware and (
        AUTHENTICATION_MIDDLEWARE not in middleware
        or middleware.index(PREFERENCES_MIDDLEWARE)
        > middleware.index(AUTHENTICATION_MIDDLEWARE)
    ):
        return []
    return [
        checks.Warning(
            f'"{PREFERENCES_MIDDLEWARE}" is missing from MIDDLEWARE, or listed before the authentication middleware.',
            hint=f'List "{PREFERENCES_MIDDLEWARE}" in MIDDLEWARE below "{AUTHENTICATION_MIDDLEWARE}".',
            id="mvp.W006",
        )
    ]


def check_preferences_middleware(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project when the preferences middleware is missing or misplaced.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        The messages from :func:`preferences_middleware_messages` for ``MIDDLEWARE``.
    """
    return preferences_middleware_messages(list(settings.MIDDLEWARE))
