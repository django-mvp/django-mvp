"""A sender that knows nothing of django-mvp, and sends mail the way allauth's adapter does.

``ConfirmationMailer.render_mail`` follows ``allauth.account.adapter.DefaultAccountAdapter``:
it renders ``<prefix>_subject.txt``, ``<prefix>_message.txt`` and ``<prefix>_message.html``
with the request, and sends the text as the body with the HTML attached. A project
changes what the email looks like by overriding the templates, never this code.
"""

from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

TEMPLATE_PREFIX = "testapp_email/email/confirm"


class ConfirmationMailer:
    """Sends the app's address confirmation email."""

    def __init__(self, request=None):
        self.request = request

    def render_mail(self, template_prefix, email, context):
        """Render the three templates of an email into a message.

        Args:
            template_prefix: The path the email's templates share, such as ``app/email/confirm``.
            email: The recipient's address.
            context: The context the templates are rendered with.

        Returns:
            A message with the rendered text as its body and the HTML attached when
            ``<prefix>_message.html`` exists.

        Raises:
            TemplateDoesNotExist: If the subject or the text template is missing.
        """
        subject = render_to_string(f"{template_prefix}_subject.txt", context)
        subject = " ".join(subject.splitlines()).strip()
        text = render_to_string(
            f"{template_prefix}_message.txt", context, self.request
        ).strip()
        message = EmailMultiAlternatives(subject, text, "noreply@example.com", [email])
        try:
            html = render_to_string(
                f"{template_prefix}_message.html", context, self.request
            ).strip()
        except TemplateDoesNotExist:
            return message
        message.attach_alternative(html, "text/html")
        return message

    def send_confirmation_mail(self, email, name, url):
        """Send the confirmation email.

        Args:
            email: The recipient's address.
            name: The recipient's name.
            url: The address of the confirmation page.
        """
        self.render_mail(TEMPLATE_PREFIX, email, {"name": name, "url": url}).send()
