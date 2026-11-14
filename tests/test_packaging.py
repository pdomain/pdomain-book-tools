"""Packaging regression tests for pdomain-book-tools.

Most of these assert invariants about ``pyproject.toml`` itself. The OpenCV
PyPI ecosystem ships four mutually exclusive distributions
(``opencv-python``, ``opencv-contrib-python``, ``opencv-python-headless``,
``opencv-contrib-python-headless``) that all install into the same ``cv2``
folder. Installing more than one leaves a mix of files from each, which can
break ``import cv2``. ``python-doctr`` requires ``opencv-python`` by name, so
this library declares that same package and nothing else.

Decision record: ``docs/decisions/2026-11-14-opencv-python-not-contrib.md``.
"""

from __future__ import annotations

import importlib.metadata
import re
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


OPENCV_DISTRIBUTIONS = frozenset(
    {
        "opencv-python",
        "opencv-contrib-python",
        "opencv-python-headless",
        "opencv-contrib-python-headless",
    }
)

# Modules that exist only in the contrib builds. Using any of them would need
# opencv-contrib-python, which clashes with python-doctr's opencv-python.
CONTRIB_ONLY_MODULES = (
    "aruco",
    "bgsegm",
    "bioinspired",
    "ccalib",
    "face",
    "freetype",
    "img_hash",
    "line_descriptor",
    "optflow",
    "saliency",
    "structured_light",
    "superres",
    "text",
    "tracking",
    "xfeatures2d",
    "ximgproc",
    "xphoto",
)


def test_declares_only_opencv_python() -> None:
    """Declare ``opencv-python``, the same package python-doctr requires.

    Any other OpenCV distribution would install a second copy of ``cv2``
    next to the one python-doctr brings in.
    """
    declared = _dep_names(_project_dependencies()) & OPENCV_DISTRIBUTIONS
    assert declared == {"opencv-python"}, (
        f"pyproject.toml declares {sorted(declared)}; declare only "
        "'opencv-python', the package python-doctr requires. See "
        "docs/decisions/2026-11-14-opencv-python-not-contrib.md."
    )


def test_environment_has_one_opencv_distribution() -> None:
    """The resolved environment holds exactly one OpenCV distribution.

    Catches a dependency upgrade that brings a second ``cv2`` provider back,
    which no installer reports.
    """
    installed = {
        dist.metadata["Name"].lower()
        for dist in importlib.metadata.distributions()
        if dist.metadata["Name"]
    }
    assert installed & OPENCV_DISTRIBUTIONS == {"opencv-python"}


def test_source_uses_no_contrib_only_module() -> None:
    """Library code calls only modules that plain ``opencv-python`` ships."""
    pattern = re.compile(r"\bcv2\.(" + "|".join(CONTRIB_ONLY_MODULES) + r")\b")
    hits = [
        f"{path.relative_to(REPO_ROOT)}:{lineno}"
        for path in sorted((REPO_ROOT / "pdomain_book_tools").rglob("*.py"))
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if pattern.search(line)
    ]
    assert not hits, f"contrib-only cv2 modules used at: {hits}"


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
    """No code imports ``cv2.cuda``, so the ``[gpu]`` extra omits ``opencv-cuda``."""
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
