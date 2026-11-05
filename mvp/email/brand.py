"""The colours and logos an email is drawn in, taken from the project's own site.

The colours are the themes ``MVP_CONFIG["theme"]`` names for the light and dark
schemes, read out of the static stylesheets that define them, so a project that
writes its own theme gets an email in that theme without configuring anything.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import tinycss2
from coloraide import Color
from django.contrib.staticfiles import finders
from django.templatetags.static import static

from mvp.config import MVP_CONFIG

#: Theme properties an email is drawn from, without their ``--color-`` prefix.
THEME_COLOURS = (
    "base-100",
    "base-200",
    "base-300",
    "base-content",
    "primary",
    "primary-content",
)

#: Where the package's own email logos are, relative to a static directory.
LOGO = "brand/email/logo.png"
LOGO_DARK = "brand/email/logo_dark.png"

#: A selector that is a theme on its own, quoted or not, with ``:root`` optional.
THEME_SELECTOR = re.compile(
    r"""^(?::root)?\[data-theme=(["']?)([\w-]+)\1\](?::root)?$"""
)

#: How much of the text colour shows in the muted colour, over the surface.
MUTED_AMOUNT = 0.7


class ThemeReader:
    """Reads theme colours out of the static stylesheets that define them."""

    @classmethod
    def read(cls, names: set[str]) -> dict[str, dict[str, str]]:
        """Read the named themes from every stylesheet the static finders list.

        Stylesheets are read in finder order and the first value found for a
        property wins, so a project's stylesheet beats the package's.

        Args:
            names: The theme names to read.

        Returns:
            For each theme name, its ``THEME_COLOURS`` as sRGB hex strings, keyed
            without the ``--color-`` prefix. A property no stylesheet gives a
            readable value for is absent.
        """
        themes: dict[str, dict[str, str]] = {name: {} for name in names}
        for path in cls.stylesheets():
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            if "data-theme" not in text:
                continue
            for rule in cls.rules(
                tinycss2.parse_stylesheet(
                    text, skip_comments=True, skip_whitespace=True
                )
            ):
                for name in cls.themes_named(rule.prelude) & names:
                    for key, value in cls.colours(rule.content).items():
                        themes[name].setdefault(key, value)
        return themes

    @staticmethod
    def stylesheets() -> Iterator[str]:
        """List the stylesheets the static finders know of.

        Returns:
            The file path of each ``.css`` file, in finder order.
        """
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                if path.endswith(".css"):
                    yield storage.path(path)

    @classmethod
    def rules(cls, nodes: list) -> Iterator[tinycss2.ast.QualifiedRule]:
        """Flatten parsed nodes into their style rules, descending into ``@layer`` blocks.

        Args:
            nodes: Parsed stylesheet nodes.

        Returns:
            Each style rule, in source order.
        """
        for node in nodes:
            if node.type == "qualified-rule":
                yield node
            elif (
                node.type == "at-rule"
                and node.lower_at_keyword == "layer"
                and node.content is not None
            ):
                yield from cls.rules(
                    tinycss2.parse_rule_list(
                        node.content, skip_comments=True, skip_whitespace=True
                    )
                )

    @staticmethod
    def themes_named(prelude: list) -> set[str]:
        """Find the themes a rule's selector list names on their own.

        A selector such as ``[data-theme=nord] .mvp-sidebar`` names a theme and
        then something inside it, so it is not the theme's colours.

        Args:
            prelude: The tokens before a rule's block.

        Returns:
            The theme names for which one of the comma-separated selectors is the theme alone.
        """
        selectors: list[list] = [[]]
        for token in prelude:
            if token.type == "literal" and token.value == ",":
                selectors.append([])
            else:
                selectors[-1].append(token)
        matches = (
            THEME_SELECTOR.match(tinycss2.serialize(selector).strip())
            for selector in selectors
        )
        return {match.group(2) for match in matches if match}

    @staticmethod
    def colours(content: list) -> dict[str, str]:
        """Read the theme properties a rule's block sets to a colour that can be read.

        A value that refers to another property, ``var()``, is skipped, as is one
        that is not a colour.

        Args:
            content: The tokens inside a rule's block.

        Returns:
            Each ``THEME_COLOURS`` property the block sets, as an sRGB hex string.
        """
        found: dict[str, str] = {}
        for declaration in tinycss2.parse_blocks_contents(
            content, skip_comments=True, skip_whitespace=True
        ):
            if declaration.type != "declaration" or not declaration.name.startswith(
                "--color-"
            ):
                continue
            key = declaration.name.removeprefix("--color-")
            value = tinycss2.serialize(declaration.value).strip()
            if key not in THEME_COLOURS or "var(" in value.lower():
                continue
            try:
                found.setdefault(
                    key, Color(value).convert("srgb").fit().to_string(hex=True)
                )
            except ValueError:
                continue
        return found


@dataclass(frozen=True)
class Palette:
    """The colours of one colour scheme, as sRGB hex strings."""

    page: str
    surface: str
    border: str
    text: str
    muted: str
    primary: str
    primary_content: str

    @classmethod
    def from_theme(cls, colours: dict[str, str]) -> "Palette":
        """Build the palette an email uses from a theme's colours.

        Args:
            colours: A theme's ``THEME_COLOURS``, as sRGB hex strings.

        Returns:
            The palette, with the muted colour the text colour over the surface.

        Raises:
            KeyError: If the theme lacks one of ``THEME_COLOURS``.
        """
        surface, text = colours["base-100"], colours["base-content"]
        muted = (
            Color(text)
            .mix(Color(surface), 1 - MUTED_AMOUNT, space="srgb")
            .to_string(hex=True)
        )
        return cls(
            page=colours["base-200"],
            surface=surface,
            border=colours["base-300"],
            text=text,
            muted=muted,
            primary=colours["primary"],
            primary_content=colours["primary-content"],
        )


@dataclass(frozen=True)
class EmailBrand:
    """The colours and logos of the project's email: both schemes and both logos.

    Attributes:
        light: The palette of the theme named by ``MVP_CONFIG["theme"]["default"]``.
        dark: The palette of the theme named by ``MVP_CONFIG["theme"]["dark"]``.
        logo: Static URL of the logo PNG.
        logo_dark: Static URL of the dark logo PNG, or ``None`` when no such file is found.
    """

    light: Palette
    dark: Palette
    logo: str
    logo_dark: str | None

    @classmethod
    @cache
    def current(cls) -> "EmailBrand":
        """Read the brand from the configured themes and the static files.

        Read once per process. Call ``EmailBrand.current.cache_clear()`` after
        changing ``MVP_CONFIG["theme"]`` or the static files.

        Returns:
            The brand.

        Raises:
            KeyError: If a configured theme lacks one of ``THEME_COLOURS``.
        """
        light_name = MVP_CONFIG["theme"]["default"]  # type: ignore[index]
        dark_name = MVP_CONFIG["theme"]["dark"]  # type: ignore[index]
        themes = ThemeReader.read({light_name, dark_name})
        return cls(
            light=Palette.from_theme(themes[light_name]),
            dark=Palette.from_theme(themes[dark_name]),
            logo=static(LOGO),
            logo_dark=static(LOGO_DARK) if finders.find(LOGO_DARK) else None,
        )
