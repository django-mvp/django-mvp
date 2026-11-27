"""The demo's sample emails: named the way a third-party sender names its templates (FS-044).

The demo's templates are the worked example of overriding a package's email, so
each carries the templates a sender looks for.
"""

import pytest
from django.contrib.sites.models import Site
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string

from mvp.email.brand import EmailBrand

PREFIXES = ["invitation", "password-reset", "policy-update", "receipt", "sign-in-code"]


@pytest.fixture(autouse=True)
def _brand_caches_restored():
    """Drop the cached site and brand a test built, so none leaks into a later test."""
    Site.objects.clear_cache()
    EmailBrand.current.cache_clear()
    yield
    Site.objects.clear_cache()
    EmailBrand.current.cache_clear()


def test_every_email_has_a_subject_and_an_html_message_under_the_senders_naming():
    missing = []
    for prefix in PREFIXES:
        for name in (f"{prefix}_subject.txt", f"{prefix}_message.html"):
            try:
                get_template(f"demo/email/{name}")
            except TemplateDoesNotExist:
                missing.append(name)

    assert not missing, f"templates the demo should carry: {missing}"


@pytest.mark.django_db
def test_the_html_message_renders_in_the_brand(rf):
    request = rf.get("/", HTTP_HOST="mail.example.org")

    html = render_to_string(
        "demo/email/invitation_message.html",
        {"changes": ["one"], "lines": []},
        request,
    )

    assert EmailBrand.current().logo in html
