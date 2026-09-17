from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import yaml

from .stereo import StereoConfig


def load_config(path: str | Path | None) -> StereoConfig:
    if path is None:
        return StereoConfig()
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    stereo = data.get("stereo", {})
    reconstruction = data.get("reconstruction", {})
    return StereoConfig(
        method=stereo.get("method", "sgbm"),
        min_disparity=int(stereo.get("min_disparity", 0)),
        num_disparities=int(stereo.get("num_disparities", 128)),
        block_size=int(stereo.get("block_size", 5)),
        p1_multiplier=int(stereo.get("p1_multiplier", 8)),
        p2_multiplier=int(stereo.get("p2_multiplier", 32)),
        uniqueness_ratio=int(stereo.get("uniqueness_ratio", 10)),
        speckle_window_size=int(stereo.get("speckle_window_size", 100)),
        speckle_range=int(stereo.get("speckle_range", 2)),
        disp12_max_diff=int(stereo.get("disp12_max_diff", 1)),
        max_depth=float(reconstruction.get("max_depth", 50000.0)),
        min_depth=float(reconstruction.get("min_depth", 0.0)),
        max_points=int(reconstruction.get("max_points", 250000)),
    )
