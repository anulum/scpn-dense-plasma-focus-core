# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — native kernel parity tests

"""Bit-exact parity between the Python floor and the native kernels.

The native module is an optional build (rust/, distribution
scpn-dense-plasma-focus-native); these tests are skipped hermetically when
it is absent and compare float64 bit patterns, never tolerances, when
present. Every parameter set is a fixture row of the source's table.
"""

from __future__ import annotations

import pytest

from physics_fixtures import ROWS, AnchorRow, bits, configuration, inputs, pinch_state
from scpn_dense_plasma_focus_core.physics import (
    beam_target_yield,
    level0_physics,
    scaling_law_yield,
)

native = pytest.importorskip("scpn_dense_plasma_focus_native")


@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_every_kernel_is_bit_exact_on_the_anchor_rows(row: AnchorRow) -> None:
    """Each native tuple reproduces the floor's record fields bit for bit."""
    model = inputs(row)
    state = pinch_state(row)
    record = level0_physics(configuration(row), model, state)
    bank = native.bank_normalisation(
        model.bank_capacitance_f,
        model.bank_inductance_h,
        model.bank_resistance_ohm,
        model.charge_voltage_v,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
    )
    assert [bits(v) for v in bank] == [
        bits(v) for v in record.bank.to_record().values()
    ]
    fill = native.fill_state(row.fill_pressure_torr, 4.0, model.fill_temperature_k)
    assert [bits(v) for v in fill] == [
        bits(v) for v in record.fill.to_record().values()
    ]
    axial = native.axial_characteristics(
        record.bank.characteristic_time_s,
        record.bank.characteristic_current_a,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
        record.bank.log_radius_ratio,
        record.fill.mass_density_kg_m3,
        model.axial_mass_factor,
        model.axial_current_factor,
        row.peak_current_a,
    )
    assert [bits(v) for v in axial] == [
        bits(record.axial.axial_transit_time_s),
        bits(record.axial.alpha),
        bits(record.axial.characteristic_axial_speed_m_s),
        bits(record.axial.terminal_sheath_speed_m_s),
    ]
    radial = native.radial_characteristics(
        record.axial.axial_transit_time_s,
        record.bank.characteristic_current_a,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
        record.bank.log_radius_ratio,
        record.bank.inductance_ratio,
        record.fill.mass_density_kg_m3,
        model.axial_current_factor,
        model.radial_mass_factor,
        model.specific_heat_ratio,
    )
    assert [bits(v) for v in radial] == [
        bits(v) for v in record.radial.to_record().values()
    ]
    slug = native.slug_relations(
        state.pinch_current_a,
        state.pinch_radius_m,
        record.fill.mass_density_kg_m3,
        model.axial_current_factor,
        model.radial_mass_factor,
        model.specific_heat_ratio,
        model.fill_molecular_mass_amu,
        model.dissociation_number,
        model.plasma_effective_charge,
    )
    assert [bits(v) for v in slug] == [
        bits(record.slug.shock_speed_m_s),
        bits(record.slug.elongation_speed_m_s),
        bits(record.slug.shock_temperature_k),
        bits(record.slug.reflected_shock_speed_m_s),
    ]
    geometry = native.pinch_geometry_estimate(row.anode_radius_m)
    assert [bits(v) for v in geometry] == [
        bits(record.geometry.minimum_radius_m),
        bits(record.geometry.maximum_length_m),
        bits(record.geometry.shock_transit_time_s),
        bits(record.geometry.pinch_lifetime_s),
    ]
    pinch = native.pinch_radiation(
        state.pinch_current_a,
        state.pinch_radius_m,
        state.pinch_length_m,
        row.anode_radius_m,
        record.fill.molecule_density_per_m3,
        model.axial_current_factor,
        model.radial_mass_factor,
        model.dissociation_number,
        model.plasma_effective_charge,
        model.atomic_number,
    )
    assert [bits(v) for v in pinch] == [
        bits(v) for v in record.pinch.to_record().values()
    ]
    beam = native.fast_ion_beam(
        state.pinch_current_a,
        state.pinch_radius_m,
        row.cathode_radius_m,
        state.diode_voltage_v,
        state.pinch_duration_s,
        state.beam_energy_fraction,
        state.beam_ion_mass_number,
        state.beam_effective_charge,
    )
    assert [bits(v) for v in beam] == [
        bits(v) for v in record.beam.to_record().values()
    ]
    assert bits(
        native.beam_target_yield(
            record.pinch.ion_density_per_m3,
            state.pinch_current_a,
            state.pinch_length_m,
            row.cathode_radius_m,
            state.pinch_radius_m,
            state.dd_neutron_cross_section_m2,
            state.diode_voltage_v,
        )
    ) == bits(record.neutron.beam_target_yield)
    if record.neutron.scaling_law_yield is None:
        with pytest.raises(ValueError, match="stated for"):
            native.scaling_law_yield(state.pinch_current_a)
    else:
        assert bits(native.scaling_law_yield(state.pinch_current_a)) == bits(
            record.neutron.scaling_law_yield
        )


def test_transparent_pinch_branch_is_bit_exact() -> None:
    """The volumetric self-absorption branch agrees bit for bit as well."""
    from scpn_dense_plasma_focus_core.physics import pinch_radiation

    arguments = (8.62e5, 0.0223, 0.188, 0.116, 1.0e18, 0.7, 0.35, 2.0, 1.0, 1.0)
    floor = pinch_radiation(*arguments)
    assert 0.5 < floor.absorption_factor <= 1.0
    assert [bits(v) for v in native.pinch_radiation(*arguments)] == [
        bits(v) for v in floor.to_record().values()
    ]


def test_native_refusals_mirror_the_floor() -> None:
    """Refusals of the native bindings are ValueError with the floor's message."""
    with pytest.raises(ValueError, match="strictly greater"):
        native.bank_normalisation(1.0e-6, 1.0e-8, 1.0e-3, 1.0e4, 0.02, 0.02, 0.1)
    with pytest.raises(ValueError, match="smaller than cathode_radius_m"):
        native.fast_ion_beam(1.0e5, 0.02, 0.02, 5.0e4, 1.0e-8, 0.14, 2.0, 1.0)
    with pytest.raises(ValueError, match="smaller than cathode_radius_m"):
        native.beam_target_yield(1.0e23, 5.0e5, 0.05, 0.005, 0.005, 1.0e-30, 1.0e5)
    with pytest.raises(ValueError, match="stated for"):
        native.scaling_law_yield(5.0e4)
    with pytest.raises(ValueError, match="stated for"):
        scaling_law_yield(5.0e4)
    with pytest.raises(ValueError, match="smaller than cathode_radius_m"):
        beam_target_yield(1.0e23, 5.0e5, 0.05, 0.005, 0.005, 1.0e-30, 1.0e5)
