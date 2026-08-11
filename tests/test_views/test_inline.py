"""Tests for InlineFormSet, InlinesMixin, MVPInlineCreateView and MVPInlineUpdateView.

Covers User Story 1 (specs/025-multiple-related-sets): a row set declared as
its own class, one set end to end — the parent's form and one related
model's rows rendered, validated and saved together on one page.

Source: mvp/views/inline.py
Spec: specs/025-multiple-related-sets/spec.md
"""

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from demo.models import Project, ProjectNote, ProjectTask
from mvp.views.inline import (
    InlineFormSet,
    InlinesMixin,
    MVPInlineCreateView,
    MVPInlineUpdateView,
)
from tests.factories import ProjectFactory, ProjectNoteFactory, ProjectTaskFactory


def _build_request(method="GET", data=None):
    """Return a request carrying working session and messages storage.

    ``as_view()`` is called directly (no middleware runs), but ``form_valid``
    needs ``request._messages`` to queue the success flash, so session and
    messages middleware are applied to the request by hand.
    """
    rf = RequestFactory()
    request = rf.post("/", data=data or {}) if method == "POST" else rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    MessageMiddleware(lambda r: None).process_request(request)
    return request


def _dispatch(view_cls, method="GET", data=None, view_kwargs=None):
    """Build a request and run it through ``view_cls`` via ``as_view()``."""
    request = _build_request(method=method, data=data)
    response = view_cls.as_view()(request, **(view_kwargs or {}))
    return request, response


def _rendered_html(response):
    """Render a ``TemplateResponse`` and return its decoded content."""
    response.render()
    return response.content.decode()


def _field_value(html, field_name):
    """Return the ``value`` of the first field named ``field_name``, or None."""
    soup = BeautifulSoup(html, "html.parser")
    field = soup.find(attrs={"name": field_name})
    if field is None:
        return None
    if field.name == "textarea":
        return field.text
    return field.get("value")


class TaskInline(InlineFormSet):
    """The worked one-set declaration used across US1's view-level tests."""

    model = ProjectTask
    fields = ["title"]


def _stub_attrs(**overrides):
    """The shared stub configuration: a Project parent with ProjectTask rows."""
    return {
        "model": Project,
        "fields": ["name"],
        "inlines": [TaskInline],
        "template_name": "form_view.html",
        "show_detail_action": False,
        "show_list_action": False,
        **overrides,
    }


def _inline_update_view_class(**attrs):
    return type("StubInlineUpdateView", (MVPInlineUpdateView,), _stub_attrs(**attrs))


def _inline_create_view_class(**attrs):
    return type("StubInlineCreateView", (MVPInlineCreateView,), _stub_attrs(**attrs))


class _StubInlinesView(InlinesMixin):
    """A bare object mixing in ``InlinesMixin``, for testing its methods in
    isolation from the rest of the view stack."""

    def __init__(self, model, object, queryset=None):
        self.model = model
        self.object = object
        self.queryset = queryset

    def get_queryset(self):
        return self.queryset


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


# ---------------------------------------------------------------------------
# T009 — get_title() defaults to verbose_name_plural (FR-011)
# ---------------------------------------------------------------------------


class TestGetTitle:
    """``get_title()`` defaults to the related model's ``verbose_name_plural``
    and an explicit ``title`` overrides it."""

    def _declaration(self, **attrs):
        cls = type("TaskInline", (InlineFormSet,), {"model": ProjectTask, **attrs})
        return cls(parent_model=Project, request=None, instance=None, view=None)

    def test_defaults_to_verbose_name_plural(self):
        declaration = self._declaration()

        assert declaration.get_title() == ProjectTask._meta.verbose_name_plural

    def test_explicit_title_overrides_the_default(self):
        declaration = self._declaration(title="Custom heading")

        assert declaration.get_title() == "Custom heading"

    def test_get_description_has_no_default(self):
        declaration = self._declaration()

        assert declaration.get_description() is None

    def test_explicit_description_is_returned(self):
        declaration = self._declaration(description="Help text")

        assert declaration.get_description() == "Help text"


# ---------------------------------------------------------------------------
# T011 — get_parent_model() resolution (FR-007, US1 s5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetParentModel:
    """``get_parent_model()`` resolves the parent the way Django's own
    model-form pages resolve it: ``self.model``, then the loaded object's
    class, then the queryset's model."""

    def test_resolves_from_model_attribute(self):
        stub = _StubInlinesView(model=Project, object=None)

        assert stub.get_parent_model() is Project

    def test_resolves_from_a_loaded_object_when_model_is_unset(self):
        project = ProjectFactory()
        stub = _StubInlinesView(model=None, object=project)

        assert stub.get_parent_model() is Project

    def test_resolves_from_queryset_alone(self):
        stub = _StubInlinesView(model=None, object=None)
        stub.queryset = Project.objects.all()

        assert stub.get_parent_model() is Project


