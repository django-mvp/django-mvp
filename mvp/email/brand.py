"""The colours an email is drawn in, read from the project's themes (sketch).

SKETCH: a quick reader so the sketch shows real theme colours. How this is
really done is research's question (planning note 2).
"""

import math
import re
from functools import cache

from django.contrib.staticfiles import finders

from mvp.config import MVP_CONFIG

STYLESHEETS = ["css/themes.css", "css/django-mvp.css"]
BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}")
VAR = re.compile(r"--color-([a-z0-9-]+)\s*:\s*([^;]+);")


def oklch_to_hex(value: str) -> str | None:
    m = re.match(r"oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)", value)
    if not m:
        return None
    lightness = float(m.group(1)) / (100 if m.group(2) else 1)
    chroma, hue = float(m.group(3)), math.radians(float(m.group(4)))
    a, b = chroma * math.cos(hue), chroma * math.sin(hue)
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def gamma(c: float) -> int:
        c = max(0.0, min(1.0, c))
        c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
        return round(c * 255)

    return "#%02x%02x%02x" % tuple(gamma(c) for c in rgb)


def to_hex(value: str) -> str | None:
    value = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value.lower()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", value):
        return "#" + "".join(ch * 2 for ch in value[1:]).lower()
    return oklch_to_hex(value)


def mix(top: str, bottom: str, amount: float) -> str:
    """``top`` laid over ``bottom`` at ``amount`` opacity, as one solid colour."""
    t = [int(top[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(bottom[i : i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x * amount + y * (1 - amount)) for x, y in zip(t, b))


def read_theme(name: str) -> dict[str, str]:
    """The theme's colours, the project's stylesheet first, then the package's."""
    colours: dict[str, str] = {}
    for path in reversed(STYLESHEETS):  # the package first, so the project's overwrites it
        found = finders.find(path)
        if not found:
            continue
        with open(found, encoding="utf-8") as fh:
            css = fh.read()
        for selector, body in BLOCK.findall(css):
            names = re.findall(r'\[data-theme=["\']?([\w-]+)["\']?\]', selector)
            if name in names and selector.strip().endswith("]"):
                for key, value in VAR.findall(body):
                    hexed = to_hex(value)
                    if hexed:
                        colours[key] = hexed
    return colours


def palette(name: str) -> dict[str, str]:
    c = read_theme(name)
    surface = c.get("base-100", "#ffffff")
    text = c.get("base-content", "#1f2937")
    return {
        "page": c.get("base-200", "#f3f4f6"),
        "surface": surface,
        "border": c.get("base-300", "#e5e7eb"),
        "text": text,
        "muted": mix(text, surface, 0.7),
        "primary": c.get("primary", "#1f2937"),
        "primary_content": c.get("primary-content", "#ffffff"),
    }


@cache
def email_brand() -> dict[str, dict[str, str]]:
    theme = MVP_CONFIG["theme"]
    return {"light": palette(theme["default"]), "dark": palette(theme["dark"])}
