from __future__ import annotations

from typing import cast

import cv2
import numpy as np
import numpy.typing as npt
import pytest

from pdomain_book_tools.image_processing.cv2_processing import textline_dewarp as td
from pdomain_book_tools.image_processing.textline_types import LineSamples, QuadCoeffs

ImageArray = npt.NDArray[np.uint8]


def test_line_samples_holds_columns_and_centroids() -> None:
    ls = LineSamples(xs=np.array([0.0, 1.0, 2.0]), ys=np.array([10.0, 10.5, 11.0]))
    assert ls.xs.shape == (3,)
    assert ls.ys.shape == (3,)
    assert ls.left == 0.0
    assert ls.right == 2.0


def test_quad_coeffs_eval_matches_polyval() -> None:
    q = QuadCoeffs(c2=0.5, c1=-1.0, c0=3.0)
    assert q.eval(2.0) == 0.5 * 4 - 1.0 * 2 + 3.0
    np.testing.assert_allclose(q.eval(np.array([0.0, 1.0])), np.array([3.0, 2.5]))


def _lined_page(
    h: int = 900,
    w: int = 700,
    n_lines: int = 14,
    top: int = 90,
    gap: int = 55,
    text: int = 255,
) -> ImageArray:
    """Foreground-is-text (255) binary page with n straight horizontal text bars."""
    img = np.zeros((h, w), np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        # broken bar (word gaps) so morph consolidation is actually exercised
        for x0 in range(60, w - 60, 70):
            _ = cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), int(text), -1)
    return img


def test_detect_textlines_recovers_known_lines() -> None:
    page = _lined_page(n_lines=14, top=90, gap=55)
    lines = td.detect_textlines(page, page_width=page.shape[1])
    # recovers ~all lines (allow the morph filter to drop an edge line or two)
    assert 12 <= len(lines) <= 14
    centers = sorted(float(ln.ys.mean()) for ln in lines)
    # consecutive line centers are ~gap apart
    diffs = np.diff(centers)
    assert abs(np.median(diffs) - 55) < 8
    # each detected line spans most of the page width (full-length lines)
    assert all(ln.width > 0.5 * page.shape[1] for ln in lines)


def test_fit_baselines_recovers_quadratic() -> None:
    xs = np.arange(0, 600, dtype=np.float64)
    true = (0.0008, -0.3, 120.0)  # c2, c1, c0
    ys = true[0] * xs * xs + true[1] * xs + true[2]
    lines = [td.LineSamples(xs=xs, ys=ys)]
    coeffs = td.fit_baselines(lines)
    assert len(coeffs) == 1
    np.testing.assert_allclose(
        [coeffs[0].c2, coeffs[0].c1, coeffs[0].c0], true, rtol=1e-3, atol=1e-3
    )


def test_fit_baselines_skips_degenerate_short_line() -> None:
    coeffs = td.fit_baselines(
        [td.LineSamples(xs=np.array([1.0, 2.0]), ys=np.array([5.0, 6.0]))]
    )
    assert len(coeffs) == 1  # linear-only line still yields a (c2=0) fit
    assert abs(coeffs[0].c2) < 1e-9


def _curved_coeffs(
    n: int = 12,
    h: int = 900,
    w: int = 700,
    amp: float = 0.00010,
    top: int = 120,
    gap: int = 60,
) -> list[QuadCoeffs]:
    """n quadratic baselines sharing the same downward bow (c2=amp)."""
    coeffs: list[QuadCoeffs] = []
    for i in range(n):
        c0 = top + i * gap
        coeffs.append(QuadCoeffs(c2=amp, c1=-amp * (w - 1), c0=c0))  # min at x=w/2
    return coeffs


def test_vertical_disparity_flattens_curved_baselines() -> None:
    h, w = 900, 700
    coeffs = _curved_coeffs(h=h, w=w)
    disp = td.build_vertical_disparity(coeffs, (h, w))
    assert disp.shape == (h, w)
    # at each baseline, source row (y + disp) should be ~constant across x
    xs = np.arange(w)
    spreads: list[float] = []
    for c in coeffs:
        rows = np.clip(c.eval(xs).astype(int), 0, h - 1)
        src = rows + disp[rows, xs]
        spreads.append(float(np.max(src) - np.min(src)))
    # raw baseline sag for reference
    raw = float(np.max(coeffs[0].eval(xs)) - np.min(coeffs[0].eval(xs)))
    assert np.mean(spreads) < 0.25 * raw  # disparity removes >75% of the bow


