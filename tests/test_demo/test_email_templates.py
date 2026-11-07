"""The demo's sample emails: named the way a third-party sender names its templates (FS-044).

The demo's templates are the worked example of overriding a package's email, so
each carries the three templates a sender looks for.
"""

import re
from pathlib import Path

import pytest
from django.contrib.sites.models import Site
from django.template.loader import get_template, render_to_string

from mvp.email.brand import EmailBrand

EMAILS = Path(__file__).parent.parent.parent / "demo" / "templates" / "demo" / "email"
PREFIXES = ["invitation", "password-reset", "policy-update", "receipt", "sign-in-code"]
TRANSLATION_MARKUP = re.compile(
    r"\{%\s*(load\s+i18n|trans|translate|blocktrans|blocktranslate)\b"
)


@pytest.mark.parametrize("prefix", PREFIXES)
class TestDemoEmailTemplates:
    def test_the_subject_and_the_html_message_exist_under_the_senders_naming(
        self, prefix
    ):
        assert get_template(f"demo/email/{prefix}_subject.txt")
        assert get_template(f"demo/email/{prefix}_message.html")

    def test_no_template_carries_translation_markup(self, prefix):
        for path in EMAILS.glob(f"{prefix}_*"):
            assert not TRANSLATION_MARKUP.search(path.read_text()), path.name

    def test_the_html_message_renders_in_the_brand(self, prefix, rf, db):
        Site.objects.clear_cache()
        EmailBrand.current.cache_clear()
        request = rf.get("/", HTTP_HOST="mail.example.org")

        html = render_to_string(
            f"demo/email/{prefix}_message.html",
            {"changes": ["one"], "lines": []},
            request,
        )

        assert EmailBrand.current().logo in html


class TestDemoReceipt:
    def test_a_line_item_is_not_collapsed_to_a_hairline(self, rf, db):
        from bs4 import BeautifulSoup

        Site.objects.clear_cache()
        EmailBrand.current.cache_clear()
        context = {
            "total": "€14.28",
            "date": "4 November 2026",
            "renews": "4 December 2026",
            "number": "R-2026-00412",
            "billing_url": "https://example.com/account/billing/",
            "lines": [{"label": "Standard plan, monthly", "amount": "€12.00"}],
        }

        html = render_to_string(
            "demo/email/receipt_message.html",
            context,
            rf.get("/", HTTP_HOST="mail.example.org"),
        )

        label = BeautifulSoup(html, "html.parser").find("td", string="Standard plan, monthly")
        assert label is not None
        assert "font-size: 0" not in label["style"]
        assert "line-height: 0" not in label["style"]
