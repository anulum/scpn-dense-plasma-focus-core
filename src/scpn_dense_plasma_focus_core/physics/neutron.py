# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — beam-target neutron yield and the empirical scaling law

"""Beam-target neutron yield and the empirical pinch-current scaling law.

The Lee model's neutron yield is the sum of a thermonuclear term (eq. 49,
needing the thermal reactivity, a shared kernel not in this repository)
and a beam-target term
``Y_bt = C_n n_i I_pinch^2 z_p^2 ln(b / rp) sigma / U^(1/2)`` (S. Lee,
J. Fusion Energ. 33 (2014) 319–335, eq. 50; IAEA-TECDOC-1829 eq. 1 with
``C_n = 8.54e8`` in SI units, calibrated at ``I_pinch = 0.5`` MA). The
same source rewrites it as ``Y_bt = J_b tau sigma n_i pi rp^2 z_p``
(TECDOC eq. 2), the identity this module's tests check against the beam
module (the two printed constants ``8.5e8`` and ``8.54e8`` agree to
0.5 %). The review also states the empirical fit of measured yields
``Y_n = 9e10 I_pinch^3.8`` (``I_pinch`` in MA, range 0.1–1 MA) with the
calibration point ``7e9`` neutrons at 0.5 MA; the fit is a consistency
instrument, not a prediction, and is refused outside its stated range.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics._transcendental import natural_log, power

#: Beam-target constant of TECDOC-1829 eq. (1), SI units.
BEAM_TARGET_CONSTANT: Final = 8.54e8
#: Empirical scaling law ``Y_n = 9e10 I_pinch^3.8`` (Lee 2014, ``I`` in MA).
SCALING_COEFFICIENT: Final = 9.0e10
SCALING_EXPONENT: Final = 3.8
#: Stated range of the scaling law in amperes.
SCALING_RANGE_A: Final = (1.0e5, 1.0e6)


@dataclass(frozen=True, slots=True)
class NeutronEstimates:
    """Beam-target yield and the scaling-law value at the declared state.

    Parameters
    ----------
    beam_target_yield
        ``Y_bt`` of eq. (50) with the declared cross-section.
    scaling_law_yield
        ``9e10 I_pinch^3.8`` (``I`` in MA), or ``None`` when the pinch
        current lies outside the law's stated range (the record then says
        so instead of refusing; the direct function refuses).
    """

    beam_target_yield: float
    scaling_law_yield: float | None

    def to_record(self) -> dict[str, Any]:
        """Project the estimates to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "beam_target_yield": self.beam_target_yield,
            "scaling_law_yield": self.scaling_law_yield,
            "scaling_law_applicable": self.scaling_law_yield is not None,
        }


def beam_target_yield(
    ion_density_per_m3: float,
    pinch_current_a: float,
    pinch_length_m: float,
    cathode_radius_m: float,
    pinch_radius_m: float,
    cross_section_m2: float,
    diode_voltage_v: float,
) -> float:
    """Evaluate the beam-target neutron yield of eq. (50).

    Parameters
    ----------
    ion_density_per_m3
        ``n_i``; strictly positive.
    pinch_current_a
        ``I_pinch``; strictly positive.
    pinch_length_m
        ``z_p``; strictly positive.
    cathode_radius_m
        ``b``; strictly positive.
    pinch_radius_m
        ``rp``; strictly positive and smaller than ``b``.
    cross_section_m2
        ``sigma`` of the D–D neutron branch at the beam energy; positive.
    diode_voltage_v
        ``U``; strictly positive.

    Returns
    -------
    float
        ``C_n n_i I^2 z_p^2 ln(b / rp) sigma / U^(1/2)``.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or non-positive, or the radii are not
        ordered.
    """
    require_positive("ion_density_per_m3", ion_density_per_m3)
    require_positive("pinch_current_a", pinch_current_a)
    require_positive("pinch_length_m", pinch_length_m)
    require_positive("cathode_radius_m", cathode_radius_m)
    require_positive("pinch_radius_m", pinch_radius_m)
    require_positive("cross_section_m2", cross_section_m2)
    require_positive("diode_voltage_v", diode_voltage_v)
    if pinch_radius_m >= cathode_radius_m:
        raise DeviceConfigurationError(
            "pinch_radius_m: must be smaller than cathode_radius_m, got "
            f"{pinch_radius_m!r} >= {cathode_radius_m!r}"
        )
    return (
        BEAM_TARGET_CONSTANT
        * ion_density_per_m3
        * (pinch_current_a * pinch_current_a)
        * (pinch_length_m * pinch_length_m)
        * natural_log(cathode_radius_m / pinch_radius_m)
        * cross_section_m2
        / math.sqrt(diode_voltage_v)
    )


def scaling_law_applies(pinch_current_a: float) -> bool:
    """Tell whether the pinch current lies inside the law's stated range.

    Parameters
    ----------
    pinch_current_a
        ``I_pinch`` in amperes; must be finite and positive.

    Returns
    -------
    bool
        ``True`` inside ``[1e5, 1e6]`` A.

    Raises
    ------
    DeviceConfigurationError
        If the current is non-finite or non-positive.
    """
    require_positive("pinch_current_a", pinch_current_a)
    low, high = SCALING_RANGE_A
    return low <= pinch_current_a <= high


def scaling_law_yield(pinch_current_a: float) -> float:
    """Evaluate the empirical scaling law ``Y_n = 9e10 I_pinch^3.8``.

    Parameters
    ----------
    pinch_current_a
        ``I_pinch`` in amperes; must lie within the stated range
        ``[1e5, 1e6]`` A.

    Returns
    -------
    float
        The fitted neutron yield.

    Raises
    ------
    DeviceConfigurationError
        If the current is non-finite, non-positive or outside the range.
    """
    if not scaling_law_applies(pinch_current_a):
        low, high = SCALING_RANGE_A
        raise DeviceConfigurationError(
            "pinch_current_a: the scaling law is stated for "
            f"[{low!r}, {high!r}] A, got {pinch_current_a!r}"
        )
    return SCALING_COEFFICIENT * power(pinch_current_a / 1.0e6, SCALING_EXPONENT)
