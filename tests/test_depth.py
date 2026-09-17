import numpy as np


def test_stereo_depth_equation():
    focal = 700.0
    baseline = 70.0
    disparity = 35.0
    depth = focal * baseline / disparity
    assert depth == 1400.0


def test_invalid_disparity_mask():
    disparity = np.array([[0.0, 10.0, -1.0, np.nan]], dtype=np.float32)
    valid = np.isfinite(disparity) & (disparity > 0)
    assert valid.tolist() == [[False, True, False, False]]
