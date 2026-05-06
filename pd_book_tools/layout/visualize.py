"""Draw a debug overlay of layout regions on a source image.

Used by the fixture regenerator and the reorg-baseline test so the same
visualization shows up next to per-step reorg debug PNGs in
``tests/fixtures/layout_regression/debug/<case>/``.

Public API:

    draw_layout_overlay(png_path, layout, dest_path) -> None
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from pd_book_tools.layout.types import PageLayout

# Color per region type (BGR for cv2). Anything not listed falls back to gray.
# Chosen to be distinguishable on both light and dark scans.
_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "text": (200, 200, 60),  # cyan-ish
    "title": (30, 200, 255),  # gold
    "section": (50, 220, 255),  # gold-light
    "list": (200, 100, 200),  # pink
    "table": (255, 50, 50),  # blue
    "figure": (50, 200, 50),  # green
    "decoration": (50, 150, 0),  # dark green
    "caption": (50, 120, 255),  # orange
    "header": (180, 60, 200),  # magenta
    "footer": (180, 60, 200),
    "footnote": (140, 60, 200),
    "formula": (220, 220, 50),
    "abandoned": (128, 128, 128),  # gray
    "sidenote": (0, 200, 255),  # bright orange — geometric heuristic
}


def draw_layout_overlay(
    png_path: Union[str, Path],
    layout: PageLayout,
    dest_path: Union[str, Path],
) -> Optional[Path]:
    """Render ``layout``'s regions on ``png_path`` and save to ``dest_path``.

    The source image is dimmed so coloured rectangles + labels stand out.
    Returns the destination path on success, ``None`` if the source image
    could not be read (so callers can skip silently). Raises ``OSError`` if
    the destination write fails (cv2.imwrite returns False on disk-full /
    bad permissions / unsupported extension); the prior contract returned
    the path even on write failure, so a caller's ``is not None`` check
    misled them into believing the file was written (L-08).
    """
    import cv2  # imported lazily — visualization is optional

    png_path = Path(png_path)
    dest_path = Path(dest_path)

    img = cv2.imread(str(png_path), cv2.IMREAD_COLOR)
    if img is None:
        return None
    overlay = cv2.addWeighted(img, 0.55, 255 * (img * 0 + 1), 0.45, 0)

    for r in layout.regions:
        color = _COLORS_BGR.get(r.type.value, (128, 128, 128))
        cv2.rectangle(overlay, (r.L, r.T), (r.R, r.B), color, thickness=3)
        label = f"{r.type.value} {r.confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        ly0 = max(r.T - 6, th + 4)
        cv2.rectangle(
            overlay,
            (r.L, ly0 - th - 4),
            (r.L + tw + 6, ly0 + 2),
            color,
            thickness=-1,
        )
        cv2.putText(
            overlay,
            label,
            (r.L + 3, ly0 - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(dest_path), overlay):
        raise OSError(
            f"cv2.imwrite failed to write layout overlay to {dest_path!s} "
            "(disk full, bad permissions, or unsupported image extension)"
        )
    return dest_path


__all__ = ["draw_layout_overlay"]
