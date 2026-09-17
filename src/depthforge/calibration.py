from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from .io_utils import match_image_pairs, read_gray, ensure_dir


@dataclass
class StereoCalibrationResult:
    K1: np.ndarray
    D1: np.ndarray
    K2: np.ndarray
    D2: np.ndarray
    R: np.ndarray
    T: np.ndarray
    E: np.ndarray
    F: np.ndarray
    R1: np.ndarray
    R2: np.ndarray
    P1: np.ndarray
    P2: np.ndarray
    Q: np.ndarray
    image_size: tuple[int, int]
    left_rms: float
    right_rms: float
    stereo_rms: float


def object_points(pattern_cols: int, pattern_rows: int, square_size: float) -> np.ndarray:
    points = np.zeros((pattern_rows * pattern_cols, 3), np.float32)
    grid = np.mgrid[0:pattern_cols, 0:pattern_rows].T.reshape(-1, 2)
    points[:, :2] = grid * float(square_size)
    return points


def find_corners(gray: np.ndarray, pattern_size: tuple[int, int], refine: bool = True):
    cols, rows = pattern_size
    corners = None
    found = False

    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, pattern_size, flags=cv2.CALIB_CB_NORMALIZE_IMAGE)
    else:
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        found, corners = cv2.findChessboardCorners(gray, pattern_size, flags)

    if not found or corners is None:
        return False, None

    if refine and not hasattr(cv2, "findChessboardCornersSB"):
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1e-4)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

    return True, corners.astype(np.float32)


def calibrate_stereo(
    left_dir: str | Path,
    right_dir: str | Path,
    pattern_cols: int,
    pattern_rows: int,
    square_size: float,
    refine_corners: bool = True,
) -> StereoCalibrationResult:
    pairs = match_image_pairs(left_dir, right_dir)
    pattern = (pattern_cols, pattern_rows)
    template = object_points(pattern_cols, pattern_rows, square_size)

    object_points_all: list[np.ndarray] = []
    image_points_l: list[np.ndarray] = []
    image_points_r: list[np.ndarray] = []
    image_size: tuple[int, int] | None = None

    for left_path, right_path in pairs:
        left = read_gray(left_path)
        right = read_gray(right_path)
        if left.shape != right.shape:
            print(f"Skipping {left_path.name}: left/right resolution differs.")
            continue
        image_size = (left.shape[1], left.shape[0])
        found_l, corners_l = find_corners(left, pattern, refine_corners)
        found_r, corners_r = find_corners(right, pattern, refine_corners)
        if found_l and found_r:
            object_points_all.append(template.copy())
            image_points_l.append(corners_l)
            image_points_r.append(corners_r)
            print(f"Accepted: {left_path.name}")
        else:
            print(f"Rejected: {left_path.name} (checkerboard not found in both images)")

    if image_size is None:
        raise ValueError("No valid calibration image pairs were found.")
    if len(object_points_all) < 5:
        raise ValueError("At least 5 valid stereo pairs are required. 15-25 pairs are recommended.")

    rms_l, K1, D1, _, _ = cv2.calibrateCamera(object_points_all, image_points_l, image_size, None, None)
    rms_r, K2, D2, _, _ = cv2.calibrateCamera(object_points_all, image_points_r, image_size, None, None)

    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        100,
        1e-6,
    )
    flags = cv2.CALIB_FIX_INTRINSIC
    stereo_rms, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
        object_points_all,
        image_points_l,
        image_points_r,
        K1,
        D1,
        K2,
        D2,
        image_size,
        criteria=criteria,
        flags=flags,
    )

    R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
        K1,
        D1,
        K2,
        D2,
        image_size,
        R,
        T,
        flags=cv2.CALIB_ZERO_DISPARITY,
        alpha=0,
    )

    return StereoCalibrationResult(
        K1=K1,
        D1=D1,
        K2=K2,
        D2=D2,
        R=R,
        T=T,
        E=E,
        F=F,
        R1=R1,
        R2=R2,
        P1=P1,
        P2=P2,
        Q=Q,
        image_size=image_size,
        left_rms=float(rms_l),
        right_rms=float(rms_r),
        stereo_rms=float(stereo_rms),
    )


def save_calibration(result: StereoCalibrationResult, output_path: str | Path) -> None:
    output_path = Path(output_path)
    ensure_dir(output_path.parent)
    np.savez_compressed(
        output_path,
        K1=result.K1,
        D1=result.D1,
        K2=result.K2,
        D2=result.D2,
        R=result.R,
        T=result.T,
        E=result.E,
        F=result.F,
        R1=result.R1,
        R2=result.R2,
        P1=result.P1,
        P2=result.P2,
        Q=result.Q,
        image_width=result.image_size[0],
        image_height=result.image_size[1],
        left_rms=result.left_rms,
        right_rms=result.right_rms,
        stereo_rms=result.stereo_rms,
    )


def load_calibration(path: str | Path) -> dict[str, np.ndarray]:
    data = np.load(path)
    required = ["K1", "D1", "K2", "D2", "R1", "R2", "P1", "P2", "Q"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Calibration file is missing keys: {missing}")
    result = {key: data[key] for key in data.files}
    result["image_size"] = (int(data["image_width"]), int(data["image_height"]))
    return result
