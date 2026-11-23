"""One search across the kinds of result a site has.

Register a kind with :func:`register`, from ``AppConfig.ready``. See
docs/developer/search.md.
"""

from mvp.search.kinds import FunctionKind, Group, Kind, Result
from mvp.search.model_kind import ModelKind
from mvp.search.registry import register, registered
from mvp.search.search import search

__all__ = [
    "FunctionKind",
    "Group",
    "Kind",
    "ModelKind",
    "Result",
    "register",
    "registered",
    "search",
]
