# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — capacitor-bank normalisation and fill state

"""Bank normalisation, scaling parameters and fill-gas state.

The Lee model normalises the circuit by ``t0 = sqrt(L0 C0)``,
``Z0 = sqrt(L0 / C0)`` and ``I0 = V0 / Z0`` and identifies three scaling
parameters of the axial phase: ``alpha = t0 / ta``, ``beta = L0 / La``
with ``La = (mu0 / 2 pi) ln(c) z0`` the inductance of the full axial
phase, and ``delta = r0 / Z0`` (S. Lee, J. Fusion Energ. 33 (2014)
319–335, eqs. 4–6 and 9 and the text before them). The quarter period
``(pi / 2) t0`` of the undamped ``L0 C0`` circuit is the rise time the
same author tabulates for twelve machines (IAEA-TECDOC-1829, Table 1),
which is the anchor of this module. The fill state is the ideal-gas
density of the declared molecular mass at the declared temperature; the
review writes the molecule number density as ``6e26 rho0 / M`` (eq. 43),
the rounded reciprocal proton mass, and the exact value is used here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics._transcendental import natural_log
from scpn_dense_plasma_focus_core.physics.constants import (
    BOLTZMANN_J_PER_K,
    MU0,
    PASCAL_PER_TORR,
    PI,
    PROTON_MASS_KG,
)


@dataclass(frozen=True, slots=True)
class BankNormalisation:
    """Normalising quantities and scaling parameters of the discharge circuit.

    Parameters
    ----------
    bank_energy_j
        ``E0 = C0 V0^2 / 2``.
    characteristic_time_s
        ``t0 = sqrt(L0 C0)``.
    surge_impedance_ohm
        ``Z0 = sqrt(L0 / C0)``.
    characteristic_current_a
        ``I0 = V0 / Z0``.
    quarter_period_s
        ``(pi / 2) t0``, the current rise time of the undamped circuit.
    damping_ratio
        ``delta = r0 / Z0``.
    log_radius_ratio
        ``ln(c)`` with ``c = b / a``.
    axial_inductance_h
        ``La = (mu0 / 2 pi) ln(c) z0``.
    inductance_ratio
        ``beta = L0 / La``.
    """

    bank_energy_j: float
    characteristic_time_s: float
    surge_impedance_ohm: float
    characteristic_current_a: float
    quarter_period_s: float
    damping_ratio: float
    log_radius_ratio: float
    axial_inductance_h: float
    inductance_ratio: float

    def to_record(self) -> dict[str, Any]:
        """Project the normalisation to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "bank_energy_j": self.bank_energy_j,
            "characteristic_time_s": self.characteristic_time_s,
            "surge_impedance_ohm": self.surge_impedance_ohm,
            "characteristic_current_a": self.characteristic_current_a,
            "quarter_period_s": self.quarter_period_s,
            "damping_ratio": self.damping_ratio,
            "log_radius_ratio": self.log_radius_ratio,
            "axial_inductance_h": self.axial_inductance_h,
            "inductance_ratio": self.inductance_ratio,
        }


