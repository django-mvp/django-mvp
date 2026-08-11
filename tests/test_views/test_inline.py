"""Tests for InlineFormSet, InlinesMixin, MVPInlineCreateView and MVPInlineUpdateView.

Covers User Story 1 (specs/025-multiple-related-sets): a row set declared as
its own class, one set end to end — the parent's form and one related
model's rows rendered, validated and saved together on one page.

Source: mvp/views/inline.py
Spec: specs/025-multiple-related-sets/spec.md
"""

import pytest
from django.core.exceptions import ImproperlyConfigured

from demo.models import Project, ProjectNote, ProjectTask
from mvp.views.inline import InlineFormSet
from tests.factories import ProjectFactory, ProjectNoteFactory, ProjectTaskFactory

# ---------------------------------------------------------------------------
# T001 — fixture models and factories for the whole feature
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRowSetFixtures:
    """The fixture models this feature's tests build on: a parent (``Project``)
    with two distinct related models (``ProjectTask``, ``ProjectNote``), one of
    which (``ProjectNote``) reaches the parent by a second relation."""

    def test_project_task_belongs_to_a_project(self):
        project = ProjectFactory()
        task = ProjectTaskFactory(project=project)

        assert task.project == project
        assert task in project.tasks.all()

    def test_project_note_reaches_the_parent_by_two_relations(self):
        project = ProjectFactory()
        other = ProjectFactory()
        note = ProjectNoteFactory(project=project, related_project=other)

        assert note.project == project
        assert note.related_project == other
        assert note in project.notes.all()
        assert note in other.cross_notes.all()

    def test_project_task_and_project_note_are_distinct_related_models(self):
        assert ProjectTask is not ProjectNote
        assert Project._meta.get_field("name")


# ---------------------------------------------------------------------------
# T002 — a declaration naming no model raises ImproperlyConfigured (FR-006)
# ---------------------------------------------------------------------------


class TestInlineFormSetRequiresModel:
    """A declaration class that does not name a related model raises
    ``ImproperlyConfigured`` naming the declaration class (FR-006, US1 s3)."""

    def test_missing_model_raises_improperly_configured_naming_the_class(self):
        class TaskInline(InlineFormSet):
            fields = ["title"]

        with pytest.raises(ImproperlyConfigured, match="TaskInline"):
            TaskInline(parent_model=Project, request=None, instance=None, view=None)
