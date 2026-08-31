# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — dense-plasma-focus parameter model

"""Validated parameter objects of a dense-plasma-focus configuration.

The derived quantity implements one standard result and nothing more:
the drive parameter ``S = I_peak / (a sqrt(p))`` in
kA cm^-1 Torr^-1/2 (S. Lee, A. Serban, IEEE Trans. Plasma Sci. 24
(1996) 1101). It is a rough consistency instrument with documented
applicability bounds; no claim about any real machine follows from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class ElectrodeSet:
    """Coaxial electrode geometry of a dense plasma focus.

    Parameters
    ----------
    anode_radius_m
        Anode (inner electrode) radius ``a`` in metres; strictly
        positive and strictly smaller than ``cathode_radius_m``.
    cathode_radius_m
        Cathode (outer electrode) radius ``b`` in metres; strictly
        positive.
    anode_length_m
        Anode length in metres; strictly positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or the coaxial ordering is
        violated.
    """

    anode_radius_m: float
    cathode_radius_m: float
    anode_length_m: float

    def __post_init__(self) -> None:
        """Validate the electrode invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or the coaxial ordering is
            violated.
        """
        require_positive("anode_radius_m", self.anode_radius_m)
        require_positive("cathode_radius_m", self.cathode_radius_m)
        require_positive("anode_length_m", self.anode_length_m)
        if self.anode_radius_m >= self.cathode_radius_m:
            raise DeviceConfigurationError(
                "anode_radius_m: must be strictly smaller than "
                f"cathode_radius_m ({self.anode_radius_m!r} >= "
                f"{self.cathode_radius_m!r}) — coaxial-gun geometry"
            )


@dataclass(frozen=True, slots=True)
class BankAndFill:
    """Capacitor-bank and fill-gas declaration of a dense plasma focus.

    Parameters
    ----------
    bank_energy_kj
        Stored bank energy in kilojoules; strictly positive.
    peak_current_ma
        Peak discharge current in mega-amperes; strictly positive.
    fill_pressure_torr
        Fill pressure in torr; strictly positive.
    deuterium_fill
        Whether the fill gas is deuterium; the drive-parameter window
        advisory applies only then.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or not strictly positive.
    """

    bank_energy_kj: float
    peak_current_ma: float
    fill_pressure_torr: float
    deuterium_fill: bool

    def __post_init__(self) -> None:
        """Validate the bank/fill invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or not strictly positive.
        """
        require_positive("bank_energy_kj", self.bank_energy_kj)
        require_positive("peak_current_ma", self.peak_current_ma)
        require_positive("fill_pressure_torr", self.fill_pressure_torr)

    def drive_parameter(self, electrodes: ElectrodeSet) -> float:
        """Lee-Serban drive parameter of the validated declaration.

        Parameters
        ----------
        electrodes
            Validated electrode set supplying the anode radius.

        Returns
        -------
        float
            ``S = I_peak / (a sqrt(p))`` in kA cm^-1 Torr^-1/2
            (Lee & Serban, IEEE TPS 24 (1996) 1101).
        """
        current_ka = self.peak_current_ma * 1.0e3
        anode_cm = electrodes.anode_radius_m * 1.0e2
        return current_ka / (anode_cm * math.sqrt(self.fill_pressure_torr))
