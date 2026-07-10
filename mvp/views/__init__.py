from .detail import MVPDetailView
from .edit import (
    MVPCreateView,
    MVPDeleteView,
    MVPFormBase,
    MVPFormView,
    MVPModelFormBase,
    MVPUpdateView,
)
from .error import bad_request, not_found, permission_denied, server_error
from .extra import MVPHomeView, MVPTemplateView
from .list import MVPListView

# Public API — concrete views and error handlers only.
# Mixins are available via full import paths:
#   from mvp.views.base import PageMixin, BaseTemplateNameMixin, ModelInfoMixin
#   from mvp.views.detail import CRUDDirectoryMixin, PageObjectMixin
#   from mvp.views.edit import NextURLMixin
#   from mvp.views.list import SearchMixin, OrderMixin
# Views built on optional third-party packages live in mvp.integrations and
# are intentionally NOT exported here:
#   from mvp.integrations.django_tables.views import MVPTableView
#   from mvp.integrations.django_filters.views import MVPFilteredListView

__all__ = [
    "MVPCreateView",
    "MVPDeleteView",
    "MVPDetailView",
    "MVPFormBase",
    "MVPFormView",
    "MVPHomeView",
    "MVPListView",
    "MVPModelFormBase",
    "MVPTemplateView",
    "MVPUpdateView",
    "bad_request",
    "not_found",
    "permission_denied",
    "server_error",
]
