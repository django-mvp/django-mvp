"""How the app reads its own preferences, apart from where it declares them."""

from object_preferences.registry import registry


def page_size_for(person) -> int:
    """Read a person's items per page, or the default when they have not chosen.

    Args:
        person: A user of the project.

    Returns:
        The number of items to show on a page.
    """
    return registry.get_preferences(person)["reminders"]["page_size"]
