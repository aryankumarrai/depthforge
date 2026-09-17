from __future__ import annotations

import cv2
import numpy as np


def draw_rectification_check(left: np.ndarray, right: np.ndarray, spacing: int = 40) -> np.ndarray:
    """Stack rectified images and overlay horizontal scan lines."""
    if left.shape != right.shape:
        raise ValueError("Images must have equal shape")
    canvas = np.hstack([left.copy(), right.copy()])
    for y in range(0, canvas.shape[0], max(1, spacing)):
        cv2.line(canvas, (0, y), (canvas.shape[1] - 1, y), (0, 255, 0), 1)
    return canvas
