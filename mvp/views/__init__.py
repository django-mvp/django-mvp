from .base import BaseTemplateNameMixin, ModelInfoMixin, MVPHomeView, MVPTemplateView, PageMixin
from .detail import CRUDDirectoryMixin, MVPDetailView, PageObjectMixin
from .edit import (
    MVPCreateView,
    MVPDeleteView,
    MVPFormBase,
    MVPFormView,
    MVPModelFormBase,
    MVPUpdateView,
    NextURLMixin,
)
from .list import (
    MVPListView,
    MVPListViewMixin,
    OrderMixin,
    SearchMixin,
    SearchOrderMixin,
)

# Public aliases — preferred import names for developers

__all__ = [
    # base
    "BaseTemplateNameMixin",
    "PageMixin",
    "MVPTemplateView",
    "MVPHomeView",
    # detail
    "ModelInfoMixin",
    "CRUDDirectoryMixin",
    "PageObjectMixin",
    "MVPDetailView",
    # edit
    "NextURLMixin",
    "MVPFormBase",
    "MVPModelFormBase",
    "MVPFormView",
    "MVPCreateView",
    "MVPUpdateView",
    "MVPDeleteView",
    # list
    "SearchMixin",
    "OrderMixin",
    "SearchOrderMixin",
    "MVPListViewMixin",
    "MVPListView",
]

try:
    from .list import MVPFilteredListView

    __all__ += ["MVPFilteredListView"]
except ImportError:
    pass

try:
    from .table import MVPTableView, MVPTableViewMixin

    __all__ += ["MVPTableView", "MVPTableViewMixin"]
except Exception:
    pass
