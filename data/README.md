# Data

## Final demo assets
The repository includes a verified synthetic stereo pair under `data/final_demo/` so the complete reconstruction pipeline can be executed without a physical camera.

- `final_demo/left.png` — left stereo image
- `final_demo/right.png` — right stereo image
- `final_demo/calibration.npz` — matching synthetic stereo calibration

Run:

```bash
python run_depthforge.py reconstruct --left data/final_demo/left.png --right data/final_demo/right.png --calibration data/final_demo/calibration.npz --output-dir outputs/final_demo --config config/default.yaml
```

## Real calibration
The `data/calibration/left/` and `data/calibration/right/` folders are intentionally kept empty in the repository. For real-camera calibration, place 15–25 matched chessboard stereo pairs there and run the calibration command described in the README. Synthetic final-demo assets are for deterministic software testing and are not a replacement for physical-camera calibration.