def test_apply_disparity_identity_maps_is_noop() -> None:
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (60, 80), dtype=np.uint8)
    h, w = img.shape
    map_x, map_y = np.meshgrid(
        np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32)
    )
    out = td.apply_disparity(img, map_x, map_y)
    assert out.shape == img.shape
    assert (
        np.abs(out[2:-2, 2:-2].astype(int) - img[2:-2, 2:-2].astype(int)).mean() < 1.0
    )


def _stair_lines(
    n: int = 10,
    h: int = 900,
    w: int = 700,
    top: int = 120,
    gap: int = 70,
    side: str = "left",
    step: float = 4.0,
) -> list[LineSamples]:
    """Lines whose reference end drifts by `step` px per line (a ragged margin)."""
    lines: list[LineSamples] = []
    for i in range(n):
        y = top + i * gap
        if side == "left":
            x0, x1 = 60 + i * step, w - 60  # left edge drifts right per line
        else:
            x0, x1 = 60, w - 60 - i * step  # right edge drifts left per line
        xs = np.arange(int(x0), int(x1), dtype=np.float64)
        lines.append(td.LineSamples(xs=xs, ys=np.full(xs.size, float(y))))
    return lines


def test_remove_short_lines_culls_below_fraction() -> None:
    lines = _stair_lines(n=6)
    lines.append(
        td.LineSamples(xs=np.arange(60, 200, dtype=np.float64), ys=np.full(140, 800.0))
    )
    kept = td.remove_short_lines(lines, frac=0.8)
    assert len(kept) == 6  # the 140px stub is < 0.8 * longest


def test_horizontal_disparity_even_page_references_min_left() -> None:
    h, w = 900, 700
    lines = _stair_lines(side="left")
    coeffs = td.fit_baselines(lines)
    # even/verso page => gutter on the right => reference the LEFT ends, target = min
    disp = td.build_horizontal_disparity(lines, coeffs, (h, w), gutter_edge="right")
    assert disp.shape == (h, w)
    # the line with the largest left-end (most indented) gets the largest +shift
    target = min(ln.left for ln in lines)
    worst = max(lines, key=lambda ln: ln.left)
    row = int(np.clip(worst.ys.mean(), 0, h - 1))
    col = int(worst.left)
    # taper is not exactly 1.0 at worst.left (lines start at x=60, not x=0),
    # so allow generous tolerance; sign contract is tighter
    assert disp[row, col] == pytest.approx(target - worst.left, abs=8.0)
    assert disp[row, col] < -0.0  # negative: pull the indented left end back to min


def test_horizontal_disparity_odd_page_references_max_right() -> None:
    h, w = 900, 700
    lines = _stair_lines(side="right")
    coeffs = td.fit_baselines(lines)
    # odd/recto page => gutter on the left => reference the RIGHT ends, target = max
    disp = td.build_horizontal_disparity(lines, coeffs, (h, w), gutter_edge="left")
    target = max(ln.right for ln in lines)
    worst = min(lines, key=lambda ln: ln.right)
    row = int(np.clip(worst.ys.mean(), 0, h - 1))
    col = int(worst.right)
    # taper is not exactly 1.0 at worst.right (lines end before w-1),
    # so allow generous tolerance; sign contract is tighter
    assert disp[row, col] == pytest.approx(target - worst.right, abs=8.0)
    assert disp[row, col] > 0.0  # positive: push the short right end out to max


def _warp_page_vertically(flat: ImageArray, amp_px: float = 22.0) -> ImageArray:
    """Apply a known downward quadratic bow to a flat lined page (forward warp).

    Uses INTER_NEAREST to keep binary images binary (foreground=255 passes through
    _ensure_foreground unchanged for detect_textlines).
    """
    h, w = flat.shape
    xs = np.arange(w, dtype=np.float32)
    bow = (amp_px * (1.0 - ((xs - w / 2) / (w / 2)) ** 2)).astype(
        np.float32
    )  # 0 at edges, amp mid
    map_x = np.broadcast_to(xs[None, :], (h, w)).astype(np.float32).copy()
    map_y = (np.arange(h, dtype=np.float32)[:, None] - bow[None, :]).astype(np.float32)
    warped = cv2.remap(
        flat, map_x, map_y, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE
    )
    return cast("ImageArray", warped)


