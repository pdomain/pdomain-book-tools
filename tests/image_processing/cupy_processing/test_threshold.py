"""Tests for cupy_processing.threshold module."""

import numpy as np
import pytest


@pytest.fixture
def cupy_threshold(cupy_module):
    from pdomain_book_tools.image_processing.cupy_processing import (
        threshold as thresh_mod,
    )

    return thresh_mod, cupy_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gradient_with_text_np() -> np.ndarray:
    """100x100 uint8 image: smooth horizontal gradient + dark text patches.

    Same fixture as the cv2 tests — used to build GPU parity inputs.
    """
    h, w = 100, 100
    gradient = np.tile(np.linspace(80, 220, w, dtype=np.float32), (h, 1)).astype(
        np.uint8
    )
    for r, col in [(10, 10), (30, 60), (60, 15), (75, 70)]:
        gradient[r : r + 10, col : col + 10] = 10
    return gradient


# ---------------------------------------------------------------------------
# otsu_binary_thresh (pre-existing tests, preserved)
# ---------------------------------------------------------------------------


class TestOtsuBinaryThresh:
    def test_bimodal_image(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((20, 20), dtype=cp.float32)
        img[:10, :] = 0.1
        img[10:, :] = 0.9
        out = thresh_mod.otsu_binary_thresh(img)
        # Output is binary uint8 (0 or 255), matching cv2 backend contract (H-16).
        assert out.dtype == cp.uint8
        assert tuple(out.shape) == (20, 20)
        # Values should be split 0/255
        flattened = out.get().ravel()
        assert set(np.unique(flattened).tolist()).issubset({0, 255})

    def test_color_image_handled(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((10, 10, 3), dtype=cp.float32)
        img[:, :, 0] = 0.1
        img[:, :, 1] = 0.5
        img[:, :, 2] = 0.9
        out = thresh_mod.otsu_binary_thresh(img)
        assert out.ndim == 2
        assert tuple(out.shape) == (10, 10)

    def test_uniform_image_does_not_crash_or_misclassify(self, cupy_threshold):
        """Regression test for H-15: uniform-valued images must not crash and
        must produce a sensible binary output.

        Originally `cp.histogram(img, bins=256, range=(min,max))` with
        `min == max` was reported to raise `ValueError: max must be larger than
        min`. In current cupy (14.x) the histogram call no longer raises but
        the downstream threshold becomes meaningless: with all pixels at the
        same value, the histogram has a single nonzero bin at index 128 over
        an arbitrary [-0.5, 0.5]-style edge span, the between-class variance
        is identically zero, and `argmax` falls back to index 0 — yielding a
        threshold like `-0.498` and a misclassified all-1.0 mask for an
        all-zero input.
        Reference contract (skimage / cv2): a uniform image's Otsu threshold
        is just the uniform value, and the binary output (using strict `>`)
        is all-zeros.
        """
        thresh_mod, cp = cupy_threshold
        for value in (0.0, 0.5, 1.0, 0.128):
            img = cp.full((10, 10), value, dtype=cp.float32)
            out = thresh_mod.otsu_binary_thresh(img)
            assert out.dtype == cp.uint8  # H-16: match cv2 backend contract
            assert tuple(out.shape) == (10, 10)
            unique = set(np.unique(out.get()).tolist())
            assert unique.issubset({0, 255}), (
                f"value={value}: expected binary output, got {unique}"
            )
            # Strict `>` against a threshold of `value` produces all-zeros for
            # a uniform image — matches skimage/cv2 semantics.
            assert unique == {0}, (
                f"value={value}: uniform image should be classified entirely "
                f"as 0 (since no pixel exceeds the uniform value), got {unique}"
            )

    def test_returns_uint8_0_255_matching_cv2_contract(self, cupy_threshold):
        """Regression test for H-16: cupy `otsu_binary_thresh` must return a
        uint8 array with values in {0, 255}, matching the cv2 backend's
        contract (`cv2.threshold(..., THRESH_BINARY+THRESH_OTSU)` returns
        uint8 0/255).

        The original cupy version returned float32 0.0/1.0, so pipeline code
        that switched backends silently received a different dtype and value
        range, breaking downstream consumers (e.g. `invert_image`) that assume
        uint8 0/255.
        """
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((20, 20), dtype=cp.float32)
        img[:10, :] = 0.1
        img[10:, :] = 0.9
        out = thresh_mod.otsu_binary_thresh(img)
        assert out.dtype == cp.uint8, (
            f"H-16: expected uint8 to match cv2 backend, got {out.dtype}"
        )
        unique = set(np.unique(out.get()).tolist())
        assert unique.issubset({0, 255}), (
            f"H-16: expected values in {{0, 255}} to match cv2 backend, got {unique}"
        )
        # Both classes must be represented for this bimodal input.
        assert unique == {0, 255}

    def test_uniform_image_returns_uint8(self, cupy_threshold):
        """H-16 + H-15 combined: the uniform-image early-return must also
        emit uint8, not float32, so callers see a single consistent dtype."""
        thresh_mod, cp = cupy_threshold
        img = cp.full((10, 10), 0.5, dtype=cp.float32)
        out = thresh_mod.otsu_binary_thresh(img)
        assert out.dtype == cp.uint8

    def test_threshold_matches_skimage_reference(self, cupy_threshold):
        """Regression test for H-14: cupy Otsu must match the standard
        between-class-variance formulation (matching skimage.filters.threshold_otsu).

        The original implementation used `weight2 = cumsum(hist)[-1] - cumsum(hist)`,
        which left bin index `k+1` excluded from both classes when paired with
        `weight2[1:]` / `mean2[1:]` in the variance expression. On non-trivial
        bimodal images this biased the threshold high, away from skimage's
        reference. The corrected version uses
        `weight2 = cp.flip(cp.cumsum(cp.flip(hist)))` so `weight2[1:]` aligns
        with the standard formulation.
        """
        thresh_mod, cp = cupy_threshold
        skimage_filters = pytest.importorskip("skimage.filters")
        threshold_otsu = skimage_filters.threshold_otsu

        # Non-trivial bimodal: two overlapping Gaussian-ish clusters so the
        # histogram has nonzero density in the valley region. Without that the
        # off-by-one is silently in a zero-count bin.
        rng = np.random.default_rng(42)
        cluster_a = rng.normal(60, 15, 1000).clip(0, 255).astype(np.uint8)
        cluster_b = rng.normal(190, 20, 1000).clip(0, 255).astype(np.uint8)
        img_np = np.concatenate([cluster_a, cluster_b]).reshape(40, 50)
        img_float = img_np.astype(np.float32) / 255.0

        # Reference threshold from the same histogram skimage would build for
        # this image (use hist= form so we compare the algorithm, not binning).
        hist_np, bin_edges = np.histogram(
            img_float, bins=256, range=(float(img_float.min()), float(img_float.max()))
        )
        bin_centers_np = (bin_edges[:-1] + bin_edges[1:]) / 2
        expected = threshold_otsu(hist=(hist_np, bin_centers_np))

        # Derive the cupy implementation's threshold by inspecting which side
        # of the binary output flips. We pick the largest input value that the
        # function maps to 0 — that is the inferred threshold (since it uses
        # strict `>`).
        img_cp = cp.asarray(img_float)
        out = thresh_mod.otsu_binary_thresh(img_cp)
        out_np = out.get() if hasattr(out, "get") else np.asarray(out)
        below = img_float[out_np == 0.0]
        assert below.size > 0, "Otsu produced an all-foreground mask"
        inferred = float(below.max())

        # Allow one bin-width of tolerance (256 bins over [min,max]).
        bin_width = float((img_float.max() - img_float.min()) / 256)
        assert abs(inferred - float(expected)) <= bin_width, (
            f"Cupy Otsu threshold {inferred} diverges from skimage reference "
            f"{expected} by more than one bin ({bin_width}) — H-14 regression"
        )


# ---------------------------------------------------------------------------
# binary_thresh_gpu (pre-existing tests, preserved)
# ---------------------------------------------------------------------------


class TestBinaryThreshGpu:
    def test_pixels_above_level_become_255(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        # level=127: pixels strictly > 127 become 255; 127 itself stays 0
        img = cp.array([[0, 100, 127, 128, 255]], dtype=cp.uint8)
        out = thresh_mod.binary_thresh_gpu(img, level=127)
        expected = cp.array([[0, 0, 0, 255, 255]], dtype=cp.uint8)
        assert cp.array_equal(out, expected)

    def test_output_dtype_is_uint8(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((10, 10), dtype=cp.uint8)
        out = thresh_mod.binary_thresh_gpu(img)
        assert out.dtype == cp.uint8

    def test_matches_cv2_reference(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        pytest.importorskip("cv2")
        import cv2
        import numpy as np

        rng = np.random.default_rng(99)
        img_np = rng.integers(0, 256, (50, 50), dtype=np.uint8)
        _, cpu = cv2.threshold(img_np, 127, 255, cv2.THRESH_BINARY)
        gpu = cp.asnumpy(thresh_mod.binary_thresh_gpu(cp.asarray(img_np), level=127))
        np.testing.assert_array_equal(cpu, gpu)


# ---------------------------------------------------------------------------
# np_uint8_* wrappers (pre-existing tests, preserved)
# ---------------------------------------------------------------------------


class TestNpUint8BinaryThresh:
    def test_returns_uint8_numpy(self, cupy_threshold):
        thresh_mod, _ = cupy_threshold
        import numpy as np

        img = np.array([[0, 100, 200]], dtype=np.uint8)
        out = thresh_mod.np_uint8_binary_thresh(img, level=127)
        assert isinstance(out, np.ndarray)
        assert out.dtype == np.uint8
        assert out[0, 0] == 0
        assert out[0, 2] == 255


class TestNpUint8FloatBinaryThresh:
    def test_returns_uint8(self, cupy_threshold):
        thresh_mod, _ = cupy_threshold
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        # The legacy ``_float_`` name is deprecated (R-30) — invoking it
        # still works but emits a DeprecationWarning. Suppress here so
        # this test stays focused on the output contract.
        import warnings as _w

        with _w.catch_warnings():
            _w.simplefilter("ignore", DeprecationWarning)
            out = thresh_mod.np_uint8_float_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        # Values should be either 0 or 255
        assert set(np.unique(out).tolist()).issubset({0, 255})


class TestNpUint8OtsuBinaryThresh:
    """R-30: canonical replacement for np_uint8_float_binary_thresh."""

    def test_canonical_name_returns_uint8(self, cupy_threshold):
        thresh_mod, _ = cupy_threshold
        img = np.zeros((20, 20), dtype=np.uint8)
        img[:10, :] = 30
        img[10:, :] = 220
        out = thresh_mod.np_uint8_otsu_binary_thresh(img)
        assert out.dtype == np.uint8
        assert out.shape == img.shape
        assert set(np.unique(out).tolist()).issubset({0, 255})

    def test_alias_emits_deprecation_warning(self, cupy_threshold):
        import pytest

        thresh_mod, _ = cupy_threshold
        img = np.zeros((20, 20), dtype=np.uint8)
        img[10:, :] = 220
        with pytest.warns(DeprecationWarning, match="np_uint8_otsu_binary_thresh"):
            out = thresh_mod.np_uint8_float_binary_thresh(img)
        # Same behavior as canonical name.
        canonical = thresh_mod.np_uint8_otsu_binary_thresh(img)
        np.testing.assert_array_equal(out, canonical)


# ---------------------------------------------------------------------------
# adaptive_binary_thresh (GPU) — new
# ---------------------------------------------------------------------------


@pytest.mark.gpu
class TestAdaptiveBinaryThreshGpu:
    def test_output_is_cupy_uint8_binary(self, cupy_threshold):
        """GPU adaptive returns a cp.ndarray of dtype uint8 with values in {0,255}."""
        thresh_mod, cp = cupy_threshold
        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)
        out = thresh_mod.adaptive_binary_thresh(img_cp)
        # Type stays on-device
        assert type(out).__module__.startswith("cupy"), (
            f"Expected cupy array, got {type(out)}"
        )
        assert out.dtype == cp.uint8
        assert tuple(out.shape) == img_np.shape
        assert set(np.unique(out.get()).tolist()).issubset({0, 255})

    def test_input_and_output_remain_on_device(self, cupy_threshold):
        """Proves no host transfer: input is cp.ndarray, output is cp.ndarray."""
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.adaptive_binary_thresh(img_cp)
        assert hasattr(out, "device"), "Output must be a CuPy device array"
        # If it were a NumPy array it would not have a .device attribute

    def test_parity_with_cv2_mean_mode(self, cupy_threshold):
        """GPU mean-mode result must be close to cv2 mean-mode result.

        We allow up to 2% of pixels to differ (border and rounding effects).
        """
        thresh_mod, cp = cupy_threshold
        pytest.importorskip("cv2")
        from pdomain_book_tools.image_processing.cv2_processing.threshold import (
            adaptive_binary_thresh as cpu_adaptive,
        )

        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)

        cpu_out = cpu_adaptive(img_np, block_size=31, c=10, mode="mean")
        gpu_out = thresh_mod.adaptive_binary_thresh(
            img_cp, block_size=31, c=10, mode="mean"
        )
        gpu_out_np = gpu_out.get()

        diff = np.sum(cpu_out != gpu_out_np)
        total = cpu_out.size
        assert diff / total < 0.02, (
            f"GPU/CPU mean-mode adaptive mismatch: {diff}/{total} pixels differ"
        )

    def test_mode_gaussian_produces_binary(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.adaptive_binary_thresh(img_cp, mode="gaussian")
        assert out.dtype == cp.uint8
        assert set(np.unique(out.get()).tolist()).issubset({0, 255})

    def test_unknown_mode_raises(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.zeros((10, 10), dtype=cp.uint8)
        with pytest.raises(ValueError, match="Unknown adaptive mode"):
            thresh_mod.adaptive_binary_thresh(img_cp, mode="bogus")


# ---------------------------------------------------------------------------
# sauvola_binary_thresh (GPU) — new
# ---------------------------------------------------------------------------


@pytest.mark.gpu
class TestSauvolaBinaryThreshGpu:
    def test_output_is_cupy_uint8_binary(self, cupy_threshold):
        """GPU Sauvola returns a cp.ndarray of dtype uint8 with values in {0,255}."""
        thresh_mod, cp = cupy_threshold
        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)
        out = thresh_mod.sauvola_binary_thresh(img_cp)
        assert type(out).__module__.startswith("cupy"), (
            f"Expected cupy array, got {type(out)}"
        )
        assert out.dtype == cp.uint8
        assert tuple(out.shape) == img_np.shape
        assert set(np.unique(out.get()).tolist()).issubset({0, 255})

    def test_input_and_output_remain_on_device(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.sauvola_binary_thresh(img_cp)
        assert hasattr(out, "device"), "Output must be a CuPy device array"

    def test_parity_with_cv2_result(self, cupy_threshold):
        """GPU Sauvola result must be very close to the cpu Sauvola result.

        Allow up to 2% pixel difference (border/rounding from uniform_filter
        vs cv2.boxFilter boundary handling).
        """
        thresh_mod, cp = cupy_threshold
        from pdomain_book_tools.image_processing.cv2_processing.threshold import (
            sauvola_binary_thresh as cpu_sauvola,
        )

        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)

        cpu_out = cpu_sauvola(img_np, window_size=25, k=0.2, r=128)
        gpu_out = thresh_mod.sauvola_binary_thresh(img_cp, window_size=25, k=0.2, r=128)
        gpu_out_np = gpu_out.get()

        diff = np.sum(cpu_out != gpu_out_np)
        total = cpu_out.size
        assert diff / total < 0.02, (
            f"GPU/CPU Sauvola mismatch: {diff}/{total} pixels differ"
        )

    def test_recovers_dark_text_patches(self, cupy_threshold):
        """Dark text patches should be classified as 0 (text)."""
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.sauvola_binary_thresh(img_cp)
        out_np = out.get()
        for r, col in [(15, 15), (35, 65), (65, 20), (80, 75)]:
            assert out_np[r, col] == 0, (
                f"GPU Sauvola: expected 0 at ({r},{col}), got {out_np[r, col]}"
            )


# ---------------------------------------------------------------------------
# niblack_binary_thresh (GPU) — new
# ---------------------------------------------------------------------------


@pytest.mark.gpu
class TestNiblackBinaryThreshGpu:
    def test_output_is_cupy_uint8_binary(self, cupy_threshold):
        """GPU Niblack returns a cp.ndarray of dtype uint8 with values in {0,255}."""
        thresh_mod, cp = cupy_threshold
        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)
        out = thresh_mod.niblack_binary_thresh(img_cp)
        assert type(out).__module__.startswith("cupy"), (
            f"Expected cupy array, got {type(out)}"
        )
        assert out.dtype == cp.uint8
        assert tuple(out.shape) == img_np.shape
        assert set(np.unique(out.get()).tolist()).issubset({0, 255})

    def test_input_and_output_remain_on_device(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.niblack_binary_thresh(img_cp)
        assert hasattr(out, "device"), "Output must be a CuPy device array"

    def test_parity_with_cv2_result(self, cupy_threshold):
        """GPU Niblack result must be very close to the cpu Niblack result.

        Allow up to 2% pixel difference (border/rounding).
        """
        thresh_mod, cp = cupy_threshold
        from pdomain_book_tools.image_processing.cv2_processing.threshold import (
            niblack_binary_thresh as cpu_niblack,
        )

        img_np = _gradient_with_text_np()
        img_cp = cp.asarray(img_np)

        cpu_out = cpu_niblack(img_np, window_size=25, k=-0.2)
        gpu_out = thresh_mod.niblack_binary_thresh(img_cp, window_size=25, k=-0.2)
        gpu_out_np = gpu_out.get()

        diff = np.sum(cpu_out != gpu_out_np)
        total = cpu_out.size
        assert diff / total < 0.02, (
            f"GPU/CPU Niblack mismatch: {diff}/{total} pixels differ"
        )

    def test_recovers_dark_text_patches(self, cupy_threshold):
        """Dark text patches should be classified as 0 (text)."""
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.niblack_binary_thresh(img_cp)
        out_np = out.get()
        for r, col in [(15, 15), (35, 65), (65, 20), (80, 75)]:
            assert out_np[r, col] == 0, (
                f"GPU Niblack: expected 0 at ({r},{col}), got {out_np[r, col]}"
            )


# ---------------------------------------------------------------------------
# binarize dispatcher (GPU) — new
# ---------------------------------------------------------------------------


@pytest.mark.gpu
class TestBinarizeGpu:
    def test_default_method_is_otsu(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img = cp.zeros((20, 20), dtype=cp.float32)
        img[:10, :] = 0.1
        img[10:, :] = 0.9
        out = thresh_mod.binarize(img)
        expected = thresh_mod.otsu_binary_thresh(img)
        assert cp.array_equal(out, expected)

    def test_adaptive_dispatches(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.binarize(img_cp, method="adaptive")
        expected = thresh_mod.adaptive_binary_thresh(img_cp)
        assert cp.array_equal(out, expected)

    def test_sauvola_dispatches(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.binarize(img_cp, method="sauvola")
        expected = thresh_mod.sauvola_binary_thresh(img_cp)
        assert cp.array_equal(out, expected)

    def test_niblack_dispatches(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.binarize(img_cp, method="niblack")
        expected = thresh_mod.niblack_binary_thresh(img_cp)
        assert cp.array_equal(out, expected)

    def test_params_forwarded(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        out = thresh_mod.binarize(img_cp, method="sauvola", window_size=15, k=0.15)
        expected = thresh_mod.sauvola_binary_thresh(img_cp, window_size=15, k=0.15)
        assert cp.array_equal(out, expected)

    def test_unknown_method_raises_value_error(self, cupy_threshold):
        thresh_mod, cp = cupy_threshold
        img_cp = cp.zeros((4, 4), dtype=cp.uint8)
        with pytest.raises(ValueError):
            thresh_mod.binarize(img_cp, method="bogus")

    def test_output_remains_on_device(self, cupy_threshold):
        """binarize dispatcher must not move data to CPU — output is cp.ndarray."""
        thresh_mod, cp = cupy_threshold
        img_cp = cp.asarray(_gradient_with_text_np())
        for method in ("adaptive", "sauvola", "niblack"):
            out = thresh_mod.binarize(img_cp, method=method)
            assert hasattr(out, "device"), (
                f"binarize(method={method!r}) returned a non-device array"
            )
