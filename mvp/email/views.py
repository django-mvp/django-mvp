"""The email preview page (sketch)."""

import re

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views import View
from django.utils.translation import gettext as _

from mvp.views.extra import MVPTemplateView

from .render import PREVIEWS, render_email

OPTIONS = {
    "scheme": ["light", "dark"],
    "images": ["on", "off"],
    "width": ["desktop", "phone"],
    "part": ["html", "text"],
}


def options(request) -> dict[str, str]:
    return {key: request.GET.get(key, values[0]) if request.GET.get(key) in values else values[0] for key, values in OPTIONS.items()}


def as_seen(html: str, scheme: str, images: str) -> str:
    """SKETCH: imitate a client in dark mode, or with images blocked."""
    if scheme == "dark":
        html = html.replace("@media (prefers-color-scheme: dark)", "@media all")
    if images == "off":
        html = re.sub(r'src="[^"]*"', 'src=""', html)
    return html


class StaffInDebugMixin(UserPassesTestMixin):
    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_staff


class EmailPreviewView(StaffInDebugMixin, MVPTemplateView):
    template_name = "mvp/email/preview.html"

    def get_page_title(self):
        return _("Emails")

    def get_page_lead(self):
        return _("Every email with a preview, rendered as it will be sent.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previews = list(PREVIEWS.values())
        name = self.request.GET.get("email") or (previews[0].name if previews else None)
        selected = PREVIEWS.get(name) if name else None
        opts = options(self.request)
        context.update(previews=previews, selected=selected, opts=opts)
        if selected:
            try:
                context["rendered"] = render_email(selected.name, selected.context, self.request)
            except Exception as error:  # noqa: BLE001 - shown on the page
                context["error"] = f"{type(error).__name__}: {error}"
            query = self.request.GET.copy()
            query["email"] = selected.name
            context["frame_url"] = reverse("mvp-email-preview-frame", args=[selected.name]) + "?" + query.urlencode()

            def link(**change):
                q = self.request.GET.copy()
                q["email"] = selected.name
                for key, value in change.items():
                    q[key] = value
                return "?" + q.urlencode()

            context["toggles"] = [
                {
                    "label": label,
                    "choices": [
                        {"text": text, "url": link(**{key: value}), "active": opts[key] == value}
                        for value, text in choices
                    ],
                }
                for key, label, choices in [
                    ("part", _("Part"), [("html", _("HTML")), ("text", _("Plain text"))]),
                    ("scheme", _("Colour scheme"), [("light", _("Light")), ("dark", _("Dark"))]),
                    ("images", _("Images"), [("on", _("Shown")), ("off", _("Blocked"))]),
                    ("width", _("Width"), [("desktop", _("Desktop")), ("phone", _("Phone"))]),
                ]
            ]
            context["email_links"] = [
                {"preview": p, "url": link(email=p.name), "active": p.name == selected.name}
                for p in previews
            ]
        return context


class EmailPreviewFrameView(StaffInDebugMixin, View):
    def get(self, request, name):
        preview = PREVIEWS.get(name)
        if not preview:
            raise Http404
        opts = options(request)
        rendered = render_email(preview.name, preview.context, request)
        return HttpResponse(as_seen(rendered.html, opts["scheme"], opts["images"]))
