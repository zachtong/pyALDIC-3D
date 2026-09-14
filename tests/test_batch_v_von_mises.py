"""von Mises equivalent strain: the plane formula of pyALDIC (2D).

The 3D code computed sqrt(e1² + e2² − e1·e2 + 3·max_shear²). The first three
terms already equal the plane von Mises sqrt(m² + 3R²), so the extra 3·R²
counted the shear twice: 32 % too high in uniaxial strain, 41 % in pure shear.
"""

from __future__ import annotations

import numpy as np
import pytest

from al_dic_3d.project.session import _result_arrays, _result_from_arrays
from al_dic_3d.strain3d import StrainResult3D, strain_tensor
from al_dic_3d.strain3d.gradients import von_mises_strain
from al_dic_3d.strain3d.model import STRAIN_FIELDS
from tests.test_strain_window import _synthetic_result


def _coef(exx: float, eyy: float, exy: float) -> np.ndarray:
    """Gradient coefficients (rows = derivative axis) of a small in-plane strain."""
    coef = np.zeros((1, 3, 3))
    coef[0, 0, 0] = exx  # du/dx
    coef[0, 1, 1] = eyy  # dv/dy
    coef[0, 1, 0] = exy  # du/dy
    coef[0, 0, 1] = exy  # dv/dx
    return coef


@pytest.mark.parametrize(
    ("exx", "eyy", "exy", "expected"),
    [
        (0.01, 0.0, 0.0, 0.01),  # uniaxial: the strain itself
        (0.0, 0.0, 0.01, np.sqrt(3.0) * 0.01),  # pure shear
        (0.01, 0.01, 0.0, 0.01),  # equibiaxial
        (0.01, -0.003, 0.0, np.sqrt(0.01**2 + 0.003**2 + 0.01 * 0.003)),  # Poisson 0.3
    ],
)
def test_von_mises_of_simple_states(exx, eyy, exy, expected):
    out = strain_tensor(_coef(exx, eyy, exy), "infinitesimal")
    assert out["von_mises"][0] == pytest.approx(expected, rel=1e-12)


def test_von_mises_matches_the_2d_engine():
    from al_dic.strain.compute_strain import _compute_derived_strains

    rng = np.random.default_rng(7)
    coef = rng.normal(scale=0.05, size=(500, 3, 3))
    for kind in ("infinitesimal", "green_lagrange", "almansi"):
        out = strain_tensor(coef, kind)
        # The 2D signature is (exx, exy, eyy).
        e1, e2, max_shear, von_mises = _compute_derived_strains(out["exx"], out["exy"], out["eyy"])
        np.testing.assert_array_equal(out["von_mises"], von_mises)
        np.testing.assert_allclose(out["e1"], e1, rtol=1e-13, atol=1e-15)
        np.testing.assert_allclose(out["e2"], e2, rtol=1e-13, atol=1e-15)
        np.testing.assert_allclose(out["max_shear"], max_shear, rtol=1e-13, atol=1e-15)


def _with_strain(von_mises_offset: float = 0.0):
    result = _synthetic_result()
    n_frames, n_pts = result.correspondence.xL.shape[:2]
    rng = np.random.default_rng(3)
    exx, eyy, exy = (rng.normal(scale=0.01, size=(n_frames, n_pts)) for _ in range(3))
    fields = {name: np.zeros((n_frames, n_pts)) for name in STRAIN_FIELDS}
    fields.update(exx=exx, eyy=eyy, exy=exy)
    fields["von_mises"] = von_mises_strain(exx, eyy, exy) + von_mises_offset
    return result, StrainResult3D(**fields)


def test_sessions_derive_von_mises_from_the_stored_components():
    import dataclasses

    # A session saved before the fix stored the old, too-high values.
    result, strain = _with_strain(von_mises_offset=0.5)
    arrays = _result_arrays(dataclasses.replace(result, strain=strain))
    loaded = _result_from_arrays(arrays, result.ref_coords, result.strategy, {})
    want = von_mises_strain(strain.exx, strain.eyy, strain.exy)
    np.testing.assert_array_equal(loaded.strain.von_mises, want)


def test_a_current_session_round_trips_bit_identically():
    import dataclasses

    result, strain = _with_strain()
    arrays = _result_arrays(dataclasses.replace(result, strain=strain))
    loaded = _result_from_arrays(arrays, result.ref_coords, result.strategy, {})
    np.testing.assert_array_equal(loaded.strain.von_mises, strain.von_mises)
