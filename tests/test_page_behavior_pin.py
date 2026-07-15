"""Behavior-pinning regression tests for ``Page``.

These tests pin the public-facing behavior of :class:`Page` after the
R-02 conversion to a pure-``@dataclass`` form and after Task 4 of the
page-split-plan which removed 11 operational metadata fields.

Observable surface area pinned:
- Constructor signature (positional + keyword args).
- Post-init attribute access for identity/blob/orphan fields.
- ``to_dict`` round-trip behavior on a representative fixture.
- Image-cache field access (``_cv2_numpy_page_image*``) before
  ``refresh_page_images()`` returns ``None``.
"""

from __future__ import annotations

import inspect

import pytest

from pdomain_book_tools.ocr.page import Page


def test_constructor_signature_pin():
    """Pin the parameter list of ``Page.__init__`` exactly.

    Task 4 (page-split-plan): 11 operational metadata fields removed.
    Constructor now contains only OCR content + identity + blob + orphan fields.
    The legacy aliases ``items`` and ``cv2_numpy_page_image`` are appended by
    the deprecation shim wrapper.
    """
    sig = inspect.signature(Page.__init__)
    params = list(sig.parameters.keys())
    assert params == [
        "self",
        "width",
        "height",
        "page_index",
        # Task 2 (page-split-plan): stable identity + blob refs added after page_index.
        "page_id",
        "image_blob_hash",
        "thumbnail_blob_hash",
        "gt_orphans",
        "blocks",
        "bounding_box",
        "page_labels",
        "name",
        "review",
        "items",
        "cv2_numpy_page_image",
    ]


def _make_minimal_page() -> Page:
    return Page(width=100, height=200, page_index=3, blocks=[])


def test_post_init_undeclared_attrs_default_values():
    """Pin default values for diagnostic attributes set in __post_init__."""
    p = _make_minimal_page()

    assert p.diagnostic_pure_ocr is None
    assert p.diagnostic_post_noise_removal is None
    assert p.diagnostic_noise_dropped_words == []
    assert p.diagnostic_noise_dropped_count == 0


def test_post_init_declared_field_defaults():
    """Pin the declared-field defaults the constructor leaves in place
    when not supplied by the caller.
    """
    p = _make_minimal_page()

    assert p.page_labels is None
    assert p.name is None
    assert p.review is None
    assert p._image_array is None
    assert p._cv2_numpy_page_image_page_with_bbox is None
    assert p._cv2_numpy_page_image_blocks_with_bboxes is None
    assert p._cv2_numpy_page_image_paragraph_with_bboxes is None
    assert p._cv2_numpy_page_image_line_with_bboxes is None
    assert p._cv2_numpy_page_image_word_with_bboxes is None
    assert p._cv2_numpy_page_image_word_with_bboxes_and_ocr_text is None
    assert p._cv2_numpy_page_image_word_with_bboxes_and_gt_text is None
    assert p._cv2_numpy_page_image_matched_word_with_colors is None
    assert p.bounding_box is None
    assert p.items == []


def test_compatibility_aliases():
    """Pin ``index`` ⇄ ``page_index``."""
    p = _make_minimal_page()
    assert p.index == p.page_index == 3
    p.index = 7
    assert p.page_index == 7


def test_to_dict_minimal_roundtrip_omits_defaults():
    """to_dict omits metadata fields at their defaults (compact output).

    Task 4 (page-split-plan): ocr_provenance, image_path, source,
    ocr_failed, provenance_* and rotation_applied no longer present.
    """
    p = _make_minimal_page()
    d = p.to_dict()

    # Always present
    assert d["type"] == "Page"
    assert d["width"] == 100
    assert d["height"] == 200
    assert d["page_index"] == 3
    assert d["items"] == []
    assert d["bounding_box"] is None

    # Removed fields must NOT appear in to_dict output
    for removed in (
        "ocr_provenance",
        "image_path",
        "source",
        "ocr_failed",
        "provenance_live_ocr",
        "provenance_saved_ocr",
        "provenance_saved",
        "rotation_applied",
        "original_ocr_tool_text",
        "original_ground_truth_text",
        "unmatched_ground_truth_lines",
    ):
        assert removed not in d, (
            f"{removed} should not appear in to_dict (removed in Task 4)"
        )

    # Optional fields omitted at default
    assert "name" not in d


def test_to_dict_with_name_roundtrip():
    """to_dict / from_dict preserves the name field."""
    p = Page(
        width=10,
        height=20,
        page_index=1,
        blocks=[],
        name="page-001",
    )
    d = p.to_dict()
    assert d["name"] == "page-001"

    p2 = Page.from_dict(d)
    assert p2.name == "page-001"
    assert p2.width == 10
    assert p2.height == 20
    assert p2.page_index == 1


# ---------------------------------------------------------------------------
# R-02 prep (2026-05-07): deprecation shim for renamed kwargs.
# ``items=`` and ``cv2_numpy_page_image=`` still work but emit
# DeprecationWarning. Both will be removed in v1.0.
# ---------------------------------------------------------------------------


def test_legacy_items_kwarg_still_works_but_warns():
    with pytest.warns(DeprecationWarning, match=r"Page\(items=\.\.\.\) is deprecated"):
        p = Page(
            width=10,
            height=20,
            page_index=0,
            items=[],  # pyright: ignore[reportCallIssue]  # legacy alias, added at runtime by Page's deprecation shim (Page.__init__ reassignment); not visible to static analysis
        )
    assert p.items == []


def test_legacy_cv2_numpy_page_image_kwarg_still_works_but_warns():
    import numpy as np

    arr = np.zeros((5, 5, 3), dtype=np.uint8)
    with pytest.warns(
        DeprecationWarning,
        match=r"Page\(cv2_numpy_page_image=\.\.\.\) is deprecated",
    ):
        p = Page(
            width=5,
            height=5,
            page_index=0,
            blocks=[],
            cv2_numpy_page_image=arr,  # pyright: ignore[reportCallIssue]  # legacy alias, added at runtime by Page's deprecation shim (Page.__init__ reassignment); not visible to static analysis
        )
    assert p.cv2_numpy_page_image is arr


def test_passing_both_old_and_new_kwarg_raises():
    with pytest.raises(TypeError, match="both 'blocks' and the deprecated alias"):
        Page(
            width=10,
            height=20,
            page_index=0,
            blocks=[],
            items=[],  # pyright: ignore[reportCallIssue]  # legacy alias, added at runtime by Page's deprecation shim (Page.__init__ reassignment); not visible to static analysis
        )
