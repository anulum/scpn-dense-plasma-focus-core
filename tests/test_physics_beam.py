# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — fast ion beam tests

"""Anchors, identities and refusals of the fast-ion-beam chain."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import INTI, NX3, PF400J, PF1000, AnchorRow, relative_gap
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    ELEMENTARY_CHARGE_C,
    FLUX_COEFFICIENT,
    PROTON_MASS_KG,
    FastIonBeam,
    fast_ion_beam,
)


def beam(row: AnchorRow) -> FastIonBeam:
    """Evaluate the beam chain of one anchor row (deuterons, ``fe = 0.14``)."""
    return fast_ion_beam(
        row.pinch_current_a,
        row.minimum_radius_m,
        row.cathode_radius_m,
        row.diode_voltage_v,
        row.pinch_duration_s,
        0.14,
        2.0,
        1.0,
    )


@pytest.mark.parametrize(
    ("row", "tolerance"),
    [(PF1000, 0.03), (NX3, 0.03), (INTI, 0.03), (PF400J, 0.12)],
    ids=["PF1000", "NX3", "INTI", "PF400J"],
)
def test_beam_chain_reproduces_table_1(row: AnchorRow, tolerance: float) -> None:
    """Flux, speed and the derived quantities (a)–(k) match the printed columns."""
    result = beam(row)
    printed = {
        "flux_per_m2_s": row.flux_per_m2_s,
        "beam_speed_m_s": row.ion_speed_m_s,
        "energy_flux_w_m2": row.energy_flux_w_m2,
        "power_flow_w": row.power_flow_w,
        "ion_current_a": row.ion_current_a,
        "fluence_per_m2": row.fluence_per_m2,
        "energy_fluence_j_m2": row.energy_fluence_j_m2,
        "ions_in_beam": row.ions_in_beam,
        "beam_energy_j": row.beam_energy_j,
        "damage_factor_w_m2_sqrt_s": row.damage_factor,
    }
    record = result.to_record()
    for name, want in printed.items():
        gap = relative_gap(record[name], want)
        assert gap <= tolerance, (row.name, name, record[name], want, gap)


def test_closed_forms_and_derived_quantities() -> None:
    """Eqs. (5)–(6) and the list (a)–(k) hold exactly at the PF1000 row."""
    row = PF1000
    result = beam(row)
    speed = math.sqrt(
        2.0 * ELEMENTARY_CHARGE_C * row.diode_voltage_v / (2.0 * PROTON_MASS_KG)
    )
    assert result.beam_speed_m_s == pytest.approx(speed, rel=1e-15)
    flux = (
        FLUX_COEFFICIENT
        * 0.14
        / math.sqrt(2.0)
        * math.log(row.cathode_radius_m / row.minimum_radius_m)
        / row.minimum_radius_m**2
        * row.pinch_current_a**2
        / math.sqrt(row.diode_voltage_v)
    )
    assert result.flux_per_m2_s == pytest.approx(flux, rel=1e-14)
    energy = ELEMENTARY_CHARGE_C * row.diode_voltage_v
    area = math.pi * row.minimum_radius_m**2
    assert result.energy_flux_w_m2 == pytest.approx(flux * energy, rel=1e-14)
    assert result.power_flow_w == pytest.approx(flux * energy * area, rel=1e-14)
    assert result.current_density_a_m2 == pytest.approx(
        flux * ELEMENTARY_CHARGE_C, rel=1e-14
    )
    assert result.ion_current_a == pytest.approx(
        flux * ELEMENTARY_CHARGE_C * area, rel=1e-14
    )
    assert result.ions_per_s == pytest.approx(flux * area, rel=1e-14)
    assert result.fluence_per_m2 == pytest.approx(
        flux * row.pinch_duration_s, rel=1e-14
    )
    assert result.energy_fluence_j_m2 == pytest.approx(
        flux * row.pinch_duration_s * energy, rel=1e-14
    )
    assert result.ions_in_beam == pytest.approx(
        flux * row.pinch_duration_s * area, rel=1e-14
    )
    assert result.beam_energy_j == pytest.approx(
        flux * row.pinch_duration_s * area * energy, rel=1e-14
    )
    assert result.damage_factor_w_m2_sqrt_s == pytest.approx(
        flux * energy * math.sqrt(row.pinch_duration_s), rel=1e-14
    )
    assert len(result.to_record()) == 12


def test_flux_scales_with_current_squared_and_mass_charge_root() -> None:
    """Eq. (6): ``J_b ∝ I^2 / sqrt(M Z_eff)``."""
    base = fast_ion_beam(1.0e5, 0.001, 0.02, 5.0e4, 1.0e-8, 0.14, 2.0, 1.0)
    twice = fast_ion_beam(2.0e5, 0.001, 0.02, 5.0e4, 1.0e-8, 0.14, 2.0, 1.0)
    heavy = fast_ion_beam(1.0e5, 0.001, 0.02, 5.0e4, 1.0e-8, 0.14, 8.0, 1.0)
    assert twice.flux_per_m2_s == pytest.approx(4.0 * base.flux_per_m2_s, rel=1e-15)
    assert heavy.flux_per_m2_s == pytest.approx(0.5 * base.flux_per_m2_s, rel=1e-15)
    assert heavy.beam_speed_m_s == pytest.approx(0.5 * base.beam_speed_m_s, rel=1e-15)


@pytest.mark.parametrize(
    "field",
    [
        "pinch_current_a",
        "pinch_radius_m",
        "cathode_radius_m",
        "diode_voltage_v",
        "pinch_duration_s",
        "beam_energy_fraction",
        "beam_ion_mass_number",
        "beam_effective_charge",
    ],
)
def test_beam_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    values = {
        "pinch_current_a": 1.0e5,
        "pinch_radius_m": 0.001,
        "cathode_radius_m": 0.02,
        "diode_voltage_v": 5.0e4,
        "pinch_duration_s": 1.0e-8,
        "beam_energy_fraction": 0.14,
        "beam_ion_mass_number": 2.0,
        "beam_effective_charge": 1.0,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        fast_ion_beam(**values)


def test_beam_refuses_a_pinch_wider_than_the_cathode() -> None:
    """``ln(b / rp)`` needs ``rp < b``."""
    with pytest.raises(DeviceConfigurationError, match="smaller than cathode_radius_m"):
        fast_ion_beam(1.0e5, 0.02, 0.02, 5.0e4, 1.0e-8, 0.14, 2.0, 1.0)
