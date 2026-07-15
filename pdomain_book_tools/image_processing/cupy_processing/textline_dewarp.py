"""CuPy mirror of cv2_processing/textline_dewarp.py — identical public API.

Uses cupyx.scipy.ndimage for morphology / labeling / resample. Detection returns
LineSamples whose arrays are cupy ndarrays; fit/build accept either backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

# Same Leptonica constants as the NumPy module (single source of truth: see plan table).
from pdomain_book_tools.image_processing.cv2_processing.textline_dewarp import (
    CSIZE1_DIV,
    CSIZE2_DIV,
    DEFAULT_SAMPLING,
    MIN_CSIZE1,
    MIN_CSIZE2,
    MIN_LINE_HEIGHT,
    MIN_LINE_WIDTH,
    SHORT_LINE_FRAC,
    TALL_RUN,
)
from pdomain_book_tools.image_processing.textline_types import LineSamples, QuadCoeffs

from ._cupy_compat import cp, require_cupy

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


def _foreground_binary(image: Any) -> Any:
    """Otsu binarize with text (dark) -> 255 foreground, for morphology (GPU path)."""
    require_cupy()
    gray = image if image.ndim == 2 else image[..., :3].mean(axis=2)
    gray = gray.astype(cp.float32)
    # Otsu on GPU histogram, INV polarity (text -> 255)
    hist = cp.histogram(gray, bins=256, range=(0, 255))[0].astype(cp.float64)
    total = gray.size
    w0 = cp.cumsum(hist)
    levels = cp.arange(256, dtype=cp.float64)
    mu = cp.cumsum(hist * levels)
    mu_t = mu[-1]
    w1 = total - w0
    between = (mu_t * w0 - mu) ** 2 / (w0 * w1 + 1e-9)
    thr = float(cp.argmax(between))
    return cp.where(gray <= thr, cp.uint8(255), cp.uint8(0))


def _ensure_foreground(binary: Any) -> Any:
    """Accept a grayscale image *or* a foreground-text binary; return text=255 (GPU)."""
    require_cupy()
    arr = cp.asarray(binary)
    if arr.dtype == cp.uint8 and bool(
        cp.isin(cp.unique(arr), cp.asarray([0, 255])).all()
    ):
        return arr
    return _foreground_binary(arr)


def _consolidate_lines(fg: Any, page_width: int) -> Any:
    """o1.3 + c{csize1}.1 + o{csize1}.1 + c{csize2}.1 (dewarp2.c:834-836, GPU path)."""
    import importlib

    _ndi = importlib.import_module("cupyx.scipy.ndimage")
    csize1 = max(MIN_CSIZE1, page_width // CSIZE1_DIV)
    csize2 = max(MIN_CSIZE2, page_width // CSIZE2_DIV)
    out = _ndi.grey_opening(fg, size=(3, 1))  # o1.3 (vertical)
    out = _ndi.grey_closing(out, size=(1, csize1))  # c{csize1}.1
    out = _ndi.grey_opening(out, size=(1, csize1))  # o{csize1}.1
    return _ndi.grey_closing(out, size=(1, csize2))  # c{csize2}.1


def _reconstruct(seed: Any, mask: Any) -> Any:
    """Morphological reconstruction by dilation of seed under mask (GPU path)."""
    import importlib

    _ndi = importlib.import_module("cupyx.scipy.ndimage")
    prev = seed
    while True:
        cur = cp.minimum(_ndi.grey_dilation(prev, size=(3, 3)), mask)
        if bool((cur == prev).all()):
            return cur
        prev = cur


def _remove_tall_components(fg: Any) -> Any:
    """e1.50 seed -> seedfill -> subtract to strip tall components (GPU path)."""
    import importlib

    _ndi = importlib.import_module("cupyx.scipy.ndimage")
    seed = _ndi.grey_erosion(fg, size=(TALL_RUN, 1))
    tall = _reconstruct(seed, fg)
    return cp.clip(fg.astype(cp.int16) - tall.astype(cp.int16), 0, 255).astype(cp.uint8)


def detect_textlines(
    binary: Any,
    *,
    page_width: int,
    binarization: str = "otsu",
    binarization_params: dict[str, Any] | None = None,
) -> list[LineSamples]:
    """Detect text lines as per-column vertical centroids (GPU path).

    ``binary`` may be a foreground-text (255) cupy array or a grayscale image.
    Returns one LineSamples per surviving line (cupy arrays), ordered top->bottom.

    Args:
        binary: Grayscale or already-binarized (text=255) CuPy array.
        page_width: Page width in pixels (used for morphology kernel sizing).
        binarization: Binarization method name. ``"otsu"`` (default) preserves
            the pre-existing code path exactly. Other methods route through the
            CuPy threshold module's ``binarize()`` and the result is inverted
            on-device to foreground=text=255 polarity.
        binarization_params: Optional keyword arguments forwarded to ``binarize()``.
    """
    require_cupy()
    import importlib

    _ndi = importlib.import_module("cupyx.scipy.ndimage")

    if binarization == "otsu":
        raw_fg = _ensure_foreground(binary)
    else:
        from pdomain_book_tools.image_processing.cupy_processing.threshold import (
            binarize as _binarize,
        )

        arr = cp.asarray(binary)
        gray = arr if arr.ndim == 2 else arr.mean(axis=2).astype(cp.uint8)
        params = binarization_params or {}
        # threshold module returns BACKGROUND=255, TEXT=0 → invert to foreground=TEXT=255
        bg_fg = _binarize(gray, method=binarization, **params)
        raw_fg = cp.where(bg_fg == 0, cp.uint8(255), cp.uint8(0))
    fg = _remove_tall_components(_consolidate_lines(raw_fg, page_width))
    labels, count = _ndi.label(fg > 0)
    lines: list[LineSamples] = []
    for lbl in range(1, int(count) + 1):
        ys, xs = cp.nonzero(labels == lbl)
        if xs.size == 0:
            continue
        if int(xs.max() - xs.min()) <= MIN_LINE_WIDTH:
            continue
        if int(ys.max() - ys.min()) <= MIN_LINE_HEIGHT:
            continue
        ux = cp.unique(xs)
        idx = cp.searchsorted(ux, xs)
        ux_size: int = ux.size
        sums = cp.zeros(ux_size, cp.float64)
        counts = cp.zeros(ux_size, cp.float64)
        cp.add.at(sums, idx, ys.astype(cp.float64))
        cp.add.at(counts, idx, 1.0)
        lines.append(LineSamples(xs=ux.astype(cp.float64), ys=sums / counts))
    lines.sort(key=lambda ln: float(ln.ys.mean()))
    return lines


def fit_baselines(lines: list[LineSamples]) -> list[QuadCoeffs]:
    """Order-2 least-squares fit per line (GPU: delegates to NumPy polyfit)."""
    coeffs: list[QuadCoeffs] = []
    for ln in lines:
        if cp is not None and isinstance(ln.xs, cp.ndarray):
            # isinstance against the unparameterized cupy.ndarray erases the
            # dtype to Unknown; the cast restores the dtype already declared
            # on LineSamples.xs.
            xs = cp.asnumpy(cast("npt.NDArray[np.float64]", ln.xs))
        else:
            xs = np.asarray(ln.xs)
        if cp is not None and isinstance(ln.ys, cp.ndarray):
            ys = cp.asnumpy(cast("npt.NDArray[np.float64]", ln.ys))
        else:
            ys = np.asarray(ln.ys)
        order = min(2, xs.size - 1)
        c = np.polyfit(xs.astype(np.float64), ys.astype(np.float64), order)
        c2, c1, c0 = (0.0, c[0], c[1]) if order == 1 else (c[0], c[1], c[2])
        coeffs.append(QuadCoeffs(c2=float(c2), c1=float(c1), c0=float(c0)))
    return coeffs


def remove_short_lines(
    lines: list[LineSamples], *, frac: float = SHORT_LINE_FRAC
) -> list[LineSamples]:
    """Drop lines shorter than ``frac`` x the longest (Leptonica dewarpRemoveShortLines)."""
    if not lines:
        return []
    longest = max(ln.width for ln in lines)
    return [ln for ln in lines if ln.width >= frac * longest]


def build_vertical_disparity(
    coeffs: list[QuadCoeffs], size: tuple[int, int], *, sampling: int = DEFAULT_SAMPLING
) -> Any:
    """Dense V(x,y): row offset that flattens each curved baseline (GPU path).

    Uses cp.polyfit/polyval when available; falls back to np.polyfit when BLAS
    libraries are not fully installed (e.g. partial CUDA install without CUBLAS).
    """
    require_cupy()
    h, w = size
    xs_full = cp.arange(w, dtype=cp.float64)
    fitted = cp.stack([c.eval(xs_full) for c in coeffs])
    refs = fitted.mean(axis=1)
    sample_x = cp.arange(0, w, sampling)
    rows_full = cp.arange(h, dtype=cp.float64)
    samp = cp.empty((h, sample_x.size), cp.float64)
    deg = min(2, len(coeffs) - 1)
    for j in range(int(sample_x.size)):
        x = int(sample_x[j])
        y_pts = fitted[:, x]
        d_pts = refs - fitted[:, x]
        order = cp.argsort(y_pts)
        try:
            cc = cp.polyfit(y_pts[order], d_pts[order], deg)
            samp[:, j] = cp.polyval(cc, rows_full)
        except (ImportError, RuntimeError):
            # Fall back to NumPy polyfit if BLAS libs unavailable
            y_np = cp.asnumpy(y_pts[order])
            d_np = cp.asnumpy(d_pts[order])
            cc_np = cast(
                "npt.NDArray[np.float64]",
                np.polyfit(y_np, d_np, deg),  # pyright: ignore[reportCallIssue, reportArgumentType]  # generic-dtype fallback array, see CuPy stub module docstring
            )
            samp[:, j] = cp.asarray(np.polyval(cc_np, cp.asnumpy(rows_full)))
    disparity = cp.empty((h, w), cp.float32)
    sx = sample_x.astype(cp.float64)
    cols = cp.arange(w, dtype=cp.float64)
    for r in range(h):
        disparity[r] = cp.interp(cols, sx, samp[r]).astype(cp.float32)
    return disparity


def build_horizontal_disparity(
    lines: list[LineSamples],
    coeffs: list[QuadCoeffs],
    size: tuple[int, int],
    *,
    gutter_edge: str,
    sampling: int = DEFAULT_SAMPLING,
) -> Any:
    """Dense H(x,y): column offset that straightens the reference margin (GPU path)."""
    require_cupy()
    h, w = size
    if gutter_edge == "left":
        ends = cp.asarray([ln.right for ln in lines])
        target = float(ends.max())
        anchor = "right"
    else:
        ends = cp.asarray([ln.left for ln in lines])
        target = float(ends.min())
        anchor = "left"
    shift = cast(
        "npt.NDArray[np.float64]",
        target - ends,  # pyright: ignore[reportOperatorIssue]  # CuPy arithmetic on generic-dtype array, see CuPy stub module docstring
    )
    ref_rows = cp.asarray(
        [
            float(c.eval((ln.left + ln.right) / 2.0))
            for c, ln in zip(coeffs, lines, strict=False)
        ]
    )
    order = cp.argsort(ref_rows)
    rows_full = cp.arange(h, dtype=cp.float64)
    margin_shift = cp.interp(rows_full, ref_rows[order], shift[order]).astype(
        cp.float32
    )
    xs_full = cp.arange(w, dtype=cp.float32)
    taper = (w - 1 - xs_full) / (w - 1) if anchor == "left" else xs_full / (w - 1)
    return (margin_shift[:, None] * taper[None, :]).astype(cp.float32)


def build_disparity_maps(
    lines: list[LineSamples],
    coeffs: list[QuadCoeffs],
    size: tuple[int, int],
    *,
    gutter_edge: str,
    sampling: int = DEFAULT_SAMPLING,
) -> tuple[Any, Any]:
    """Combined backward maps: map_x = x + H, map_y = y + V (GPU path)."""
    require_cupy()
    h, w = size
    vdisp = build_vertical_disparity(coeffs, size, sampling=sampling)
    hdisp = build_horizontal_disparity(
        lines, coeffs, size, gutter_edge=gutter_edge, sampling=sampling
    )
    mesh = cp.meshgrid(
        cp.arange(h, dtype=cp.float32), cp.arange(w, dtype=cp.float32), indexing="ij"
    )
    ys, xs = mesh[0], mesh[1]
    return (xs + hdisp).astype(cp.float32), (ys + vdisp).astype(cp.float32)


def apply_disparity(image: Any, map_x: Any, map_y: Any) -> Any:
    """Resample ``image`` through backward maps via cupyx map_coordinates (GPU path)."""
    require_cupy()
    import importlib

    _ndi = importlib.import_module("cupyx.scipy.ndimage")
    src = cp.asarray(image)
    coords = cp.stack([cp.asarray(map_y), cp.asarray(map_x)])
    return _ndi.map_coordinates(src, coords, order=3, mode="nearest")
