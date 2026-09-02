# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — radial (slug) phase characteristic quantities

"""Characteristic quantities and instantaneous relations of the radial phase.

The Lee model replaces the snowplow by a slug model in the radial phase
(S. Lee, J. Fusion Energ. 33 (2014) 319–335): a shock front driven by the
magnetic piston at speed
``drs/dt = -[mu0 (gamma + 1) / rho0]^(1/2) (fc / sqrt(fmr)) I / (4 pi rp)``
(eq. 14), an axial elongation ``dzf/dt = -(2 / (gamma + 1)) drs/dt``
(eq. 15), the shocked-gas temperature
``T = (M / (R0 D)) 2 (gamma - 1) / (gamma + 1)^2 (drs/dt)^2`` (eq. 32,
``D = DN (1 + Z)``), and a reflected shock at ``0.3`` of the on-axis
shock speed (eq. 34). Its normalisation yields the characteristic radial
transit time ``tr`` (eq. 26), the speed ``vr = a / tr`` (eq. 27), the
scaling parameters ``alpha1 = ta / tr`` (eq. 25) and
``beta1 = beta / (F ln c)`` with ``F = z0 / a`` (eq. 24), and the
geometric ratio ``vr / va = [(c^2 - 1)(gamma + 1) / (4 ln c)]^(1/2)``
(eq. 28, stated for equal mass factors; the review prints "typically 2.5"
for ``c ~ 3.4``, ``gamma = 5/3``, which evaluates to 2.40). The
rule-of-thumb pinch geometry of the same author (ICTP 2168-10 (2012),
Table 3: ``rmin = 0.15 a``, ``zmax = 1.5 a``, radial-shock transit
``5e-6 a`` s, pinch lifetime ``1e-6 a`` s for deuterium, ``a`` in metres)
is reported as an estimate with the spread of its Table 2 as declared
bounds. No equation is integrated here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics.constants import (
    MOLAR_GAS_CONSTANT_J_PER_KMOL_K,
    MU0,
    PI,
)

#: Reflected-shock speed as a fraction of the on-axis shock speed (eq. 34).
REFLECTED_SHOCK_FRACTION: Final = 0.3
#: Rule-of-thumb pinch geometry for deuterium (ICTP 2168-10, Table 3).
RULE_MIN_RADIUS_RATIO: Final = 0.15
RULE_MAX_LENGTH_RATIO: Final = 1.5
RULE_SHOCK_TRANSIT_S_PER_M: Final = 5.0e-6
RULE_PINCH_LIFETIME_S_PER_M: Final = 1.0e-6
#: Spread of the same quantities over three machines (ICTP 2168-10, Table 2).
RULE_MIN_RADIUS_RATIO_BOUNDS: Final = (0.14, 0.17)
RULE_MAX_LENGTH_RATIO_BOUNDS: Final = (1.4, 1.6)
RULE_PINCH_DURATION_BOUNDS_S_PER_M: Final = (8.0e-7, 1.4e-6)


def require_specific_heat_ratio(gamma: float) -> float:
    """Return ``gamma`` when finite and strictly greater than one.

    Parameters
    ----------
    gamma
        Specific heat ratio.

    Returns
    -------
    float
        The validated ratio.

    Raises
    ------
    DeviceConfigurationError
        If ``gamma`` is non-finite or not strictly greater than one.
    """
    require_positive("specific_heat_ratio", gamma)
    if gamma <= 1.0:
        raise DeviceConfigurationError(
            f"specific_heat_ratio: must be strictly greater than 1, got {gamma!r}"
        )
    return gamma


@dataclass(frozen=True, slots=True)
class RadialCharacteristics:
    """Characteristic quantities of the radial phase.

    Parameters
    ----------
    radial_transit_time_s
        ``tr`` of eq. (26).
    characteristic_radial_speed_m_s
        ``vr = a / tr`` of eq. (27).
    alpha1
        ``ta / tr`` of eq. (25).
    aspect_ratio
        ``F = z0 / a``.
    beta1
        ``beta / (F ln c)`` of eq. (24).
    geometric_speed_ratio
        ``[(c^2 - 1)(gamma + 1) / (4 ln c)]^(1/2)`` of eq. (28).
    """

    radial_transit_time_s: float
    characteristic_radial_speed_m_s: float
    alpha1: float
    aspect_ratio: float
    beta1: float
    geometric_speed_ratio: float

    def to_record(self) -> dict[str, Any]:
        """Project the characteristics to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "radial_transit_time_s": self.radial_transit_time_s,
            "characteristic_radial_speed_m_s": self.characteristic_radial_speed_m_s,
            "alpha1": self.alpha1,
            "aspect_ratio": self.aspect_ratio,
            "beta1": self.beta1,
            "geometric_speed_ratio": self.geometric_speed_ratio,
        }


