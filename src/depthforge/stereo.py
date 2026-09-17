from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .calibration import load_calibration
from .io_utils import ensure_dir, save_json, save_npy, write_ply


@dataclass
class StereoConfig:
    method: str = "sgbm"
    min_disparity: int = 0
    num_disparities: int = 128
    block_size: int = 5
    p1_multiplier: int = 8
    p2_multiplier: int = 32
    uniqueness_ratio: int = 10
    speckle_window_size: int = 100
    speckle_range: int = 2
    disp12_max_diff: int = 1
    max_depth: float = 50000.0
    min_depth: float = 0.0
    max_points: int = 250000


def _validate_num_disparities(value: int) -> int:
    if value <= 0 or value % 16 != 0:
        raise ValueError("num_disparities must be a positive multiple of 16")
    return value


def _validate_block_size(value: int) -> int:
    if value < 3 or value % 2 == 0:
        raise ValueError("block_size must be an odd integer >= 3")
    return value


def create_matcher(config: StereoConfig, image_channels: int = 1):
    num_disp = _validate_num_disparities(config.num_disparities)
    block = _validate_block_size(config.block_size)

    if config.method.lower() == "bm":
        return cv2.StereoBM_create(numDisparities=num_disp, blockSize=max(block, 5))

    if config.method.lower() != "sgbm":
        raise ValueError("method must be either 'sgbm' or 'bm'")

    channels = max(image_channels, 1)
    p1 = config.p1_multiplier * channels * block * block
    p2 = config.p2_multiplier * channels * block * block
    return cv2.StereoSGBM_create(
        minDisparity=config.min_disparity,
        numDisparities=num_disp,
        blockSize=block,
        P1=p1,
        P2=p2,
        disp12MaxDiff=config.disp12_max_diff,
        uniquenessRatio=config.uniqueness_ratio,
        speckleWindowSize=config.speckle_window_size,
        speckleRange=config.speckle_range,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY,
    )


def rectify_pair(left: np.ndarray, right: np.ndarray, calibration: dict[str, np.ndarray]):
    image_size = (left.shape[1], left.shape[0])
    expected = calibration.get("image_size")
    if expected and image_size != expected:
        print(f"Warning: input image size {image_size} differs from calibration size {expected}.")

    map1x, map1y = cv2.initUndistortRectifyMap(
        calibration["K1"], calibration["D1"], calibration["R1"], calibration["P1"], image_size, cv2.CV_32FC1
    )
    map2x, map2y = cv2.initUndistortRectifyMap(
        calibration["K2"], calibration["D2"], calibration["R2"], calibration["P2"], image_size, cv2.CV_32FC1
    )
    rect_l = cv2.remap(left, map1x, map1y, cv2.INTER_LINEAR)
    rect_r = cv2.remap(right, map2x, map2y, cv2.INTER_LINEAR)
    return rect_l, rect_r


def compute_disparity(rectified_left: np.ndarray, rectified_right: np.ndarray, config: StereoConfig) -> np.ndarray:
    if rectified_left.shape[:2] != rectified_right.shape[:2]:
        raise ValueError("Rectified left and right images must have identical dimensions")

    left_gray = cv2.cvtColor(rectified_left, cv2.COLOR_BGR2GRAY) if rectified_left.ndim == 3 else rectified_left
    right_gray = cv2.cvtColor(rectified_right, cv2.COLOR_BGR2GRAY) if rectified_right.ndim == 3 else rectified_right

    matcher = create_matcher(config, image_channels=1)
    raw = matcher.compute(left_gray, right_gray)
    return raw.astype(np.float32) / 16.0


def disparity_visualization(disparity: np.ndarray) -> np.ndarray:
    valid = np.isfinite(disparity) & (disparity > 0)
    result = np.zeros(disparity.shape, dtype=np.uint8)
    if np.any(valid):
        lo, hi = np.percentile(disparity[valid], [2, 98])
        if hi <= lo:
            hi = lo + 1.0
        scaled = np.clip((disparity - lo) / (hi - lo), 0, 1)
        result = (scaled * 255).astype(np.uint8)
        result[~valid] = 0
    return cv2.applyColorMap(result, cv2.COLORMAP_TURBO)


