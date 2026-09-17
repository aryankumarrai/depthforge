# DepthForge: Stereo Vision Based Depth Estimation and 3D Reconstruction

**Student:** Aryan Kumar Rai  
**Course:** Computer Vision  
**Project type:** Command-line computer-vision application

---

## 1. Abstract

DepthForge is a classical stereo-vision system that reconstructs approximate 3D structure from a pair of calibrated stereo images. The system estimates camera parameters, performs stereo rectification, computes dense disparity, converts disparity into depth, and exports a colored 3D point cloud.

## 2. Problem Statement

Recovering depth from a single image is ambiguous. A calibrated stereo pair provides two viewpoints of the same scene, allowing depth to be inferred from the displacement of corresponding image points.

## 3. Objectives

1. Calibrate a stereo camera using a chessboard target.
2. Estimate the relative pose of the two cameras.
3. Rectify the stereo pair.
4. Estimate dense disparity.
5. Recover metric 3D coordinates.
6. Export a colored point cloud.
7. Evaluate reconstruction quality and discuss limitations.

## 4. Computer Vision Concepts Used

- Pinhole camera model
- Camera calibration
- Lens distortion
- Stereo calibration
- Epipolar geometry
- Stereo rectification
- Disparity estimation
- Depth estimation
- 3D reconstruction

## 5. System Architecture

```text
Left Image + Right Image
          |
          v
   Stereo Calibration
          |
          v
   Stereo Rectification
          |
          v
  Disparity Estimation
          |
          v
     Depth Recovery
          |
          v
   3D Reprojection
          |
          v
    Colored Point Cloud
```

## 6. Methodology

### 6.1 Camera Calibration

Describe the chessboard pattern, number of images, image resolution, square size, intrinsic matrices and distortion coefficients.

### 6.2 Stereo Calibration

Describe estimation of relative rotation `R` and translation `T` between the cameras.

### 6.3 Rectification

Explain how `R1`, `R2`, `P1`, `P2` and `Q` are used.

### 6.4 Disparity Estimation

Document the selected matching method and its parameters. Explain the relationship:

`d = x_left - x_right`

### 6.5 Depth Estimation

For a rectified stereo camera:

`Z = fB/d`

Explain why larger disparity corresponds to smaller depth.

### 6.6 3D Reconstruction

Explain reprojection of disparity pixels using the `Q` matrix and the generation of the colored PLY point cloud.

## 7. Experimental Setup

Fill in:

- Camera model:
- Image resolution:
- Number of calibration pairs:
- Checkerboard inner corners:
- Square size:
- Stereo baseline:
- Disparity method:
- Number of disparities:
- Block size:

## 8. Results

Insert screenshots of:

1. Original stereo image pair
2. Rectified pair
3. Disparity map
4. Depth visualization
5. 3D point cloud

## 9. Quantitative Evaluation

Report:

| Metric | Value |
|---|---:|
| Left camera RMS reprojection error | |
| Right camera RMS reprojection error | |
| Stereo calibration RMS error | |
| Valid disparity ratio | |
| Valid depth ratio | |
| Runtime per image pair | |
| Median depth on validation target | |
| Absolute depth error | |

## 10. Failure Cases

Discuss examples involving:

- Textureless surfaces
- Reflective objects
- Repetitive patterns
- Occlusion
- Very distant objects
- Calibration errors

## 11. Limitations

State limitations of classical stereo matching and any hardware/data limitations.

## 12. Conclusion

Summarize what the project demonstrates and what was learned from implementing the stereo pipeline.

## 13. Future Work

Possible extensions include left-right consistency checks, plane segmentation, point-cloud filtering, real-time stereo video, surface normal estimation and visual odometry.

## 14. References

1. Richard Szeliski, *Computer Vision: Algorithms and Applications*.
2. Richard Hartley and Andrew Zisserman, *Multiple View Geometry in Computer Vision*.
3. OpenCV documentation for camera calibration, stereo rectification and stereo matching.
