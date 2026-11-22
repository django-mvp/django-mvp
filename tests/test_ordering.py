"""Tests for ``mvp.ordering.save_order``.

Source: mvp/ordering.py
"""

import pytest
from django.db import transaction
from django.db.models import QuerySet

from mvp.ordering import InvalidOrder, save_order
from tests.factories import ProjectFactory, ProjectTaskFactory


def positions(project):
    """Return ``{title: position}`` for the project's tasks."""
    return {t.title: t.position for t in project.tasks.all()}


@pytest.fixture
def project():
    """A project with three tasks, all at position zero."""
    project = ProjectFactory()
    for title in ("a", "b", "c"):
        ProjectTaskFactory(project=project, title=title)
    return project


def ids_of(project, *titles):
    """Return the primary keys of the named tasks, as strings."""
    return [str(project.tasks.get(title=title).pk) for title in titles]


@pytest.mark.django_db
class TestSaveOrder:
    """Numbering records in the order a list was received."""

    def test_numbers_the_records_in_the_given_order(self, project):
        """Each record's position is its index in the given identifiers."""
        save_order(project.tasks.all(), ids_of(project, "c", "a", "b"))

        assert positions(project) == {"c": 0, "a": 1, "b": 2}

    def test_returns_the_records_in_the_new_order(self, project):
        """The return value lists the records in the order given."""
        saved = save_order(project.tasks.all(), ids_of(project, "b", "c", "a"))

        assert [t.title for t in saved] == ["b", "c", "a"]

    def test_accepts_identifiers_as_strings(self, project):
        """Identifiers arrive as text and are converted by the primary key."""
        ids = ids_of(project, "b", "a", "c")
        assert all(isinstance(i, str) for i in ids)

        save_order(project.tasks.all(), ids)

        assert positions(project) == {"b": 0, "a": 1, "c": 2}

    def test_records_outside_the_queryset_keep_their_positions(self, project):
        """Only the queryset's records are renumbered."""
        other = ProjectFactory()
        outsider = ProjectTaskFactory(project=other, title="x", position=7)

        save_order(project.tasks.all(), ids_of(project, "c", "b", "a"))

        outsider.refresh_from_db()
        assert outsider.position == 7

    def test_writes_to_the_named_field(self, project):
        """``field`` picks the column that receives the numbers."""
        save_order(
            project.tasks.all(), ids_of(project, "b", "c", "a"), field="position"
        )

        assert positions(project) == {"b": 0, "c": 1, "a": 2}

    def test_a_duplicate_is_refused_and_nothing_changes(self, project):
        """An identifier named twice raises and leaves every row as it was."""
        ids = ids_of(project, "a", "b", "c")
        before = positions(project)

        with pytest.raises(InvalidOrder):
            save_order(project.tasks.all(), [ids[0], ids[1], ids[1]])

        assert positions(project) == before

    def test_an_identifier_outside_the_queryset_is_refused(self, project):
        """A record the queryset does not hold cannot be ordered."""
        outsider = ProjectTaskFactory(project=ProjectFactory(), title="x")
        ids = ids_of(project, "a", "b", "c")
        before = positions(project)

        with pytest.raises(InvalidOrder):
            save_order(project.tasks.all(), [*ids, str(outsider.pk)])

        assert positions(project) == before
        outsider.refresh_from_db()
        assert outsider.position == 0

    def test_a_record_left_out_is_refused(self, project):
        """An order that omits a record of the queryset is refused whole."""
        ids = ids_of(project, "a", "b")
        before = positions(project)

        with pytest.raises(InvalidOrder):
            save_order(project.tasks.all(), ids)

        assert positions(project) == before

    def test_an_identifier_the_key_cannot_convert_is_refused(self, project):
        """Text that is not a valid primary key raises ``InvalidOrder``."""
        ids = ids_of(project, "a", "b")
        before = positions(project)

        with pytest.raises(InvalidOrder):
            save_order(project.tasks.all(), [*ids, "not-a-number"])

        assert positions(project) == before

    def test_invalid_order_is_a_value_error(self):
        """Callers that catch ``ValueError`` also catch the refusal."""
        assert issubclass(InvalidOrder, ValueError)


@pytest.mark.django_db(transaction=True)
class TestSaveOrderTransaction:
    """The save is atomic."""

    def test_the_write_happens_inside_a_transaction(self, project, monkeypatch):
        """The numbers are written in an atomic block, and a failure undoes them."""
        original = QuerySet.bulk_update
        inside = []

        def failing_bulk_update(self, objs, fields, *args, **kwargs):
            original(self, objs, fields, *args, **kwargs)
            inside.append(transaction.get_connection().in_atomic_block)
            raise RuntimeError("fail after writing")

        monkeypatch.setattr(QuerySet, "bulk_update", failing_bulk_update)

        with pytest.raises(RuntimeError):
            save_order(project.tasks.all(), ids_of(project, "c", "b", "a"))

        assert inside == [True]
        assert positions(project) == {"a": 0, "b": 0, "c": 0}
