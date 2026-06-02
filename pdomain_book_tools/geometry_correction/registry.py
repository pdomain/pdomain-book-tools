"""Backend registry for geometry-correction backends.

Each backend kind (deskew, dewarp, page_side, curvature) maps a name to a
zero-argument factory callable that returns a fresh backend instance.
"""

from __future__ import annotations

from collections.abc import Callable

Registry = dict[str, dict[str, Callable[[], object]]]
_REGISTRY: Registry = {"deskew": {}, "dewarp": {}, "page_side": {}, "curvature": {}}


def _register(kind: str, name: str, factory: Callable[[], object]) -> None:
    _REGISTRY[kind][name] = factory


def _get(kind: str, name: str) -> object:
    try:
        return _REGISTRY[kind][name]()
    except KeyError as exc:
        raise KeyError(
            f"no {kind} backend named {name!r}; have {sorted(_REGISTRY[kind])}"
        ) from exc


def available(kind: str) -> list[str]:
    """Return sorted list of registered backend names for *kind*."""
    return sorted(_REGISTRY[kind])


def register_deskew(name: str, factory: Callable[[], object]) -> None:
    """Register a deskew backend factory under *name*."""
    _register("deskew", name, factory)


def register_dewarp(name: str, factory: Callable[[], object]) -> None:
    """Register a dewarp backend factory under *name*."""
    _register("dewarp", name, factory)


def register_page_side(name: str, factory: Callable[[], object]) -> None:
    """Register a page-side detector factory under *name*."""
    _register("page_side", name, factory)


def register_curvature(name: str, factory: Callable[[], object]) -> None:
    """Register a curvature detector factory under *name*."""
    _register("curvature", name, factory)


def get_deskew(name: str) -> object:
    """Return a new instance of the named deskew backend."""
    return _get("deskew", name)


def get_dewarp(name: str) -> object:
    """Return a new instance of the named dewarp backend."""
    return _get("dewarp", name)


def get_page_side(name: str) -> object:
    """Return a new instance of the named page-side detector."""
    return _get("page_side", name)


def get_curvature(name: str) -> object:
    """Return a new instance of the named curvature detector."""
    return _get("curvature", name)
