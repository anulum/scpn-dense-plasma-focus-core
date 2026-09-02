# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — composed level-0 physics record

"""Level-0 physics record of one validated device configuration.

The record composes the closed forms of the Lee model (S. Lee, J. Fusion
Energ. 33 (2014) 319–335; S. H. Saw and S. Lee, IAEA-TECDOC-1829 (2017);
S. Lee, ICTP 2168-10 (2012)) on the validated
:class:`~scpn_dense_plasma_focus_core.configuration.DeviceConfiguration`
together with the declared model inputs the configuration does not carry
(bank circuit values, fill gas, model factors, plasma charge state) and a
declared pinch state. It serialises canonically with a SHA-256 digest and
states its own non-claims: every number is a closed-form evaluation at
``computational_prototype`` maturity; no phase is integrated, no shot is
simulated, no current waveform is fitted, and no value describes any
real machine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.configuration import DeviceConfiguration
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import require_positive
from scpn_dense_plasma_focus_core.physics.axial import (
    AxialCharacteristics,
    axial_characteristics,
)
from scpn_dense_plasma_focus_core.physics.bank import (
    BankNormalisation,
    FillState,
    bank_normalisation,
    fill_state,
)
from scpn_dense_plasma_focus_core.physics.beam import FastIonBeam, fast_ion_beam
from scpn_dense_plasma_focus_core.physics.neutron import (
    NeutronEstimates,
    beam_target_yield,
    scaling_law_applies,
    scaling_law_yield,
)
from scpn_dense_plasma_focus_core.physics.pinch import (
    PinchRadiation,
    PinchState,
    pinch_radiation,
)
from scpn_dense_plasma_focus_core.physics.radial import (
    PinchGeometryEstimate,
    RadialCharacteristics,
    SlugRelations,
    pinch_geometry_estimate,
    radial_characteristics,
    require_specific_heat_ratio,
    slug_relations,
)

LEVEL0_SCHEMA: Final = "scpn.dense-plasma-focus-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
LEVEL0_NON_CLAIMS: Final = (
    "closed-form evaluation of the published relations of the Lee model on a "
    "synthetic configuration and a declared pinch state",
    "no phase of the model is integrated; no shot is simulated; no current "
    "waveform is fitted",
    "no yield, gain, reactivity, confinement or breakeven statement; the "
    "beam-target and scaling-law values are consistency instruments at the "
    "declared inputs",
    "no value describes or validates any real machine; the anchors reproduce "
    "numbers printed in the sources, which are themselves outputs of the "
    "fitted code",
)
#: Relative tolerance between the declared bank energy and ``C0 V0^2 / 2``
#: (the source's own table rounds ``E0`` to one significant digit for
#: sub-kilojoule machines, a 2 % gap; 5 % still rejects a wrong unit).
BANK_ENERGY_CONSISTENCY: Final = 0.05


def require_fraction(name: str, value: float) -> float:
    """Return ``value`` when strictly positive and at most one.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Model factor under validation.

    Returns
    -------
    float
        The validated factor.

    Raises
    ------
    DeviceConfigurationError
        If the value is non-finite, non-positive or greater than one.
    """
    require_positive(name, value)
    if value > 1.0:
        raise DeviceConfigurationError(f"{name}: must not exceed 1, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class ModelInputs:
    """Declared inputs of the level-0 models beyond the configuration.

    Parameters
    ----------
    bank_capacitance_f
        ``C0``; positive.
    bank_inductance_h
        ``L0``; positive.
    bank_resistance_ohm
        ``r0``; positive.
    charge_voltage_v
        ``V0``; positive.
    fill_molecular_mass_amu
        ``M`` of the fill molecule (``4`` for deuterium); positive.
    fill_temperature_k
        ``T0`` of the fill; positive (the sources do not print it).
    dissociation_number
        ``DN`` (``2`` for deuterium); positive.
    specific_heat_ratio
        ``gamma``; greater than one.
    axial_mass_factor
        ``fm`` in ``(0, 1]``.
    axial_current_factor
        ``fc`` in ``(0, 1]``.
    radial_mass_factor
        ``fmr`` in ``(0, 1]``.
    radial_current_factor
        ``fcr`` in ``(0, 1]`` (declared for completeness; the level-0
        closed forms use ``fc`` as the review prints them).
    plasma_effective_charge
        ``Z`` of the pinch plasma (``1`` for fully ionised deuterium);
        positive.
    atomic_number
        ``Z_n`` of the fill (``1`` for deuterium); positive.

    Raises
    ------
    DeviceConfigurationError
        If any input violates its bound.
    """

    bank_capacitance_f: float
    bank_inductance_h: float
    bank_resistance_ohm: float
    charge_voltage_v: float
    fill_molecular_mass_amu: float
    fill_temperature_k: float
    dissociation_number: float
    specific_heat_ratio: float
    axial_mass_factor: float
    axial_current_factor: float
    radial_mass_factor: float
    radial_current_factor: float
    plasma_effective_charge: float
    atomic_number: float

    def __post_init__(self) -> None:
        """Validate every declared input.

        Raises
        ------
        DeviceConfigurationError
            If any input violates its bound.
        """
        require_positive("bank_capacitance_f", self.bank_capacitance_f)
        require_positive("bank_inductance_h", self.bank_inductance_h)
        require_positive("bank_resistance_ohm", self.bank_resistance_ohm)
        require_positive("charge_voltage_v", self.charge_voltage_v)
        require_positive("fill_molecular_mass_amu", self.fill_molecular_mass_amu)
        require_positive("fill_temperature_k", self.fill_temperature_k)
        require_positive("dissociation_number", self.dissociation_number)
        require_specific_heat_ratio(self.specific_heat_ratio)
        require_fraction("axial_mass_factor", self.axial_mass_factor)
        require_fraction("axial_current_factor", self.axial_current_factor)
        require_fraction("radial_mass_factor", self.radial_mass_factor)
        require_fraction("radial_current_factor", self.radial_current_factor)
        require_positive("plasma_effective_charge", self.plasma_effective_charge)
        require_positive("atomic_number", self.atomic_number)

    def to_record(self) -> dict[str, Any]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "bank_capacitance_f": self.bank_capacitance_f,
            "bank_inductance_h": self.bank_inductance_h,
            "bank_resistance_ohm": self.bank_resistance_ohm,
            "charge_voltage_v": self.charge_voltage_v,
            "fill_molecular_mass_amu": self.fill_molecular_mass_amu,
            "fill_temperature_k": self.fill_temperature_k,
            "dissociation_number": self.dissociation_number,
            "specific_heat_ratio": self.specific_heat_ratio,
            "axial_mass_factor": self.axial_mass_factor,
            "axial_current_factor": self.axial_current_factor,
            "radial_mass_factor": self.radial_mass_factor,
            "radial_current_factor": self.radial_current_factor,
            "plasma_effective_charge": self.plasma_effective_charge,
            "atomic_number": self.atomic_number,
        }


@dataclass(frozen=True, slots=True)
class Level0PhysicsRecord:
    """The level-0 models evaluated on one configuration and pinch state.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the record was built from.
    inputs
        Declared model inputs.
    pinch_state
        Declared pinch state.
    drive_parameter_ka_per_cm_sqrt_torr
        The configuration's Lee–Serban drive parameter.
    bank
        Circuit normalisation and scaling parameters.
    fill
        Fill-gas state.
    axial
        Axial-phase characteristic quantities.
    radial
        Radial-phase characteristic quantities.
    geometry
        Rule-of-thumb pinch geometry.
    slug
        Slug relations at the pinch current and radius.
    pinch
        Pinch-phase closed forms.
    beam
        Fast-ion-beam quantities.
    neutron
        Beam-target and scaling-law yields.
    """

    configuration_digest_sha256: str
    inputs: ModelInputs
    pinch_state: PinchState
    drive_parameter_ka_per_cm_sqrt_torr: float
    bank: BankNormalisation
    fill: FillState
    axial: AxialCharacteristics
    radial: RadialCharacteristics
    geometry: PinchGeometryEstimate
    slug: SlugRelations
    pinch: PinchRadiation
    beam: FastIonBeam
    neutron: NeutronEstimates

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            Schema identity, non-claims, and every model record.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "non_claims": list(LEVEL0_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "inputs": self.inputs.to_record(),
            "pinch_state": self.pinch_state.to_record(),
            "drive_parameter_ka_per_cm_sqrt_torr": (
                self.drive_parameter_ka_per_cm_sqrt_torr
            ),
            "bank": self.bank.to_record(),
            "fill": self.fill.to_record(),
            "axial": self.axial.to_record(),
            "radial": self.radial.to_record(),
            "geometry": self.geometry.to_record(),
            "slug": self.slug.to_record(),
            "pinch": self.pinch.to_record(),
            "beam": self.beam.to_record(),
            "neutron": self.neutron.to_record(),
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(
    configuration: DeviceConfiguration, inputs: ModelInputs, pinch_state: PinchState
) -> Level0PhysicsRecord:
    """Evaluate every level-0 model on a validated configuration.

    Parameters
    ----------
    configuration
        Validated device configuration (electrodes, bank energy, peak
        current, fill pressure).
    inputs
        Declared model inputs.
    pinch_state
        Declared pinch state.

    Returns
    -------
    Level0PhysicsRecord
        The composed record.

    Raises
    ------
    DeviceConfigurationError
        If the declared circuit energy ``C0 V0^2 / 2`` differs from the
        configuration's bank energy by more than 5 %, the pinch current
        exceeds the configuration's peak current, or the pinch radius is
        not smaller than the anode radius.
    """
    electrodes = configuration.electrodes
    bank = bank_normalisation(
        inputs.bank_capacitance_f,
        inputs.bank_inductance_h,
        inputs.bank_resistance_ohm,
        inputs.charge_voltage_v,
        electrodes.anode_radius_m,
        electrodes.cathode_radius_m,
        electrodes.anode_length_m,
    )
    declared_energy = configuration.bank.bank_energy_kj * 1.0e3
    if (
        abs(bank.bank_energy_j - declared_energy)
        > BANK_ENERGY_CONSISTENCY * declared_energy
    ):
        raise DeviceConfigurationError(
            "bank_energy_kj: the configuration declares "
            f"{declared_energy!r} J but C0 V0^2 / 2 = {bank.bank_energy_j!r} J "
            f"(tolerance {BANK_ENERGY_CONSISTENCY:.0%})"
        )
    peak_current = configuration.bank.peak_current_ma * 1.0e6
    if pinch_state.pinch_current_a > peak_current:
        raise DeviceConfigurationError(
            "pinch_current_a: must not exceed the configuration's peak current, "
            f"got {pinch_state.pinch_current_a!r} > {peak_current!r}"
        )
    if pinch_state.pinch_radius_m >= electrodes.anode_radius_m:
        raise DeviceConfigurationError(
            "pinch_radius_m: must be smaller than anode_radius_m, got "
            f"{pinch_state.pinch_radius_m!r} >= {electrodes.anode_radius_m!r}"
        )
    fill = fill_state(
        configuration.bank.fill_pressure_torr,
        inputs.fill_molecular_mass_amu,
        inputs.fill_temperature_k,
    )
    axial = axial_characteristics(
        bank.characteristic_time_s,
        bank.characteristic_current_a,
        electrodes.anode_radius_m,
        electrodes.cathode_radius_m,
        electrodes.anode_length_m,
        bank.log_radius_ratio,
        fill.mass_density_kg_m3,
        inputs.axial_mass_factor,
        inputs.axial_current_factor,
        peak_current,
    )
    radial = radial_characteristics(
        axial.axial_transit_time_s,
        bank.characteristic_current_a,
        electrodes.anode_radius_m,
        electrodes.cathode_radius_m,
        electrodes.anode_length_m,
        bank.log_radius_ratio,
        bank.inductance_ratio,
        fill.mass_density_kg_m3,
        inputs.axial_current_factor,
        inputs.radial_mass_factor,
        inputs.specific_heat_ratio,
    )
    slug = slug_relations(
        pinch_state.pinch_current_a,
        pinch_state.pinch_radius_m,
        fill.mass_density_kg_m3,
        inputs.axial_current_factor,
        inputs.radial_mass_factor,
        inputs.specific_heat_ratio,
        inputs.fill_molecular_mass_amu,
        inputs.dissociation_number,
        inputs.plasma_effective_charge,
    )
    pinch = pinch_radiation(
        pinch_state.pinch_current_a,
        pinch_state.pinch_radius_m,
        pinch_state.pinch_length_m,
        electrodes.anode_radius_m,
        fill.molecule_density_per_m3,
        inputs.axial_current_factor,
        inputs.radial_mass_factor,
        inputs.dissociation_number,
        inputs.plasma_effective_charge,
        inputs.atomic_number,
    )
    beam = fast_ion_beam(
        pinch_state.pinch_current_a,
        pinch_state.pinch_radius_m,
        electrodes.cathode_radius_m,
        pinch_state.diode_voltage_v,
        pinch_state.pinch_duration_s,
        pinch_state.beam_energy_fraction,
        pinch_state.beam_ion_mass_number,
        pinch_state.beam_effective_charge,
    )
    neutron = NeutronEstimates(
        beam_target_yield=beam_target_yield(
            pinch.ion_density_per_m3,
            pinch_state.pinch_current_a,
            pinch_state.pinch_length_m,
            electrodes.cathode_radius_m,
            pinch_state.pinch_radius_m,
            pinch_state.dd_neutron_cross_section_m2,
            pinch_state.diode_voltage_v,
        ),
        scaling_law_yield=(
            scaling_law_yield(pinch_state.pinch_current_a)
            if scaling_law_applies(pinch_state.pinch_current_a)
            else None
        ),
    )
    return Level0PhysicsRecord(
        configuration_digest_sha256=configuration.digest_sha256(),
        inputs=inputs,
        pinch_state=pinch_state,
        drive_parameter_ka_per_cm_sqrt_torr=configuration.drive_parameter(),
        bank=bank,
        fill=fill,
        axial=axial,
        radial=radial,
        geometry=pinch_geometry_estimate(electrodes.anode_radius_m),
        slug=slug,
        pinch=pinch,
        beam=beam,
        neutron=neutron,
    )
