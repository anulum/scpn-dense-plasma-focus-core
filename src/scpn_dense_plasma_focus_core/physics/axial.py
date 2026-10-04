# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — axial (snowplow) phase characteristic quantities

"""Characteristic quantities of the axial snowplow phase.

The Lee model's axial phase couples the snowplow equation of motion to the
circuit equation (S. Lee, J. Fusion Energ. 33 (2014) 319–335, eqs. 1–2).
Its normalisation yields the characteristic axial transit time
``ta = [4 pi^2 (c^2 - 1) / (mu0 ln c)]^(1/2) (sqrt(fm) / fc) z0 /
((I0 / a) / sqrt(rho0))`` (eq. 5), the first scaling parameter
``alpha = t0 / ta`` (eq. 6) and the characteristic axial speed
``va = z0 / ta`` (eq. 7). Setting the
acceleration of eq. (1) to zero at a declared constant current ``I``
gives the terminal sheath speed
``v_inf(I) = [(fc^2 / fm) mu0 ln c / (4 pi^2 rho0 (c^2 - 1))]^(1/2) I / a``,
which at the peak current reproduces the tabulated peak axial speeds of
twelve machines to within 7–14 % (always above them: the fitted peak
speed is not attained exactly at peak current), the anchor of this
module with a declared 15 % tolerance. No equation is integrated here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics.constants import MU0, PI
from scpn_dense_plasma_focus_core.physics.numerics import natural_log


@dataclass(frozen=True, slots=True)
class AxialCharacteristics:
    """Characteristic quantities of the axial phase.

    Parameters
    ----------
    axial_transit_time_s
        ``ta`` of eq. (5).
    alpha
        ``t0 / ta`` of eq. (6).
    characteristic_axial_speed_m_s
        ``va = z0 / ta`` of eq. (7).
    drive_current_a
        Declared current at which the terminal speed is evaluated.
    terminal_sheath_speed_m_s
        ``v_inf`` at the declared current (eq. 1 with zero acceleration).
    """

    axial_transit_time_s: float
    alpha: float
    characteristic_axial_speed_m_s: float
    drive_current_a: float
    terminal_sheath_speed_m_s: float

    def to_record(self) -> dict[str, float]:
        """Project the characteristics to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every field under its name.
        """
        return {
            "axial_transit_time_s": self.axial_transit_time_s,
            "alpha": self.alpha,
            "characteristic_axial_speed_m_s": self.characteristic_axial_speed_m_s,
            "drive_current_a": self.drive_current_a,
            "terminal_sheath_speed_m_s": self.terminal_sheath_speed_m_s,
        }


def _geometry_factors(
    anode_radius_m: float,
    cathode_radius_m: float,
    log_radius_ratio: float,
    mass_density_kg_m3: float,
) -> tuple[float, float]:
    """Evaluate the two geometry factors after checking the coaxial relation.

    Parameters
    ----------
    anode_radius_m, cathode_radius_m
        Positive electrode radii in metres, with the cathode outside the anode.
    log_radius_ratio
        Exact deterministic ``ln(b/a)`` returned by bank normalisation.
    mass_density_kg_m3
        Positive fill density in kilograms per cubic metre.

    Returns
    -------
    tuple[float, float]
        Transit radicand and the density-weighted terminal geometry factor.

    Raises
    ------
    DeviceConfigurationError
        If the relation is inconsistent or a factor is unrepresentable.
    """
    if cathode_radius_m <= anode_radius_m:
        raise DeviceConfigurationError(
            "cathode_radius_m: must be strictly greater than anode_radius_m, "
            f"got {cathode_radius_m!r} <= {anode_radius_m!r}"
        )
    ratio = require_positive("radius_ratio", cathode_radius_m / anode_radius_m)
    if log_radius_ratio != natural_log(ratio):
        raise DeviceConfigurationError(
            "log_radius_ratio: must equal deterministic ln(cathode_radius_m / "
            "anode_radius_m) from bank_normalisation"
        )
    radius_difference = require_positive(
        "radius_squared_ratio_minus_one", ratio * ratio - 1.0
    )
    magnetic_factor = require_positive("magnetic_log_factor", MU0 * log_radius_ratio)
    geometry = require_positive(
        "axial_geometry_factor", (4.0 * PI * PI * radius_difference) / magnetic_factor
    )
    denominator = require_positive(
        "terminal_geometry_denominator",
        4.0 * PI * PI * mass_density_kg_m3 * radius_difference,
    )
    return geometry, require_positive(
        "terminal_geometry_factor", magnetic_factor / denominator
    )


def axial_characteristics(
    characteristic_time_s: float,
    characteristic_current_a: float,
    anode_radius_m: float,
    cathode_radius_m: float,
    anode_length_m: float,
    log_radius_ratio: float,
    mass_density_kg_m3: float,
    axial_mass_factor: float,
    axial_current_factor: float,
    drive_current_a: float,
) -> AxialCharacteristics:
    """Evaluate the axial-phase characteristic quantities.

    Parameters
    ----------
    characteristic_time_s
        ``t0 = sqrt(L0 C0)``; strictly positive.
    characteristic_current_a
        ``I0 = V0 / Z0``; strictly positive.
    anode_radius_m
        ``a``; strictly positive.
    cathode_radius_m
        ``b``; finite and strictly greater than ``anode_radius_m``.
    anode_length_m
        ``z0``; strictly positive.
    log_radius_ratio
        Exact deterministic ``ln(b / a)`` from :func:`bank_normalisation`;
        strictly positive and derived from the declared radii, not fitted.
    mass_density_kg_m3
        Fill mass density ``rho0``; strictly positive.
    axial_mass_factor
        ``fm``; strictly positive.
    axial_current_factor
        ``fc``; strictly positive.
    drive_current_a
        Current at which the terminal sheath speed is evaluated; strictly
        positive.

    Returns
    -------
    AxialCharacteristics
        Transit time, ``alpha``, characteristic and terminal speeds.

    Raises
    ------
    DeviceConfigurationError
        If an input is non-finite/non-positive, the coaxial or logarithmic
        relation is inconsistent, or an intermediate/output cannot be
        represented as a finite positive binary64 value. No value is clamped.
    """
    for name, value in (
        ("characteristic_time_s", characteristic_time_s),
        ("characteristic_current_a", characteristic_current_a),
        ("anode_radius_m", anode_radius_m),
        ("cathode_radius_m", cathode_radius_m),
        ("anode_length_m", anode_length_m),
        ("log_radius_ratio", log_radius_ratio),
        ("mass_density_kg_m3", mass_density_kg_m3),
        ("axial_mass_factor", axial_mass_factor),
        ("axial_current_factor", axial_current_factor),
        ("drive_current_a", drive_current_a),
    ):
        require_positive(name, value)
    geometry, terminal_geometry = _geometry_factors(
        anode_radius_m, cathode_radius_m, log_radius_ratio, mass_density_kg_m3
    )
    current_per_radius = require_positive(
        "characteristic_current_per_radius", characteristic_current_a / anode_radius_m
    )
    drive = require_positive(
        "axial_drive", current_per_radius / math.sqrt(mass_density_kg_m3)
    )
    mass_current_factor = require_positive(
        "axial_mass_current_factor", math.sqrt(axial_mass_factor) / axial_current_factor
    )
    transit = require_positive(
        "axial_transit_time_s",
        math.sqrt(geometry) * mass_current_factor * anode_length_m / drive,
    )
    current_mass_factor = require_positive(
        "terminal_current_mass_factor",
        (axial_current_factor * axial_current_factor) / axial_mass_factor,
    )
    terminal_radicand = require_positive(
        "terminal_speed_squared_factor", current_mass_factor * terminal_geometry
    )
    drive_per_radius = require_positive(
        "drive_current_per_radius", drive_current_a / anode_radius_m
    )
    terminal = require_positive(
        "terminal_sheath_speed_m_s", math.sqrt(terminal_radicand) * drive_per_radius
    )
    return AxialCharacteristics(
        axial_transit_time_s=transit,
        alpha=require_positive("alpha", characteristic_time_s / transit),
        characteristic_axial_speed_m_s=require_positive(
            "characteristic_axial_speed_m_s", anode_length_m / transit
        ),
        drive_current_a=drive_current_a,
        terminal_sheath_speed_m_s=terminal,
    )
