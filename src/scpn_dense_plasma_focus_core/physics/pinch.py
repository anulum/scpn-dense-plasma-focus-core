# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — pinch-phase closed forms

"""Closed forms of the pinch (slow compression) phase at a declared pinch state.

The Lee model's pinch phase couples the piston motion to the energy
balance ``dQ/dt = dQ_J/dt + dQ_B/dt + dQ_L/dt`` (S. Lee, J. Fusion Energ.
33 (2014) 319–335, eqs. 38–48). This module evaluates the printed closed
forms at a declared pinch state, never the integration: the pinch ion
density ``N_i = N0 fmr (a / rp)^2`` (eq. 43), the Bennett temperature
``T = mu0 I^2 fc^2 / (8 pi^2 k_B D N0 a^2 fmr)`` (eq. 41), the Spitzer
resistance ``R = 1290 Z zf / (pi rp^2 T^(3/2))`` (eq. 40), the Joule power
``R I^2 fc^2`` (eq. 39), the bremsstrahlung ``-1.6e-40 N_i^2 pi rp^2 zf
T^(1/2) Z^3`` (eq. 42), the line loss ``-4.6e-31 N_i^2 Z Z_n^4 pi rp^2 zf
/ T`` (eq. 44), the photonic excitation number ``M = 1.66e-15 rp
Z_n^(1/2) N_i / (Z T^1.5)`` with ``T`` in eV (eq. 46), the self-absorption
factor ``A = A2^(1 + M)``, ``A1 = 1 + 1e-14 N_i Z / T^3.5``, ``A2 = 1 / A1``
(eq. 47, ``T`` in eV as for eq. 46; the review states the unit once for
both), and the surface-emission line loss ``-4.62e-16 Z^(1/2) Z_n^3.5 rp
zf T^4`` that replaces the volumetric term once ``A`` falls to ``1/e``
(eq. 48 and the text after it); an absorption factor below the smallest
normal double is reported as exactly zero (fully absorbed) instead of
being refused, since the surface term then applies. Honest limit
recorded in the evidence
record: the review's tabulated pinch temperatures and densities are
outputs of the integrated code at the end of the pinch phase and are not
reproduced by eqs. (41) and (43) evaluated at the tabulated minimum
radius and fill (a hand check gives factors of about 3 and 5), so these
quantities carry no printed anchor; their tests are identities and
scalings. The real-exponent power of eq. (47) uses the vendored
deterministic kernel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics.constants import (
    BOLTZMANN_J_PER_K,
    ELEMENTARY_CHARGE_C,
    INV_E,
    MU0,
    PI,
)
from scpn_dense_plasma_focus_core.physics.numerics import (
    EXP_MIN,
    exponential,
    natural_log,
)

#: Spitzer resistance coefficient of eq. (40), SI.
SPITZER_COEFFICIENT: Final = 1290.0
#: Bremsstrahlung coefficient of eq. (42), SI.
BREMSSTRAHLUNG_COEFFICIENT: Final = 1.6e-40
#: Line-radiation coefficient of eq. (44), SI.
LINE_COEFFICIENT: Final = 4.6e-31
#: Photonic excitation coefficient of eq. (46), ``T`` in eV.
EXCITATION_COEFFICIENT: Final = 1.66e-15
#: Self-absorption coefficient of eq. (47), ``T`` in eV.
ABSORPTION_COEFFICIENT: Final = 1.0e-14
#: Surface-emission coefficient of eq. (48), SI.
SURFACE_EMISSION_COEFFICIENT: Final = 4.62e-16


@dataclass(frozen=True, slots=True)
class PinchState:
    """Declared pinch state at which the closed forms are evaluated.

    Parameters
    ----------
    pinch_current_a
        ``I_pinch`` at the start of the slow compression phase; positive.
    pinch_radius_m
        ``rp``; positive and smaller than the anode radius (checked when
        the record is built).
    pinch_length_m
        ``zp`` (``zf`` of the pinch phase); positive.
    pinch_duration_s
        ``tau``, the beam-target interaction time taken as the pinch
        duration; positive.
    diode_voltage_v
        ``U``, the diode voltage accelerating the beam; positive. The
        review's fitted rule is ``U = 3 V_max``; the TECDOC-1829 table
        prints ``U`` equal to its ``V_max`` column, so ``U`` is declared
        here and the rule is offered as :func:`diode_voltage_rule`.
    beam_energy_fraction
        ``fe``, the fraction of the pinch inductive energy converted into
        beam kinetic energy (``0.14`` in the source); in ``(0, 1]``.
    beam_ion_mass_number
        ``M`` of the beam ion (``2`` for deuterons); positive.
    beam_effective_charge
        ``Z_eff`` of the beam ion (``1`` for deuterons); positive.
    dd_neutron_cross_section_m2
        ``sigma`` of the D–D neutron branch at the beam energy; positive
        and declared (the cross-section parametrisation is a shared
        kernel, not this repository's).

    Raises
    ------
    DeviceConfigurationError
        If any value is non-finite, non-positive, or the fraction exceeds
        one.
    """

    pinch_current_a: float
    pinch_radius_m: float
    pinch_length_m: float
    pinch_duration_s: float
    diode_voltage_v: float
    beam_energy_fraction: float
    beam_ion_mass_number: float
    beam_effective_charge: float
    dd_neutron_cross_section_m2: float

    def __post_init__(self) -> None:
        """Validate every declared value.

        Raises
        ------
        DeviceConfigurationError
            If any value is non-finite, non-positive, or the fraction
            exceeds one.
        """
        require_positive("pinch_current_a", self.pinch_current_a)
        require_positive("pinch_radius_m", self.pinch_radius_m)
        require_positive("pinch_length_m", self.pinch_length_m)
        require_positive("pinch_duration_s", self.pinch_duration_s)
        require_positive("diode_voltage_v", self.diode_voltage_v)
        require_positive("beam_energy_fraction", self.beam_energy_fraction)
        if self.beam_energy_fraction > 1.0:
            raise DeviceConfigurationError(
                "beam_energy_fraction: must not exceed 1, got "
                f"{self.beam_energy_fraction!r}"
            )
        require_positive("beam_ion_mass_number", self.beam_ion_mass_number)
        require_positive("beam_effective_charge", self.beam_effective_charge)
        require_positive(
            "dd_neutron_cross_section_m2", self.dd_neutron_cross_section_m2
        )

    def to_record(self) -> dict[str, Any]:
        """Project the state to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "pinch_current_a": self.pinch_current_a,
            "pinch_radius_m": self.pinch_radius_m,
            "pinch_length_m": self.pinch_length_m,
            "pinch_duration_s": self.pinch_duration_s,
            "diode_voltage_v": self.diode_voltage_v,
            "beam_energy_fraction": self.beam_energy_fraction,
            "beam_ion_mass_number": self.beam_ion_mass_number,
            "beam_effective_charge": self.beam_effective_charge,
            "dd_neutron_cross_section_m2": self.dd_neutron_cross_section_m2,
        }


