# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — level-0 physics test fixtures

"""Anchor rows and builders shared by the level-0 physics tests.

The anchor rows carry the parameter columns printed in Table 1 of
IAEA-TECDOC-1829 (Saw and Lee, p. 86) for four of the twelve machines the
source tabulates, so that the source's own printed outputs can serve as
anchors. Every row is a fixture that reproduces published numbers computed
by the source's fitted code; none is a description, measurement or
validation of any machine's behaviour, and no other value in this module
describes a real machine.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

from scpn_dense_plasma_focus_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
)
from scpn_dense_plasma_focus_core.parameters import BankAndFill, ElectrodeSet
from scpn_dense_plasma_focus_core.physics import ModelInputs, PinchState

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
FILL_TEMPERATURE_K = 300.0
SPECIFIC_HEAT_RATIO = 5.0 / 3.0
#: Declared D–D neutron-branch cross-section fixture (order of 10 mb).
CROSS_SECTION_M2 = 1.5e-30


@dataclass(frozen=True, slots=True)
class AnchorRow:
    """One column of TECDOC-1829 Table 1 in SI units plus its printed outputs."""

    name: str
    bank_energy_kj: float
    capacitance_f: float
    inductance_h: float
    resistance_ohm: float
    cathode_radius_m: float
    anode_radius_m: float
    anode_length_m: float
    charge_voltage_v: float
    fill_pressure_torr: float
    rise_time_s: float
    peak_current_a: float
    pinch_current_a: float
    minimum_radius_m: float
    maximum_length_m: float
    pinch_duration_s: float
    diode_voltage_v: float
    fluence_per_m2: float
    flux_per_m2_s: float
    energy_fluence_j_m2: float
    energy_flux_w_m2: float
    power_flow_w: float
    ions_in_beam: float
    beam_energy_j: float
    ion_current_a: float
    damage_factor: float
    ion_speed_m_s: float
    peak_axial_speed_m_s: float
    axial_mass_factor: float
    axial_current_factor: float
    radial_mass_factor: float
    radial_current_factor: float
    drive_factor: float


PF1000 = AnchorRow(
    "PF1000",
    486.0,
    1332.0e-6,
    33.0e-9,
    6.3e-3,
    0.160,
    0.116,
    0.600,
    27.0e3,
    3.5,
    10.4e-6,
    1846.0e3,
    862.0e3,
    0.0223,
    0.188,
    255.0e-9,
    126.0e3,
    5.75e20,
    2.3e27,
    1.16e7,
    4.56e13,
    7.14e10,
    899.0e15,
    18201.0,
    564.0e3,
    2.30e10,
    3.47e6,
    10.8e4,
    0.14,
    0.70,
    0.35,
    0.70,
    85.5,
)
NX3 = AnchorRow(
    "NX3",
    14.5,
    100.0e-6,
    50.0e-9,
    2.3e-3,
    0.052,
    0.026,
    0.160,
    17.0e3,
    11.0,
    3.51e-6,
    564.0e3,
    347.0e3,
    0.0040,
    0.040,
    46.0e-9,
    84.0e3,
    8.29e20,
    18.1e27,
    1.12e7,
    24.5e13,
    1.23e10,
    41.5e15,
    561.0,
    145.0e3,
    5.24e10,
    2.84e6,
    7.7e4,
    0.10,
    0.70,
    0.25,
    0.70,
    65.4,
)
INTI = AnchorRow(
    "INTI",
    3.4,
    30.0e-6,
    110.0e-9,
    12.0e-3,
    0.032,
    0.010,
    0.160,
    15.0e3,
    3.5,
    2.85e-6,
    180.0e3,
    122.0e3,
    0.0013,
    0.014,
    7.6e-9,
    74.1e3,
    2.14e20,
    28.1e27,
    0.25e7,
    33.4e13,
    0.18e10,
    1.15e15,
    13.6,
    24.1e3,
    2.91e10,
    2.66e6,
    9.5e4,
    0.08,
    0.70,
    0.16,
    0.70,
    102.0,
)
PF400J = AnchorRow(
    "PF400J",
    0.4,
    1.0e-6,
    40.0e-9,
    10.0e-3,
    0.016,
    0.006,
    0.017,
    28.0e3,
    6.6,
    0.31e-6,
    129.0e3,
    84.0e3,
    0.0009,
    0.008,
    5.1e-9,
    53.4e3,
    1.68e20,
    33.0e27,
    0.14e7,
    28.3e13,
    0.07e10,
    0.39e15,
    3.3,
    12.2e3,
    2.02e10,
    2.26e6,
    8.9e4,
    0.08,
    0.70,
    0.11,
    0.70,
    83.5,
)
ROWS = (PF1000, NX3, INTI, PF400J)


def configuration(row: AnchorRow = PF1000) -> DeviceConfiguration:
    """Return the validated configuration of one anchor row."""
    return DeviceConfiguration(
        identifier="dense_plasma_focus",
        electrodes=ElectrodeSet(
            anode_radius_m=row.anode_radius_m,
            cathode_radius_m=row.cathode_radius_m,
            anode_length_m=row.anode_length_m,
        ),
        bank=BankAndFill(
            bank_energy_kj=row.bank_energy_kj,
            peak_current_ma=row.peak_current_a / 1.0e6,
            fill_pressure_torr=row.fill_pressure_torr,
            deuterium_fill=True,
        ),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def inputs(row: AnchorRow = PF1000, /, **overrides: float) -> ModelInputs:
    """Return the model inputs of one anchor row (deuterium fill)."""
    values: dict[str, float] = {
        "bank_capacitance_f": row.capacitance_f,
        "bank_inductance_h": row.inductance_h,
        "bank_resistance_ohm": row.resistance_ohm,
        "charge_voltage_v": row.charge_voltage_v,
        "fill_molecular_mass_amu": 4.0,
        "fill_temperature_k": FILL_TEMPERATURE_K,
        "dissociation_number": 2.0,
        "specific_heat_ratio": SPECIFIC_HEAT_RATIO,
        "axial_mass_factor": row.axial_mass_factor,
        "axial_current_factor": row.axial_current_factor,
        "radial_mass_factor": row.radial_mass_factor,
        "radial_current_factor": row.radial_current_factor,
        "plasma_effective_charge": 1.0,
        "atomic_number": 1.0,
    }
    values.update(overrides)
    return ModelInputs(**values)


def pinch_state(row: AnchorRow = PF1000, /, **overrides: float) -> PinchState:
    """Return the declared pinch state of one anchor row (deuteron beam)."""
    values: dict[str, float] = {
        "pinch_current_a": row.pinch_current_a,
        "pinch_radius_m": row.minimum_radius_m,
        "pinch_length_m": row.maximum_length_m,
        "pinch_duration_s": row.pinch_duration_s,
        "diode_voltage_v": row.diode_voltage_v,
        "beam_energy_fraction": 0.14,
        "beam_ion_mass_number": 2.0,
        "beam_effective_charge": 1.0,
        "dd_neutron_cross_section_m2": CROSS_SECTION_M2,
    }
    values.update(overrides)
    return PinchState(**values)


def relative_gap(got: float, want: float) -> float:
    """Relative difference with the printed value as the scale."""
    return abs(got - want) / abs(want)


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)
