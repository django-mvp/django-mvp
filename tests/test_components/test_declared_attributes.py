"""Every name a component declares in ``<c-vars>`` must be read by its own template.

A declared name that the template never reads is worse than an undocumented
one. Cotton strips declared names out of the attribute pass-through, so setting
it does nothing *and* it never reaches the DOM either — there is no error, no
warning, and nothing in the rendered page to tell the caller it was ignored.
``CONTEXT.md`` forbids them for that reason.

"Read" means read as a template expression: ``{{ name }}``, a ``{% %}`` tag that
names it, or a dynamic attribute such as ``:title="name"``. A literal HTML
attribute that merely contains the word does not count — ``data-prefix="$"``
alongside a declared ``prefix`` is exactly the shape this guard exists to catch.

Declarations are read out of the template source rather than from a rendered
page: a ghost attribute produces no output at all, so there is nothing in the
DOM to assert against.
"""

import re
from pathlib import Path

import pytest

import mvp

COTTON_DIR = Path(next(iter(mvp.__path__))).resolve() / "templates" / "cotton"

CVARS = re.compile(r"<c-vars\b(?P<body>.*?)/?>", re.DOTALL)

# An attribute value is a quoted string, which may itself contain a quoted
# `{% trans "..." %}` default, or a bare token such as `False`.
VALUE = r"""(?:"(?:\{%.*?%\}|[^"])*"|'(?:\{%.*?%\}|[^'])*'|[^\s"'<>=]+)"""
DECLARATION = re.compile(
    r"(?P<name>:?[A-Za-z_][\w-]*)(?:\s*=\s*(?:%s))?" % VALUE, re.DOTALL
)

EXPRESSION = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)
DYNAMIC_ATTR = re.compile(r"""(?<![\w:]):[A-Za-z_][\w-]*\s*=\s*"([^"]*)\"""")
COMMENT_BLOCK = re.compile(
    r"\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}", re.DOTALL
)


def declared_names(cvars_body):
    """Every attribute name declared inside a ``<c-vars>`` tag, in order."""
    names = []
    end_of_previous = 0
    for match in DECLARATION.finditer(cvars_body):
        if match.start() < end_of_previous:
            continue
        end_of_previous = match.end()
        names.append(match.group("name").lstrip(":"))
    return names


def expressions(body):
    """Every template expression in a component body, joined into one string.

    Prose inside ``{% comment %}`` is dropped first: a props list in a comment
    block names attributes without reading any of them.
    """
    body = COMMENT_BLOCK.sub("", body)
    return " ".join(EXPRESSION.findall(body) + DYNAMIC_ATTR.findall(body))


def is_read(name, source):
    """Is ``name`` read as a variable anywhere in ``source``?

    Cotton exposes a hyphenated attribute under an underscored name, so
    ``hide-label`` is declared one way and read the other.
    """
    spellings = {name, name.replace("-", "_")}
    return any(re.search(rf"\b{re.escape(s)}\b", source) for s in spellings)


def components_with_declarations():
    """Each packaged component template that declares attributes, by path."""
    found = []
    for path in sorted(COTTON_DIR.rglob("*.html")):
        source = path.read_text()
        if CVARS.search(source):
            found.append(path.relative_to(COTTON_DIR).as_posix())
    return found


COMPONENTS = components_with_declarations()


class TestDeclaredAttributesAreRead:
    def test_inventory_is_nonempty(self):
        assert len(COMPONENTS) > 50, "cotton template discovery looks broken"

    @pytest.mark.parametrize("relpath", COMPONENTS)
    def test_no_declared_attribute_goes_unread(self, relpath):
        source = (COTTON_DIR / relpath).read_text()
        declaration = CVARS.search(source)
        body = source[: declaration.start()] + source[declaration.end() :]

        unread = [
            name
            for name in declared_names(declaration.group("body"))
            if not is_read(name, expressions(body))
        ]

        assert not unread, (
            f"{relpath} declares {', '.join(unread)} and never reads it. "
            "Read it, or drop the declaration so a caller's value reaches the DOM."
        )


class TestTheGuardItselfReadsDeclarations:
    """The parser has to survive the declaration shapes the package uses."""

    def test_a_translated_default_is_one_declaration(self):
        assert declared_names(' label="{% trans "Search" %}" ') == ["label"]

    def test_an_unquoted_default_is_one_declaration(self):
        assert declared_names(" row=False wrap=False ") == ["row", "wrap"]

    def test_a_dynamic_declaration_drops_its_colon(self):
        assert declared_names(""" :size_opts="{'sm': 'x'}" """) == ["size_opts"]

    def test_a_literal_attribute_is_not_a_read(self):
        assert not is_read("prefix", expressions('<pre data-prefix="$">'))

    def test_a_variable_is_a_read(self):
        assert is_read("prefix", expressions('<pre data-prefix="{{ prefix }}">'))

    def test_a_dynamic_attribute_is_a_read(self):
        assert is_read("info", expressions('<c-page.info :text="info" />'))

    def test_a_comment_block_is_not_a_read(self):
        assert not is_read(
            "fade", expressions("{% comment %}fade — dims the page{% endcomment %}")
        )