def diode_voltage_rule(peak_induced_voltage_v: float, multiplier: float = 3.0) -> float:
    """Apply the review's fitted diode-voltage rule ``U = 3 V_max``.

    Parameters
    ----------
    peak_induced_voltage_v
        ``V_max`` of the pre-pinch radial phase; strictly positive.
    multiplier
        The fitted factor (``3`` in the review; ``1`` for the strong
        radiative-collapse case where ``U = V_max*``); strictly positive.

    Returns
    -------
    float
        ``multiplier * V_max``.

    Raises
    ------
    DeviceConfigurationError
        If either value is non-finite or non-positive.
    """
    require_positive("peak_induced_voltage_v", peak_induced_voltage_v)
    require_positive("multiplier", multiplier)
    return multiplier * peak_induced_voltage_v


@dataclass(frozen=True, slots=True)
class PinchRadiation:
    """Pinch-phase closed forms at the declared state.

    Parameters
    ----------
    ion_density_per_m3
        ``N_i`` of eq. (43).
    bennett_temperature_k
        ``T`` of eq. (41).
    temperature_ev
        The same temperature in electronvolts (``k_B T / e``).
    spitzer_resistance_ohm
        ``R`` of eq. (40).
    joule_power_w
        ``R I^2 fc^2`` of eq. (39); positive.
    bremsstrahlung_power_w
        Eq. (42); negative.
    line_power_w
        Eq. (44), volumetric; negative.
    photonic_excitation_number
        ``M`` of eq. (46).
    absorption_factor
        ``A`` of eq. (47) in ``(0, 1]``.
    surface_line_power_w
        Eq. (48); negative.
    effective_line_power_w
        ``A`` times the volumetric term while ``A > 1/e``, otherwise the
        surface term.
    net_power_w
        ``dQ/dt`` of eq. (45) with the effective line term.
    """

    ion_density_per_m3: float
    bennett_temperature_k: float
    temperature_ev: float
    spitzer_resistance_ohm: float
    joule_power_w: float
    bremsstrahlung_power_w: float
    line_power_w: float
    photonic_excitation_number: float
    absorption_factor: float
    surface_line_power_w: float
    effective_line_power_w: float
    net_power_w: float

    def to_record(self) -> dict[str, Any]:
        """Project the closed forms to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "ion_density_per_m3": self.ion_density_per_m3,
            "bennett_temperature_k": self.bennett_temperature_k,
            "temperature_ev": self.temperature_ev,
            "spitzer_resistance_ohm": self.spitzer_resistance_ohm,
            "joule_power_w": self.joule_power_w,
            "bremsstrahlung_power_w": self.bremsstrahlung_power_w,
            "line_power_w": self.line_power_w,
            "photonic_excitation_number": self.photonic_excitation_number,
            "absorption_factor": self.absorption_factor,
            "surface_line_power_w": self.surface_line_power_w,
            "effective_line_power_w": self.effective_line_power_w,
            "net_power_w": self.net_power_w,
        }


def pinch_radiation(
    pinch_current_a: float,
    pinch_radius_m: float,
    pinch_length_m: float,
    anode_radius_m: float,
    molecule_density_per_m3: float,
    axial_current_factor: float,
    radial_mass_factor: float,
    dissociation_number: float,
    plasma_effective_charge: float,
    atomic_number: float,
) -> PinchRadiation:
    """Evaluate the pinch-phase closed forms at a declared state.

    Parameters
    ----------
    pinch_current_a
        ``I``; strictly positive.
    pinch_radius_m
        ``rp``; strictly positive.
    pinch_length_m
        ``zf``; strictly positive.
    anode_radius_m
        ``a``; strictly positive.
    molecule_density_per_m3
        ``N0``; strictly positive.
    axial_current_factor
        ``fc``; strictly positive.
    radial_mass_factor
        ``fmr``; strictly positive.
    dissociation_number
        ``DN``; strictly positive.
    plasma_effective_charge
        ``Z``; strictly positive (the radiation terms divide by it).
    atomic_number
        ``Z_n``; strictly positive.

    Returns
    -------
    PinchRadiation
        Density, Bennett temperature, resistance and the power terms.

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or non-positive.
    """
    require_positive("pinch_current_a", pinch_current_a)
    require_positive("pinch_radius_m", pinch_radius_m)
    require_positive("pinch_length_m", pinch_length_m)
    require_positive("anode_radius_m", anode_radius_m)
    require_positive("molecule_density_per_m3", molecule_density_per_m3)
    require_positive("axial_current_factor", axial_current_factor)
    require_positive("radial_mass_factor", radial_mass_factor)
    require_positive("dissociation_number", dissociation_number)
    require_positive("plasma_effective_charge", plasma_effective_charge)
    require_positive("atomic_number", atomic_number)
    radius_ratio = anode_radius_m / pinch_radius_m
    density = (
        molecule_density_per_m3 * radial_mass_factor * (radius_ratio * radius_ratio)
    )
    departure = dissociation_number * (1.0 + plasma_effective_charge)
    sheath_current = pinch_current_a * axial_current_factor
    temperature = (MU0 * sheath_current * sheath_current) / (
        8.0
        * PI
        * PI
        * BOLTZMANN_J_PER_K
        * departure
        * molecule_density_per_m3
        * anode_radius_m
        * anode_radius_m
        * radial_mass_factor
    )
    temperature_ev = temperature * (BOLTZMANN_J_PER_K / ELEMENTARY_CHARGE_C)
    cross_section = PI * pinch_radius_m * pinch_radius_m
    sqrt_temperature = math.sqrt(temperature)
    resistance = (SPITZER_COEFFICIENT * plasma_effective_charge * pinch_length_m) / (
        cross_section * (temperature * sqrt_temperature)
    )
    joule = resistance * sheath_current * sheath_current
    charge_cubed = (
        plasma_effective_charge * plasma_effective_charge * plasma_effective_charge
    )
    bremsstrahlung = 0.0 - (
        BREMSSTRAHLUNG_COEFFICIENT
        * (density * density)
        * cross_section
        * pinch_length_m
        * sqrt_temperature
        * charge_cubed
    )
    atomic_squared = atomic_number * atomic_number
    line = 0.0 - (
        LINE_COEFFICIENT
        * (density * density)
        * plasma_effective_charge
        * (atomic_squared * atomic_squared)
        * cross_section
        * pinch_length_m
        / temperature
    )
    sqrt_ev = math.sqrt(temperature_ev)
    excitation = (
        EXCITATION_COEFFICIENT * pinch_radius_m * math.sqrt(atomic_number) * density
    ) / (plasma_effective_charge * (temperature_ev * sqrt_ev))
    ev_cubed = temperature_ev * temperature_ev * temperature_ev
    absorption_1 = 1.0 + (
        ABSORPTION_COEFFICIENT * density * plasma_effective_charge
    ) / (ev_cubed * sqrt_ev)
    absorption_2 = 1.0 / absorption_1
    exponent = (1.0 + excitation) * natural_log(absorption_2)
    absorption = 0.0 if exponent < EXP_MIN else exponential(exponent)
    surface = 0.0 - (
        SURFACE_EMISSION_COEFFICIENT
        * math.sqrt(plasma_effective_charge)
        * (atomic_number * atomic_squared * math.sqrt(atomic_number))
        * pinch_radius_m
        * pinch_length_m
        * ((temperature * temperature) * (temperature * temperature))
    )
    effective = absorption * line if absorption > INV_E else surface
    return PinchRadiation(
        ion_density_per_m3=density,
        bennett_temperature_k=temperature,
        temperature_ev=temperature_ev,
        spitzer_resistance_ohm=resistance,
        joule_power_w=joule,
        bremsstrahlung_power_w=bremsstrahlung,
        line_power_w=line,
        photonic_excitation_number=excitation,
        absorption_factor=absorption,
        surface_line_power_w=surface,
        effective_line_power_w=effective,
        net_power_w=joule + bremsstrahlung + effective,
    )
