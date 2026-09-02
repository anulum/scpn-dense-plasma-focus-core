# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — radial-phase, slug and rule-of-thumb tests

"""Anchors, identities and refusals of the radial-phase closed forms."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import NX3, PF400J, ROWS, AnchorRow
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    MU0,
    REFLECTED_SHOCK_FRACTION,
    RULE_MAX_LENGTH_RATIO_BOUNDS,
    RULE_MIN_RADIUS_RATIO_BOUNDS,
    RadialCharacteristics,
    pinch_geometry_estimate,
    radial_characteristics,
    require_specific_heat_ratio,
    slug_relations,
)

GAMMA = 5.0 / 3.0


def radial(row: AnchorRow, gamma: float = GAMMA) -> RadialCharacteristics:
    """Evaluate the radial characteristics with synthetic upstream values."""
    log_ratio = math.log(row.cathode_radius_m / row.anode_radius_m)
    return radial_characteristics(
        3.0e-6,
        5.0e6,
        row.anode_radius_m,
        row.cathode_radius_m,
        row.anode_length_m,
        log_ratio,
        0.85,
        7.5e-4,
        row.axial_current_factor,
        row.radial_mass_factor,
        gamma,
    )


def test_geometric_speed_ratio_reproduces_the_printed_typical_value() -> None:
    """Eq. (28) at ``c = 3.4``, ``gamma = 5/3`` evaluates to the printed ~2.5."""
    result = radial_characteristics(
        3.0e-6, 5.0e6, 0.01, 0.034, 0.16, math.log(3.4), 0.85, 7.5e-4, 0.7, 0.16, GAMMA
    )
    assert result.geometric_speed_ratio == pytest.approx(2.40, abs=0.01)
    assert abs(result.geometric_speed_ratio - 2.5) / 2.5 <= 0.05


def test_radial_closed_forms_follow_their_definitions() -> None:
    """``vr = a / tr``, ``alpha1 = ta / tr``, ``beta1 = beta / (F ln c)`` hold."""
    row = ROWS[0]
    result = radial(row)
    log_ratio = math.log(row.cathode_radius_m / row.anode_radius_m)
    expected_transit = (
        4.0
        * math.pi
        / math.sqrt(MU0 * (GAMMA + 1.0))
        * math.sqrt(row.radial_mass_factor)
        / row.axial_current_factor
        * row.anode_radius_m
        / ((5.0e6 / row.anode_radius_m) / math.sqrt(7.5e-4))
    )
    assert result.radial_transit_time_s == pytest.approx(expected_transit, rel=1e-14)
    assert (
        result.characteristic_radial_speed_m_s
        == row.anode_radius_m / result.radial_transit_time_s
    )
    assert result.alpha1 == 3.0e-6 / result.radial_transit_time_s
    assert result.aspect_ratio == row.anode_length_m / row.anode_radius_m
    assert result.beta1 == 0.85 / (result.aspect_ratio * log_ratio)
    ratio = row.cathode_radius_m / row.anode_radius_m
    assert result.geometric_speed_ratio == pytest.approx(
        math.sqrt((ratio**2 - 1.0) * (GAMMA + 1.0) / (4.0 * log_ratio)), rel=1e-15
    )
    assert set(result.to_record()) == {
        "radial_transit_time_s",
        "characteristic_radial_speed_m_s",
        "alpha1",
        "aspect_ratio",
        "beta1",
        "geometric_speed_ratio",
    }


@pytest.mark.parametrize(
    "field",
    [
        "axial_transit_time_s",
        "characteristic_current_a",
        "anode_radius_m",
        "cathode_radius_m",
        "anode_length_m",
        "log_radius_ratio",
        "inductance_ratio",
        "mass_density_kg_m3",
        "axial_current_factor",
        "radial_mass_factor",
    ],
)
def test_radial_refuses_non_positive_inputs(field: str) -> None:
    """Every argument is validated fail-closed."""
    values = {
        "axial_transit_time_s": 3.0e-6,
        "characteristic_current_a": 5.0e6,
        "anode_radius_m": 0.116,
        "cathode_radius_m": 0.16,
        "anode_length_m": 0.6,
        "log_radius_ratio": 0.32,
        "inductance_ratio": 0.85,
        "mass_density_kg_m3": 7.5e-4,
        "axial_current_factor": 0.7,
        "radial_mass_factor": 0.35,
        "specific_heat_ratio": GAMMA,
    }
    values[field] = 0.0
    with pytest.raises(DeviceConfigurationError, match=field):
        radial_characteristics(**values)


@pytest.mark.parametrize("gamma", [1.0, 0.5, math.nan])
def test_specific_heat_ratio_must_exceed_one(gamma: float) -> None:
    """``gamma <= 1`` and non-finite values are refused."""
    with pytest.raises(DeviceConfigurationError, match="specific_heat_ratio"):
        require_specific_heat_ratio(gamma)
    with pytest.raises(DeviceConfigurationError, match="specific_heat_ratio"):
        radial(ROWS[0], gamma)


def test_slug_relations_signs_and_closed_forms() -> None:
    """Shock inward, elongation and reflected shock outward, eqs. (14)–(34)."""
    slug = slug_relations(8.62e5, 0.0223, 7.5e-4, 0.7, 0.35, GAMMA, 4.0, 2.0, 1.0)
    expected_shock = (
        -math.sqrt(MU0 * (GAMMA + 1.0) / 7.5e-4)
        * (0.7 / math.sqrt(0.35))
        * (8.62e5 / (4.0 * math.pi * 0.0223))
    )
    assert slug.shock_speed_m_s == pytest.approx(expected_shock, rel=1e-14)
    assert slug.shock_speed_m_s < 0.0
    assert slug.elongation_speed_m_s == pytest.approx(
        -(2.0 / (GAMMA + 1.0)) * slug.shock_speed_m_s, rel=1e-15
    )
    assert slug.reflected_shock_speed_m_s == pytest.approx(
        -REFLECTED_SHOCK_FRACTION * slug.shock_speed_m_s, rel=1e-15
    )
    departure = 2.0 * (1.0 + 1.0)
    assert slug.shock_temperature_k == pytest.approx(
        4.0
        / (8314.462618 * departure)
        * 2.0
        * (GAMMA - 1.0)
        / (GAMMA + 1.0) ** 2
        * slug.shock_speed_m_s**2,
        rel=1e-14,
    )
    assert slug.current_a == 8.62e5
    assert slug.piston_radius_m == 0.0223
    assert set(slug.to_record()) == {
        "current_a",
        "piston_radius_m",
        "shock_speed_m_s",
        "elongation_speed_m_s",
        "shock_temperature_k",
        "reflected_shock_speed_m_s",
    }


def test_slug_shock_speed_scales_with_current_and_inverse_radius() -> None:
    """Eq. (14): ``drs/dt ∝ I / rp``."""
    base = slug_relations(1.0e5, 0.01, 7.5e-4, 0.7, 0.35, GAMMA, 4.0, 2.0, 1.0)
    twice = slug_relations(2.0e5, 0.02, 7.5e-4, 0.7, 0.35, GAMMA, 4.0, 2.0, 1.0)
    assert twice.shock_speed_m_s == pytest.approx(base.shock_speed_m_s, rel=1e-15)
    neutral = slug_relations(1.0e5, 0.01, 7.5e-4, 0.7, 0.35, GAMMA, 4.0, 2.0, 0.0)
    assert neutral.shock_temperature_k == pytest.approx(
        2.0 * base.shock_temperature_k, rel=1e-15
    )


@pytest.mark.parametrize(
    "field",
    [
        "current_a",
        "piston_radius_m",
        "mass_density_kg_m3",
        "axial_current_factor",
        "radial_mass_factor",
        "specific_heat_ratio",
        "molecular_mass_amu",
        "dissociation_number",
        "plasma_effective_charge",
    ],
)
def test_slug_refuses_invalid_inputs(field: str) -> None:
    """Every argument is validated; a negative effective charge is refused."""
    values = {
        "current_a": 8.62e5,
        "piston_radius_m": 0.0223,
        "mass_density_kg_m3": 7.5e-4,
        "axial_current_factor": 0.7,
        "radial_mass_factor": 0.35,
        "specific_heat_ratio": GAMMA,
        "molecular_mass_amu": 4.0,
        "dissociation_number": 2.0,
        "plasma_effective_charge": 1.0,
    }
    values[field] = -1.0
    with pytest.raises(DeviceConfigurationError, match=field):
        slug_relations(**values)
    if field == "plasma_effective_charge":
        values[field] = math.nan
        with pytest.raises(DeviceConfigurationError, match=field):
            slug_relations(**values)


def test_rule_of_thumb_geometry_and_its_printed_spread() -> None:
    """The scaled estimate and the tabulated ratios of two small machines."""
    estimate = pinch_geometry_estimate(0.026)
    assert estimate.minimum_radius_m == pytest.approx(0.15 * 0.026, rel=1e-15)
    assert estimate.maximum_length_m == pytest.approx(1.5 * 0.026, rel=1e-15)
    assert estimate.shock_transit_time_s == pytest.approx(5.0e-6 * 0.026, rel=1e-15)
    assert estimate.pinch_lifetime_s == pytest.approx(1.0e-6 * 0.026, rel=1e-15)
    record = estimate.to_record()
    assert record["bounds"]["minimum_radius_ratio"] == list(
        RULE_MIN_RADIUS_RATIO_BOUNDS
    )
    assert record["bounds"]["maximum_length_ratio"] == list(
        RULE_MAX_LENGTH_RATIO_BOUNDS
    )
    assert record["anode_radius_m"] == 0.026
    for row in (NX3, PF400J):
        ratio = row.minimum_radius_m / row.anode_radius_m
        low, high = RULE_MIN_RADIUS_RATIO_BOUNDS
        assert low <= ratio <= high, row.name
    low, high = RULE_MAX_LENGTH_RATIO_BOUNDS
    assert low <= NX3.maximum_length_m / NX3.anode_radius_m <= high
    with pytest.raises(DeviceConfigurationError, match="anode_radius_m"):
        pinch_geometry_estimate(0.0)
