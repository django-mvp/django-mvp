"""Work out the classes daisy-cotton's components can render, and which are styled.

The set is read from the templates, never by rendering a component. A class is
written literally, built by ``{% variation %}``, built by ``{% responsive %}``,
or a literal stem joined to a template variable (``mask-half-{{ item.half }}``).
"""

import re
from pathlib import Path

from daisy_cotton.templatetags.daisy_cotton import BREAKPOINTS

# Values a template variable joined to a literal stem can take. daisy-cotton
# takes them from ``rating_items`` in its template tags.
STEM_VALUES = {"mask-half-": ("1", "2")}

COMMENTS = re.compile(
    r"\{#.*?#\}|\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}|<!--.*?-->", re.DOTALL
)
VARIATION_TAG = re.compile(r"\{%\s*variation\b(.*?)%\}", re.DOTALL)
VARIATION_ARGS = re.compile(
    r"^\s*\S+\s+([\"'])(.*?)\1\s+([\"'])(.*?)\3(\s+as\s+\w+)?\s*$"
)
RESPONSIVE_TAG = re.compile(r"\{%\s*responsive\b(.*?)%\}", re.DOTALL)
RESPONSIVE_ARGS = re.compile(r"^\s*\S+\s+([\"'])(.*?)\1(\s+as\s+\w+)?\s*$")
TEMPLATE_TAG = re.compile(r"\{%.*?%\}", re.DOTALL)
TEMPLATE_VARIABLE = re.compile(r"\{\{.*?\}\}", re.DOTALL)
CLASS_ATTRIBUTE = re.compile(
    r"(?<![\w:@.-])[\w-]*class\s*=\s*(?:\"([^\"]*)\"|'([^']*)')"
)
SOURCE_INLINE = re.compile(r"@source\s+inline\(\s*\"([^\"]*)\"\s*\)")
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
VARIABLE_MARK = "\x00"


def component_classes(templates_dir):
    """Return the classes the templates under a directory can render.

    Literal classes are read from every attribute whose name is or ends in
    ``class``, after comments, template tags and template variables are taken
    out. Each ``{% variation %}`` gives ``base-option`` for every option, and
    each ``{% responsive %}`` gives the class plain and at every breakpoint. A
    class the caller supplies (``{{ class }}``) adds nothing.

    Args:
        templates_dir: The directory holding the templates, read recursively.

    Returns:
        The set of class names.

    Raises:
        ValueError: A literal is joined to a template variable and ``STEM_VALUES``
            has no values for it, or a ``variation`` or ``responsive`` tag is not
            written with quoted literals.
    """
    classes = set()
    for path in sorted(Path(templates_dir).rglob("*.html")):
        source = COMMENTS.sub("", path.read_text(encoding="utf-8"))

        for tag in VARIATION_TAG.findall(source):
            match = VARIATION_ARGS.match(tag)
            if match is None:
                raise ValueError(f"Cannot read the variation tag {tag!r} in {path}")
            base, options = match.group(2), match.group(4)
            classes |= {f"{base}-{option}" for option in options.split(",")}

        for tag in RESPONSIVE_TAG.findall(source):
            match = RESPONSIVE_ARGS.match(tag)
            if match is None:
                raise ValueError(f"Cannot read the responsive tag {tag!r} in {path}")
            name = match.group(2)
            classes |= {name, *(f"{bp}:{name}" for bp in BREAKPOINTS)}

        source = TEMPLATE_TAG.sub(" ", source)
        source = TEMPLATE_VARIABLE.sub(VARIABLE_MARK, source)
        for double, single in CLASS_ATTRIBUTE.findall(source):
            for token in (double or single).split():
                if token == VARIABLE_MARK:
                    continue
                if VARIABLE_MARK not in token:
                    classes.add(token)
                    continue
                stem = token.split(VARIABLE_MARK)[0]
                if stem not in STEM_VALUES:
                    raise ValueError(
                        f"No values for the stem {stem!r} (from {token!r}) in {path}"
                    )
                classes |= {f"{stem}{value}" for value in STEM_VALUES[stem]}

    return classes


def unstyled_classes(classes, stylesheet):
    """Return the classes that have no selector in a stylesheet.

    A selector is a dot, the class name with every character outside
    ``[A-Za-z0-9_-]`` backslash-escaped, and then no further name character or
    backslash. A name that starts with a digit is written the way CSS writes it,
    with a code-point escape: ``2xl:drawer-open`` is ``.\\32 xl\\:drawer-open``.

    Args:
        classes: The class names to look for.
        stylesheet: The stylesheet text.

    Returns:
        The set of class names with no selector.
    """

    def escape(name):
        return re.sub(r"[^A-Za-z0-9_-]", lambda m: "\\" + m.group(), name)

    def has_selector(name):
        if name[0].isdigit():
            written = f"\\3{name[0]} {escape(name[1:])}"
        else:
            written = escape(name)
        pattern = rf"(?<!\\)\.{re.escape(written)}(?![A-Za-z0-9_\\-])"
        return re.search(pattern, stylesheet) is not None

    return {name for name in classes if not has_selector(name)}


def safelisted_classes(preset):
    """Return every class an ``@source inline()`` entry in a preset declares.

    Brace groups are expanded, nested ones included, and an empty option stands
    for no text. CSS comments are ignored.

    Args:
        preset: The preset stylesheet text.

    Returns:
        The set of class names.
    """

    def expand(pattern):
        start = pattern.find("{")
        if start == -1:
            return {pattern}
        depth, options, option_start = 0, [], start + 1
        for index in range(start, len(pattern)):
            char = pattern[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    options.append(pattern[option_start:index])
                    end = index
                    break
            elif char == "," and depth == 1:
                options.append(pattern[option_start:index])
                option_start = index + 1
        expanded = set()
        for option in options:
            expanded |= expand(pattern[:start] + option + pattern[end + 1 :])
        return expanded

    classes = set()
    for pattern in SOURCE_INLINE.findall(CSS_COMMENT.sub("", preset)):
        classes |= expand(pattern)
    return classes
