"""PP-DocLayout adapter tests.

The smoke test downloads ~132 MB of weights on first run; mark the slow
test with ``pytest.mark.slow`` so ``-m 'not slow'`` skips it.
"""

import numpy as np
import pytest

from pd_book_tools.layout._mappings import PP_DOCLAYOUT_TO_PGDP
from pd_book_tools.layout.types import RegionType


def test_mapping_targets_are_known_region_types():
    """Every non-None PP-DocLayout mapping resolves to a known RegionType."""
    valid_values = {rt.value for rt in RegionType}
    for native, mapped in PP_DOCLAYOUT_TO_PGDP.items():
        if mapped is None:
            continue
        assert mapped in valid_values, (
            f"PP-DocLayout label {native!r} maps to {mapped!r}, "
            "which is not a RegionType — update RegionType or the mapping."
        )


@pytest.mark.slow
def test_smoke_load_and_infer_blank_page():
    """End-to-end: load model, run on a blank synthetic page.

    Marked slow because the first call downloads ~132 MB; skip with
    ``-m 'not slow'``.
    """
    from pd_book_tools.layout.adapters.pp_doclayout import (
        PPDocLayoutPlusLDetector,
    )

    det = PPDocLayoutPlusLDetector(device="cpu", confidence=0.5)
    blank = np.full((1200, 800, 3), 255, dtype=np.uint8)
    layout = det.detect(blank)
    assert layout.image_width == 800
    assert layout.image_height == 1200
    assert layout.detector == "pp-doclayout-plus-l"
    # No predictions on a blank page is fine; we just want to know the
    # adapter ran without errors.
    assert isinstance(layout.regions, list)
