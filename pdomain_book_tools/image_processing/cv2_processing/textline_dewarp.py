"""NumPy / OpenCV textline-disparity dewarp (clean-room, Leptonica-faithful).

Pipeline: binarize -> morph-consolidate lines -> strip tall components ->
size-filter -> per-column vertical centroid (detect_textlines); order-2 baseline
fit (fit_baselines); dense vertical + horizontal disparity maps
(build_disparity_maps); cv2.remap resample (apply_disparity).

All sizes/SELs are verbatim from DanBloomberg/leptonica src/dewarp2.c — see the
plan's "Confirmed Leptonica constants" table.
"""

from __future__ import annotations

import cv2
import numpy as np

from pdomain_book_tools.image_processing.textline_types import LineSamples, QuadCoeffs

# --- Leptonica dewarp2.c constants (confirmed verbatim against master) ---------
MIN_CSIZE1 = 15  # csize1 = max(15, w/80)  (dewarp2.c:832)
MIN_CSIZE2 = 40  # csize2 = max(40, w/30)  (dewarp2.c:833)
CSIZE1_DIV = 80
CSIZE2_DIV = 30
TALL_RUN = 50  # e1.50 vertical-run seed  (dewarp2.c:840)
MIN_LINE_WIDTH = 100  # pixaSelectBySize width > 100  (dewarp2.c:864)
MIN_LINE_HEIGHT = 4  # pixaSelectBySize height > 4   (dewarp2.c:864)
DEFAULT_SAMPLING = 30  # Leptonica DefaultArraySampling (dewarp1.c:424)
SHORT_LINE_FRAC = 0.8  # dewarpRemoveShortLines fraction (dewarp2.c:197)


def _foreground_binary(image: np.ndarray) -> np.ndarray:
    """Otsu binarize with text (dark) -> 255 foreground, for morphology."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, fg = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return np.asarray(fg, dtype=np.uint8)


def _ensure_foreground(binary: np.ndarray) -> np.ndarray:
    """Accept a grayscale image *or* a foreground-text binary; return text=255."""
    if binary.dtype == np.uint8 and set(np.unique(binary)).issubset({0, 255}):
        return binary
    return _foreground_binary(binary)


def _consolidate_lines(fg: np.ndarray, page_width: int) -> np.ndarray:
    """o1.3 + c{csize1}.1 + o{csize1}.1 + c{csize2}.1  (dewarp2.c:834-836)."""
    csize1 = max(MIN_CSIZE1, page_width // CSIZE1_DIV)
    csize2 = max(MIN_CSIZE2, page_width // CSIZE2_DIV)
    out = cv2.morphologyEx(
        fg, cv2.MORPH_OPEN, np.ones((3, 1), np.uint8)
    )  # o1.3 (vertical)
    out = cv2.morphologyEx(
        out, cv2.MORPH_CLOSE, np.ones((1, csize1), np.uint8)
    )  # c{csize1}.1
    out = cv2.morphologyEx(
        out, cv2.MORPH_OPEN, np.ones((1, csize1), np.uint8)
    )  # o{csize1}.1
    return cv2.morphologyEx(
        out, cv2.MORPH_CLOSE, np.ones((1, csize2), np.uint8)
    )  # c{csize2}.1


def _reconstruct(seed: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Morphological reconstruction by dilation of seed under mask (to convergence)."""
    kernel = np.ones((3, 3), np.uint8)
    prev = seed
    while True:
        cur = cv2.bitwise_and(cv2.dilate(prev, kernel), mask)
        if np.array_equal(cur, prev):
            return np.asarray(cur, dtype=np.uint8)
        prev = cur


def _remove_tall_components(fg: np.ndarray) -> np.ndarray:
    """e1.50 seed -> seedfill -> XOR to strip figures/drop-caps (dewarp2.c:838-844)."""
    seed = cv2.erode(fg, np.ones((TALL_RUN, 1), np.uint8))  # keep >=50px vertical runs
    tall = _reconstruct(np.asarray(seed, dtype=np.uint8), fg)
    return np.asarray(cv2.subtract(fg, tall), dtype=np.uint8)


