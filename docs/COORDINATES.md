# COORDINATES — the single pixel/world coordinate convention for pyALDIC-3D

> Coordinate conventions are the **#1 silent killer** in a stereo-DIC port
> (01 §D.4): MATLAB indexes images row-first and transposes for display, numpy is
> `[row, col]`, and the intrinsic matrix `K` is `(u, v)`. This document fixes ONE
> convention for the whole `al_dic_3d` package. Every module obeys it; the
> round-trip test in `tests/test_geometry_roundtrip.py` enforces it.

## 1. Pixel coordinates: `(u, v)`

A pixel coordinate is the pair **`(u, v)`**:

- `u` = **column** index = horizontal = the `x` axis, increasing to the **right**.
- `v` = **row** index = vertical = the `y` axis, increasing **downward**.
- Origin `(0, 0)` is the center of the top-left pixel (OpenCV convention).

This matches the intrinsic matrix `K` and every `cv2` call, so no transpose or
axis-swap is ever needed at a `cv2` boundary.

Point arrays are always `(N, 2)` `float64`, column 0 = `u`, column 1 = `v`.
This is the SAME order the 2D engine uses (`coords[:, 0] = x = col`,
`coords[:, 1] = y = row`), so 2D↔3D hand-offs need no remapping.

## 2. numpy image arrays: `[v, u]`

An image loaded as a numpy array is indexed **`image[v, u]` = `image[row, col]`**.
So converting a pixel `(u, v)` to an array index is `image[int(round(v)), int(round(u))]`.
Never index an image with `(u, v)` directly.

## 3. Intrinsics and distortion

The intrinsic matrix is

```
K = [[fx, skew, cx],
     [ 0,   fy, cy],
     [ 0,    0,  1]]
```

Distortion uses the **Brown–Conrady** model in OpenCV coefficient order
`[k1, k2, p1, p2, k3]`. Given a normalized (pinhole) coordinate `(x, y)` with
`r² = x² + y²`:

```
radial = 1 + k1·r² + k2·r⁴ + k3·r⁶
x_d = x·radial + 2·p1·x·y + p2·(r² + 2·x²)
y_d = y·radial + p1·(r² + 2·y²) + 2·p2·x·y
u   = fx·x_d + skew·y_d + cx
v   = fy·y_d + cy
```

Forward distortion (`world → pixel`) is computed by `calibration.geometry.project_points`.
Inverse (`pixel → normalized undistorted`) is done by `calibration.geometry.undistort_points`
via `cv2.undistortPoints` (matching the MATLAB `funUndistortPoints` step).

## 4. World frame and extrinsics

- **World frame = the left camera's optical frame** (`R = I`, `T = 0`), per
  `stereoReconstruction_quadtree.m` and decision in 01 §E. The default camera key
  for the world is `"L"`.
- A camera's pose `(R, T)` maps **world → that camera**: `X_cam = R · X_world + T`,
  with `R` a `(3, 3)` rotation and `T` a `(3,)` translation, in calibration length
  units (typically mm). `StereoRig.extrinsics[("L", "R")] = (R, T)`.
- The `3×4` projection matrix for a camera is `P = K · [R | T]`; for the left
  camera `P_L = K_L · [I | 0]`.

## 5. Triangulation input

Triangulation (`reconstruct.triangulate_dlt`) consumes **normalized, undistorted**
coordinates (the output of `undistort_points`, i.e. `cv2.undistortPoints` with no
`P`), NOT raw pixels. It uses `P_L = [I | 0]` and `P_R = [R | T]` (no `K`, since
the inputs are already normalized), so the recovered `X` is directly in world
metric units. Match on **raw** images; undistort only the matched point
coordinates, only at the triangulation boundary (01 §E invariant).

## 6. Invalid points

`NaN` marks an invalid/failed point and **propagates end-to-end**: a `NaN` pixel
undistorts to `NaN`, triangulates to a `NaN` 3D point, and yields `NaN` strain.
Arrays are `float64`. Never use a sentinel like `-1` or `0` for "missing".

## 7. The round-trip contract (enforced by test)

```
X (N,3 world)
  ── project_points (L: R=I,T=0) ──▶ uv_L (N,2 pixels)
  ── project_points (R: R,T)     ──▶ uv_R (N,2 pixels)
uv_L, uv_R
  ── undistort_points ──▶ xn_L, xn_R (N,2 normalized)
  ── triangulate_dlt(·, ·, R, T) ──▶ X_rec (N,3 world)

assert X_rec ≈ X   (atol 1e-9 with zero distortion; ~1e-6 with distortion,
                    bounded by cv2.undistortPoints' iterative inverse)
```

If this test ever fails, a coordinate convention has drifted — fix the code, never
the test.
