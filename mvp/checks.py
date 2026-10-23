"""System checks for how a project lists django-mvp and daisy-cotton, and names its title layouts."""

from collections.abc import Sequence
from typing import Any

from django.apps import apps
from django.core import checks
from django.core.checks import CheckMessage
from django.core.exceptions import ImproperlyConfigured

from .config import MVP_CONFIG
from .utils import title_layout_component

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
