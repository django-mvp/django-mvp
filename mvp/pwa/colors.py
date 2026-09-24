"""Theme colours for the manifest, read from the package's committed stylesheet."""

import math
import re
from functools import cache
from pathlib import Path

STYLESHEET = Path(__file__).parents[1] / "static" / "css" / "django-mvp.css"

BASE_100 = re.compile(
    r"\[data-theme=(?P<name>[\w-]+)\]\{[^}]*?"
    r"--color-base-100:oklch\((?P<l>[\d.]+)(?P<percent>%?) (?P<c>[\d.]+) (?P<h>[\d.]+)\)"
)


class ThemeColors:
    """The ``base-100`` colour of every theme the package ships, as ``#rrggbb``.

    DaisyUI declares each theme's colours as OKLCH custom properties. Manifest
    colours must be understood by every browser, so they are converted to hex.
    Reading the stylesheet the pages already use means the two cannot disagree.
    """

    @classmethod
    def for_theme(cls, name):
        """The hex colour for ``name``, or ``None`` if the package does not ship it."""
        return cls.table().get(name)

    @classmethod
    @cache
    def table(cls):
        """Every shipped theme's colour, parsed once per process."""
        css = STYLESHEET.read_text(encoding="utf-8")
        return {
            match["name"]: cls.to_hex(
                float(match["l"]) / (100 if match["percent"] else 1),
                float(match["c"]),
                float(match["h"]),
            )
            for match in BASE_100.finditer(css)
        }

    @staticmethod
    def to_hex(lightness, chroma, hue):
        """Convert OKLCH to gamma-encoded sRGB, clamped to the gamut."""
        a = chroma * math.cos(math.radians(hue))
        b = chroma * math.sin(math.radians(hue))
        l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
        m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
        s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
        linear = (
            4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
            -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
            -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
        )
        channels = []
        for value in linear:
            value = min(max(value, 0.0), 1.0)
            encoded = (
                12.92 * value
                if value <= 0.0031308
                else 1.055 * value ** (1 / 2.4) - 0.055
            )
            channels.append(round(encoded * 255))
        return "#{:02x}{:02x}{:02x}".format(*channels)
