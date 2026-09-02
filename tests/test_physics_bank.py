# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — bank normalisation and fill state tests

"""Anchors, identities and refusals of the bank normalisation and fill state."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import ROWS, AnchorRow, relative_gap
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    BOLTZMANN_J_PER_K,
    MU0,
    PASCAL_PER_TORR,
    PROTON_MASS_KG,
    bank_normalisation,
    fill_state,
)


def normalisation(row: AnchorRow):  # type: ignore[no-untyped-def]
    """Evaluate the bank normalisation of one anchor row."""
    return bank_normalisation(
        row.capacitance_f,
        row.inductance_h,
        row.resistance_ohm,
        row.charge_voltage_v,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
    )


@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_bank_energy_and_rise_time_reproduce_table_1(row: AnchorRow) -> None:
    """``C0 V0^2 / 2`` and ``(pi/2) sqrt(L0 C0)`` match the printed columns.

    The table prints ``E0`` with two significant digits (one for the
    sub-kilojoule PF400J, whose 392 J reads ``0.4``), hence 2.5 %.
    """
    bank = normalisation(row)
    assert relative_gap(bank.bank_energy_j, row.bank_energy_kj * 1.0e3) <= 0.025
    assert relative_gap(bank.quarter_period_s, row.rise_time_s) <= 0.02


def test_closed_forms_and_scaling_parameters() -> None:
    """Every normalising quantity follows its definition."""
    bank = normalisation(ROWS[0])
    row = ROWS[0]
    assert bank.characteristic_time_s == math.sqrt(row.inductance_h * row.capacitance_f)
    assert bank.surge_impedance_ohm == math.sqrt(row.inductance_h / row.capacitance_f)
    assert (
        bank.characteristic_current_a == row.charge_voltage_v / bank.surge_impedance_ohm
    )
    assert bank.damping_ratio == row.resistance_ohm / bank.surge_impedance_ohm
    assert bank.log_radius_ratio == pytest.approx(
        math.log(row.cathode_radius_m / row.anode_radius_m), rel=1e-15
    )
    assert bank.axial_inductance_h == pytest.approx(
        MU0 / (2.0 * math.pi) * bank.log_radius_ratio * row.anode_length_m, rel=1e-15
    )
    assert bank.inductance_ratio == row.inductance_h / bank.axial_inductance_h
    assert set(bank.to_record()) == {
        "bank_energy_j",
        "characteristic_time_s",
        "surge_impedance_ohm",
        "characteristic_current_a",
        "quarter_period_s",
        "damping_ratio",
        "log_radius_ratio",
        "axial_inductance_h",
        "inductance_ratio",
    }


@pytest.mark.parametrize(
    "field",
    [
        "capacitance_f",
        "inductance_h",
        "resistance_ohm",
        "charge_voltage_v",
        "anode_radius_m",
        "cathode_radius_m",
        "anode_length_m",
    ],
)
def test_bank_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    row = ROWS[0]
    values = {
        "capacitance_f": row.capacitance_f,
        "inductance_h": row.inductance_h,
        "resistance_ohm": row.resistance_ohm,
        "charge_voltage_v": row.charge_voltage_v,
        "anode_radius_m": row.anode_radius_m,
        "cathode_radius_m": row.cathode_radius_m,
        "anode_length_m": row.anode_length_m,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        bank_normalisation(**values)


def test_bank_refuses_unordered_radii() -> None:
    """A cathode at or inside the anode is refused."""
    with pytest.raises(DeviceConfigurationError, match="strictly greater"):
        bank_normalisation(1.0e-6, 1.0e-8, 1.0e-3, 1.0e4, 0.02, 0.02, 0.1)


def test_fill_state_is_the_ideal_gas_of_the_declared_molecule() -> None:
    """Pressure, mass, densities follow the ideal-gas definition."""
    fill = fill_state(3.5, 4.0, 300.0)
    assert fill.pressure_pa == 3.5 * PASCAL_PER_TORR
    assert fill.molecular_mass_kg == 4.0 * PROTON_MASS_KG
    assert fill.molecule_density_per_m3 == fill.pressure_pa / (
        BOLTZMANN_J_PER_K * 300.0
    )
    assert (
        fill.mass_density_kg_m3 == fill.molecule_density_per_m3 * fill.molecular_mass_kg
    )
    assert fill.mass_density_kg_m3 == pytest.approx(7.48e-4, rel=0.01)
    assert set(fill.to_record()) == {
        "pressure_pa",
        "molecular_mass_kg",
        "molecule_density_per_m3",
        "mass_density_kg_m3",
    }
    assert fill_state(7.0, 4.0, 300.0).mass_density_kg_m3 == pytest.approx(
        2.0 * fill.mass_density_kg_m3, rel=1e-15
    )


@pytest.mark.parametrize(
    "field", ["pressure_torr", "molecular_mass_amu", "temperature_k"]
)
def test_fill_refuses_non_positive_inputs(field: str) -> None:
    """Every fill argument is validated fail-closed."""
    values = {"pressure_torr": 3.5, "molecular_mass_amu": 4.0, "temperature_k": 300.0}
    values[field] = -1.0
    with pytest.raises(DeviceConfigurationError, match=field):
        fill_state(**values)