def radial_characteristics(
    axial_transit_time_s: float,
    characteristic_current_a: float,
    anode_radius_m: float,
    cathode_radius_m: float,
    anode_length_m: float,
    log_radius_ratio: float,
    inductance_ratio: float,
    mass_density_kg_m3: float,
    axial_current_factor: float,
    radial_mass_factor: float,
    specific_heat_ratio: float,
) -> RadialCharacteristics:
    """Evaluate the radial-phase characteristic quantities.

    Parameters
    ----------
    axial_transit_time_s
        ``ta``; strictly positive.
    characteristic_current_a
        ``I0``; strictly positive.
    anode_radius_m
        ``a``; strictly positive.
    cathode_radius_m
        ``b``; strictly positive.
    anode_length_m
        ``z0``; strictly positive.
    log_radius_ratio
        ``ln(b / a)``; strictly positive.
    inductance_ratio
        ``beta = L0 / La``; strictly positive.
    mass_density_kg_m3
        ``rho0``; strictly positive.
    axial_current_factor
        ``fc`` (the review keeps the axial value in the radial piston);
        strictly positive.
    radial_mass_factor
        ``fmr``; strictly positive.
    specific_heat_ratio
        ``gamma``; strictly greater than one.

    Returns
    -------
    RadialCharacteristics
        Transit time, speed, ``alpha1``, aspect ratio, ``beta1`` and the
        geometric speed ratio.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite, non-positive, or ``gamma <= 1``.
    """
    require_positive("axial_transit_time_s", axial_transit_time_s)
    require_positive("characteristic_current_a", characteristic_current_a)
    require_positive("anode_radius_m", anode_radius_m)
    require_positive("cathode_radius_m", cathode_radius_m)
    require_positive("anode_length_m", anode_length_m)
    require_positive("log_radius_ratio", log_radius_ratio)
    require_positive("inductance_ratio", inductance_ratio)
    require_positive("mass_density_kg_m3", mass_density_kg_m3)
    require_positive("axial_current_factor", axial_current_factor)
    require_positive("radial_mass_factor", radial_mass_factor)
    require_specific_heat_ratio(specific_heat_ratio)
    ratio = cathode_radius_m / anode_radius_m
    drive = (characteristic_current_a / anode_radius_m) / math.sqrt(mass_density_kg_m3)
    transit = (
        (4.0 * PI)
        / math.sqrt(MU0 * (specific_heat_ratio + 1.0))
        * (math.sqrt(radial_mass_factor) / axial_current_factor)
        * anode_radius_m
        / drive
    )
    aspect = anode_length_m / anode_radius_m
    return RadialCharacteristics(
        radial_transit_time_s=transit,
        characteristic_radial_speed_m_s=anode_radius_m / transit,
        alpha1=axial_transit_time_s / transit,
        aspect_ratio=aspect,
        beta1=inductance_ratio / (aspect * log_radius_ratio),
        geometric_speed_ratio=math.sqrt(
            ((ratio * ratio - 1.0) * (specific_heat_ratio + 1.0))
            / (4.0 * log_radius_ratio)
        ),
    )


