"""The previews the stand-in sender declares, found by ``MvpConfig.ready`` while ``DEBUG`` is on (FS-044)."""

from mvp.email.previews import register

register(
    "testapp_email/email/confirm_message.html",
    "Confirm your address",
    {"name": "Ada", "url": "https://example.org/confirm/abc/"},
    subject="testapp_email/email/confirm_subject.txt",
    text="testapp_email/email/confirm_message.txt",
    group="Accounts",
)
