# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — neutron estimate tests

"""Calibration anchor, the source's own identity, scalings and refusals."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import PF1000
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    BEAM_TARGET_CONSTANT,
    SCALING_RANGE_A,
    NeutronEstimates,
    beam_target_yield,
    fast_ion_beam,
    scaling_law_applies,
    scaling_law_yield,
)


def test_scaling_law_reproduces_its_own_calibration_point() -> None:
    """``9e10 * 0.5^3.8`` lands within 10 % of the printed ``7e9`` at 0.5 MA."""
    value = scaling_law_yield(5.0e5)
    assert value == pytest.approx(9.0e10 * 0.5**3.8, rel=1e-13)
    assert abs(value - 7.0e9) / 7.0e9 <= 0.10
    low, high = SCALING_RANGE_A
    assert scaling_law_yield(low) < scaling_law_yield(high)


@pytest.mark.parametrize("current", [0.0, 5.0e4, 1.1e6, math.inf])
def test_scaling_law_is_refused_outside_its_stated_range(current: float) -> None:
    """The fit is stated for 0.1–1 MA; anything else is refused."""
    with pytest.raises(DeviceConfigurationError, match="pinch_current_a"):
        scaling_law_yield(current)


def test_beam_target_yield_closed_form_and_the_sources_identity() -> None:
    """Eq. (50) with ``C_n``; TECDOC eq. (2) with the beam module agrees to 1 %."""
    row = PF1000
    n_i = 1.0e24
    sigma = 1.5e-30
    direct = beam_target_yield(
        n_i,
        row.pinch_current_a,
        row.maximum_length_m,
        row.cathode_radius_m,
        row.minimum_radius_m,
        sigma,
        row.diode_voltage_v,
    )
    expected = (
        BEAM_TARGET_CONSTANT
        * n_i
        * row.pinch_current_a**2
        * row.maximum_length_m**2
        * math.log(row.cathode_radius_m / row.minimum_radius_m)
        * sigma
        / math.sqrt(row.diode_voltage_v)
    )
    assert direct == pytest.approx(expected, rel=1e-14)
    # TECDOC eq. (2): Y = J_b tau sigma n_i pi rp^2 z_p with tau = 1e-6 z_p,
    # fe = 0.14, M = 2, Z_eff = 1 reproduces eq. (1) up to the 8.5 / 8.54
    # rounding of the two printed constants.
    tau = 1.0e-6 * row.maximum_length_m
    beam = fast_ion_beam(
        row.pinch_current_a,
        row.minimum_radius_m,
        row.cathode_radius_m,
        row.diode_voltage_v,
        tau,
        0.14,
        2.0,
        1.0,
    )
    via_beam = (
        beam.fluence_per_m2
        * sigma
        * n_i
        * math.pi
        * row.minimum_radius_m**2
        * row.maximum_length_m
    )
    assert abs(via_beam - direct) / direct <= 0.01


def test_beam_target_yield_scales_linearly_in_density_and_cross_section() -> None:
    """Eq. (50): ``Y ∝ n_i sigma``."""
    base = beam_target_yield(1.0e23, 5.0e5, 0.05, 0.05, 0.005, 1.0e-30, 1.0e5)
    assert beam_target_yield(2.0e23, 5.0e5, 0.05, 0.05, 0.005, 2.0e-30, 1.0e5) == (
        pytest.approx(4.0 * base, rel=1e-15)
    )


@pytest.mark.parametrize(
    "field",
    [
        "ion_density_per_m3",
        "pinch_current_a",
        "pinch_length_m",
        "cathode_radius_m",
        "pinch_radius_m",
        "cross_section_m2",
        "diode_voltage_v",
    ],
)
def test_beam_target_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    values = {
        "ion_density_per_m3": 1.0e23,
        "pinch_current_a": 5.0e5,
        "pinch_length_m": 0.05,
        "cathode_radius_m": 0.05,
        "pinch_radius_m": 0.005,
        "cross_section_m2": 1.0e-30,
        "diode_voltage_v": 1.0e5,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        beam_target_yield(**values)


def test_beam_target_refuses_unordered_radii_and_records() -> None:
    """``rp >= b`` is refused; the estimates record projects both values."""
    with pytest.raises(DeviceConfigurationError, match="smaller than cathode_radius_m"):
        beam_target_yield(1.0e23, 5.0e5, 0.05, 0.005, 0.005, 1.0e-30, 1.0e5)
    record = NeutronEstimates(beam_target_yield=1.0, scaling_law_yield=2.0).to_record()
    assert record == {
        "beam_target_yield": 1.0,
        "scaling_law_yield": 2.0,
        "scaling_law_applicable": True,
    }
    absent = NeutronEstimates(beam_target_yield=1.0, scaling_law_yield=None).to_record()
    assert absent["scaling_law_yield"] is None
    assert absent["scaling_law_applicable"] is False
    assert scaling_law_applies(5.0e5)
    assert not scaling_law_applies(8.4e4)
    with pytest.raises(DeviceConfigurationError, match="pinch_current_a"):
        scaling_law_applies(0.0)