def _mean_abs_curvature(page: ImageArray, w: int) -> float:
    lines = td.detect_textlines(page, page_width=w)
    if not lines:
        return 0.0
    return float(np.mean([abs(c.c2) for c in td.fit_baselines(lines)]))


def test_round_trip_reduces_baseline_curvature() -> None:
    h, w = 1000, 760
    # Use INTER_NEAREST so warped stays binary (foreground=255); _ensure_foreground passes through
    flat = _lined_page(h=h, w=w, n_lines=14, top=90, gap=60)
    warped = _warp_page_vertically(flat, amp_px=22.0)
    curv_before = _mean_abs_curvature(warped, w)

    lines = td.remove_short_lines(td.detect_textlines(warped, page_width=w))
    coeffs = td.fit_baselines(lines)
    map_x, map_y = td.build_disparity_maps(lines, coeffs, (h, w), gutter_edge="none")
    dewarped = td.apply_disparity(warped, map_x, map_y)

    curv_after = _mean_abs_curvature(dewarped, w)
    assert curv_before > 0
    assert curv_after < 0.4 * curv_before  # most of the bow removed


def test_build_disparity_maps_shapes_and_identity_baseline() -> None:
    h, w = 400, 300
    # perfectly flat lines => maps ~ identity
    lines = [
        td.LineSamples(
            xs=np.arange(40, 260, dtype=np.float64), ys=np.full(220, float(y))
        )
        for y in range(80, 320, 40)
    ]
    coeffs = td.fit_baselines(lines)
    map_x, map_y = td.build_disparity_maps(lines, coeffs, (h, w), gutter_edge="none")
    assert map_x.shape == (h, w)
    assert map_y.shape == (h, w)
    ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    assert np.abs(map_x - xs).max() < 2.0
    assert np.abs(map_y - ys).max() < 2.0


# ---------------------------------------------------------------------------
# Binarization-parameter wiring tests
# ---------------------------------------------------------------------------


def test_detect_textlines_default_equals_explicit_otsu() -> None:
    """binarization="otsu" must produce byte-identical output to the default."""
    page = _lined_page(n_lines=14, top=90, gap=55)
    lines_default = td.detect_textlines(page, page_width=page.shape[1])
    lines_explicit = td.detect_textlines(
        page, page_width=page.shape[1], binarization="otsu"
    )
    assert len(lines_default) == len(lines_explicit)
    for ld, le in zip(lines_default, lines_explicit, strict=True):
        np.testing.assert_array_equal(ld.xs, le.xs)
        np.testing.assert_array_equal(ld.ys, le.ys)


def _gradient_page(
    h: int = 900, w: int = 700, n_lines: int = 14, top: int = 90, gap: int = 55
) -> ImageArray:
    """Dark-text-on-light-background page with a strong horizontal illumination gradient.

    The left half is near-white (240) and the right half fades to mid-grey (~120).
    Global Otsu will pick a threshold in the middle and miss lines on one side;
    Sauvola/Niblack local methods handle it well.
    """
    # Start with a light background that varies column-wise
    bg = np.linspace(240, 120, w, dtype=np.float32)
    img = np.tile(bg, (h, 1)).astype(np.uint8)
    # Draw dark text bars (value = 30)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            img[y : y + 10, x0 : x0 + 50] = 30
    return img


def test_detect_textlines_sauvola_handles_illumination_gradient() -> None:
    """Sauvola binarization should recover most lines under uneven illumination."""
    page = _gradient_page(n_lines=14, top=90, gap=55)
    lines = td.detect_textlines(page, page_width=page.shape[1], binarization="sauvola")
    # Sauvola's local stats handle the gradient; recover most of 14 lines
    assert 8 <= len(lines) <= 14


def test_detect_textlines_niblack_does_not_raise() -> None:
    """Niblack binarization should run without error (behavioral/wiring smoke test)."""
    page = _gradient_page(n_lines=14, top=90, gap=55)
    # Just verify no exception; line count depends on k/gradient interaction
    lines = td.detect_textlines(page, page_width=page.shape[1], binarization="niblack")
    assert isinstance(lines, list)


def test_detect_textlines_unknown_method_raises() -> None:
    page = _lined_page()
    with pytest.raises(ValueError, match="Unknown binarization method"):
        td.detect_textlines(page, page_width=page.shape[1], binarization="bogus")
