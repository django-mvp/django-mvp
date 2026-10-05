"""System checks for how a project lists django-mvp and daisy-cotton."""

from collections.abc import Sequence
from typing import Any

from django.apps import apps
from django.core import checks
from django.core.checks import CheckMessage

HINT = 'List "daisy_cotton" in INSTALLED_APPS directly below "mvp".'


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