def bank_normalisation(
    capacitance_f: float,
    inductance_h: float,
    resistance_ohm: float,
    charge_voltage_v: float,
    anode_radius_m: float,
    cathode_radius_m: float,
    anode_length_m: float,
) -> BankNormalisation:
    """Evaluate the circuit normalisation and the scaling parameters.

    Parameters
    ----------
    capacitance_f
        Bank capacitance ``C0``; strictly positive.
    inductance_h
        Static inductance ``L0``; strictly positive.
    resistance_ohm
        Stray resistance ``r0``; strictly positive.
    charge_voltage_v
        Charge voltage ``V0``; strictly positive.
    anode_radius_m
        Anode radius ``a``; strictly positive.
    cathode_radius_m
        Cathode radius ``b``; strictly greater than ``a``.
    anode_length_m
        Anode length ``z0``; strictly positive.

    Returns
    -------
    BankNormalisation
        The evaluated quantities (Lee 2014, eqs. 4–6, 9 and text).

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or non-positive, or the radii are not
        ordered.
    """
    require_positive("capacitance_f", capacitance_f)
    require_positive("inductance_h", inductance_h)
    require_positive("resistance_ohm", resistance_ohm)
    require_positive("charge_voltage_v", charge_voltage_v)
    require_positive("anode_radius_m", anode_radius_m)
    require_positive("cathode_radius_m", cathode_radius_m)
    require_positive("anode_length_m", anode_length_m)
    if cathode_radius_m <= anode_radius_m:
        raise DeviceConfigurationError(
            "cathode_radius_m: must be strictly greater than anode_radius_m, got "
            f"{cathode_radius_m!r} <= {anode_radius_m!r}"
        )
    energy = 0.5 * capacitance_f * charge_voltage_v * charge_voltage_v
    time = math.sqrt(inductance_h * capacitance_f)
    impedance = math.sqrt(inductance_h / capacitance_f)
    current = charge_voltage_v / impedance
    quarter = (PI / 2.0) * time
    damping = resistance_ohm / impedance
    log_ratio = natural_log(cathode_radius_m / anode_radius_m)
    axial_inductance = (MU0 / (2.0 * PI)) * log_ratio * anode_length_m
    return BankNormalisation(
        bank_energy_j=energy,
        characteristic_time_s=time,
        surge_impedance_ohm=impedance,
        characteristic_current_a=current,
        quarter_period_s=quarter,
        damping_ratio=damping,
        log_radius_ratio=log_ratio,
        axial_inductance_h=axial_inductance,
        inductance_ratio=inductance_h / axial_inductance,
    )


@dataclass(frozen=True, slots=True)
class FillState:
    """Ambient fill-gas state before the discharge.

    Parameters
    ----------
    pressure_pa
        Fill pressure in pascals.
    molecular_mass_kg
        ``M m_p`` for the declared molecular mass number ``M``.
    molecule_density_per_m3
        ``N0 = p / (k_B T0)``; the review's ``6e26 rho0 / M`` with the
        exact reciprocal proton mass.
    mass_density_kg_m3
        ``rho0 = N0 M m_p``.
    """

    pressure_pa: float
    molecular_mass_kg: float
    molecule_density_per_m3: float
    mass_density_kg_m3: float

    def to_record(self) -> dict[str, Any]:
        """Project the fill state to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "pressure_pa": self.pressure_pa,
            "molecular_mass_kg": self.molecular_mass_kg,
            "molecule_density_per_m3": self.molecule_density_per_m3,
            "mass_density_kg_m3": self.mass_density_kg_m3,
        }


def fill_state(
    pressure_torr: float, molecular_mass_amu: float, temperature_k: float
) -> FillState:
    """Evaluate the ideal-gas fill state.

    Parameters
    ----------
    pressure_torr
        Fill pressure in torr; strictly positive.
    molecular_mass_amu
        Molecular mass number ``M`` (``4`` for deuterium molecules); the
        sources scale it by the proton mass; strictly positive.
    temperature_k
        Fill temperature in kelvin; strictly positive and declared by the
        caller (the sources do not print it).

    Returns
    -------
    FillState
        Pressure in pascals (exact ``101325 / 760`` per torr), molecular
        mass, molecule number density and mass density.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or non-positive.
    """
    require_positive("pressure_torr", pressure_torr)
    require_positive("molecular_mass_amu", molecular_mass_amu)
    require_positive("temperature_k", temperature_k)
    pressure = pressure_torr * PASCAL_PER_TORR
    mass = molecular_mass_amu * PROTON_MASS_KG
    density = pressure / (BOLTZMANN_J_PER_K * temperature_k)
    return FillState(
        pressure_pa=pressure,
        molecular_mass_kg=mass,
        molecule_density_per_m3=density,
        mass_density_kg_m3=density * mass,
    )
