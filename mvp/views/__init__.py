from .base import (
    BaseTemplateNameMixin,
    ModelInfoMixin,
    MVPHomeView,
    MVPTemplateView,
    PageMixin,
)
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
    "BaseTemplateNameMixin",
    "CRUDDirectoryMixin",
    "MVPCreateView",
    "MVPDeleteView",
    "MVPDetailView",
    "MVPFormBase",
    "MVPFormView",
    "MVPHomeView",
    "MVPListView",
    "MVPListViewMixin",
    "MVPModelFormBase",
    "MVPTemplateView",
    "MVPUpdateView",
    "ModelInfoMixin",
    "NextURLMixin",
    "OrderMixin",
    "PageMixin",
    "PageObjectMixin",
    "SearchMixin",
    "SearchOrderMixin",
]

try:
    from .list import MVPFilteredListView

    __all__ += ["MVPFilteredListView"]
except ImportError:
    pass

try:
    from .table import MVPTableView, MVPTableViewMixin

    __all__ += ["MVPTableView", "MVPTableViewMixin"]
except Exception:  # noqa: S110
    pass
