import logging

import cupy as cp
import numpy as np
from cupyx.scipy.ndimage import find_objects
from cupyx.scipy.ndimage import label as ndimage_label

logger = logging.getLogger(__name__)


def contour_size_stats_gpu(img_cp: cp.ndarray) -> dict:
    """
    Compute bounding-box size statistics for every connected component in the image.

    Returns a dict with:
        count     — number of components
        median_w  — median bounding-box width  (px)
        median_h  — median bounding-box height (px)
        mean_w    — mean bounding-box width    (px)
        mean_h    — mean bounding-box height   (px)
        p10_w     — 10th-percentile width      (px)
        p10_h     — 10th-percentile height     (px)

    Typical use: pass the result to remove_small_contours_adaptive_gpu, or
    inspect median_w / median_h to set explicit thresholds for
    remove_small_contours_gpu.

    For binarised book pages (text=255, background=0) the median will reflect
    the typical character bounding-box size, which is a stable reference point
    that is unaffected by page numbers, footnotes, or decorative rules — they
    all use characters of a similar or identical size to the body text.
    """
    labeled, n_labels = ndimage_label(img_cp > 0)
    if n_labels == 0:
        return {
            "count": 0,
            "median_w": 0,
            "median_h": 0,
            "mean_w": 0,
            "mean_h": 0,
            "p10_w": 0,
            "p10_h": 0,
        }

    objects = find_objects(labeled)
    widths = []
    heights = []
    for slices in objects:
        if slices is None:
            continue
        sy, sx = slices
        heights.append(sy.stop - sy.start)
        widths.append(sx.stop - sx.start)

    if not widths:
        return {
            "count": 0,
            "median_w": 0,
            "median_h": 0,
            "mean_w": 0,
            "mean_h": 0,
            "p10_w": 0,
            "p10_h": 0,
        }

    w_arr = np.array(widths, dtype=np.float32)
    h_arr = np.array(heights, dtype=np.float32)
    return {
        "count": len(widths),
        "median_w": float(np.median(w_arr)),
        "median_h": float(np.median(h_arr)),
        "mean_w": float(np.mean(w_arr)),
        "mean_h": float(np.mean(h_arr)),
        "p10_w": float(np.percentile(w_arr, 10)),
        "p10_h": float(np.percentile(h_arr, 10)),
    }


def remove_small_contours_gpu(
    img_cp: cp.ndarray,
    min_w_pct: float = 0.04,
    min_w_pixels: int = 5,
    min_h_pct: float = 0.03,
    min_h_pixels: int = 5,
    nearby_pixel_count: int = 10,
    search_w_pixels: int | None = None,
    search_h_pixels: int | None = None,
) -> cp.ndarray:
    """
    Remove small, isolated connected components from a grayscale image.

    A component is removed when both:
      - its bounding box is below the size threshold
        (width  < max(img_w * min_w_pct, min_w_pixels)  AND
         height < max(img_h * min_h_pct, min_h_pixels))
      - its neighbourhood contains fewer than nearby_pixel_count × 255 pixels.

    search_w_pixels / search_h_pixels: optional explicit search-area half-widths.
    When omitted the search area defaults to pixels_w × 0.75 / pixels_h × 0.5,
    which is appropriate when the threshold itself is large (non-adaptive use).
    Pass a larger value when the threshold is small (e.g. from the adaptive
    path) so that neighbour detection spans a full character width and avoids
    incorrectly removing TOC leader dots that are spaced wider than the threshold.

    For book-page pipelines where adaptive threshold selection is preferred,
    see remove_small_contours_adaptive_gpu.

    img_cp: 2-D uint8 CuPy array (non-zero pixels are foreground).
    Returns a copy with isolated small components zeroed out.
    """
    labeled, n_labels = ndimage_label(img_cp > 0)
    if n_labels == 0:
        return img_cp.copy()

    img_h, img_w = img_cp.shape[:2]
    pixels_w = max(int(img_w * min_w_pct), min_w_pixels)
    pixels_h = max(int(img_h * min_h_pct), min_h_pixels)
    threshold_sum = 255 * nearby_pixel_count

    # Search area half-extents: default scales with the threshold so that the
    # neighbourhood is proportional to the component size being evaluated.
    sw = search_w_pixels if search_w_pixels is not None else int(pixels_w * 0.75)
    sh = search_h_pixels if search_h_pixels is not None else int(pixels_h * 0.5)

    result = img_cp.copy()
    objects = find_objects(labeled)

    for i, slices in enumerate(objects):
        if slices is None:
            continue

        sy, sx = slices
        h_reg = sy.stop - sy.start
        w_reg = sx.stop - sx.start
        y, x = sy.start, sx.start

        if w_reg >= pixels_w or h_reg >= pixels_h:
            continue

        contour_sum = int(cp.sum(result[sy, sx]))
        if contour_sum == 0:
            continue

        minX = max(0, x - sw)
        maxX = min(img_w, x + w_reg + sw)
        minY = max(0, y - sh)
        maxY = min(img_h, y + h_reg + sh)

        search_sum = int(cp.sum(result[minY:maxY, minX:maxX])) - contour_sum
        if search_sum < threshold_sum:
            result[sy, sx] = 0

    return result


