"""Example emails for the preview page, named the way allauth names its templates."""

from mvp.email.previews import register

register(
    "demo/email/sign-in-code_message.html",
    "Sign-in code",
    {"code": "482 913"},
    subject="demo/email/sign-in-code_subject.txt",
    group="Accounts",
)
register(
    "demo/email/password-reset_message.html",
    "Password reset",
    {
        "name": "Ada",
        "reset_url": "https://example.com/account/password/reset/key/3f-c8a1b2d4e5f60718293a4b5c6d7e8f90/",
    },
    subject="demo/email/password-reset_subject.txt",
    group="Accounts",
)
register(
    "demo/email/receipt_message.html",
    "Payment receipt",
    {
        "total": "€14.28",
        "date": "4 November 2026",
        "renews": "4 December 2026",
        "number": "R-2026-00412",
        "billing_url": "https://example.com/account/billing/",
        "lines": [
            {"label": "Standard plan, monthly", "amount": "€12.00"},
            {"label": "VAT (19%)", "amount": "€2.28"},
        ],
    },
    subject="demo/email/receipt_subject.txt",
    group="Payments",
)
register(
    "demo/email/policy-update_message.html",
    "Privacy policy update (own plain text and footer)",
    {
        "effective": "1 December 2026",
        "policy_url": "https://example.com/legal/privacy/",
        "postal_address": "Example GmbH, Musterstraße 12, 10115 Berlin, Germany",
        "changes": [
            "We now name every company that processes your data on our behalf.",
            "Analytics no longer use cookies.",
            "You can download everything we hold about you from your account.",
        ],
    },
    subject="demo/email/policy-update_subject.txt",
    text="demo/email/policy-update_message.txt",
    group="Compliance",
)
register(
    "demo/email/invitation_message.html",
    "Invitation (long names)",
    {
        "inviter": "Maximiliane Theodora von Hohenberg-Lichtenstein",
        "inviter_email": "maximiliane.von.hohenberg-lichtenstein@research-institute.example.org",
        "project": "Geothermal heat-flow measurements across the North German Basin, 2019 to 2026",
        "message": "Could you check the borehole temperatures for the Brandenburg sites before we publish? Thanks!",
        "accept_url": "https://example.com/invitations/accept/9c1e7b3a-55f2-4d6e-8a0b-1f2e3d4c5b6a/",
        "expires": "18 November 2026",
    },
    subject="demo/email/invitation_subject.txt",
    group="Notifications",
)
register(
    "demo/email/does-not-exist_message.html",
    "Broken email (shows a render error)",
    {},
    group="Notifications",
)
