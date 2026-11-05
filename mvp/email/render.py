"""Render an email to its subject, HTML and plain text (sketch)."""

import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.utils import translation

from mvp.config import MVP_CONFIG
from mvp.utils import logo_url, site_name

from .brand import email_brand


@dataclass
class Rendered:
    subject: str
    html: str
    text: str


class TextFromHTML(HTMLParser):
    """SKETCH: a crude converter, so the preview has a plain-text part to show."""

    BLOCK = {"p", "div", "h1", "h2", "h3", "tr", "table", "ul", "li", "br", "hr"}
    VOID = {"br", "hr", "img", "meta", "link", "input"}

    def __init__(self):
        super().__init__()
        self.out: list[str] = []
        self.stack: list[tuple[str, bool, str | None]] = []

    @property
    def skipping(self) -> bool:
        return any(skip for _, skip, _ in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        hidden = tag in ("head", "style", "script", "title") or "display:none" in (a.get("style") or "").replace(" ", "")
        if tag not in self.VOID:
            self.stack.append((tag, hidden, a.get("href") if tag == "a" else None))
        if self.skipping:
            return
        if tag == "a":
            self.link_start = len(self.out)
        if tag == "img" and a.get("alt") and "display:none" not in (a.get("style") or "").replace(" ", ""):
            self.out.append(a["alt"])
        if tag in self.BLOCK:
            self.out.append("\n")
        if tag == "hr":
            self.out.append("-" * 40 + "\n")
        if tag == "li":
            self.out.append("- ")
        if tag == "td":
            self.out.append("  ")

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        while self.stack:
            name, _, href = self.stack.pop()
            if name == tag:
                break
        else:
            return
        if self.skipping:
            return
        shown = "".join(self.out[getattr(self, "link_start", len(self.out)):]).strip()
        if tag == "a" and href and not href.startswith("mailto:") and shown != href:
            self.out.append(f" ({href})")
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skipping:
            self.out.append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        text = unescape("".join(self.out))
        lines = [line.strip() for line in text.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def site_root(request) -> str:
    return request.build_absolute_uri("/").rstrip("/")


def brand_context(request) -> dict:
    root = site_root(request)
    light = logo_url(request, 48, "light")
    dark = logo_url(request, 48, "dark")
    return {
        "brand": email_brand(),
        "site_name": MVP_CONFIG["site_name"] or site_name(request),
        "site_url": root + "/",
        "logo_light": root + light if light.startswith("/") else light,
        "logo_dark": (root + dark if dark.startswith("/") else dark) if dark and dark != light else None,
    }


def render_email(name: str, context: dict, request, language: str | None = None) -> Rendered:
    with translation.override(language or translation.get_language()):
        ctx = {**brand_context(request), **context}
        subject = " ".join(render_to_string(f"{name}/subject.txt", ctx, request=request).split())
        html = render_to_string(f"{name}/body.html", ctx, request=request)
        try:
            text = render_to_string(f"{name}/body.txt", ctx, request=request)
        except Exception:
            parser = TextFromHTML()
            parser.feed(html)
            text = parser.text()
    return Rendered(subject=subject, html=html, text=text)


@dataclass
class Preview:
    name: str
    label: str
    context: dict = field(default_factory=dict)
    group: str = ""


PREVIEWS: dict[str, Preview] = {}


def preview(name: str, label: str, context: dict, group: str = "") -> None:
    PREVIEWS[name] = Preview(name=name, label=label, context=context, group=group)