def remove_small_contours_adaptive_gpu(
    img_cp: cp.ndarray,
    size_fraction: float = 0.15,
    nearby_pixel_count: int = 10,
) -> cp.ndarray:
    """
    Remove small, isolated components using thresholds derived from the image itself.

    The removal threshold is set to size_fraction × median bounding-box size of
    all connected components.  Because page numbers and footnotes use characters
    of the same size as body text, the median is dominated by real content and
    the adaptive threshold will never rise high enough to threaten legitimate text.

    size_fraction=0.15 (default) means a component must be smaller than 15% of
    the median character width AND 15% of the median character height before it
    is even considered for removal — genuine text characters always survive.

    The search area used to decide whether a small component has neighbours is
    set to one full median character width (horizontally) and half the median
    character height (vertically).  This is intentionally larger than the
    removal threshold so that leader dots in a table of contents
    (e.g. "Chapter . . . . . 50") are recognised as having neighbours even
    though the inter-dot spacing exceeds the small removal threshold.

    img_cp: 2-D uint8 CuPy array (non-zero pixels are foreground).
    Returns a copy with isolated noise components zeroed out.
    """
    stats = contour_size_stats_gpu(img_cp)
    if stats["count"] == 0:
        return img_cp.copy()

    # Minimum of 2: a 1×1 pixel is always noise; real characters are ≥ 2px.
    pixels_w = max(2, int(stats["median_w"] * size_fraction))
    pixels_h = max(2, int(stats["median_h"] * size_fraction))

    # Search area: one character width / half character height so the neighbour
    # check spans the typical inter-dot gap in a TOC leader row.
    search_w = max(pixels_w, int(stats["median_w"]))
    search_h = max(pixels_h, int(stats["median_h"] * 0.5))

    logger.debug(
        f"remove_small_contours_adaptive_gpu: n={stats['count']}, "
        f"median=({stats['median_w']:.1f}w, {stats['median_h']:.1f}h), "
        f"threshold=({pixels_w}w, {pixels_h}h), "
        f"search_area=({search_w}w, {search_h}h)"
    )

    return remove_small_contours_gpu(
        img_cp,
        min_w_pct=0,
        min_w_pixels=pixels_w,
        min_h_pct=0,
        min_h_pixels=pixels_h,
        nearby_pixel_count=nearby_pixel_count,
        search_w_pixels=search_w,
        search_h_pixels=search_h,
    )


def np_uint8_remove_small_contours(img: np.ndarray, **kwargs) -> np.ndarray:
    """Transfers img to GPU, removes small/isolated contours, returns CPU uint8 array."""
    return cp.asnumpy(remove_small_contours_gpu(cp.asarray(img), **kwargs))


def np_uint8_remove_small_contours_adaptive(
    img: np.ndarray,
    size_fraction: float = 0.15,
    nearby_pixel_count: int = 10,
) -> np.ndarray:
    """Transfers img to GPU, removes noise adaptively, returns CPU uint8 array."""
    return cp.asnumpy(
        remove_small_contours_adaptive_gpu(
            cp.asarray(img),
            size_fraction=size_fraction,
            nearby_pixel_count=nearby_pixel_count,
        )
    )
