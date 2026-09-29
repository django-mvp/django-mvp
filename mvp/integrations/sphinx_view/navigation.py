"""Sphinx extension: write the whole navigation tree beside the JSON build.

Sphinx renders each page's table of contents with only that page's branch
opened, so a sidebar built from it changes shape from page to page. This
extension writes the full tree once per build, as ``navigation.json``, for
:class:`~mvp.integrations.sphinx_view.menus.DocumentationMenu` to draw.

Add it after ``sphinx_view`` in the project's ``conf.py``::

    extensions = ["sphinx_view", "mvp.integrations.sphinx_view.navigation"]

It imports nothing from Django, so the docs build needs no settings.
"""

import json
from pathlib import Path

from sphinx import addnodes

FILENAME = "navigation.json"


def toctrees(env, docname):
    """Yield the toctree nodes of ``docname``, hidden ones included.

    A hidden toctree is how a Sphinx project lists pages for the navigation
    alone, so the sidebar draws its entries like any other.
    """
    yield from env.get_doctree(docname).findall(addnodes.toctree)


def entries(builder, toctree, seen):
    """Return the pages ``toctree`` lists, each with the pages it lists in turn."""
    env = builder.env
    found = []
    for title, ref in toctree["entries"]:
        if ref == "self" or ref not in env.titles or ref in seen:
            # External links and self-references are not pages this view serves.
            continue
        children = []
        for child in toctrees(env, ref):
            children.extend(entries(builder, child, seen | {ref}))
        found.append(
            {
                "title": title or env.titles[ref].astext(),
                "url": builder.get_target_uri(ref),
                "children": children,
            }
        )
    return found


def write_navigation(app, exception):
    """Write ``navigation.json`` into the build directory once the build ends."""
    if exception is not None or app.builder.format != "html":
        return
    root = app.config.root_doc
    sections = [
        {
            "caption": toctree.get("caption") or "",
            "entries": entries(app.builder, toctree, {root}),
        }
        for toctree in toctrees(app.env, root)
    ]
    navigation = {"title": app.env.titles[root].astext(), "sections": sections}
    target = Path(app.outdir) / FILENAME
    target.write_text(json.dumps(navigation, indent=2), encoding="utf-8")


def setup(app):
    """Register the extension with Sphinx."""
    app.connect("build-finished", write_navigation)
    return {"version": "1", "parallel_read_safe": True}
