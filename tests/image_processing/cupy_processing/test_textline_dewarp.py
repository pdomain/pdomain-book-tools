import numpy as np
import pytest


def _lined_page(h=900, w=700, n_lines=14, top=90, gap=55):
    import cv2

    img = np.zeros((h, w), np.uint8)
    for i in range(n_lines):
        y = top + i * gap
        for x0 in range(60, w - 60, 70):
            cv2.rectangle(img, (x0, y), (x0 + 50, y + 10), 255, -1)
    return img


@pytest.mark.gpu
@pytest.mark.cupy
class TestCuPyTextlineDewarpParity:
    def test_detect_textlines_parity_with_numpy(self, cupy_module):
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing import (
            textline_dewarp as gtd,
        )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        page = _lined_page()
        cpu_lines = ctd.detect_textlines(page, page_width=page.shape[1])
        gpu_lines = gtd.detect_textlines(cp.asarray(page), page_width=page.shape[1])
        assert abs(len(gpu_lines) - len(cpu_lines)) <= 1
        cpu_centers = sorted(float(l.ys.mean()) for l in cpu_lines)
        gpu_centers = sorted(float(cp.asnumpy(l.ys).mean()) for l in gpu_lines)
        n = min(len(cpu_centers), len(gpu_centers))
        np.testing.assert_allclose(gpu_centers[:n], cpu_centers[:n], atol=3.0)

    def test_full_map_parity_with_numpy(self, cupy_module):
        cp = cupy_module
        from pdomain_book_tools.image_processing.cupy_processing import (
            textline_dewarp as gtd,
        )
        from pdomain_book_tools.image_processing.cv2_processing import (
            textline_dewarp as ctd,
        )

        page = _lined_page(h=1000, w=760, n_lines=14, top=90, gap=60)
        h, w = page.shape
        c_lines = ctd.remove_short_lines(ctd.detect_textlines(page, page_width=w))
        c_mx, c_my = ctd.build_disparity_maps(
            c_lines, ctd.fit_baselines(c_lines), (h, w), gutter_edge="none"
        )

        g_lines = gtd.remove_short_lines(
            gtd.detect_textlines(cp.asarray(page), page_width=w)
        )
        g_mx, g_my = gtd.build_disparity_maps(
            g_lines, gtd.fit_baselines(g_lines), (h, w), gutter_edge="none"
        )
        np.testing.assert_allclose(cp.asnumpy(g_mx), c_mx, atol=2.0)
        np.testing.assert_allclose(cp.asnumpy(g_my), c_my, atol=2.0)
