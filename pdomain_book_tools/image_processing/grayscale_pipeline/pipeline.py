"""Grayscale pipeline orchestrator.

Chains the stage sequence:
    flatten? (color BGR) → converter (color → gray) → clahe? (gray) → output_range? (gray)

Selects GPU ops when ``use_gpu=True`` and CuPy is available; falls back to
CPU ops silently when CuPy is not installed.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from pdomain_book_tools.image_processing.cupy_processing._cupy_compat import (
    cupy_available,
)
from pdomain_book_tools.image_processing.grayscale_pipeline import ops_cpu
from pdomain_book_tools.image_processing.grayscale_pipeline.config import (
    Converter,
    GrayscaleConfig,
)

U8 = npt.NDArray[np.uint8]


def run_grayscale_pipeline(
    img: U8,
    config: GrayscaleConfig,
    *,
    use_gpu: bool,
) -> U8:
    """Run the full grayscale pipeline on a BGR uint8 image.

    Stage order:
    1. Flatten (optional) — low-frequency background normalisation.
    2. Converter — colour-to-grayscale algorithm selected by ``config.converter``.
    3. CLAHE (optional) — local contrast enhancement.
    4. Output-range stretch (optional) — linear min-max rescaling.

    Args:
        img: BGR uint8 ndarray of shape (H, W, 3).
        config: :class:`GrayscaleConfig` controlling all stages.
        use_gpu: Request GPU execution.  Falls back to CPU when CuPy is not
            available so callers need not guard the call site.

    Returns:
        Grayscale uint8 ndarray of shape (H, W).
    """
    _use_gpu = use_gpu and cupy_available()

    # --- Stage 1: flatten (optional, colour space) ---------------------------
    color: U8 = img
    if config.flatten.enabled:
        if _use_gpu:
            from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

            color = ops_gpu.flatten_gpu(
                img, radius=config.flatten.radius, strength=config.flatten.strength
            )
        else:
            color = ops_cpu.flatten(
                img, radius=config.flatten.radius, strength=config.flatten.strength
            )

    # --- Stage 2: converter (colour → gray) ----------------------------------
    gray: U8
    converter = config.converter

    if converter == Converter.color2gray:
        if _use_gpu:
            from pdomain_book_tools.image_processing.cupy_processing.color_to_gray import (
                np_uint8_color_to_gray,
            )

            gray = np_uint8_color_to_gray(
                color,
                radius=config.color2gray.radius,
                samples=config.color2gray.samples,
                iterations=config.color2gray.iterations,
                enhance_shadows=config.color2gray.enhance_shadows,
            )
        else:
            from pdomain_book_tools.image_processing.grayscale_pipeline.color2gray_cpu import (
                color2gray_cpu,
            )

            gray = color2gray_cpu(
                color,
                radius=config.color2gray.radius,
                samples=config.color2gray.samples,
                iterations=config.color2gray.iterations,
                enhance_shadows=config.color2gray.enhance_shadows,
            )
    elif _use_gpu:
        from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

        if converter == Converter.luma:
            gray = ops_gpu.luma_gpu(color, bt709=False)
        elif converter == Converter.luma_bt709:
            gray = ops_gpu.luma_gpu(color, bt709=True)
        elif converter == Converter.lab_l:
            gray = ops_gpu.lab_l_gpu(color)
        else:
            # Converter.best_channel
            gray = ops_gpu.best_channel_gpu(color, channel=config.channel)
    elif converter == Converter.luma:
        gray = ops_cpu.luma(color, bt709=False)
    elif converter == Converter.luma_bt709:
        gray = ops_cpu.luma(color, bt709=True)
    elif converter == Converter.lab_l:
        gray = ops_cpu.lab_l(color)
    else:
        # Converter.best_channel
        gray = ops_cpu.best_channel(color, channel=config.channel)

    # --- Stage 3: CLAHE (optional, grayscale) --------------------------------
    if config.clahe.enabled:
        if _use_gpu:
            from pdomain_book_tools.image_processing.grayscale_pipeline import ops_gpu

            gray = ops_gpu.clahe_gpu(
                gray,
                clip_limit=config.clahe.clip_limit,
                tile_grid=config.clahe.tile_grid,
            )
        else:
            gray = ops_cpu.clahe(
                gray,
                clip_limit=config.clahe.clip_limit,
                tile_grid=config.clahe.tile_grid,
            )

    # --- Stage 4: output range (optional, grayscale) -------------------------
    if config.output_range is not None:
        gray = ops_cpu.apply_output_range(gray, config.output_range)

    return gray
