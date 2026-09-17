from __future__ import annotations

import argparse
import json
from pathlib import Path

from .calibration import calibrate_stereo, save_calibration
from .pipeline import load_config
from .stereo import run_reconstruction


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depthforge",
        description="Classical stereo vision pipeline for depth estimation and 3D reconstruction.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    cal = sub.add_parser("calibrate", help="Calibrate a stereo camera using paired chessboard images.")
    cal.add_argument("--left-dir", required=True)
    cal.add_argument("--right-dir", required=True)
    cal.add_argument("--output", required=True)
    cal.add_argument("--pattern-cols", type=int, default=9)
    cal.add_argument("--pattern-rows", type=int, default=6)
    cal.add_argument("--square-size", type=float, default=25.0)
    cal.add_argument("--no-refine", action="store_true")

    rec = sub.add_parser("reconstruct", help="Rectify a stereo pair, estimate depth and export a point cloud.")
    rec.add_argument("--left", required=True)
    rec.add_argument("--right", required=True)
    rec.add_argument("--calibration", required=True)
    rec.add_argument("--output-dir", required=True)
    rec.add_argument("--config", default=None)
    rec.add_argument("--method", choices=["sgbm", "bm"], default=None)
    rec.add_argument("--num-disparities", type=int, default=None)
    rec.add_argument("--block-size", type=int, default=None)
    rec.add_argument("--max-depth", type=float, default=None)
    rec.add_argument("--max-points", type=int, default=None)

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "calibrate":
        result = calibrate_stereo(
            args.left_dir,
            args.right_dir,
            args.pattern_cols,
            args.pattern_rows,
            args.square_size,
            refine_corners=not args.no_refine,
        )
        save_calibration(result, args.output)
        print("\nCalibration complete.")
        print(f"Valid stereo pairs: {args.left_dir} / {args.right_dir}")
        print(f"Image size: {result.image_size[0]} x {result.image_size[1]}")
        print(f"Left RMS error:   {result.left_rms:.6f}")
        print(f"Right RMS error:  {result.right_rms:.6f}")
        print(f"Stereo RMS error: {result.stereo_rms:.6f}")
        print(f"Saved: {args.output}")
        return

    config = load_config(args.config)
    if args.method is not None:
        config.method = args.method
    if args.num_disparities is not None:
        config.num_disparities = args.num_disparities
    if args.block_size is not None:
        config.block_size = args.block_size
    if args.max_depth is not None:
        config.max_depth = args.max_depth
    if args.max_points is not None:
        config.max_points = args.max_points

    metrics = run_reconstruction(
        args.left,
        args.right,
        args.calibration,
        args.output_dir,
        config,
    )
    print("\nReconstruction complete.")
    print(json.dumps(metrics, indent=2))