def detect_textlines(binary: np.ndarray, *, page_width: int) -> list[LineSamples]:
    """Detect text lines as per-column vertical centroids.

    ``binary`` may be a foreground-text (255) binary or a grayscale image (binarized
    internally). Returns one LineSamples per surviving line, ordered top->bottom.
    """
    fg = _ensure_foreground(binary)
    consolidated = _remove_tall_components(_consolidate_lines(fg, page_width))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        consolidated, connectivity=8
    )
    lines: list[LineSamples] = []
    for lbl in range(1, count):
        if stats[lbl, cv2.CC_STAT_WIDTH] <= MIN_LINE_WIDTH:
            continue
        if stats[lbl, cv2.CC_STAT_HEIGHT] <= MIN_LINE_HEIGHT:
            continue
        ys, xs = np.nonzero(labels == lbl)
        ux = np.unique(xs)
        # weighted vertical centroid per column
        sums = np.zeros(ux.size, np.float64)
        counts = np.zeros(ux.size, np.float64)
        idx = np.searchsorted(ux, xs)
        np.add.at(sums, idx, ys)
        np.add.at(counts, idx, 1.0)
        cy = sums / counts
        lines.append(LineSamples(xs=ux.astype(np.float64), ys=cy))
    lines.sort(key=lambda ln: float(ln.ys.mean()))
    return lines


def fit_baselines(lines: list[LineSamples]) -> list[QuadCoeffs]:
    """Order-2 least-squares fit per line (Leptonica ptaGetQuadraticLSF, order 2)."""
    coeffs: list[QuadCoeffs] = []
    for ln in lines:
        order = min(2, ln.xs.size - 1)  # avoid rank warnings on 2-pt lines
        c = np.polyfit(
            np.asarray(ln.xs, np.float64), np.asarray(ln.ys, np.float64), order
        )
        c2, c1, c0 = (0.0, c[0], c[1]) if order == 1 else (c[0], c[1], c[2])
        coeffs.append(QuadCoeffs(c2=float(c2), c1=float(c1), c0=float(c0)))
    return coeffs


def build_vertical_disparity(
    coeffs: list[QuadCoeffs], size: tuple[int, int], *, sampling: int = DEFAULT_SAMPLING
) -> np.ndarray:
    """Dense V(x,y): row offset that flattens each curved baseline to its mean row.

    Per Leptonica: at each sampled column, each detected baseline contributes an
    (actual_row, offset) pair where offset = refs[i] - actual_row brings the curved
    text to its mean reference row. A polynomial is fit over (actual_row, offset)
    across all lines; the dense map is evaluated at every row and interpolated across
    x. The resulting disparity is used as a backward-map offset: ``map_y = y + disp``
    maps each output row to the corresponding source row. Returns float32 (h, w).
    """
    h, w = size
    xs_full = np.arange(w, dtype=np.float64)
    fitted = np.stack([c.eval(xs_full) for c in coeffs])  # (L, w) actual baseline rows
    refs = fitted.mean(axis=1)  # (L,) flat target row per line
    sample_x = np.arange(0, w, sampling)
    rows_full = np.arange(h, dtype=np.float64)
    samp = np.empty((h, sample_x.size), np.float64)
    for j, x in enumerate(sample_x):
        y_pts = fitted[:, x]
        d_pts = refs - fitted[:, x]  # signed offset: pull bow toward its mean row
        order = np.argsort(y_pts)
        deg = min(2, len(coeffs) - 1)
        cc = np.polyfit(y_pts[order], d_pts[order], deg)
        samp[:, j] = np.polyval(cc, rows_full)
    disparity = np.empty((h, w), np.float32)
    for r in range(h):
        disparity[r] = np.interp(np.arange(w), sample_x, samp[r]).astype(np.float32)
    return disparity