def depth_visualization(points_3d: np.ndarray, min_depth: float, max_depth: float) -> np.ndarray:
    z = points_3d[:, :, 2]
    valid = np.isfinite(z) & (z > min_depth) & (z <= max_depth)
    image = np.zeros(z.shape, dtype=np.uint8)
    if np.any(valid):
        inv = 1.0 / np.maximum(z, 1e-6)
        vals = inv[valid]
        lo, hi = np.percentile(vals, [2, 98])
        if hi <= lo:
            hi = lo + 1e-9
        scaled = np.clip((inv - lo) / (hi - lo), 0, 1)
        image = (scaled * 255).astype(np.uint8)
        image[~valid] = 0
    return cv2.applyColorMap(image, cv2.COLORMAP_TURBO)


def reconstruct_points(
    rectified_left: np.ndarray,
    disparity: np.ndarray,
    calibration: dict[str, np.ndarray],
    config: StereoConfig,
):
    points_3d = cv2.reprojectImageTo3D(disparity, calibration["Q"], handleMissingValues=True)
    z = points_3d[:, :, 2]
    valid = (
        np.isfinite(disparity)
        & (disparity > float(config.min_disparity))
        & np.isfinite(points_3d).all(axis=2)
        & (z > config.min_depth)
        & (z <= config.max_depth)
    )
    ys, xs = np.where(valid)
    if len(xs) == 0:
        return points_3d, np.empty((0, 3), np.float32), np.empty((0, 3), np.uint8), valid

    points = points_3d[ys, xs].astype(np.float32)
    colors = rectified_left[ys, xs].astype(np.uint8)

    if len(points) > config.max_points:
        # Deterministic spatially spread subsample.
        indices = np.linspace(0, len(points) - 1, config.max_points, dtype=np.int64)
        points = points[indices]
        colors = colors[indices]

    return points_3d, points, colors, valid


def run_reconstruction(
    left_path: str | Path,
    right_path: str | Path,
    calibration_path: str | Path,
    output_dir: str | Path,
    config: StereoConfig,
) -> dict:
    left = cv2.imread(str(left_path), cv2.IMREAD_COLOR)
    right = cv2.imread(str(right_path), cv2.IMREAD_COLOR)
    if left is None or right is None:
        raise ValueError("Could not read left/right stereo images")
    if left.shape != right.shape:
        raise ValueError(f"Left/right image shape mismatch: {left.shape} vs {right.shape}")

    calibration = load_calibration(calibration_path)
    rect_l, rect_r = rectify_pair(left, right, calibration)
    disparity = compute_disparity(rect_l, rect_r, config)
    points_3d, points, colors, valid_mask = reconstruct_points(rect_l, disparity, calibration, config)

    output_dir = ensure_dir(output_dir)
    cv2.imwrite(str(output_dir / "rectified_left.png"), rect_l)
    cv2.imwrite(str(output_dir / "rectified_right.png"), rect_r)
    cv2.imwrite(str(output_dir / "disparity.png"), disparity_visualization(disparity))
    cv2.imwrite(str(output_dir / "depth_visualization.png"), depth_visualization(points_3d, config.min_depth, config.max_depth))
    save_npy(output_dir / "disparity_raw.npy", disparity)
    save_npy(output_dir / "depth.npy", points_3d)
    write_ply(output_dir / "point_cloud.ply", points, colors)

    valid_disparity = np.isfinite(disparity) & (disparity > config.min_disparity)
    valid_z = valid_mask & np.isfinite(points_3d[:, :, 2])
    z_values = points_3d[:, :, 2][valid_z]
    metrics = {
        "method": config.method,
        "image_width": int(left.shape[1]),
        "image_height": int(left.shape[0]),
        "valid_disparity_ratio": float(valid_disparity.mean()),
        "valid_depth_ratio": float(valid_mask.mean()),
        "point_count": int(len(points)),
        "depth_median": float(np.median(z_values)) if len(z_values) else None,
        "depth_min": float(np.min(z_values)) if len(z_values) else None,
        "depth_max": float(np.max(z_values)) if len(z_values) else None,
    }
    save_json(output_dir / "metrics.json", metrics)
    return metrics
