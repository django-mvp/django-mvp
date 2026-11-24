"""The layout code, such as ``lHh LpR lff``, read into what the templates need.

Three groups of three letters are the top, middle and bottom rows of the
layout, each read left, centre and right:

========  ================================
Letter    Area
========  ================================
``h``     the header
``l``     the left sidebar
``p``     the page
``r``     the right sidebar
``f``     the footer
========  ================================

A corner names the area that reaches it. An upper-case header, sidebar or
footer letter keeps that area in place while the layout scrolls. The rules are
Quasar's ``QLayout`` ``view`` property, and sphinx-daisyui reads its own
``layout`` option the same way.
"""

import re
from dataclasses import dataclass
from typing import ClassVar

from django.utils.safestring import mark_safe

AREA_NAMES = {
    "h": "header",
    "l": "left",
    "p": "page",
    "r": "right",
    "f": "footer",
}
SHAPE = re.compile(r"^[hl]h[hr] lpr [fl]f[fr]$")
HEADER_HEIGHT = "var(--dcl-header-h, 0px)"
FOOTER_HEIGHT = "var(--dcl-footer-h, 0px)"


class LayoutViewError(ValueError):
    """A value that is not a layout code."""


@dataclass(frozen=True)
class LayoutView:
    """A layout code read into the facts the layout's markup and styles need."""

    DEFAULT: ClassVar[str] = "hHh lpr fFf"

    code: str
    areas: str
    header_fixed: bool
    left_fixed: bool
    right_fixed: bool
    footer_fixed: bool
    left_top: str
    left_bottom: str
    right_top: str
    right_bottom: str
    # Which corners each sidebar reaches, for the playground's explanation.
    left_reaches_top: bool
    left_reaches_bottom: bool
    right_reaches_top: bool
    right_reaches_bottom: bool

    @classmethod
    def parse(cls, value: object) -> "LayoutView":
        """Read a layout code, or raise ``LayoutViewError`` saying what is wrong."""
        if value is None or value == "":
            value = cls.DEFAULT
        if not isinstance(value, str):
            raise LayoutViewError(cls.refusal(value))
        code = " ".join(value.split()) or cls.DEFAULT
        if not SHAPE.match(code.lower()):
            raise LayoutViewError(cls.refusal(value))
        rows = code.split(" ")
        lower = [row.lower() for row in rows]
        header_fixed = rows[0][1] == "H"
        footer_fixed = rows[2][1] == "F"
        left_fixed = "L" in (rows[0][0], rows[1][0], rows[2][0])
        right_fixed = "R" in (rows[0][2], rows[1][2], rows[2][2])
        return cls(
            code=code,
            areas=mark_safe(cls.template_areas(lower)),  # noqa: S308 - letters only
            header_fixed=header_fixed,
            left_fixed=left_fixed,
            right_fixed=right_fixed,
            footer_fixed=footer_fixed,
            left_top=HEADER_HEIGHT if header_fixed and lower[0][0] == "h" else "0px",
            left_bottom=FOOTER_HEIGHT if footer_fixed and lower[2][0] == "f" else "0px",
            right_top=HEADER_HEIGHT if header_fixed and lower[0][2] == "h" else "0px",
            right_bottom=FOOTER_HEIGHT if footer_fixed and lower[2][2] == "f" else "0px",
            left_reaches_top=lower[0][0] == "l",
            left_reaches_bottom=lower[2][0] == "l",
            right_reaches_top=lower[0][2] == "r",
            right_reaches_bottom=lower[2][2] == "r",
        )

    @staticmethod
    def template_areas(rows: list[str]) -> str:
        """Write rows of area letters as a ``grid-template-areas`` value."""
        return " ".join(
            "'" + " ".join(AREA_NAMES[letter] for letter in row) + "'" for row in rows
        )

    @staticmethod
    def refusal(value: object) -> str:
        """The message for a value that is not a layout code."""
        return (
            f"{value!r} is not a layout code. A layout code is three groups of three "
            "letters separated by spaces, such as 'hHh lpr fFf'. The top row is h or l, "
            "then h, then h or r. The middle row is l, p, r. The bottom row is f or l, "
            "then f, then f or r. An upper-case letter keeps that area in place while "
            "the layout scrolls."
        )

    def explain(self) -> list[str]:
        """Plain sentences saying what the code does, for the playground."""
        lines = []
        if self.left_reaches_top and self.left_reaches_bottom:
            lines.append("The left sidebar runs the full height, beside the header and the footer.")
        elif self.left_reaches_top:
            lines.append("The left sidebar reaches the top, beside the header.")
        elif self.left_reaches_bottom:
            lines.append("The left sidebar reaches the bottom, beside the footer.")
        else:
            lines.append("The left sidebar sits between the header and the footer.")
        if self.right_reaches_top and self.right_reaches_bottom:
            lines.append("The right sidebar runs the full height, beside the header and the footer.")
        elif self.right_reaches_top:
            lines.append("The right sidebar reaches the top, beside the header.")
        elif self.right_reaches_bottom:
            lines.append("The right sidebar reaches the bottom, beside the footer.")
        else:
            lines.append("The right sidebar sits between the header and the footer.")
        fixed = [
            name
            for name, flag in (
                ("the header", self.header_fixed),
                ("the left sidebar", self.left_fixed),
                ("the right sidebar", self.right_fixed),
                ("the footer", self.footer_fixed),
            )
            if flag
        ]
        if fixed:
            joined = fixed[0] if len(fixed) == 1 else ", ".join(fixed[:-1]) + " and " + fixed[-1]
            lines.append(f"While the page scrolls, {joined} stay{'s' if len(fixed) == 1 else ''} in place.")
        else:
            lines.append("Everything scrolls with the page.")
        return lines