def apply_disparity(
    image: np.ndarray, map_x: np.ndarray, map_y: np.ndarray
) -> np.ndarray:
    """Resample ``image`` through backward maps via cv2.remap (cubic, replicate border)."""
    return cv2.remap(  # type: ignore[return-value]
        image,
        np.asarray(map_x, np.float32),
        np.asarray(map_y, np.float32),
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def remove_short_lines(
    lines: list[LineSamples], *, frac: float = SHORT_LINE_FRAC
) -> list[LineSamples]:
    """Drop lines shorter than ``frac`` x the longest (Leptonica dewarpRemoveShortLines)."""
    if not lines:
        return []
    longest = max(ln.width for ln in lines)
    return [ln for ln in lines if ln.width >= frac * longest]


def build_horizontal_disparity(
    lines: list[LineSamples],
    coeffs: list[QuadCoeffs],
    size: tuple[int, int],
    *,
    gutter_edge: str,
    sampling: int = DEFAULT_SAMPLING,
) -> np.ndarray:
    """Dense H(x,y): column offset that straightens the reference margin.

    Even/verso pages (gutter on the right) reference the LEFT line-ends against their
    minimum; odd/recto pages (gutter on the left) reference the RIGHT line-ends
    against their maximum (spec step 5). The per-line margin shift is interpolated
    vertically across baseline rows and tapered linearly to 0 at the opposite margin.
    Returns float32 (h, w).
    """
    h, w = size
    if gutter_edge == "left":  # odd/recto: right margin is reference
        ends = np.array([ln.right for ln in lines])
        target = float(ends.max())
        anchor = "right"
    else:  # even/verso (or "none"): left margin
        ends = np.array([ln.left for ln in lines])
        target = float(ends.min())
        anchor = "left"
    shift = target - ends  # signed column shift per line at its margin
    ref_rows = np.array(
        [
            float(c.eval((ln.left + ln.right) / 2.0))
            for c, ln in zip(coeffs, lines, strict=False)
        ]
    )
    order = np.argsort(ref_rows)
    rows_full = np.arange(h)
    margin_shift = np.interp(rows_full, ref_rows[order], shift[order]).astype(
        np.float32
    )
    xs_full = np.arange(w, dtype=np.float32)
    taper = (
        (w - 1 - xs_full) / (w - 1) if anchor == "left" else xs_full / (w - 1)
    )  # 1 at ref margin, 0 at opposite
    return (margin_shift[:, None] * taper[None, :]).astype(np.float32)


def build_disparity_maps(
    lines: list[LineSamples],
    coeffs: list[QuadCoeffs],
    size: tuple[int, int],
    *,
    gutter_edge: str,
    sampling: int = DEFAULT_SAMPLING,
) -> tuple[np.ndarray, np.ndarray]:
    """Combined backward maps: map_x = x + H, map_y = y + V (spec step 6).

    ``lines`` supplies the line-end positions for horizontal disparity (the spec's
    ``line_ends``); ``coeffs`` are their order-2 baselines.
    """
    h, w = size
    vdisp = build_vertical_disparity(coeffs, size, sampling=sampling)
    hdisp = build_horizontal_disparity(
        lines, coeffs, size, gutter_edge=gutter_edge, sampling=sampling
    )
    ys, xs = np.meshgrid(
        np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij"
    )
    map_x = (xs + hdisp).astype(np.float32)
    map_y = (ys + vdisp).astype(np.float32)
    return map_x, map_y


__all__ = [
    "LineSamples",
    "QuadCoeffs",
    "apply_disparity",
    "build_disparity_maps",
    "build_horizontal_disparity",
    "build_vertical_disparity",
    "detect_textlines",
    "fit_baselines",
    "remove_short_lines",
]
