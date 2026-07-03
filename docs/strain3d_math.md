# 3D Surface Strain — method derivation

> The single source of truth for `al_dic_3d.strain3d`. Extracted from the MATLAB
> mainline (`3D-Stereo-ALDIC/func_quadtree/PlaneFit3_Quadtree.m` +
> `computeStrain3D.m`, with `func/GetRTMatrix.m` for the optional specimen frame
> and `func_quadtree/funSmoothDisp_Quadtree.m` for optional pre-smoothing). Not a
> literal port — the math is extracted and re-expressed for a NumPy point-cloud
> implementation. On any conflict this document wins; amend it before the code.

## 0. Inputs and outputs

Strain is computed **per frame** from a `Reconstruction3D` (01 §E) plus the
frame-1 reference **2D** node coordinates (the left-camera mesh pixels):

- `ref_2d` — `(n, 2)` reference node coordinates in the **left image** (pixels).
  Used ONLY for the neighbourhood (VSG) search — the strain gauge is a pixel
  window, exactly as in MATLAB.
- `ref_3d = reconstruction.points[0]` — `(n, 3)` reference 3D world positions
  `P¹` (mm). The plane fit and the displacement-gradient fit are done on these
  (Lagrangian / total-Lagrange strain).
- `disp_k = reconstruction.displacement[k]` — `(n, 3)` cumulative displacement
  `Dᵏ = Pᵏ − P¹` (mm).

Output `StrainResult3D`, per frame per node: `exx, eyy, exy` (Green–Lagrange, in
the local tangent frame), `e1, e2` (principal), `max_shear`, `von_mises`, and
`dwdx, dwdy` (out-of-plane slopes, diagnostics). `NaN` = invalid / void.

## 1. Virtual strain gauge (VSG) neighbourhood

Strain is evaluated at **every** node (strain winstep = 1). For node *i* the
neighbourhood is the set of nodes inside a **square (Chebyshev) window** centred
on *i* in the reference image:

```
strain_length = (strain_size − 1) · winstepsize + 1     [pixels]   (VSG side)
vsg_radius     = 0.5 · strain_length                     [pixels, Chebyshev]
neighbours(i)  = { j : ‖ref_2d[j] − ref_2d[i]‖_∞ ≤ vsg_radius }
```

`strain_size` is the VSG size in grid steps (odd, e.g. 5). Require at least
`MIN_NEIGHBORS = 9` finite-displacement neighbours for a stable fit; nodes with
fewer are **void** (strain = NaN). MATLAB additionally splits the field by
connected mask region (`bwconncomp`) so a gauge never straddles two disconnected
ROI patches; v1 treats the ROI as a single region (documented limitation —
masked multi-region strain is deferred).

The window is a **square in pixel space**, so `scipy.spatial.cKDTree` with the
Chebyshev metric (`p = inf`) and `query_ball_point(radius = vsg_radius)`
reproduces `knnsearch(...,'Distance','chebychev')` + the radius filter.

## 2. Local tangent frame (the plane fit)

For a **curved** surface the displacement gradients must be taken in the local
tangent plane, not the camera frame. For each node's neighbourhood (reference 3D
coords `X = ref_3d[neighbours]`):

1. Least-squares fit the local **surface** plane `Z = a·X + b·Y + c`:

   ```
   [X  Y  1] · [a b c]ᵀ = Z              (solve for a, b, c)
   ```

2. Build an orthonormal tangent frame `R = [x̂, ŷ, ẑ]` (columns) from the plane
   normal (MATLAB `PlaneFit3_Quadtree.m:99–102`):

   ```
   ẑ = normalize([a, b, −1])             (surface normal)
   x̂ = normalize([1,0,0] − ([1,0,0]·ẑ) ẑ)   (world +X projected onto the plane)
   ŷ = ẑ × x̂
   ```

   `[1,0,0]` is the seed for x̂; if the surface is near-vertical (ẑ ≈ ±x̂) this is
   ill-conditioned — a v1 caveat (bumps/plates are fine; near-vertical facets
   are not expected on a stereo-DIC surface).

## 3. Displacement gradients in the local frame

Rotate BOTH the reference coordinates and the displacements into the local frame
and fit the in-plane gradients (MATLAB "策略2", `:121–126`):

