# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — pinch-phase closed-form tests

"""Identities, scalings, branches and refusals of the pinch-phase closed forms.

No printed anchor exists for these quantities (see the module docstring
and the evidence record); the tests prove the closed forms and the
self-absorption branches, nothing more.
"""

from __future__ import annotations

import math

import pytest

from physics_fixtures import pinch_state
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    BOLTZMANN_J_PER_K,
    ELEMENTARY_CHARGE_C,
    MU0,
    PinchRadiation,
    PinchState,
    diode_voltage_rule,
    pinch_radiation,
)
from scpn_dense_plasma_focus_core.physics.constants import INV_E

DENSE = {
    "pinch_current_a": 8.62e5,
    "pinch_radius_m": 0.0223,
    "pinch_length_m": 0.188,
    "anode_radius_m": 0.116,
    "molecule_density_per_m3": 1.1266e23,
    "axial_current_factor": 0.7,
    "radial_mass_factor": 0.35,
    "dissociation_number": 2.0,
    "plasma_effective_charge": 1.0,
    "atomic_number": 1.0,
}
SPARSE = {**DENSE, "molecule_density_per_m3": 1.0e18}


def radiation(**overrides: float) -> PinchRadiation:
    """Evaluate the dense fixture with overrides."""
    return pinch_radiation(**{**DENSE, **overrides})


def test_density_temperature_and_resistance_follow_the_closed_forms() -> None:
    """Eqs. (43), (41), (40), (39), (42), (44) hold at the dense fixture."""
    result = radiation()
    ratio = DENSE["anode_radius_m"] / DENSE["pinch_radius_m"]
    assert result.ion_density_per_m3 == pytest.approx(
        DENSE["molecule_density_per_m3"] * 0.35 * ratio**2, rel=1e-15
    )
    sheath = 8.62e5 * 0.7
    departure = 2.0 * 2.0
    expected_t = (
        MU0
        * sheath**2
        / (
            8.0
            * math.pi**2
            * BOLTZMANN_J_PER_K
            * departure
            * DENSE["molecule_density_per_m3"]
            * 0.116**2
            * 0.35
        )
    )
    assert result.bennett_temperature_k == pytest.approx(expected_t, rel=1e-14)
    assert result.temperature_ev == pytest.approx(
        expected_t * BOLTZMANN_J_PER_K / ELEMENTARY_CHARGE_C, rel=1e-15
    )
    area = math.pi * 0.0223**2
    assert result.spitzer_resistance_ohm == pytest.approx(
        1290.0 * 1.0 * 0.188 / (area * expected_t**1.5), rel=1e-14
    )
    assert result.joule_power_w == pytest.approx(
        result.spitzer_resistance_ohm * sheath**2, rel=1e-15
    )
    n_i = result.ion_density_per_m3
    assert result.bremsstrahlung_power_w == pytest.approx(
        -1.6e-40 * n_i**2 * area * 0.188 * math.sqrt(expected_t), rel=1e-14
    )
    assert result.line_power_w == pytest.approx(
        -4.6e-31 * n_i**2 * area * 0.188 / expected_t, rel=1e-14
    )
    assert result.surface_line_power_w == pytest.approx(
        -4.62e-16 * 0.0223 * 0.188 * expected_t**4, rel=1e-14
    )
    assert result.joule_power_w > 0.0
    assert result.bremsstrahlung_power_w < 0.0
    assert result.line_power_w < 0.0
    assert result.surface_line_power_w < 0.0
    assert set(result.to_record()) == {
        "ion_density_per_m3",
        "bennett_temperature_k",
        "temperature_ev",
        "spitzer_resistance_ohm",
        "joule_power_w",
        "bremsstrahlung_power_w",
        "line_power_w",
        "photonic_excitation_number",
        "absorption_factor",
        "surface_line_power_w",
        "effective_line_power_w",
        "net_power_w",
    }


def test_dense_state_is_fully_absorbed_and_uses_the_surface_term() -> None:
    """A very opaque column: ``A`` underflows to exactly zero, eq. (48) applies."""
    result = radiation()
    assert result.absorption_factor == 0.0
    assert result.photonic_excitation_number > 1.0e3
    assert result.effective_line_power_w == result.surface_line_power_w
    assert result.net_power_w == (
        result.joule_power_w
        + result.bremsstrahlung_power_w
        + result.surface_line_power_w
    )


def test_sparse_state_is_transparent_and_uses_the_volumetric_term() -> None:
    """A tenuous column: ``A`` near one, eq. (44) scaled by ``A`` applies."""
    result = pinch_radiation(**SPARSE)
    assert INV_E < result.absorption_factor <= 1.0
    assert (
        result.effective_line_power_w == result.absorption_factor * result.line_power_w
    )
    assert result.net_power_w == (
        result.joule_power_w
        + result.bremsstrahlung_power_w
        + result.effective_line_power_w
    )


def test_absorption_factor_is_monotone_in_density() -> None:
    """More particles absorb more: ``A`` never increases with density."""
    previous = 1.0
    for exponent in range(18, 25):
        current = pinch_radiation(
            **{**DENSE, "molecule_density_per_m3": 10.0**exponent}
        ).absorption_factor
        assert 0.0 <= current <= previous
        previous = current


def test_bennett_temperature_scales_with_current_squared() -> None:
    """Eq. (41): ``T ∝ I^2``."""
    single = radiation(pinch_current_a=2.0e5).bennett_temperature_k
    double = radiation(pinch_current_a=4.0e5).bennett_temperature_k
    assert double == pytest.approx(4.0 * single, rel=1e-15)


@pytest.mark.parametrize("field", list(DENSE))
def test_pinch_radiation_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    with pytest.raises(DeviceConfigurationError, match=field):
        pinch_radiation(**{**DENSE, field: 0.0})


def test_pinch_state_validation_and_record() -> None:
    """Every declared value is validated; the fraction is bounded by one."""
    state = pinch_state()
    assert set(state.to_record()) == {
        "pinch_current_a",
        "pinch_radius_m",
        "pinch_length_m",
        "pinch_duration_s",
        "diode_voltage_v",
        "beam_energy_fraction",
        "beam_ion_mass_number",
        "beam_effective_charge",
        "dd_neutron_cross_section_m2",
    }
    for field in state.to_record():
        with pytest.raises(DeviceConfigurationError, match=field):
            pinch_state(**{field: 0.0})
    with pytest.raises(DeviceConfigurationError, match="beam_energy_fraction"):
        pinch_state(beam_energy_fraction=1.5)
    assert isinstance(pinch_state(beam_energy_fraction=1.0), PinchState)


def test_diode_voltage_rule() -> None:
    """``U = 3 V_max`` by default; the multiplier is declared and validated."""
    assert diode_voltage_rule(4.2e4) == 3.0 * 4.2e4
    assert diode_voltage_rule(4.2e4, 1.0) == 4.2e4
    with pytest.raises(DeviceConfigurationError, match="peak_induced_voltage_v"):
        diode_voltage_rule(0.0)
    with pytest.raises(DeviceConfigurationError, match="multiplier"):
        diode_voltage_rule(4.2e4, 0.0)
