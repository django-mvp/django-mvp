from django.core.exceptions import ImproperlyConfigured

from .list import MVPListViewMixin

try:
    from django_tables2.views import SingleTableView
except ImportError as e:
    raise ImproperlyConfigured(
        "MyTableView requires 'django_tables2'. Install it via: pip install django-mvp[django-tables2]"
    ) from e


class MVPTableView(MVPListViewMixin, SingleTableView):
    base_template_name = "table_view.html"
