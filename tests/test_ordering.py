"""Tests for ``mvp.ordering.save_order``.

Source: mvp/ordering.py
"""

import pytest
from django.db.models import QuerySet

from mvp.ordering import InvalidOrder, save_order
from tests.factories import OrderLineFactory, ProjectFactory, ProjectTaskFactory


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

    def test_records_outside_the_queryset_keep_their_positions(self, project):
        """Only the queryset's records are renumbered."""
        other = ProjectFactory()
        outsider = ProjectTaskFactory(project=other, title="x", position=7)

        save_order(project.tasks.all(), ids_of(project, "c", "b", "a"))

        outsider.refresh_from_db()
        assert outsider.position == 7

    def test_writes_to_the_named_field(self):
        """``field`` picks the column that receives the numbers, and no other."""
        lines = [OrderLineFactory(quantity=5) for _ in range(3)]
        ids = [str(lines[2].pk), str(lines[0].pk), str(lines[1].pk)]

        save_order(type(lines[0]).objects.all(), ids, field="quantity")

        stored = type(lines[0]).objects.all()
        quantities = {str(line.pk): line.quantity for line in stored}
        assert [quantities[pk] for pk in ids] == [0, 1, 2]

    def test_a_sliced_queryset_is_ordered(self, project):
        """A queryset cut with a slice still names exactly its own records."""
        ids = ids_of(project, "a", "b", "c")
        tasks = project.tasks.order_by("pk")[:3]

        save_order(tasks, list(reversed(ids)))

        assert positions(project) == {"c": 0, "b": 1, "a": 2}

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


@pytest.mark.django_db(transaction=True)
class TestSaveOrderTransaction:
    """The save is atomic."""

    def test_a_failure_after_the_numbers_are_written_undoes_them(
        self, project, monkeypatch
    ):
        """The numbers are written and then the save fails: none of them stay."""
        original = QuerySet.bulk_update

        def failing_bulk_update(self, objs, fields, *args, **kwargs):
            original(self, objs, fields, *args, **kwargs)
            raise RuntimeError("fail after writing")

        monkeypatch.setattr(QuerySet, "bulk_update", failing_bulk_update)

        with pytest.raises(RuntimeError):
            save_order(project.tasks.all(), ids_of(project, "c", "b", "a"))

        assert positions(project) == {"a": 0, "b": 0, "c": 0}
