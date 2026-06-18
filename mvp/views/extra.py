"""Concrete extra views for django-mvp.

This module provides concrete Django view classes that developers use directly —
not mixins. It includes the landing/home page view and a template view helper.

Example usage::

    from mvp.views.extra import MVPHomeView, MVPTemplateView


    class DashboardView(MVPHomeView):
        dashboard_template_name = "myapp/dashboard.html"
        landing_template_name = "myapp/landing.html"
"""

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from django.views import generic

from .base import PageMixin


class MVPTemplateView(PageMixin, generic.TemplateView):
    """TemplateView with support for page configuration features like title and breadcrumbs."""

    pass


class MVPHomeView(MVPTemplateView):
    """Home page view. Shows stats and recent activity for authenticated users. Landing page for unauthenticated users."""

    page_title = _("Home")
    dashboard_template_name = "mvp/dashboard.html"
    landing_template_name = "mvp/landing.html"

    def get_template_names(self):
        """Choose template based on authentication status."""
        if self.landing_template_name is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires `landing_template_name` to be set."
            )
        if self.request.user.is_authenticated:
            if self.dashboard_template_name is None:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__} requires `dashboard_template_name` to be set for authenticated users."
                )
            return [self.dashboard_template_name]
        return [self.landing_template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context = self.get_dashboard_context(context)
        else:
            context = self.get_landing_context(context)

        return context

    def get_landing_context(self, context):
        """Context for unauthenticated users."""
        return context

    def get_dashboard_context(self, context):
        """Context for authenticated users."""
        return context
