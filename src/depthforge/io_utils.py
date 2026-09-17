from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def list_images(directory: str | Path) -> list[Path]:
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)


def match_image_pairs(left_dir: str | Path, right_dir: str | Path) -> list[tuple[Path, Path]]:
    left = {p.stem: p for p in list_images(left_dir)}
    right = {p.stem: p for p in list_images(right_dir)}
    common = sorted(set(left) & set(right))
    if not common:
        raise ValueError("No matching left/right image pairs found. Filenames must share the same stem.")
    missing_left = sorted(set(right) - set(left))
    missing_right = sorted(set(left) - set(right))
    if missing_left:
        print(f"Warning: right-only files ignored: {missing_left}")
    if missing_right:
        print(f"Warning: left-only files ignored: {missing_right}")
    return [(left[name], right[name]) for name in common]


def read_color(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def read_gray(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def save_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_npy(path: str | Path, array: np.ndarray) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    np.save(path, array)


def write_ply(path: str | Path, points: np.ndarray, colors_bgr: np.ndarray) -> None:
    """Write an ASCII PLY with XYZ coordinates and RGB colors."""
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points must have shape (N, 3)")
    if colors_bgr.shape != (len(points), 3):
        raise ValueError("colors_bgr must have shape (N, 3)")

    path = Path(path)
    ensure_dir(path.parent)

    colors_rgb = colors_bgr[:, ::-1].astype(np.uint8)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("ply\n")
        handle.write("format ascii 1.0\n")
        handle.write(f"element vertex {len(points)}\n")
        handle.write("property float x\n")
        handle.write("property float y\n")
        handle.write("property float z\n")
        handle.write("property uchar red\n")
        handle.write("property uchar green\n")
        handle.write("property uchar blue\n")
        handle.write("end_header\n")
        for point, color in zip(points, colors_rgb):
            handle.write(
                f"{float(point[0]):.6f} {float(point[1]):.6f} {float(point[2]):.6f} "
                f"{int(color[0])} {int(color[1])} {int(color[2])}\n"
            )
