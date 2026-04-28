from django.utils.translation import gettext_lazy as _

from .generic import MVPTemplateView


class MVPHomeView(MVPTemplateView):
    """Home page view. Shows stats and recent activity for authenticated users. Landing page for unauthenticated users."""

    page_title = _("Home")
    template_name_user = "mvp/home/user.html"
    template_name_anon = "mvp/home/anon.html"

    def get_template_names(self):
        """Choose template based on authentication status."""
        if self.request.user.is_authenticated:
            return [self.template_name_user]
        return [self.template_name_anon]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context = self.get_user_context(context)
        else:
            context = self.get_anon_context(context)

        return context

    def get_anon_context(self, context):
        """Context for unauthenticated users."""
        return context

    def get_user_context(self, context):
        """Context for authenticated users."""
        return context
