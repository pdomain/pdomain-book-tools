"""Packaging regression tests for pdomain-book-tools.

These don't exercise the running library — they assert invariants about
``pyproject.toml`` itself. The OpenCV PyPI ecosystem ships four mutually
exclusive distributions (``opencv-python``, ``opencv-contrib-python``,
``opencv-python-headless``, ``opencv-contrib-python-headless``) that all
install into the same ``cv2`` namespace. Declaring more than one is a
known footgun: pip resolves them independently, and whichever wheel
unpacks last wins, so runtime behavior depends on install order across
the wider environment. ``opencv-contrib-python`` is a strict superset of
``opencv-python`` (adds ``xfeatures2d``, SIFT, etc.), so the right move
is to keep contrib and drop the plain package.

This library uses the *headless* contrib build (``opencv-contrib-python-headless``)
because the full build bundles Qt GUI plugins under ``cv2/qt/plugins/`` and
sets ``QT_QPA_PLATFORM_PLUGIN_PATH`` at import time, hijacking Qt's
platform-plugin resolution for the whole process. That breaks any
PyQt6/QtWebEngine window launched downstream (e.g. ``pdomain-ocr-simple-gui
--desktop``). The headless build provides the identical ``cv2`` API and all
contrib modules without the bundled Qt plugins.

Regressions: H-17 in ``docs/review/bugs-high.md`` (dual-opencv conflict);
QT_QPA hijack confirmed on ``pdomain-ocr-simple-gui --desktop`` 2026-06-06.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _project_dependencies() -> list[str]:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    return list(data["project"]["dependencies"])


def _dep_names(deps: list[str]) -> set[str]:
    """Strip version specifiers and return bare distribution names."""
    names: set[str] = set()
    for dep in deps:
        # Names end at the first space, comparator, paren, or bracket.
        for sep in (" ", "<", ">", "=", "!", "~", "(", "[", ";"):
            idx = dep.find(sep)
            if idx != -1:
                dep = dep[:idx]
        names.add(dep.strip().lower())
    return names


def test_opencv_python_and_contrib_not_both_declared() -> None:
    """Reject having both plain and contrib (or plain-headless and contrib-headless).

    They install into the same ``cv2`` namespace; declaring both produces
    nondeterministic installs depending on resolver/install order. Keep
    only the contrib variant (strict superset, adds ``xfeatures2d``, SIFT, etc.).
    See H-17 in ``docs/review/bugs-high.md``.
    """
    names = _dep_names(_project_dependencies())
    assert not ("opencv-python" in names and "opencv-contrib-python" in names), (
        "pyproject.toml declares both 'opencv-python' and "
        "'opencv-contrib-python'; keep only 'opencv-contrib-python' "
        "(it is a strict superset). See H-17 in docs/review/bugs-high.md."
    )
    assert not (
        "opencv-python-headless" in names and "opencv-contrib-python-headless" in names
    ), (
        "pyproject.toml declares both 'opencv-python-headless' and "
        "'opencv-contrib-python-headless'; keep only "
        "'opencv-contrib-python-headless' (strict superset)."
    )


def test_opencv_headless_not_mixed_with_full() -> None:
    """Headless and full OpenCV wheels also conflict in the cv2 namespace."""
    names = _dep_names(_project_dependencies())
    full = {"opencv-python", "opencv-contrib-python"}
    headless = {"opencv-python-headless", "opencv-contrib-python-headless"}
    assert not (names & full and names & headless), (
        "pyproject.toml mixes full and headless OpenCV wheels — they "
        "install to the same cv2 namespace and conflict at runtime."
    )


def test_opencv_headless_build_declared() -> None:
    """Assert the *headless* contrib build is declared, never the full build.

    The full ``opencv-contrib-python`` wheel bundles Qt GUI plugins under
    ``cv2/qt/plugins/`` and unconditionally sets ``QT_QPA_PLATFORM_PLUGIN_PATH``
    on ``import cv2``, hijacking Qt's platform-plugin resolution for the whole
    process.  That breaks any downstream PyQt6/QtWebEngine window (confirmed:
    ``pdomain-ocr-simple-gui --desktop`` crash 2026-06-06).

    ``opencv-contrib-python-headless`` ships the identical ``cv2`` API and all
    contrib modules (``ximgproc``, ``xfeatures2d``, etc.) without the bundled
    Qt plugins — it is the correct dependency for a headless OCR/image library.
    """
    names = _dep_names(_project_dependencies())
    full_builds = {"opencv-python", "opencv-contrib-python"}
    assert not (names & full_builds), (
        f"pyproject.toml declares a full (GUI-capable) OpenCV wheel "
        f"({names & full_builds}). Switch to 'opencv-contrib-python-headless' "
        f"to prevent QT_QPA_PLATFORM_PLUGIN_PATH hijacking in downstream "
        f"PyQt6/QtWebEngine applications."
    )
    assert "opencv-contrib-python-headless" in names, (
        "pyproject.toml must declare 'opencv-contrib-python-headless'. "
        "The headless build provides the full cv2 + contrib API without "
        "bundled Qt plugins."
    )


def test_tomllib_available() -> None:
    """Sanity check: tomllib is stdlib on 3.11+; this repo requires >=3.11.

    We rely on tomllib here; if the project's minimum Python is ever lowered
    below 3.11 this test surfaces it loudly so we can swap to ``tomli``.
    """
    assert sys.version_info >= (3, 11), (
        "tomllib is stdlib on Python 3.11+; switch to tomli if "
        "supporting older interpreters."
    )