@dataclass(frozen=True, slots=True)
class SlugRelations:
    """Instantaneous slug-model relations at a declared current and piston radius.

    Parameters
    ----------
    current_a
        Declared circuit current ``I``.
    piston_radius_m
        Declared piston (current sheath) radius ``rp``.
    shock_speed_m_s
        ``drs/dt`` of eq. (14); negative (inward).
    elongation_speed_m_s
        ``dzf/dt`` of eq. (15); positive.
    shock_temperature_k
        ``T`` of eq. (32) behind the shock.
    reflected_shock_speed_m_s
        ``0.3`` of the on-axis shock speed, outward (eq. 34).
    """

    current_a: float
    piston_radius_m: float
    shock_speed_m_s: float
    elongation_speed_m_s: float
    shock_temperature_k: float
    reflected_shock_speed_m_s: float

    def to_record(self) -> dict[str, Any]:
        """Project the relations to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "current_a": self.current_a,
            "piston_radius_m": self.piston_radius_m,
            "shock_speed_m_s": self.shock_speed_m_s,
            "elongation_speed_m_s": self.elongation_speed_m_s,
            "shock_temperature_k": self.shock_temperature_k,
            "reflected_shock_speed_m_s": self.reflected_shock_speed_m_s,
        }


def slug_relations(
    current_a: float,
    piston_radius_m: float,
    mass_density_kg_m3: float,
    axial_current_factor: float,
    radial_mass_factor: float,
    specific_heat_ratio: float,
    molecular_mass_amu: float,
    dissociation_number: float,
    plasma_effective_charge: float,
) -> SlugRelations:
    """Evaluate the slug-model relations at one instant.

    Parameters
    ----------
    current_a
        Circuit current ``I``; strictly positive.
    piston_radius_m
        Piston radius ``rp``; strictly positive.
    mass_density_kg_m3
        ``rho0``; strictly positive.
    axial_current_factor
        ``fc``; strictly positive.
    radial_mass_factor
        ``fmr``; strictly positive.
    specific_heat_ratio
        ``gamma``; strictly greater than one.
    molecular_mass_amu
        Molecular mass number ``M`` (kg per kmol); strictly positive.
    dissociation_number
        ``DN`` (``2`` for deuterium); strictly positive.
    plasma_effective_charge
        ``Z`` of the departure coefficient ``D = DN (1 + Z)``; finite and
        non-negative (``0`` is the un-ionised limit).

    Returns
    -------
    SlugRelations
        Shock, elongation and reflected-shock speeds and the shock
        temperature (eqs. 14, 15, 32, 34; the review rounds ``R0`` to
        ``8e3`` J kmol^-1 K^-1, the exact value is used).

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite, non-positive, ``gamma <= 1`` or the
        effective charge is negative.
    """
    require_positive("current_a", current_a)
    require_positive("piston_radius_m", piston_radius_m)
    require_positive("mass_density_kg_m3", mass_density_kg_m3)
    require_positive("axial_current_factor", axial_current_factor)
    require_positive("radial_mass_factor", radial_mass_factor)
    require_specific_heat_ratio(specific_heat_ratio)
    require_positive("molecular_mass_amu", molecular_mass_amu)
    require_positive("dissociation_number", dissociation_number)
    if not math.isfinite(plasma_effective_charge) or plasma_effective_charge < 0.0:
        raise DeviceConfigurationError(
            "plasma_effective_charge: must be finite and non-negative, got "
            f"{plasma_effective_charge!r}"
        )
    shock = 0.0 - math.sqrt(
        (MU0 * (specific_heat_ratio + 1.0)) / mass_density_kg_m3
    ) * (axial_current_factor / math.sqrt(radial_mass_factor)) * (
        current_a / (4.0 * PI * piston_radius_m)
    )
    elongation = 0.0 - (2.0 / (specific_heat_ratio + 1.0)) * shock
    departure = dissociation_number * (1.0 + plasma_effective_charge)
    temperature = (
        (molecular_mass_amu / (MOLAR_GAS_CONSTANT_J_PER_KMOL_K * departure))
        * (
            (2.0 * (specific_heat_ratio - 1.0))
            / ((specific_heat_ratio + 1.0) * (specific_heat_ratio + 1.0))
        )
        * (shock * shock)
    )
    return SlugRelations(
        current_a=current_a,
        piston_radius_m=piston_radius_m,
        shock_speed_m_s=shock,
        elongation_speed_m_s=elongation,
        shock_temperature_k=temperature,
        reflected_shock_speed_m_s=0.0 - REFLECTED_SHOCK_FRACTION * shock,
    )


@dataclass(frozen=True, slots=True)
class PinchGeometryEstimate:
    """Rule-of-thumb pinch geometry scaled from the anode radius.

    Parameters
    ----------
    anode_radius_m
        ``a``.
    minimum_radius_m
        ``0.15 a``.
    maximum_length_m
        ``1.5 a``.
    shock_transit_time_s
        ``5e-6 a`` (``a`` in metres).
    pinch_lifetime_s
        ``1e-6 a`` (``a`` in metres).
    """

    anode_radius_m: float
    minimum_radius_m: float
    maximum_length_m: float
    shock_transit_time_s: float
    pinch_lifetime_s: float

    def to_record(self) -> dict[str, Any]:
        """Project the estimate and its declared bounds to a record.

        Returns
        -------
        dict[str, Any]
            Every field under its name plus the published spread of the
            ratios as ``bounds``.
        """
        return {
            "anode_radius_m": self.anode_radius_m,
            "minimum_radius_m": self.minimum_radius_m,
            "maximum_length_m": self.maximum_length_m,
            "shock_transit_time_s": self.shock_transit_time_s,
            "pinch_lifetime_s": self.pinch_lifetime_s,
            "bounds": {
                "minimum_radius_ratio": list(RULE_MIN_RADIUS_RATIO_BOUNDS),
                "maximum_length_ratio": list(RULE_MAX_LENGTH_RATIO_BOUNDS),
                "pinch_duration_s_per_m": list(RULE_PINCH_DURATION_BOUNDS_S_PER_M),
            },
        }


def pinch_geometry_estimate(anode_radius_m: float) -> PinchGeometryEstimate:
    """Scale the rule-of-thumb pinch geometry from the anode radius.

    Parameters
    ----------
    anode_radius_m
        Anode radius ``a``; strictly positive.

    Returns
    -------
    PinchGeometryEstimate
        The four scaled quantities (ICTP 2168-10, Table 3, deuterium).

    Raises
    ------
    DeviceConfigurationError
        If the radius is non-finite or non-positive.
    """
    require_positive("anode_radius_m", anode_radius_m)
    return PinchGeometryEstimate(
        anode_radius_m=anode_radius_m,
        minimum_radius_m=RULE_MIN_RADIUS_RATIO * anode_radius_m,
        maximum_length_m=RULE_MAX_LENGTH_RATIO * anode_radius_m,
        shock_transit_time_s=RULE_SHOCK_TRANSIT_S_PER_M * anode_radius_m,
        pinch_lifetime_s=RULE_PINCH_LIFETIME_S_PER_M * anode_radius_m,
    )
