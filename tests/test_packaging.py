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

Regression: H-17 in ``docs/review/bugs-high.md``.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
COVERAGERC_CPU = REPO_ROOT / ".coveragerc.cpu"


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
    """Reject having both ``opencv-python`` and ``opencv-contrib-python``.

    They install into the same ``cv2`` namespace; declaring both produces
    nondeterministic installs depending on resolver/install order. Keep
    only ``opencv-contrib-python`` (strict superset).
    """
    names = _dep_names(_project_dependencies())
    assert not ("opencv-python" in names and "opencv-contrib-python" in names), (
        "pyproject.toml declares both 'opencv-python' and "
        "'opencv-contrib-python'; keep only 'opencv-contrib-python' "
        "(it is a strict superset). See H-17 in docs/review/bugs-high.md."
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


def test_gpu_extra_does_not_declare_unused_opencv_cuda() -> None:
    """No code imports ``cv2.cuda``, and the package drags in ``opencv-python``.

    ``opencv-cuda`` depends on ``opencv-python``, which conflicts in the ``cv2``
    namespace with the ``opencv-contrib-python`` this project requires.
    """
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    gpu_names = _dep_names(list(data["project"]["optional-dependencies"]["gpu"]))
    assert "opencv-cuda" not in gpu_names


def test_coverage_config_does_not_omit_the_missing_cv2cuda_package() -> None:
    """The ``cv2cuda_processing`` package does not exist, so omitting it is dead."""
    assert not (
        REPO_ROOT / "pdomain_book_tools" / "image_processing" / "cv2cuda_processing"
    ).exists()
    assert "cv2cuda_processing" not in PYPROJECT.read_text(encoding="utf-8")
    assert "cv2cuda_processing" not in COVERAGERC_CPU.read_text(encoding="utf-8")


def test_tomllib_available() -> None:
    """Sanity check: tomllib is stdlib on 3.11+; this repo requires >=3.11.

    We rely on tomllib here; if the project's minimum Python is ever lowered
    below 3.11 this test surfaces it loudly so we can swap to ``tomli``.
    """
    assert sys.version_info >= (3, 11), (
        "tomllib is stdlib on Python 3.11+; switch to tomli if "
        "supporting older interpreters."
    )
