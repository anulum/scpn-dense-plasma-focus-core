# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — fast ion beam closed forms

"""Fast-ion-beam flux, fluence and derived quantities at a declared pinch state.

The extended Lee model derives the beam ion flux from the fraction ``fe``
of the pinch inductive energy converted into beam kinetic energy and the
diode voltage ``U`` (S. H. Saw and S. Lee in IAEA-TECDOC-1829 (2017),
pp. 84–86): the beam speed ``v_b = [2 e Z_eff U / (M m_p)]^(1/2)``
(eq. 5) and the flux
``J_b = 2.75e15 fe / (M Z_eff)^(1/2) ln(b / rp) / rp^2 I_pinch^2 / U^(1/2)``
(eq. 6, the printed constant being the source's rounding of
``mu0 / (2.83 pi^2 (e m_p)^(1/2))``, kept as printed so the tabulated
values are reproduced). The derived quantities follow the source's list
(a)–(k): energy flux ``J_b Z_eff e U``, power flow, current density,
ion current, ions per second, fluence ``J_b tau``, energy fluence, ions
in the beam, beam energy and the damage factor ``J_b Z_eff e U tau^(1/2)``.
Anchors: the PF1000, NX3 and INTI columns of the source's Table 1 within
3 % and the PF400J column within 12 % (its two-digit pinch radius enters
as ``rp^-2``). No value describes any machine's behaviour: the anchors
reproduce numbers printed in the source, which are themselves outputs of
the fitted code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics._transcendental import natural_log
from scpn_dense_plasma_focus_core.physics.constants import (
    ELEMENTARY_CHARGE_C,
    PI,
    PROTON_MASS_KG,
)

#: Flux coefficient of eq. (6), ``mu0 / (2.83 pi^2 (e m_p)^(1/2))`` as printed.
FLUX_COEFFICIENT: Final = 2.75e15


@dataclass(frozen=True, slots=True)
class FastIonBeam:
    """Fast-ion-beam quantities at the declared pinch state.

    Parameters
    ----------
    beam_speed_m_s
        ``v_b`` of eq. (5).
    flux_per_m2_s
        ``J_b`` of eq. (6).
    energy_flux_w_m2
        ``J_b Z_eff e U``.
    power_flow_w
        Energy flux times the pinch cross-section.
    current_density_a_m2
        ``J_b e Z_eff``.
    ion_current_a
        Current density times the pinch cross-section.
    ions_per_s
        ``J_b`` times the pinch cross-section.
    fluence_per_m2
        ``J_b tau``.
    energy_fluence_j_m2
        Fluence times ``Z_eff e U``.
    ions_in_beam
        Fluence times the pinch cross-section.
    beam_energy_j
        Ions in the beam times ``Z_eff e U``.
    damage_factor_w_m2_sqrt_s
        ``J_b Z_eff e U tau^(1/2)``.
    """

    beam_speed_m_s: float
    flux_per_m2_s: float
    energy_flux_w_m2: float
    power_flow_w: float
    current_density_a_m2: float
    ion_current_a: float
    ions_per_s: float
    fluence_per_m2: float
    energy_fluence_j_m2: float
    ions_in_beam: float
    beam_energy_j: float
    damage_factor_w_m2_sqrt_s: float

    def to_record(self) -> dict[str, Any]:
        """Project the beam quantities to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "beam_speed_m_s": self.beam_speed_m_s,
            "flux_per_m2_s": self.flux_per_m2_s,
            "energy_flux_w_m2": self.energy_flux_w_m2,
            "power_flow_w": self.power_flow_w,
            "current_density_a_m2": self.current_density_a_m2,
            "ion_current_a": self.ion_current_a,
            "ions_per_s": self.ions_per_s,
            "fluence_per_m2": self.fluence_per_m2,
            "energy_fluence_j_m2": self.energy_fluence_j_m2,
            "ions_in_beam": self.ions_in_beam,
            "beam_energy_j": self.beam_energy_j,
            "damage_factor_w_m2_sqrt_s": self.damage_factor_w_m2_sqrt_s,
        }


def fast_ion_beam(
    pinch_current_a: float,
    pinch_radius_m: float,
    cathode_radius_m: float,
    diode_voltage_v: float,
    pinch_duration_s: float,
    beam_energy_fraction: float,
    beam_ion_mass_number: float,
    beam_effective_charge: float,
) -> FastIonBeam:
    """Evaluate the fast-ion-beam closed forms.

    Parameters
    ----------
    pinch_current_a
        ``I_pinch``; strictly positive.
    pinch_radius_m
        ``rp``; strictly positive and smaller than the cathode radius.
    cathode_radius_m
        ``b``; strictly positive.
    diode_voltage_v
        ``U``; strictly positive.
    pinch_duration_s
        ``tau``; strictly positive.
    beam_energy_fraction
        ``fe``; strictly positive.
    beam_ion_mass_number
        ``M``; strictly positive.
    beam_effective_charge
        ``Z_eff``; strictly positive.

    Returns
    -------
    FastIonBeam
        Speed, flux and the derived quantities (a)–(k).

    Raises
    ------
    DeviceConfigurationError
        If any input is non-finite or non-positive, or the pinch radius is
        not smaller than the cathode radius.
    """
    require_positive("pinch_current_a", pinch_current_a)
    require_positive("pinch_radius_m", pinch_radius_m)
    require_positive("cathode_radius_m", cathode_radius_m)
    require_positive("diode_voltage_v", diode_voltage_v)
    require_positive("pinch_duration_s", pinch_duration_s)
    require_positive("beam_energy_fraction", beam_energy_fraction)
    require_positive("beam_ion_mass_number", beam_ion_mass_number)
    require_positive("beam_effective_charge", beam_effective_charge)
    if pinch_radius_m >= cathode_radius_m:
        raise DeviceConfigurationError(
            "pinch_radius_m: must be smaller than cathode_radius_m, got "
            f"{pinch_radius_m!r} >= {cathode_radius_m!r}"
        )
    speed = math.sqrt(
        (2.0 * ELEMENTARY_CHARGE_C * beam_effective_charge * diode_voltage_v)
        / (beam_ion_mass_number * PROTON_MASS_KG)
    )
    log_ratio = natural_log(cathode_radius_m / pinch_radius_m)
    flux = (
        (FLUX_COEFFICIENT * beam_energy_fraction)
        / math.sqrt(beam_ion_mass_number * beam_effective_charge)
        * (log_ratio / (pinch_radius_m * pinch_radius_m))
        * ((pinch_current_a * pinch_current_a) / math.sqrt(diode_voltage_v))
    )
    ion_energy = beam_effective_charge * ELEMENTARY_CHARGE_C * diode_voltage_v
    cross_section = PI * pinch_radius_m * pinch_radius_m
    energy_flux = flux * ion_energy
    current_density = flux * ELEMENTARY_CHARGE_C * beam_effective_charge
    fluence = flux * pinch_duration_s
    ions = fluence * cross_section
    return FastIonBeam(
        beam_speed_m_s=speed,
        flux_per_m2_s=flux,
        energy_flux_w_m2=energy_flux,
        power_flow_w=energy_flux * cross_section,
        current_density_a_m2=current_density,
        ion_current_a=current_density * cross_section,
        ions_per_s=flux * cross_section,
        fluence_per_m2=fluence,
        energy_fluence_j_m2=fluence * ion_energy,
        ions_in_beam=ions,
        beam_energy_j=ions * ion_energy,
        damage_factor_w_m2_sqrt_s=energy_flux * math.sqrt(pinch_duration_s),
    )
