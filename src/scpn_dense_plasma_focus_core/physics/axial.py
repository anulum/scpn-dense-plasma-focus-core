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
from typing import Any

from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics.constants import MU0, PI


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

    def to_record(self) -> dict[str, Any]:
        """Project the characteristics to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "axial_transit_time_s": self.axial_transit_time_s,
            "alpha": self.alpha,
            "characteristic_axial_speed_m_s": self.characteristic_axial_speed_m_s,
            "drive_current_a": self.drive_current_a,
            "terminal_sheath_speed_m_s": self.terminal_sheath_speed_m_s,
        }


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
        ``b``; strictly positive (ordering is enforced by the caller).
    anode_length_m
        ``z0``; strictly positive.
    log_radius_ratio
        ``ln(b / a)``; strictly positive.
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
        If any input is non-finite or non-positive.
    """
    require_positive("characteristic_time_s", characteristic_time_s)
    require_positive("characteristic_current_a", characteristic_current_a)
    require_positive("anode_radius_m", anode_radius_m)
    require_positive("cathode_radius_m", cathode_radius_m)
    require_positive("anode_length_m", anode_length_m)
    require_positive("log_radius_ratio", log_radius_ratio)
    require_positive("mass_density_kg_m3", mass_density_kg_m3)
    require_positive("axial_mass_factor", axial_mass_factor)
    require_positive("axial_current_factor", axial_current_factor)
    require_positive("drive_current_a", drive_current_a)
    ratio = cathode_radius_m / anode_radius_m
    geometry = (4.0 * PI * PI * (ratio * ratio - 1.0)) / (MU0 * log_radius_ratio)
    drive = (characteristic_current_a / anode_radius_m) / math.sqrt(mass_density_kg_m3)
    transit = (
        math.sqrt(geometry)
        * (math.sqrt(axial_mass_factor) / axial_current_factor)
        * anode_length_m
        / drive
    )
    terminal = math.sqrt(
        ((axial_current_factor * axial_current_factor) / axial_mass_factor)
        * (
            (MU0 * log_radius_ratio)
            / (4.0 * PI * PI * mass_density_kg_m3 * (ratio * ratio - 1.0))
        )
    ) * (drive_current_a / anode_radius_m)
    return AxialCharacteristics(
        axial_transit_time_s=transit,
        alpha=characteristic_time_s / transit,
        characteristic_axial_speed_m_s=anode_length_m / transit,
        drive_current_a=drive_current_a,
        terminal_sheath_speed_m_s=terminal,
    )
