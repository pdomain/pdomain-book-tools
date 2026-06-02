import numpy as np

from pdomain_book_tools.image_processing.textline_types import LineSamples, QuadCoeffs


def test_line_samples_holds_columns_and_centroids():
    ls = LineSamples(xs=np.array([0.0, 1.0, 2.0]), ys=np.array([10.0, 10.5, 11.0]))
    assert ls.xs.shape == (3,)
    assert ls.ys.shape == (3,)
    assert ls.left == 0.0
    assert ls.right == 2.0


def test_quad_coeffs_eval_matches_polyval():
    q = QuadCoeffs(c2=0.5, c1=-1.0, c0=3.0)
    assert q.eval(2.0) == 0.5 * 4 - 1.0 * 2 + 3.0
    np.testing.assert_allclose(q.eval(np.array([0.0, 1.0])), np.array([3.0, 2.5]))
