"""System checks for the kinds a site registers and the search setting."""

from collections.abc import Collection, Sequence
from typing import Any

from django.apps import apps
from django.core import checks
from django.core.checks import CheckMessage
from modelsearch import index

from mvp.config import MVP_CONFIG
from mvp.search import registry
from mvp.search.kinds import Kind, ModelKind


def model_kinds(kinds: Sequence[Kind]) -> list[ModelKind]:
    """Pick the model kinds out of a list of kinds.

    Args:
        kinds: Registered kinds of any sort.

    Returns:
        The kinds that are :class:`~mvp.search.kinds.ModelKind` instances.
    """
    return [kind for kind in kinds if isinstance(kind, ModelKind)]


def unregistered_kind_messages(
    names: Sequence[str], registered: Collection[str]
) -> list[CheckMessage]:
    """Judge the kind names ``MVP_CONFIG["search"]["kinds"]`` holds.

    Args:
        names: The names the setting lists.
        registered: The names kinds are registered under.

    Returns:
        One ``mvp.E004`` error for each name no kind is registered under.
    """
    return [
        checks.Error(
            f'MVP_CONFIG["search"]["kinds"] names {name!r}, '
            "but no search kind is registered under that name.",
            hint="Register the kind from AppConfig.ready, or remove the name.",
            id="mvp.E004",
        )
        for name in names
        if name not in registered
    ]


def unindexed_model_messages(kinds: Sequence[Kind]) -> list[CheckMessage]:
    """Judge whether each model kind's model is indexed by modelsearch.

    Args:
        kinds: Registered kinds of any sort.

    Returns:
        One ``mvp.E006`` error for each model kind whose model is not indexed.
    """
    return [
        checks.Error(
            f"The search kind {kind.name!r} searches {kind.model.__name__}, "
            "which modelsearch does not index.",
            hint="Make the model inherit index.Indexed and give it search_fields.",
            id="mvp.E006",
        )
        for kind in model_kinds(kinds)
        if not index.class_is_indexed(kind.model)
    ]


def missing_pk_filter_messages(kinds: Sequence[Kind]) -> list[CheckMessage]:
    """Judge whether each indexed model filters on its primary key.

    Args:
        kinds: Registered kinds of any sort.

    Returns:
        One ``mvp.E007`` error for each model kind whose indexed model has no
        ``FilterField`` on its primary key. A model that is not indexed is left
        to :func:`unindexed_model_messages`.
    """
    messages: list[CheckMessage] = []
    for kind in model_kinds(kinds):
        model: Any = kind.model
        if not index.class_is_indexed(model):
            continue
        pk_attname = model._meta.pk.attname  # type: ignore[union-attr]
        filtered = {
            field.get_attname(model)
            for field in model.get_search_fields()
            if isinstance(field, index.FilterField)
        }
        if pk_attname not in filtered:
            messages.append(
                checks.Error(
                    f"The search kind {kind.name!r} searches {model.__name__}, "
                    f"which has no FilterField on its primary key {pk_attname!r}.",
                    hint=f'Add index.FilterField("{pk_attname}") to search_fields. '
                    '"pk" is not recognised.',
                    id="mvp.E007",
                )
            )
    return messages


def missing_modelsearch_messages(
    kinds: Sequence[Kind], app_names: Collection[str]
) -> list[CheckMessage]:
    """Judge whether model kinds have the app they need.

    Args:
        kinds: Registered kinds of any sort.
        app_names: The names of the installed apps.

    Returns:
        One ``mvp.E008`` error when a model kind is registered and
        ``modelsearch`` is not in ``INSTALLED_APPS``, and nothing otherwise.
    """
    if not model_kinds(kinds) or "modelsearch" in app_names:
        return []
    return [
        checks.Error(
            "A model kind is registered, but modelsearch is not in INSTALLED_APPS.",
            hint='Add "modelsearch" to INSTALLED_APPS and run migrate.',
            id="mvp.E008",
        )
    ]


def check_search(app_configs: Any, **kwargs: Any) -> list[CheckMessage]:
    """Tell the project when its search kinds or setting are wrong.

    Args:
        app_configs: The app configs Django asks the check about. Unused.
        **kwargs: Anything else Django passes a check. Unused.

    Returns:
        The messages from the four checks above for the registered kinds and the
        installed apps.
    """
    kinds = registry.default_registry.registered()
    return [
        *unregistered_kind_messages(
            MVP_CONFIG["search"]["kinds"],  # type: ignore[index]
            {kind.name for kind in kinds},
        ),
        *unindexed_model_messages(kinds),
        *missing_pk_filter_messages(kinds),
        *missing_modelsearch_messages(
            kinds, [config.name for config in apps.get_app_configs()]
        ),
    ]
