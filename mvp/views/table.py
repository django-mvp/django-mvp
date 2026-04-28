from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView

from .list import MVPListViewMixin

try:
    from django_tables2.views import SingleTableMixin, SingleTableView
except ImportError as e:
    raise ImproperlyConfigured(
        "MyTableView requires 'django_tables2'. Install it via: pip install django-mvp[django-tables2]"
    ) from e


class MVPTableViewMixin(MVPListViewMixin, SingleTableMixin):
    base_template_name = "table_view.html"


class MVPTableView(MVPTableViewMixin, ListView):
    base_template_name = "table_view.html"
