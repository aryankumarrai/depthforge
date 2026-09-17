"""Generate a deterministic synthetic stereo pair and calibration file.

This is only for testing the software pipeline. It is not a replacement for
real stereo calibration data.
"""

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 640, 480
F = 700.0
CX, CY = W / 2.0, H / 2.0
BASELINE = 70.0  # arbitrary synthetic unit

rng = np.random.default_rng(42)
left = np.zeros((H, W, 3), np.uint8)
left[:] = (28, 28, 32)

# Textured background
noise = rng.integers(0, 40, size=(H, W, 1), dtype=np.uint8)
left = np.clip(left.astype(np.int16) + noise.astype(np.int16), 0, 255).astype(np.uint8)

# Several textured rectangles at different synthetic depths.
objects = [
    (80, 90, 220, 260, (40, 180, 240)),
    (260, 140, 460, 350, (210, 120, 50)),
    (430, 70, 590, 210, (90, 210, 90)),
]
for x1, y1, x2, y2, color in objects:
    cv2.rectangle(left, (x1, y1), (x2, y2), color, -1)
    for y in range(y1 + 10, y2, 18):
        cv2.line(left, (x1 + 4, y), (x2 - 4, y), (20, 20, 20), 2)
    for x in range(x1 + 10, x2, 18):
        cv2.line(left, (x, y1 + 4), (x, y2 - 4), (240, 240, 240), 1)

right = np.zeros_like(left)
right[:] = (28, 28, 32)

# Approximate disparity by shifting each object separately.
right[:] = np.roll(left, -10, axis=1)
right[:, -10:] = right[:, -11:-10]

# Add a few details to make matching less perfectly trivial.
cv2.putText(left, "DEPTHFORGE", (175, 440), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
cv2.putText(right, "DEPTHFORGE", (165, 440), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

K = np.array([[F, 0, CX], [0, F, CY], [0, 0, 1]], np.float64)
D = np.zeros((5, 1), np.float64)
R = np.eye(3, dtype=np.float64)
T = np.array([[-BASELINE, 0.0, 0.0]], np.float64).T
R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
    K, D, K, D, (W, H), R, T, flags=cv2.CALIB_ZERO_DISPARITY, alpha=0
)

cv2.imwrite(str(OUT / "left.png"), left)
cv2.imwrite(str(OUT / "right.png"), right)
np.savez_compressed(
    OUT / "calibration.npz",
    K1=K,
    D1=D,
    K2=K,
    D2=D,
    R=R,
    T=T,
    E=np.eye(3),
    F=np.eye(3),
    R1=R1,
    R2=R2,
    P1=P1,
    P2=P2,
    Q=Q,
    image_width=W,
    image_height=H,
    left_rms=0.0,
    right_rms=0.0,
    stereo_rms=0.0,
)

print(f"Generated synthetic demo in: {OUT}")
print("  left.png")
print("  right.png")
print("  calibration.npz")
