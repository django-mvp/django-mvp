"""Saving the order a reorderable list was left in."""

from django.core.exceptions import ValidationError
from django.db import transaction


class InvalidOrder(ValueError):
    """Raised when a received order cannot be saved as given."""


def save_order(queryset, ids, *, field="position"):
    """Number a queryset's records in the order the identifiers were given.

    The queryset is the access rule: only its records can be named, and only
    they are written. The order is refused whole, with nothing saved, when it
    names a record twice, names one outside the queryset, leaves one of the
    queryset's records out, or contains an identifier the primary key cannot
    convert.

    Args:
        queryset: The records the order covers, already limited to what the
            current user may reorder.
        ids: The primary keys in their new order, as received (strings are
            converted with the primary key's own ``to_python``).
        field: The integer field that receives ``0, 1, 2, ...``.

    Returns:
        The records, in the order given.

    Raises:
        InvalidOrder: If the order is not exactly the queryset's records,
            each named once.
    """
    pk_field = queryset.model._meta.pk
    try:
        keys = [pk_field.to_python(value) for value in ids]
    except (ValidationError, TypeError, ValueError) as error:
        raise InvalidOrder("An identifier is not a valid primary key.") from error
    if len(set(keys)) != len(keys):
        raise InvalidOrder("An identifier appears more than once.")

    with transaction.atomic():
        records = {record.pk: record for record in queryset}
        if set(keys) != set(records):
            raise InvalidOrder("The order must name each record exactly once.")
        ordered = [records[key] for key in keys]
        for position, record in enumerate(ordered):
            setattr(record, field, position)
        queryset.model._base_manager.bulk_update(ordered, [field])
    return ordered
