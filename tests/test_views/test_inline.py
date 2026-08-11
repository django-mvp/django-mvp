"""Tests for InlineFormSet, InlinesMixin, MVPInlineCreateView and MVPInlineUpdateView.

Covers User Story 1 (specs/025-multiple-related-sets): a row set declared as
its own class, one set end to end — the parent's form and one related
model's rows rendered, validated and saved together on one page.

Source: mvp/views/inline.py
Spec: specs/025-multiple-related-sets/spec.md
"""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

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


# ---------------------------------------------------------------------------
# T004 — get_factory_kwargs() folds the shorthands in (FR-002, FR-013, R9)
# ---------------------------------------------------------------------------


class TestGetFactoryKwargs:
    """``get_factory_kwargs()`` assembles the kwargs ``inlineformset_factory``
    builds the formset class from, folding the shorthand attributes in."""

    def _declaration(self, **attrs):
        cls = type("TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs})
        return cls(parent_model=Project, request=None, instance=None, view=None)

    def test_folds_shorthand_attributes_in(self):
        declaration = self._declaration(fields=["title"], extra=2, can_delete=False)

        kwargs = declaration.get_factory_kwargs()

        assert kwargs["fields"] == ["title"]
        assert kwargs["extra"] == 2
        assert kwargs["can_delete"] is False

    def test_explicit_factory_kwargs_key_wins_over_its_shorthand(self):
        declaration = self._declaration(
            fields=["title"], factory_kwargs={"fields": ["title", "project"]}
        )

        kwargs = declaration.get_factory_kwargs()

        assert kwargs["fields"] == ["title", "project"]

    def test_validate_max_is_set_exactly_when_max_num_is(self):
        without_cap = self._declaration(fields=["title"])
        with_cap = self._declaration(fields=["title"], max_num=5)

        assert "validate_max" not in without_cap.get_factory_kwargs()
        assert with_cap.get_factory_kwargs()["validate_max"] is True
        assert with_cap.get_factory_kwargs()["max_num"] == 5

    def test_absolute_max_is_never_present(self):
        declaration = self._declaration(fields=["title"], max_num=5)

        assert "absolute_max" not in declaration.get_factory_kwargs()

    def test_validate_min_is_set_exactly_when_min_num_is(self):
        without_floor = self._declaration(fields=["title"])
        with_floor = self._declaration(fields=["title"], min_num=1)

        assert "validate_min" not in without_floor.get_factory_kwargs()
        assert with_floor.get_factory_kwargs()["validate_min"] is True
        assert with_floor.get_factory_kwargs()["min_num"] == 1


# ---------------------------------------------------------------------------
# T006 — a set declaring min_num rejects a submission with fewer rows
# (FR-023, US1 s9)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMinNumRejectsFewerRows:
    """A set declaring ``min_num`` rejects a submission carrying fewer rows
    than the minimum."""

    def _post_formset(self, project, min_rows, total_forms, quantities):
        cls = type(
            "TaskInline",
            (InlineFormSet,),
            {"model": ProjectTask, "fields": ["title"], "min_num": min_rows},
        )
        data = {
            "tasks-TOTAL_FORMS": str(total_forms),
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
        }
        for i, title in enumerate(quantities):
            data[f"tasks-{i}-title"] = title
        request = RequestFactory().post("/", data=data)
        declaration = cls(
            parent_model=Project, request=request, instance=project, view=None
        )
        return declaration.construct_formset()

    def test_submission_below_the_minimum_is_rejected(self):
        project = ProjectFactory()
        formset = self._post_formset(
            project, min_rows=2, total_forms=1, quantities=["Only one"]
        )

        assert not formset.is_valid()
        assert formset.non_form_errors()

    def test_submission_at_the_minimum_is_accepted(self):
        project = ProjectFactory()
        formset = self._post_formset(
            project, min_rows=2, total_forms=2, quantities=["First", "Second"]
        )

        assert formset.is_valid()


# ---------------------------------------------------------------------------
# T007 — get_formset_kwargs() (FR-004, R3, R6)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetFormsetKwargs:
    """``get_formset_kwargs()`` carries the instance-level kwargs the
    formset is constructed from."""

    def _declaration(self, request=None, **attrs):
        cls = type(
            "TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs}
        )
        return cls(
            parent_model=Project,
            request=request or RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )

    @pytest.fixture(autouse=True)
    def _project(self):
        self.project = ProjectFactory()

    def test_carries_the_instance(self):
        declaration = self._declaration()

        assert declaration.get_formset_kwargs()["instance"] is self.project

    def test_get_carries_no_data_or_files(self):
        declaration = self._declaration(request=RequestFactory().get("/"))

        kwargs = declaration.get_formset_kwargs()

        assert "data" not in kwargs
        assert "files" not in kwargs

    def test_post_carries_data_and_files(self):
        request = RequestFactory().post("/", data={"tasks-TOTAL_FORMS": "0"})
        declaration = self._declaration(request=request)

        kwargs = declaration.get_formset_kwargs()

        assert kwargs["data"] is request.POST
        assert kwargs["files"] is request.FILES

    def test_declared_prefix_is_put_in(self):
        declaration = self._declaration(prefix="custom")

        assert declaration.get_formset_kwargs()["prefix"] == "custom"

    def test_unset_prefix_is_omitted_entirely(self):
        declaration = self._declaration()

        assert "prefix" not in declaration.get_formset_kwargs()

    def test_mutating_the_returned_form_kwargs_does_not_alter_the_class_attribute(
        self,
    ):
        cls = type(
            "TaskInline",
            (InlineFormSet,),
            {"model": ProjectTask, "form_kwargs": {"label_suffix": "!"}},
        )
        first = cls(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )
        second = cls(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=self.project,
            view=None,
        )

        first_kwargs = first.get_formset_kwargs()
        first_kwargs["form_kwargs"]["label_suffix"] = "MUTATED"

        assert cls.form_kwargs == {"label_suffix": "!"}
        assert second.get_formset_kwargs()["form_kwargs"] == {"label_suffix": "!"}
