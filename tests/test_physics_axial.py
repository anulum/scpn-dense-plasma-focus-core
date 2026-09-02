# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — axial-phase characteristic tests

"""Anchors, identities, scalings and refusals of the axial characteristics."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import ROWS, AnchorRow, relative_gap
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    MU0,
    AxialCharacteristics,
    axial_characteristics,
    bank_normalisation,
    fill_state,
)


def axial(row: AnchorRow, drive_current_a: float | None = None) -> AxialCharacteristics:
    """Evaluate the axial characteristics of one anchor row."""
    bank = bank_normalisation(
        row.capacitance_f,
        row.inductance_h,
        row.resistance_ohm,
        row.charge_voltage_v,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
    )
    fill = fill_state(row.fill_pressure_torr, 4.0, 300.0)
    return axial_characteristics(
        bank.characteristic_time_s,
        bank.characteristic_current_a,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
        bank.log_radius_ratio,
        fill.mass_density_kg_m3,
        row.axial_mass_factor,
        row.axial_current_factor,
        row.peak_current_a if drive_current_a is None else drive_current_a,
    )


@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_terminal_speed_at_peak_current_reproduces_peak_axial_speed(
    row: AnchorRow,
) -> None:
    """``v_inf(I_peak)`` lands within 15 % of the printed peak axial speed.

    The closed form overestimates every row by 7–14 % (the fitted peak
    speed is not attained exactly at peak current); the tolerance and the
    sign of the deviation are the declared evidence, not a claim.
    """
    result = axial(row)
    gap = relative_gap(result.terminal_sheath_speed_m_s, row.peak_axial_speed_m_s)
    assert gap <= 0.15, (row.name, gap)
    assert result.terminal_sheath_speed_m_s > row.peak_axial_speed_m_s


def test_transit_time_speed_and_alpha_follow_their_definitions() -> None:
    """``va = z0 / ta``, ``alpha = t0 / ta`` and eq. (5) hold exactly."""
    row = ROWS[0]
    result = axial(row)
    bank = bank_normalisation(
        row.capacitance_f,
        row.inductance_h,
        row.resistance_ohm,
        row.charge_voltage_v,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
    )
    fill = fill_state(row.fill_pressure_torr, 4.0, 300.0)
    ratio = row.cathode_radius_m / row.anode_radius_m
    expected_transit = (
        math.sqrt(4.0 * math.pi**2 * (ratio**2 - 1.0) / (MU0 * bank.log_radius_ratio))
        * math.sqrt(row.axial_mass_factor)
        / row.axial_current_factor
        * row.anode_length_m
        / (
            (bank.characteristic_current_a / row.anode_radius_m)
            / math.sqrt(fill.mass_density_kg_m3)
        )
    )
    assert result.axial_transit_time_s == pytest.approx(expected_transit, rel=1e-14)
    assert (
        result.characteristic_axial_speed_m_s
        == row.anode_length_m / result.axial_transit_time_s
    )
    assert result.alpha == bank.characteristic_time_s / result.axial_transit_time_s
    assert result.drive_current_a == row.peak_current_a
    assert set(result.to_record()) == {
        "axial_transit_time_s",
        "alpha",
        "characteristic_axial_speed_m_s",
        "drive_current_a",
        "terminal_sheath_speed_m_s",
    }


def test_terminal_speed_is_linear_in_the_drive_current() -> None:
    """Eq. (1) at rest gives ``v_inf ∝ I``."""
    row = ROWS[1]
    single = axial(row, 2.0e5).terminal_sheath_speed_m_s
    double = axial(row, 4.0e5).terminal_sheath_speed_m_s
    assert double == pytest.approx(2.0 * single, rel=1e-15)


@pytest.mark.parametrize(
    "field",
    [
        "characteristic_time_s",
        "characteristic_current_a",
        "anode_radius_m",
        "cathode_radius_m",
        "anode_length_m",
        "log_radius_ratio",
        "mass_density_kg_m3",
        "axial_mass_factor",
        "axial_current_factor",
        "drive_current_a",
    ],
)
def test_axial_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    values = {
        "characteristic_time_s": 6.6e-6,
        "characteristic_current_a": 5.4e6,
        "anode_radius_m": 0.116,
        "cathode_radius_m": 0.16,
        "anode_length_m": 0.6,
        "log_radius_ratio": 0.32,
        "mass_density_kg_m3": 7.5e-4,
        "axial_mass_factor": 0.14,
        "axial_current_factor": 0.7,
        "drive_current_a": 1.8e6,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        axial_characteristics(**values)