```
X_loc = X · R          (n_nbr, 3)     local reference coords
U_loc = disp · R       (n_nbr, 3)     local displacement components
[X_loc[:,0]  X_loc[:,1]  1] · G2 = U_loc      (least squares, per component)
```

`G2` is `(3, 3)`: rows = fit terms `(∂/∂x_loc, ∂/∂y_loc, const)`, columns =
local displacement component `(U_loc, V_loc, W_loc)`. Drop the constant row and
zero the out-of-plane (`z_loc`) derivative row — the gauge is a surface, so only
in-plane gradients are meaningful:

```
coefficients = [ ∂/∂x_loc                (row 0)
                 ∂/∂y_loc                (row 1)
                 0  0  0 ]               (row 2, z-derivative dropped)
```

`coefficients[a, b]` = ∂(local disp component *b*) / ∂(local axis *a*).

**Other coordinate modes** (parametrised, not the default):
- `camera0`: fit `disp = a·X + b·Y + c·Z + d` directly in the world frame; keep
  the full `(3,3)` gradient (no rotation, no z-zeroing).
- `specific`: same as `local` but `R` is a fixed user specimen frame from
  `GetRTMatrix` (§5) instead of the per-node plane normal.

## 4. Green–Lagrange strain (`computeStrain3D.m`)

From the local displacement-gradient matrix build the deformation gradient and
the Green–Lagrange strain (rotation-invariant, so rigid motion → 0):

```
F = I + coefficientsᵀ
      = [ 1+u_x   u_y     u_z
          v_x    1+v_y    v_z
          w_x     w_y   1+w_z ]           (u_x = ∂U_loc/∂x_loc, etc.)

E = ½ (Fᵀ F − I)

exx = E[0,0]      eyy = E[1,1]      exy = E[0,1]
dwdx = w_x = coefficients[0,2]      dwdy = w_y = coefficients[1,2]
```

(In `local`/`specific` the z-derivative row is 0 so `u_z = v_z = w_z = 0`.)
Derived quantities:

```
max_shear = sqrt( (½(exx − eyy))² + exy² )
e1        = ½(exx + eyy) + max_shear                 (major principal)
e2        = ½(exx + eyy) − max_shear                 (minor principal)
von_mises = sqrt( e1² + e2² − e1·e2 + 3·max_shear² )
```

## 5. Optional post/pre-steps (parametrised, default off)

- **Specimen frame** (`GetRTMatrix.m`): interpolate the 3D positions of 3 user
  base points `(O, X, Y)` from `ref_2d → ref_3d`, then Gram–Schmidt:
  `x̂ = (X−O)/‖·‖`, `ẑ = x̂ × (Y−O)/‖·‖` normalised, `ŷ = ẑ × x̂`; `R = [x̂ ŷ ẑ]`,
  `T = O`. Feeds the `specific` coordinate mode so strain is reported in the
  specimen frame. Optional post-step on `Reconstruction3D`.
- **Displacement smoothing** (`funSmoothDisp_Quadtree.m`): MATLAB grids the
  scattered displacement (`gridfit`, springs regulariser) then Gaussian-filters
  (default σ = 0.5, size 3) `Smooth3DTimes` times before the gradient fit. v1
  provides an optional scattered smoothing of the same spirit; default off
  (`smooth_times = 0`) so the raw field is used.

## 6. Validation (the Phase-3 gate)

Analytic fields, computed directly (no rendering) on a synthetic node cloud:
1. **Rigid rotation → 0 strain**: `disp = (R·Pᵀ)ᵀ − P` for a rotation `R`;
   `F = R`, `E = ½(RᵀR − I) = 0` — every component ≈ 0.
2. **Uniaxial stretch on a plane**: `disp = [ε·X, 0, 0]`; `exx = ε + ½ε²`,
   `eyy = exy = 0`.
3. **Uniaxial stretch on a curved surface** (cylinder/sphere cap): stretch along
   a principal surface direction; the recovered in-plane strain matches the
   applied value within tolerance (tests the tangent-frame handling).
Plus MATLAB `strainPerFrame` parity on the baseline dataset (deferred with the
other MATLAB-parity gates until the user provides it), and a VSG-size sensitivity
study in `reports/phase3_strain.pdf`.
