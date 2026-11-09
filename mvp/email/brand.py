"""The colours and logos an email is drawn in, taken from the project's own site.

The colours are the themes ``MVP_CONFIG["theme"]`` names for the light and dark
schemes, read out of the static stylesheets that define them, so a project that
writes its own theme gets an email in that theme without configuring anything.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
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

#: The project's logo the email PNGs are drawn from, relative to a static directory.
LOGO_SOURCE = "brand/logo.svg"

#: The package's own static directory.
PACKAGE_STATIC = Path(__file__).resolve().parents[1] / "static"

#: A selector that is a theme on its own, quoted or not, with ``:root`` optional.
THEME_SELECTOR = re.compile(
    r"""^(?::root)?\[data-theme=(["']?)([\w-]+)\1\](?::root)?$"""
)

#: How much of the text colour shows in the muted colour, over the surface.
MUTED_AMOUNT = 0.7


class UnresolvedReference(ValueError):
    """A ``var()`` names a custom property the theme gives no value, and has no fallback.

    Attributes:
        name: The custom property, such as ``--brand-ink``.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.name = name


class ThemeReader:
    """Reads theme colours out of the static stylesheets that define them."""

    @classmethod
    def read(
        cls, names: set[str]
    ) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str], str | None]]:
        """Read the named themes from every stylesheet the static finders list.

        Args:
            names: The theme names to read.

        Returns:
            What ``colours()`` gives for the custom properties ``declarations()``
            finds for the named themes.
        """
        return cls.colours(names, cls.declarations(names))

    @classmethod
    def declarations(cls, names: set[str]) -> dict[str, dict[str, list[list]]]:
        """Gather the custom properties the named themes declare, in every stylesheet.

        Stylesheets are read in finder order, so a project's stylesheet comes
        before the package's. The package's own stylesheets are read last,
        whatever the finders list.

        Args:
            names: The theme names to read.

        Returns:
            For each named theme some rule names on its own, each custom property
            its rules declare, mapped to the values found for it in order.
        """
        found: dict[str, dict[str, list[list]]] = {}
        for path in cls.stylesheets():
            text = Path(path).read_text(encoding="utf-8", errors="replace")
            if "data-theme" not in text:
                continue
            for rule in cls.rules(
                tinycss2.parse_stylesheet(
                    text, skip_comments=True, skip_whitespace=True
                )
            ):
                named = cls.themes_named(rule.prelude) & names
                if not named:
                    continue
                declared = [
                    (declaration.name, declaration.value)
                    for declaration in tinycss2.parse_blocks_contents(
                        rule.content, skip_comments=True, skip_whitespace=True
                    )
                    if declaration.type == "declaration"
                    and declaration.name.startswith("--")
                ]
                for name in named:
                    properties = found.setdefault(name, {})
                    for prop, value in declared:
                        properties.setdefault(prop, []).append(value)
        return found

    @staticmethod
    def stylesheets() -> Iterator[str]:
        """List the stylesheets the static finders know of.

        Returns:
            The file path of each ``.css`` file the finders list, in finder order, then
            the package's own ``.css`` files, wherever the finders list them.
        """
        packaged = sorted((PACKAGE_STATIC / "css").glob("*.css"))
        own = {path.resolve() for path in packaged}
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                if (
                    path.endswith(".css")
                    and Path(storage.path(path)).resolve() not in own
                ):
                    yield storage.path(path)
        for path in packaged:
            yield str(path)

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

    @classmethod
    def colours(
        cls, names: set[str], declared: dict[str, dict[str, list[list]]]
    ) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str], str | None]]:
        """Read each theme's ``THEME_COLOURS`` from the custom properties it declares.

        The first value found for a colour that can be read wins. A ``var()`` in
        it takes the first value found for that property in the same theme, or
        its fallback when the theme gives the property none.

        Args:
            names: The theme names to read.
            declared: What ``declarations()`` found for them.

        Returns:
            For each theme name, its ``THEME_COLOURS`` as sRGB hex strings, keyed
            without the ``--color-`` prefix, where a property no stylesheet gives
            a readable value for is absent; and the ``(theme, property)`` pairs
            that were given a value which could not be read before any that
            could, each mapped to the custom property a ``var()`` in it could
            not resolve, or ``None`` when the value is not a colour.
        """
        themes: dict[str, dict[str, str]] = {name: {} for name in names}
        unreadable: dict[tuple[str, str], str | None] = {}
        for name, properties in declared.items():
            for key in THEME_COLOURS:
                prop = f"--color-{key}"
                for value in properties.get(prop, []):
                    try:
                        text = tinycss2.serialize(
                            cls.substitute(value, properties, {prop})
                        ).strip()
                        themes[name][key] = (
                            Color(text).convert("srgb").fit().to_string(hex=True)
                        )
                        break
                    except UnresolvedReference as missing:
                        unreadable.setdefault((name, key), missing.name)
                    except ValueError:
                        unreadable.setdefault((name, key), None)
        return themes, unreadable

    @classmethod
    def substitute(
        cls, tokens: list, properties: dict[str, list[list]], seen: set[str]
    ) -> list:
        """Replace every ``var()`` in a value with what it refers to.

        Args:
            tokens: The value's tokens.
            properties: The theme's custom properties, each with its values in order.
            seen: The properties being resolved already, which a ``var()`` may
                not refer back to.

        Returns:
            The value's tokens with no ``var()`` left in them.

        Raises:
            UnresolvedReference: If a ``var()`` refers to a property the theme
                gives no value, or one that refers back to itself, and has no
                fallback.
            ValueError: If a ``var()`` names no custom property.
        """
        result = []
        for token in tokens:
            if token.type != "function":
                result.append(token)
            elif token.lower_name == "var":
                result += cls.reference(token.arguments, properties, seen)
            else:
                result.append(
                    tinycss2.ast.FunctionBlock(
                        token.source_line,
                        token.source_column,
                        token.name,
                        cls.substitute(token.arguments, properties, seen),
                    )
                )
        return result

    @classmethod
    def reference(
        cls, arguments: list, properties: dict[str, list[list]], seen: set[str]
    ) -> list:
        """Resolve one ``var()`` from its arguments.

        Args:
            arguments: The tokens inside the ``var()``.
            properties: The theme's custom properties, each with its values in order.
            seen: The properties being resolved already.

        Returns:
            The tokens the ``var()`` stands for.

        Raises:
            UnresolvedReference: If the property cannot be resolved and there is no fallback.
            ValueError: If the ``var()`` names no custom property.
        """
        significant = [token for token in arguments if token.type != "whitespace"]
        if not significant or significant[0].type != "ident":
            raise ValueError("var() names no custom property")
        name = significant[0].value
        if not name.startswith("--"):
            raise ValueError(f"var({name}) names no custom property")
        comma = next(
            (
                index
                for index, token in enumerate(arguments)
                if token.type == "literal" and token.value == ","
            ),
            None,
        )
        fallback = None if comma is None else arguments[comma + 1 :]
        if name not in seen and name in properties:
            try:
                return cls.substitute(properties[name][0], properties, seen | {name})
            except UnresolvedReference:
                if fallback is None:
                    raise
        elif fallback is None:
            raise UnresolvedReference(name)
        return cls.substitute(fallback, properties, seen)


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
class BrandProblem:
    """Something in the project's theme or logo that the email cannot use.

    Attributes:
        id: The system check id the problem is reported under.
        message: What the email cannot use, and why.
        hint: What to do about it.
    """

    id: str
    message: str
    hint: str

    def __str__(self) -> str:
        """Give the message."""
        return self.message


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
    found_problems: tuple[BrandProblem, ...] = field(
        default=(), repr=False, compare=False
    )

    @classmethod
    @cache
    def current(cls) -> "EmailBrand":
        """Read the brand from the configured themes and the static files.

        Read once per process. Call ``EmailBrand.current.cache_clear()`` after
        changing ``MVP_CONFIG["theme"]`` or the static files. A property the
        configured theme lacks, or gives an unreadable value, comes from the
        package's theme of the same name and then from its ``light`` or ``dark``.

        Returns:
            The brand.
        """
        light_name = MVP_CONFIG["theme"]["default"]  # type: ignore[index]
        dark_name = MVP_CONFIG["theme"]["dark"]  # type: ignore[index]
        names = {light_name, dark_name, "light", "dark"}
        declared = ThemeReader.declarations(names)
        themes, unreadable = ThemeReader.colours(names, declared)
        configured = dict.fromkeys((light_name, dark_name))
        problems = [
            BrandProblem(
                "mvp.W002",
                f'The theme "{name}" is not defined by any stylesheet, so the email uses the package\'s own colours.',
                'Define the theme in a stylesheet your static files serve, or fix MVP_CONFIG["theme"].',
            )
            for name in configured
            if name not in declared
        ]
        problems += [
            cls.unreadable_problem(name, key, missing)
            for (name, key), missing in sorted(unreadable.items())
            if name in configured
        ]
        problems += cls.stale_logo_problems()
        return cls(
            light=Palette.from_theme({**themes["light"], **themes[light_name]}),
            dark=Palette.from_theme({**themes["dark"], **themes[dark_name]}),
            logo=static(LOGO),
            logo_dark=static(LOGO_DARK) if finders.find(LOGO_DARK) else None,
            found_problems=tuple(problems),
        )

    @staticmethod
    def unreadable_problem(name: str, key: str, missing: str | None) -> BrandProblem:
        """Describe a theme colour the email cannot read.

        Args:
            name: The theme.
            key: The colour, without its ``--color-`` prefix.
            missing: The custom property a ``var()`` in the value could not
                resolve, or ``None`` when the value is not a colour.

        Returns:
            The problem, reported under ``mvp.W003``.
        """
        if missing is None:
            return BrandProblem(
                "mvp.W003",
                f'The theme "{name}" sets --color-{key} to a value that is not a colour, '
                "so the email uses the package's own colour.",
                "Write the colour as hex, rgb(), hsl() or oklch().",
            )
        return BrandProblem(
            "mvp.W003",
            f'The theme "{name}" sets --color-{key} through {missing}, which has no value in that theme, '
            "so the email uses the package's own colour.",
            f"Set {missing} in a rule for the theme, or give the var() a fallback.",
        )

    @staticmethod
    def stale_logo_problems() -> list[BrandProblem]:
        """Find a project logo whose email PNG still comes from the package.

        Returns:
            One problem when ``brand/logo.svg`` is found outside the package and
            ``brand/email/logo.png`` only inside it, and none otherwise.
        """
        source, png = finders.find(LOGO_SOURCE), finders.find(LOGO)
        if not source or Path(source).resolve().is_relative_to(PACKAGE_STATIC):
            return []
        if png and not Path(png).resolve().is_relative_to(PACKAGE_STATIC):
            return []
        return [
            BrandProblem(
                "mvp.W004",
                f"The project has its own {LOGO_SOURCE}, but the email still shows the package's {LOGO}.",
                "Run: python manage.py mvp_email_logos",
            )
        ]

    @classmethod
    def problems(cls) -> list[BrandProblem]:
        """List what the email cannot use of the project's theme and logo.

        Returns:
            One problem for each configured theme no stylesheet defines, for
            each colour that could not be read, and for a project logo whose
            email PNG still comes from the package, in the order found.
        """
        return list(cls.current().found_problems)