# ---------------------------------------------------------------------------
# T013 — an update page with one declaration renders the parent form and the
# set's rows through the packaged components, from a real request (US1 s1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineUpdatePageRendering:
    """A GET renders the parent's form and the declared set's rows through
    the packaged formset components (US1 s1)."""

    def test_renders_parent_form_and_existing_rows(self):
        project = ProjectFactory(name="Website revamp")
        ProjectTaskFactory(project=project, title="Design mockups")
        ProjectTaskFactory(project=project, title="Build the homepage")
        view_cls = _inline_update_view_class(success_url="/done/")

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)
        soup = BeautifulSoup(html, "html.parser")

        assert soup.find(attrs={"name": "name"}).get("value") == "Website revamp"
        titles = [
            tag.get("value")
            for tag in soup.find_all(attrs={"name": lambda n: n and n.endswith("-title")})
        ]
        assert "Design mockups" in titles
        assert "Build the homepage" in titles

    def test_context_carries_the_inlines_list(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(success_url="/done/")

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        assert len(response.context_data["inlines"]) == 1
        assert response.context_data["inlines"][0].title == "project tasks"


# ---------------------------------------------------------------------------
# T016 — a row form whose widget carries media renders that media
# (S3R SPEC-004, Article XIII)
# ---------------------------------------------------------------------------


class _WidgetWithMedia(forms.TextInput):
    class Media:
        css = {"all": ["custom-row-widget.css"]}
        js = ["custom-row-widget.js"]


class _TaskFormWithMedia(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ["title"]
        widgets = {"title": _WidgetWithMedia}


class TaskInlineWithMedia(InlineFormSet):
    model = ProjectTask
    form = _TaskFormWithMedia


@pytest.mark.django_db
class TestInlineRowMediaRenders:
    """A row form whose widget carries media renders that media on the page
    — the media blocks iterate the sets as well as the standalone formset,
    so a list of inlines does not silently drop them."""

    def test_row_widget_media_renders_on_the_page(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInlineWithMedia]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)

        assert "custom-row-widget.css" in html
        assert "custom-row-widget.js" in html


# ---------------------------------------------------------------------------
# T017-T018 — a valid submission saves the parent and the set's rows and
# redirects; the parent is saved exactly once (US1 s2, R9's second decision)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInlineValidSubmission:
    """A valid submission saves the parent and the declared set's rows
    together, in one transaction, and redirects."""

    def test_update_valid_submission_persists_parent_and_rows(self):
        project = ProjectFactory(name="Original")
        existing = ProjectTaskFactory(project=project, title="Existing task")
        view_cls = _inline_update_view_class(success_url="/done/")
        data = {
            "name": "Renamed",
            "tasks-TOTAL_FORMS": "2",
            "tasks-INITIAL_FORMS": "1",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-id": str(existing.pk),
            "tasks-0-title": "Renamed task",
            "tasks-1-title": "New task",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        assert response["Location"] == "/done/"
        project.refresh_from_db()
        assert project.name == "Renamed"
        assert set(project.tasks.values_list("title", flat=True)) == {
            "Renamed task",
            "New task",
        }

    def test_parent_is_saved_exactly_once(self, monkeypatch):
        project = ProjectFactory(name="Original")
        save_calls = []
        original_save = Project.save

        def counting_save(self, *args, **kwargs):
            save_calls.append(1)
            return original_save(self, *args, **kwargs)

        monkeypatch.setattr(Project, "save", counting_save)
        view_cls = _inline_update_view_class(success_url="/done/")
        data = {
            "name": "Counted Once",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "One task",
        }

        _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert len(save_calls) == 1

    def test_create_attaches_all_new_rows_to_the_newly_created_parent(self):
        view_cls = _inline_create_view_class(success_url="/done/")
        data = {
            "name": "Fresh Project",
            "tasks-TOTAL_FORMS": "2",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "First task",
            "tasks-1-title": "Second task",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 302
        new_project = Project.objects.get(name="Fresh Project")
        assert set(
            new_project.tasks.values_list("title", flat=True)
        ) == {"First task", "Second task"}


# ---------------------------------------------------------------------------
# T019 — overriding get_factory_kwargs() reaches a parameter the shorthands
# do not expose: can_order (FR-020, US1 s6)
# ---------------------------------------------------------------------------


class TestGetFactoryKwargsOverride:
    """A subclass overriding ``get_factory_kwargs()`` — the super-and-extend
    pattern — reaches a formset-class parameter with no attribute of its
    own. ``can_order`` is the worked case: it is deliberately not an
    ``InlineFormSet`` attribute (it is a distinct, user-driven reordering
    feature, unlike FR-022's display order)."""

    def test_can_order_reaches_the_formset_through_the_override(self):
        class OrderedTaskInline(InlineFormSet):
            model = ProjectTask
            fields = ["title"]

            def get_factory_kwargs(self):
                kwargs = super().get_factory_kwargs()
                kwargs["can_order"] = True
                return kwargs

        declaration = OrderedTaskInline(
            parent_model=Project, request=None, instance=None, view=None
        )

        assert declaration.get_factory_kwargs()["can_order"] is True
        formset_class = declaration.get_formset_class()
        assert formset_class.can_order is True

    def test_can_order_is_not_a_declaration_attribute(self):
        assert not hasattr(InlineFormSet, "can_order")


# ---------------------------------------------------------------------------
# T020-T021 — get_form_kwargs(index): Django's own per-form hook
# (FR-021, US1 s7, R13)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetFormKwargsPerForm:
    """``get_form_kwargs(index)`` is called once per form with that form's
    index, and with ``None`` for the blank template form."""

    def test_called_once_per_form_with_its_index_and_none_for_the_empty_form(self):
        project = ProjectFactory()
        ProjectTaskFactory(project=project)
        calls = []

        class RecordingTaskInline(InlineFormSet):
            model = ProjectTask
            fields = ["title"]
            extra = 1

            def get_form_kwargs(self, index):
                calls.append(index)
                return super().get_form_kwargs(index)

        declaration = RecordingTaskInline(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=project,
            view=None,
        )
        formset = declaration.construct_formset()

        list(formset.forms)  # forces construction of every form (1 existing + 1 extra)
        formset.empty_form  # the blank template form

        assert calls[:-1] == [0, 1]
        assert calls[-1] is None  # the empty form is built with index None

    def test_a_declaration_can_give_each_form_a_different_value_per_index(self):
        project = ProjectFactory()
        ProjectTaskFactory(project=project)
        ProjectTaskFactory(project=project)

        class VaryingTaskInline(InlineFormSet):
            model = ProjectTask
            fields = ["title"]

            def get_form_kwargs(self, index):
                kwargs = super().get_form_kwargs(index)
                kwargs["label_suffix"] = f"row-{index}" if index is not None else "blank"
                return kwargs

        declaration = VaryingTaskInline(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=project,
            view=None,
        )
        formset = declaration.construct_formset()

        assert formset.forms[0].label_suffix == "row-0"
        assert formset.forms[1].label_suffix == "row-1"
        assert formset.empty_form.label_suffix == "blank"

    def test_shared_form_kwargs_is_the_default_when_undeclared(self):
        project = ProjectFactory()
        ProjectTaskFactory(project=project)

        class PlainTaskInline(InlineFormSet):
            model = ProjectTask
            fields = ["title"]
            form_kwargs = {"label_suffix": "shared"}

        declaration = PlainTaskInline(
            parent_model=Project,
            request=RequestFactory().get("/"),
            instance=project,
            view=None,
        )
        formset = declaration.construct_formset()

        assert formset.forms[0].label_suffix == "shared"
        assert formset.empty_form.label_suffix == "shared"


# ---------------------------------------------------------------------------
# T022-T023 — sort_forms() decides display order only (FR-022, US1 s8)
# ---------------------------------------------------------------------------


class _ReversedTaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    extra = 0

    def sort_forms(self, forms):
        return list(reversed(forms))


@pytest.mark.django_db
class TestSortFormsIsDisplayOnly:
    """A declaration reversing the given order renders in that order, and
    the order rows are validated and saved in is unchanged."""

    def test_reversed_declaration_renders_in_reverse(self):
        project = ProjectFactory()
        first = ProjectTaskFactory(project=project, title="First")
        second = ProjectTaskFactory(project=project, title="Second")
        assert first.pk < second.pk
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[_ReversedTaskInline]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)
        soup = BeautifulSoup(html, "html.parser")
        titles_in_order = [
            tag.get("value")
            for tag in soup.find_all(attrs={"name": lambda n: n and n.endswith("-title")})
            if tag.get("value")
        ]

        assert titles_in_order == ["Second", "First"]

    def test_the_saved_order_matches_the_submitted_index_not_the_display_order(self):
        project = ProjectFactory()
        first = ProjectTaskFactory(project=project, title="First")
        second = ProjectTaskFactory(project=project, title="Second")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[_ReversedTaskInline]
        )
        data = {
            "name": project.name,
            "tasks-TOTAL_FORMS": "2",
            "tasks-INITIAL_FORMS": "2",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-id": str(first.pk),
            "tasks-0-title": "Updated First",
            "tasks-1-id": str(second.pk),
            "tasks-1-title": "Updated Second",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.title == "Updated First"
        assert second.title == "Updated Second"


# ---------------------------------------------------------------------------
# T024 — InlineFormsetMixin and the six inline_* attributes are gone;
# InlineFormSet is exported, MVPInlineCreateView/MVPInlineUpdateView keep
# their names (FR-024)
# ---------------------------------------------------------------------------


class TestInlineViewsPublicAPI:
    """``mvp.views`` exports the declaration class and the two concrete
    views, not ``InlinesMixin`` — the rule already stated in
    ``mvp/views/__init__.py``: the package exports views, not mixins."""

    def test_inline_form_set_is_exported(self):
        from mvp.views import InlineFormSet as ExportedInlineFormSet

        assert ExportedInlineFormSet is InlineFormSet

    def test_create_and_update_views_keep_their_names(self):
        from mvp.views import MVPInlineCreateView, MVPInlineUpdateView

        assert MVPInlineCreateView is not None
        assert MVPInlineUpdateView is not None

    def test_inlines_mixin_is_not_exported(self):
        import mvp.views

        assert not hasattr(mvp.views, "InlinesMixin")

    def test_the_old_inline_formset_mixin_no_longer_exists(self):
        import mvp.views.inline

        assert not hasattr(mvp.views.inline, "InlineFormsetMixin")

    def test_no_inline_star_attribute_survives_on_the_new_surface(self):
        removed = {
            "inline_model",
            "inline_fields",
            "inline_extra",
            "inline_can_delete",
            "inline_max_num",
            "inline_title",
            "inline_description",
            "inline_form_class",
        }
        present = removed & set(dir(InlineFormSet)) | removed & set(
            dir(InlinesMixin)
        )
        assert present == set()


# ---------------------------------------------------------------------------
# Shared multi-set declarations (US2). ``ProjectNote`` reaches ``Project`` by
# two relations, so a declaration over it must name which one it uses
# (``fk_name``) or Django's own factory raises for the ambiguity.
# ---------------------------------------------------------------------------


class NoteViaProjectInline(InlineFormSet):
    model = ProjectNote
    fields = ["text"]
    fk_name = "project"


class NoteViaRelatedProjectInline(InlineFormSet):
    model = ProjectNote
    fields = ["text"]
    fk_name = "related_project"


# ---------------------------------------------------------------------------
# T025 — two declarations render as two sets, each under its own heading, in
# the declared order (US2 s1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTwoInlineSetsRenderInOrder:
    """A view listing two declaration classes renders both sets, each under
    its own heading, in the order the view lists them."""

    def test_both_sets_render_under_their_own_headings_in_declared_order(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)

        tasks_index = html.index(str(ProjectTask._meta.verbose_name_plural))
        notes_index = html.index(str(ProjectNote._meta.verbose_name_plural))
        assert tasks_index < notes_index

    def test_context_carries_both_sets_in_declared_order(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        inlines = response.context_data["inlines"]
        assert len(inlines) == 2
        assert inlines[0].title == "project tasks"
        assert inlines[1].title == "project notes"


# ---------------------------------------------------------------------------
# T027 — two sets over the same related model through different relations
# both build, with different prefixes, neither declaring one (US2 s6, R3)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSameModelDifferentRelationsGetDifferentPrefixes:
    """Two sets naming ``ProjectNote`` through two different foreign keys
    both build, and their default prefixes differ without either
    declaration setting ``prefix`` (R3's claim)."""

    def test_both_sets_build_with_different_default_prefixes(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/",
            inlines=[NoteViaProjectInline, NoteViaRelatedProjectInline],
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        assert response.status_code == 200
        inlines = response.context_data["inlines"]
        assert len(inlines) == 2
        assert inlines[0].prefix == "notes"
        assert inlines[1].prefix == "cross_notes"
        assert inlines[0].prefix != inlines[1].prefix

    def test_neither_declaration_sets_a_prefix(self):
        assert NoteViaProjectInline.prefix is None
        assert NoteViaRelatedProjectInline.prefix is None


# ---------------------------------------------------------------------------
# T028-T029 — two declarations resolving to the same prefix raise
# ImproperlyConfigured naming both and the fix, at page-build time
# (FR-005, US2 s5)
# ---------------------------------------------------------------------------


class _DuplicateTaskInline(InlineFormSet):
    """Same related model, same relation, no prefix override — collides
    with ``TaskInline``'s default prefix."""

    model = ProjectTask
    fields = ["title"]


@pytest.mark.django_db
class TestDuplicatePrefixRaisesAtBuildTime:
    """Two declarations resolving to the same prefix raise
    ``ImproperlyConfigured`` naming both declaration classes and the fix,
    when the page is built — not merely when it is rendered."""

    def test_raises_naming_both_declarations_and_the_fix(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, _DuplicateTaskInline]
        )

        with pytest.raises(ImproperlyConfigured) as excinfo:
            _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        message = str(excinfo.value)
        assert "TaskInline" in message
        assert "_DuplicateTaskInline" in message
        assert "prefix" in message

    def test_raises_from_as_view_not_from_a_template_render(self):
        """Built through ``as_view()`` alone — the error must fire before
        any template touches the sets, matching FR-005."""
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, _DuplicateTaskInline]
        )
        request = _build_request(method="GET")

        with pytest.raises(ImproperlyConfigured):
            view_cls.as_view()(request, pk=project.pk)


# ---------------------------------------------------------------------------
# T030 — a submission adding a row to each set saves both against the
# parent (US2 s2)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMultiSetValidSubmission:
    """A submission adding a row to each of two sets saves both, and both
    rows belong to the parent record."""

    def test_rows_added_to_both_sets_are_saved_against_the_parent(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )
        data = {
            "name": "Original",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "New task",
            "notes-TOTAL_FORMS": "1",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
            "notes-0-text": "New note",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        project.refresh_from_db()
        assert set(project.tasks.values_list("title", flat=True)) == {"New task"}
        assert set(project.notes.values_list("text", flat=True)) == {"New note"}


# ---------------------------------------------------------------------------
# T031 — a row invalid in the second set leaves nothing saved (US2 s3,
# FR-009)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvalidSecondSetLeavesNothingSaved:
    """A row invalid in the second set leaves nothing saved: not the first
    set's rows, not the parent's own change. Asserted by counting rows and
    re-reading the parent from the database, never by trusting the
    response."""

    def test_nothing_is_saved_when_the_second_set_has_an_invalid_row(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )
        data = {
            "name": "Renamed",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "Would-be task",
            "notes-TOTAL_FORMS": "1",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
            # a filled field over max_length: invalid without being an
            # unchanged extra row Django's formset would silently skip
            "notes-0-text": "x" * 201,
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 200
        project.refresh_from_db()
        assert project.name == "Original"
        assert project.tasks.count() == 0
        assert project.notes.count() == 0


# ---------------------------------------------------------------------------
# T032 — two sets carrying a same-named field each receive only their own
# rows' values (US2 s4)
# ---------------------------------------------------------------------------


class _PrimaryTaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    prefix = "primary"


class _SecondaryTaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    prefix = "secondary"


@pytest.mark.django_db
class TestSameNamedFieldAcrossSetsStaysScoped:
    """Two sets sharing a field name (``title``, on the same related model
    through the same relation, distinguished only by an explicit prefix)
    each receive only their own rows' submitted values."""

    def test_each_set_receives_only_its_own_values(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/",
            inlines=[_PrimaryTaskInline, _SecondaryTaskInline],
        )
        data = {
            "name": "Original",
            "primary-TOTAL_FORMS": "1",
            "primary-INITIAL_FORMS": "0",
            "primary-MIN_NUM_FORMS": "0",
            "primary-MAX_NUM_FORMS": "1000",
            "primary-0-title": "Primary title",
            "secondary-TOTAL_FORMS": "1",
            "secondary-INITIAL_FORMS": "0",
            "secondary-MIN_NUM_FORMS": "0",
            "secondary-MAX_NUM_FORMS": "1000",
            "secondary-0-title": "Secondary title",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        assert set(project.tasks.values_list("title", flat=True)) == {
            "Primary title",
            "Secondary title",
        }


# ---------------------------------------------------------------------------
# T033 — a page where one set among several needs multipart encodes the
# form for uploads (FR-012, US2 s7, S3R ARCH-002)
# ---------------------------------------------------------------------------


class _UploadTaskForm(forms.ModelForm):
    upload = forms.FileField(required=False)

    class Meta:
        model = ProjectTask
        fields = ["title"]


class _UploadTaskInline(InlineFormSet):
    model = ProjectTask
    form = _UploadTaskForm
    prefix = "uploads"


@pytest.mark.django_db
class TestMultipartWhenAnySetNeedsIt:
    """A page carrying several sets is encoded for uploads when any one of
    them needs it, even when the others do not."""

    def test_form_is_multipart_when_one_of_several_sets_needs_it(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, _UploadTaskInline]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)

        assert 'enctype="multipart/form-data"' in html


# ---------------------------------------------------------------------------
# T034 — two sets with different max_num caps: a submission within one and
# above the other rejects only the set that is over (FR-013, US2 s8, R9)
# ---------------------------------------------------------------------------


class _CappedTaskInline(InlineFormSet):
    model = ProjectTask
    fields = ["title"]
    prefix = "capped_tasks"
    max_num = 1


@pytest.mark.django_db
class TestPerSetCapsIndependent:
    """Two sets with different row caps: a submission within one cap and
    above the other rejects only the set that is over, and a submission
    within a cap after row removals is accepted."""

    def _data(self, project, task_titles, note_texts):
        data = {
            "name": project.name,
            "capped_tasks-TOTAL_FORMS": str(len(task_titles)),
            "capped_tasks-INITIAL_FORMS": "0",
            "capped_tasks-MIN_NUM_FORMS": "0",
            "capped_tasks-MAX_NUM_FORMS": "1000",
            "notes-TOTAL_FORMS": str(len(note_texts)),
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
        }
        for i, title in enumerate(task_titles):
            data[f"capped_tasks-{i}-title"] = title
        for i, text in enumerate(note_texts):
            data[f"notes-{i}-text"] = text
        return data

    def test_only_the_set_over_its_cap_is_rejected(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/",
            inlines=[_CappedTaskInline, NoteViaProjectInline],
        )
        data = self._data(
            project,
            task_titles=["First", "Second"],  # over the cap of 1
            note_texts=["A note"],  # NoteViaProjectInline has no cap
        )

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 200
        inlines = response.context_data["inlines"]
        assert not inlines[0].is_valid()
        assert inlines[0].non_form_errors()
        assert inlines[1].is_valid()

    def test_within_a_cap_after_removals_is_accepted(self):
        project = ProjectFactory(name="Original")
        existing_one = ProjectTaskFactory(project=project, title="Keep")
        existing_two = ProjectTaskFactory(project=project, title="Drop")
        view_cls = _inline_update_view_class(
            success_url="/done/",
            inlines=[_CappedTaskInline, NoteViaProjectInline],
        )
        data = {
            "name": project.name,
            "capped_tasks-TOTAL_FORMS": "2",
            "capped_tasks-INITIAL_FORMS": "2",
            "capped_tasks-MIN_NUM_FORMS": "0",
            "capped_tasks-MAX_NUM_FORMS": "1000",
            "capped_tasks-0-id": str(existing_one.pk),
            "capped_tasks-0-title": "Keep",
            "capped_tasks-1-id": str(existing_two.pk),
            "capped_tasks-1-title": "Drop",
            "capped_tasks-1-DELETE": "on",
            "notes-TOTAL_FORMS": "0",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        assert set(project.tasks.values_list("title", flat=True)) == {"Keep"}


# ---------------------------------------------------------------------------
# T036 — a declaration naming fk_name builds against that relation and
# reaches its rows (FR-019, US2 s9)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFkNameBuildsAgainstNamedRelation:
    """A declaration naming ``fk_name`` builds against that relation and its
    rows are those the named relation reaches, not the other one."""

    def test_reaches_only_rows_through_the_named_relation(self):
        project = ProjectFactory()
        other = ProjectFactory()
        ProjectNoteFactory(project=project, text="Owned note")
        cross_note = ProjectNoteFactory(
            project=other, related_project=project, text="Cross-referenced note"
        )
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[NoteViaRelatedProjectInline]
        )

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        formset = response.context_data["inlines"][0]
        assert list(formset.queryset) == [cross_note]


# ---------------------------------------------------------------------------
# T037 — two sets each with an invalid row both report their own errors on
# redisplay (US3 s1, FR-008)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBothSetsReportErrorsOnRedisplay:
    """Two sets each carrying an invalid row: the redisplayed page shows an
    error against both rows, asserted from the response context's formsets.

    The parent form here is valid, so this path already runs through
    ``form_valid``'s ``all_valid`` call (US1/US2) — no production change is
    expected; this test pins the behaviour that already generalised.
    """

    def test_both_sets_report_their_own_row_errors(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )
        data = {
            "name": "Original",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "x" * 201,
            "notes-TOTAL_FORMS": "1",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
            "notes-0-text": "x" * 201,
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 200
        inlines = response.context_data["inlines"]
        assert not inlines[0].is_valid()
        assert inlines[0].forms[0].errors
        assert not inlines[1].is_valid()
        assert inlines[1].forms[0].errors


# ---------------------------------------------------------------------------
# T038 — an invalid parent form together with invalid sets shows both
# (US3 s2, R11, S3R SPEC-002)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvalidParentFormStillValidatesSets:
    """An invalid parent form together with invalid sets shows both: Django's
    ``ProcessFormView.post`` routes straight to ``form_invalid`` when the
    parent form fails, so nothing calls ``is_valid()`` on the sets unless
    the view does that itself on this path too.

    The assertion reads ``formset._errors is not None`` rather than
    ``formset.errors``/``formset.non_form_errors``. Both of those are
    properties that call ``full_clean()`` on access
    (``django/forms/formsets.py``), so an assertion against them would pass
    whether or not the view validated the sets — the vacuous-test shape
    FS-024's design review caught. ``_errors`` is populated only if
    something already called ``is_valid()``.
    """

    def test_sets_are_validated_even_when_the_parent_form_is_invalid(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )
        data = {
            "name": "",  # required field left blank: parent form is invalid
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "x" * 201,
            "notes-TOTAL_FORMS": "1",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
            "notes-0-text": "x" * 201,
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 200
        assert response.context_data["form"].is_valid() is False
        inlines = response.context_data["inlines"]
        assert inlines[0]._errors is not None
        assert inlines[1]._errors is not None
        assert not inlines[1].is_valid()
        assert inlines[1].forms[0].errors


# ---------------------------------------------------------------------------
# T040 — a refused submission redisplays every set with the submitted
# values, while the page's object-derived parts show the stored record
# (US3 s3, FR-010)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRefusedSubmissionKeepsObjectDerivedPartsOnTheStoredRecord:
    """A refused submission redisplays a set carrying the submitted values,
    while the page's object-derived parts (the breadcrumb naming the
    record) show the stored record — even though the parent form's own
    fields validated individually, since Django's ``_post_clean`` still
    writes them onto ``self.object`` in place before the page as a whole is
    refused for a failing set."""

    def test_set_keeps_submitted_value_while_breadcrumb_shows_stored_name(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[TaskInline, NoteViaProjectInline]
        )
        data = {
            "name": "Submitted But Rejected",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "x" * 201,  # invalid: over max_length
            "notes-TOTAL_FORMS": "0",
            "notes-INITIAL_FORMS": "0",
            "notes-MIN_NUM_FORMS": "0",
            "notes-MAX_NUM_FORMS": "1000",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )
        breadcrumbs = response.context_data["page"]["breadcrumbs"]
        html = _rendered_html(response)

        assert response.status_code == 200
        assert _field_value(html, "name") == "Submitted But Rejected"
        assert _field_value(html, "tasks-0-title") == "x" * 201
        assert breadcrumbs[1]["text"] == "Original"


# ---------------------------------------------------------------------------
# Guards carried over from FS-024, restored against the new surface: the
# declaration classes replaced the `inline_*` attributes, but FR-009's single
# transaction, the remove control and the create page's refusal path are
# unchanged requirements, and the rewrite of this file left each of them with
# no test (D15).
# ---------------------------------------------------------------------------


class _SimulatedRowFailure(Exception):
    """Raised by a monkeypatched ``ProjectTask.save`` to force a partial save."""


@pytest.mark.django_db
class TestSaveFailurePartwayThroughRollsBackEverything:
    """A failure raised while saving rows leaves the parent's changes
    unpersisted and queues no success message (FR-009, SC-002).

    A row that fails *validation* never reaches the transaction at all, so it
    cannot tell whether ``form_valid`` wraps the writes or merely orders them.
    Only a failure raised after the block is entered does.
    """

    def test_row_save_failure_rolls_back_parent_and_queues_no_message(
        self, monkeypatch
    ):
        project = ProjectFactory(name="Original")
        original_save = ProjectTask.save

        def failing_save(self, *args, **kwargs):
            if self.title == "boom":
                raise _SimulatedRowFailure("boom")
            return original_save(self, *args, **kwargs)

        monkeypatch.setattr(ProjectTask, "save", failing_save)
        view_cls = _inline_update_view_class(success_url="/done/")
        data = {
            "name": "Changed Name",
            "tasks-TOTAL_FORMS": "2",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "saved first",
            "tasks-1-title": "boom",
        }
        request = _build_request(method="POST", data=data)

        with pytest.raises(_SimulatedRowFailure):
            view_cls.as_view()(request, pk=project.pk)

        project.refresh_from_db()
        assert project.name == "Original"
        assert not ProjectTask.objects.filter(title="saved first").exists()
        assert not ProjectTask.objects.filter(title="boom").exists()
        assert list(request._messages) == []


class _DeletableTaskInline(InlineFormSet):
    """A set carrying the remove control, which the default declaration also
    has — named here so the DELETE flag is what the test is about."""

    model = ProjectTask
    fields = ["title"]
    can_delete = True


@pytest.mark.django_db
class TestSubmittedRemoveFlagRemovesTheRow:
    """The server-side half of the remove control: what a submitted ``DELETE``
    flag does to a related record, and what it does to a row added in the same
    submission (the count FR-013 excludes from a cap)."""

    def test_delete_on_an_existing_row_deletes_that_record(self):
        project = ProjectFactory(name="Existing")
        existing = ProjectTaskFactory(project=project, title="Doomed")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[_DeletableTaskInline]
        )
        data = {
            "name": "Existing",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "1",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-id": str(existing.pk),
            "tasks-0-title": "Doomed",
            "tasks-0-DELETE": "on",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        assert not ProjectTask.objects.filter(pk=existing.pk).exists()

    def test_delete_on_a_row_added_in_the_same_submission_creates_nothing(self):
        project = ProjectFactory(name="Existing")
        view_cls = _inline_update_view_class(
            success_url="/done/", inlines=[_DeletableTaskInline]
        )
        data = {
            "name": "Existing",
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "Never Stored",
            "tasks-0-DELETE": "on",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        assert not ProjectTask.objects.filter(title="Never Stored").exists()
        assert ProjectTask.objects.count() == 0


@pytest.mark.django_db
class TestCreatePageRefusedByItsParentFormPersistsNothing:
    """On a create page, an invalid parent form with a valid row persists
    neither part, and the page comes back carrying every submitted value.

    The update-page equivalent is covered above; create is the path where
    ``self.object`` is ``None`` throughout, so the refusal runs through
    different state.
    """

    def test_invalid_parent_persists_nothing_and_preserves_both_parts(self):
        view_cls = _inline_create_view_class(success_url="/done/")
        too_long_name = "x" * 250  # Project.name has max_length=200
        data = {
            "name": too_long_name,
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "A Valid Row",
        }

        _, response = _dispatch(view_cls, method="POST", data=data)

        assert response.status_code == 200
        html = _rendered_html(response)
        assert _field_value(html, "name") == too_long_name
        assert _field_value(html, "tasks-0-title") == "A Valid Row"
        assert Project.objects.count() == 0
        assert ProjectTask.objects.count() == 0


# ---------------------------------------------------------------------------
# US4 — a page that edits only the related rows (#213)
#
# `fields = []` on an update view is the whole configuration: no new view
# class, no page-selecting attribute (plan.md "The rows-only page").
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# T042 — a rows-only page renders no parent field, and every set against the
# record the URL identifies (FR-014, US4 s1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRowsOnlyPageRendersNoParentFields:
    """An update view configured with ``fields = []`` renders no parent
    field, and every configured set against the record the URL identifies."""

    def test_no_parent_field_input_renders(self):
        project = ProjectFactory(name="Website revamp")
        view_cls = _inline_update_view_class(success_url="/done/", fields=[])

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})
        html = _rendered_html(response)

        assert _field_value(html, "name") is None

    def test_each_sets_rows_are_the_urls_record_rows(self):
        project = ProjectFactory(name="Website revamp")
        other_project = ProjectFactory(name="Someone else's project")
        ProjectTaskFactory(project=project, title="Mine")
        ProjectTaskFactory(project=other_project, title="Not mine")
        view_cls = _inline_update_view_class(success_url="/done/", fields=[])

        _, response = _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        inlines = response.context_data["inlines"]
        assert len(inlines) == 1
        assert {
            form.instance.title for form in inlines[0].forms if form.instance.pk
        } == {"Mine"}


# ---------------------------------------------------------------------------
# T043 — `fields = None` still raises Django's own error: only an empty
# collection selects the rows-only page (plan risk 4)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFieldsNoneStillRaisesDjangosOwnError:
    """``fields = None`` (Django's "not configured") is not treated as
    ``fields = []`` (this feature's "deliberately none"). The unconfigured
    page still raises Django's own error, not this feature's."""

    def test_unconfigured_fields_raises_djangos_own_message(self):
        project = ProjectFactory()
        view_cls = _inline_update_view_class(success_url="/done/", fields=None)

        with pytest.raises(ImproperlyConfigured) as excinfo:
            _dispatch(view_cls, method="GET", view_kwargs={"pk": project.pk})

        assert "without the 'fields' attribute is prohibited" in str(excinfo.value)


# ---------------------------------------------------------------------------
# T044 — the rows-only branch: no parent form fields, sets bound to the
# loaded instance. No new view class, no page-selecting attribute. Verified
# by T042/T043 above needing no production code — both already green,
# because `fields = []` renders through Django's own empty-form machinery
# and every set already binds to `self.object` via the existing multi-set
# construction (US1-3). Nothing to add here.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# T045 — a valid submission saves the rows and leaves the record's own
# field values unchanged (FR-015, US4 s2)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRowsOnlySavesRowsLeavesParentFieldValuesUnchanged:
    """A valid submission on a rows-only page saves the rows against the
    URL's record, and every one of the parent's own columns reads what it
    read before the submission."""

    def test_rows_land_and_parent_field_values_are_unchanged(self):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(success_url="/done/", fields=[])
        data = {
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "New task",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Original"
        assert set(project.tasks.values_list("title", flat=True)) == {"New task"}


# ---------------------------------------------------------------------------
# T047 — the concurrency test: a change another writer makes to the
# parent's own field while the rows-only page is open survives the
# submission (FR-015, US4 s4, research R12)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestConcurrentWriteToParentFieldSurvivesTheSubmission:
    """Load the rows-only page for a parent, have another writer change one
    of that parent's own fields while the page is open, then post the
    submission from the page that was loaded. That other change must
    survive — this is red against a naive ``form.save()`` implementation
    and green against never saving the parent form (FR-015, R12).

    Django's own ``UpdateView.post()`` re-fetches the object fresh at the
    start of every request, so the race this simulates is not "another
    request landed between GET and POST" (a fresh POST already sees that)
    but the narrower, real window every writer has to contend with: another
    writer's change lands after this request has already read its own copy
    of the record and before this request writes anything back. Monkey-
    patching ``get_object`` to perform that second write immediately after
    the read is what puts a genuinely stale value in this request's memory.
    """

    def test_concurrent_change_to_parent_field_survives(self, monkeypatch):
        project = ProjectFactory(name="Original")
        view_cls = _inline_update_view_class(success_url="/done/", fields=[])
        original_get_object = view_cls.get_object

        def get_object_then_concurrent_write(self, queryset=None):
            obj = original_get_object(self, queryset)
            # Simulate another process changing this record's own field in
            # the window between this request reading it and writing it
            # back — a raw queryset write that bypasses `obj` entirely.
            Project.objects.filter(pk=obj.pk).update(name="Changed By Someone Else")
            return obj

        monkeypatch.setattr(view_cls, "get_object", get_object_then_concurrent_write)
        data = {
            "tasks-TOTAL_FORMS": "1",
            "tasks-INITIAL_FORMS": "0",
            "tasks-MIN_NUM_FORMS": "0",
            "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-title": "New task",
        }

        _, response = _dispatch(
            view_cls, method="POST", data=data, view_kwargs={"pk": project.pk}
        )

        assert response.status_code == 302
        project.refresh_from_db()
        assert project.name == "Changed By Someone Else"
        assert set(project.tasks.values_list("title", flat=True)) == {"New task"}
