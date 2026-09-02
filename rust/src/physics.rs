// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Dense Plasma Focus Core — level-0 closed forms of the Lee model

//! Closed forms of the Lee model mirrored operation for operation from
//! `scpn_dense_plasma_focus_core.physics`: bank normalisation, fill state,
//! axial and radial characteristic quantities, slug relations, the
//! rule-of-thumb pinch geometry, the pinch-phase power terms, the fast ion
//! beam chain and the neutron estimates. Input validation is the Python
//! floor's responsibility; the kernels here assume admissible inputs
//! except where a vendored kernel refuses (logarithm, power).

use std::fmt;

use crate::transcendental::{exponential, natural_log, power, NumericsError, EXP_MIN};
use crate::{
    BOLTZMANN_J_PER_K, ELEMENTARY_CHARGE_C, INV_E, MOLAR_GAS_CONSTANT_J_PER_KMOL_K, MU0,
    PASCAL_PER_TORR, PI, PROTON_MASS_KG,
};

/// Reflected-shock speed as a fraction of the on-axis shock speed (eq. 34).
pub const REFLECTED_SHOCK_FRACTION: f64 = 0.3;
/// Rule-of-thumb pinch geometry for deuterium (ICTP 2168-10, Table 3).
pub const RULE_MIN_RADIUS_RATIO: f64 = 0.15;
/// Rule-of-thumb maximum pinch length ratio.
pub const RULE_MAX_LENGTH_RATIO: f64 = 1.5;
/// Rule-of-thumb radial-shock transit per metre of anode radius.
pub const RULE_SHOCK_TRANSIT_S_PER_M: f64 = 5.0e-6;
/// Rule-of-thumb pinch lifetime per metre of anode radius.
pub const RULE_PINCH_LIFETIME_S_PER_M: f64 = 1.0e-6;
/// Spitzer resistance coefficient of eq. (40), SI.
pub const SPITZER_COEFFICIENT: f64 = 1290.0;
/// Bremsstrahlung coefficient of eq. (42), SI.
pub const BREMSSTRAHLUNG_COEFFICIENT: f64 = 1.6e-40;
/// Line-radiation coefficient of eq. (44), SI.
pub const LINE_COEFFICIENT: f64 = 4.6e-31;
/// Photonic excitation coefficient of eq. (46), `T` in eV.
pub const EXCITATION_COEFFICIENT: f64 = 1.66e-15;
/// Self-absorption coefficient of eq. (47), `T` in eV.
pub const ABSORPTION_COEFFICIENT: f64 = 1.0e-14;
/// Surface-emission coefficient of eq. (48), SI.
pub const SURFACE_EMISSION_COEFFICIENT: f64 = 4.62e-16;
/// Flux coefficient of TECDOC-1829 eq. (6) as printed.
pub const FLUX_COEFFICIENT: f64 = 2.75e15;
/// Beam-target constant of TECDOC-1829 eq. (1), SI units.
pub const BEAM_TARGET_CONSTANT: f64 = 8.54e8;
/// Empirical scaling law coefficient (`I` in MA).
pub const SCALING_COEFFICIENT: f64 = 9.0e10;
/// Empirical scaling law exponent.
pub const SCALING_EXPONENT: f64 = 3.8;
/// Stated range of the scaling law in amperes.
pub const SCALING_RANGE_A: (f64, f64) = (1.0e5, 1.0e6);

/// Rejection of an inadmissible input of a kernel that validates.
#[derive(Debug, Clone, PartialEq)]
pub struct PhysicsError {
    /// Human-readable description naming the field and the violated bound.
    pub message: String,
}

impl fmt::Display for PhysicsError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

impl std::error::Error for PhysicsError {}

impl From<NumericsError> for PhysicsError {
    fn from(error: NumericsError) -> Self {
        PhysicsError {
            message: error.message,
        }
    }
}

/// Bank normalisation and scaling parameters (Lee 2014, eqs. 4–6, 9).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct BankNormalisation {
    pub bank_energy_j: f64,
    pub characteristic_time_s: f64,
    pub surge_impedance_ohm: f64,
    pub characteristic_current_a: f64,
    pub quarter_period_s: f64,
    pub damping_ratio: f64,
    pub log_radius_ratio: f64,
    pub axial_inductance_h: f64,
    pub inductance_ratio: f64,
}

/// Bank normalisation, see the Python floor `bank.bank_normalisation`.
///
/// # Errors
///
/// Returns [`PhysicsError`] when the radii are not ordered (the vendored
/// logarithm would refuse a non-positive ratio otherwise).
pub fn bank_normalisation(
    capacitance_f: f64,
    inductance_h: f64,
    resistance_ohm: f64,
    charge_voltage_v: f64,
    anode_radius_m: f64,
    cathode_radius_m: f64,
    anode_length_m: f64,
) -> Result<BankNormalisation, PhysicsError> {
    if cathode_radius_m <= anode_radius_m {
        return Err(PhysicsError {
            message: format!(
                "cathode_radius_m: must be strictly greater than anode_radius_m, got {cathode_radius_m:?} <= {anode_radius_m:?}"
            ),
        });
    }
    let energy = 0.5 * capacitance_f * charge_voltage_v * charge_voltage_v;
    let time = (inductance_h * capacitance_f).sqrt();
    let impedance = (inductance_h / capacitance_f).sqrt();
    let current = charge_voltage_v / impedance;
    let quarter = (PI / 2.0) * time;
    let damping = resistance_ohm / impedance;
    let log_ratio = natural_log(cathode_radius_m / anode_radius_m)?;
    let axial_inductance = (MU0 / (2.0 * PI)) * log_ratio * anode_length_m;
    Ok(BankNormalisation {
        bank_energy_j: energy,
        characteristic_time_s: time,
        surge_impedance_ohm: impedance,
        characteristic_current_a: current,
        quarter_period_s: quarter,
        damping_ratio: damping,
        log_radius_ratio: log_ratio,
        axial_inductance_h: axial_inductance,
        inductance_ratio: inductance_h / axial_inductance,
    })
}

/// Ideal-gas fill state.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct FillState {
    pub pressure_pa: f64,
    pub molecular_mass_kg: f64,
    pub molecule_density_per_m3: f64,
    pub mass_density_kg_m3: f64,
}

/// Fill state, see the Python floor `bank.fill_state`.
#[must_use]
pub fn fill_state(pressure_torr: f64, molecular_mass_amu: f64, temperature_k: f64) -> FillState {
    let pressure = pressure_torr * PASCAL_PER_TORR;
    let mass = molecular_mass_amu * PROTON_MASS_KG;
    let density = pressure / (BOLTZMANN_J_PER_K * temperature_k);
    FillState {
        pressure_pa: pressure,
        molecular_mass_kg: mass,
        molecule_density_per_m3: density,
        mass_density_kg_m3: density * mass,
    }
}

/// Axial-phase characteristic quantities (Lee 2014, eqs. 5–7 and eq. 1 at rest).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct AxialCharacteristics {
    pub axial_transit_time_s: f64,
    pub alpha: f64,
    pub characteristic_axial_speed_m_s: f64,
    pub terminal_sheath_speed_m_s: f64,
}

/// Axial characteristics, see the Python floor `axial.axial_characteristics`.
#[must_use]
#[allow(clippy::too_many_arguments)]
pub fn axial_characteristics(
    characteristic_time_s: f64,
    characteristic_current_a: f64,
    anode_radius_m: f64,
    cathode_radius_m: f64,
    anode_length_m: f64,
    log_radius_ratio: f64,
    mass_density_kg_m3: f64,
    axial_mass_factor: f64,
    axial_current_factor: f64,
    drive_current_a: f64,
) -> AxialCharacteristics {
    let ratio = cathode_radius_m / anode_radius_m;
    let geometry = (4.0 * PI * PI * (ratio * ratio - 1.0)) / (MU0 * log_radius_ratio);
    let drive = (characteristic_current_a / anode_radius_m) / mass_density_kg_m3.sqrt();
    let transit =
        geometry.sqrt() * (axial_mass_factor.sqrt() / axial_current_factor) * anode_length_m
            / drive;
    let terminal = (((axial_current_factor * axial_current_factor) / axial_mass_factor)
        * ((MU0 * log_radius_ratio)
            / (4.0 * PI * PI * mass_density_kg_m3 * (ratio * ratio - 1.0))))
        .sqrt()
        * (drive_current_a / anode_radius_m);
    AxialCharacteristics {
        axial_transit_time_s: transit,
        alpha: characteristic_time_s / transit,
        characteristic_axial_speed_m_s: anode_length_m / transit,
        terminal_sheath_speed_m_s: terminal,
    }
}

/// Radial-phase characteristic quantities (Lee 2014, eqs. 24–28).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct RadialCharacteristics {
    pub radial_transit_time_s: f64,
    pub characteristic_radial_speed_m_s: f64,
    pub alpha1: f64,
    pub aspect_ratio: f64,
    pub beta1: f64,
    pub geometric_speed_ratio: f64,
}

/// Radial characteristics, see the Python floor `radial.radial_characteristics`.
#[must_use]
#[allow(clippy::too_many_arguments)]
pub fn radial_characteristics(
    axial_transit_time_s: f64,
    characteristic_current_a: f64,
    anode_radius_m: f64,
    cathode_radius_m: f64,
    anode_length_m: f64,
    log_radius_ratio: f64,
    inductance_ratio: f64,
    mass_density_kg_m3: f64,
    axial_current_factor: f64,
    radial_mass_factor: f64,
    specific_heat_ratio: f64,
) -> RadialCharacteristics {
    let ratio = cathode_radius_m / anode_radius_m;
    let drive = (characteristic_current_a / anode_radius_m) / mass_density_kg_m3.sqrt();
    let transit = (4.0 * PI) / (MU0 * (specific_heat_ratio + 1.0)).sqrt()
        * (radial_mass_factor.sqrt() / axial_current_factor)
        * anode_radius_m
        / drive;
    let aspect = anode_length_m / anode_radius_m;
    RadialCharacteristics {
        radial_transit_time_s: transit,
        characteristic_radial_speed_m_s: anode_radius_m / transit,
        alpha1: axial_transit_time_s / transit,
        aspect_ratio: aspect,
        beta1: inductance_ratio / (aspect * log_radius_ratio),
        geometric_speed_ratio: (((ratio * ratio - 1.0) * (specific_heat_ratio + 1.0))
            / (4.0 * log_radius_ratio))
            .sqrt(),
    }
}

/// Instantaneous slug relations (Lee 2014, eqs. 14, 15, 32, 34).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SlugRelations {
    pub shock_speed_m_s: f64,
    pub elongation_speed_m_s: f64,
    pub shock_temperature_k: f64,
    pub reflected_shock_speed_m_s: f64,
}

/// Slug relations, see the Python floor `radial.slug_relations`.
#[must_use]
#[allow(clippy::too_many_arguments)]
pub fn slug_relations(
    current_a: f64,
    piston_radius_m: f64,
    mass_density_kg_m3: f64,
    axial_current_factor: f64,
    radial_mass_factor: f64,
    specific_heat_ratio: f64,
    molecular_mass_amu: f64,
    dissociation_number: f64,
    plasma_effective_charge: f64,
) -> SlugRelations {
    let shock = 0.0
        - ((MU0 * (specific_heat_ratio + 1.0)) / mass_density_kg_m3).sqrt()
            * (axial_current_factor / radial_mass_factor.sqrt())
            * (current_a / (4.0 * PI * piston_radius_m));
    let elongation = 0.0 - (2.0 / (specific_heat_ratio + 1.0)) * shock;
    let departure = dissociation_number * (1.0 + plasma_effective_charge);
    let temperature = (molecular_mass_amu / (MOLAR_GAS_CONSTANT_J_PER_KMOL_K * departure))
        * ((2.0 * (specific_heat_ratio - 1.0))
            / ((specific_heat_ratio + 1.0) * (specific_heat_ratio + 1.0)))
        * (shock * shock);
    SlugRelations {
        shock_speed_m_s: shock,
        elongation_speed_m_s: elongation,
        shock_temperature_k: temperature,
        reflected_shock_speed_m_s: 0.0 - REFLECTED_SHOCK_FRACTION * shock,
    }
}

/// Rule-of-thumb pinch geometry (ICTP 2168-10, Table 3).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PinchGeometryEstimate {
    pub minimum_radius_m: f64,
    pub maximum_length_m: f64,
    pub shock_transit_time_s: f64,
    pub pinch_lifetime_s: f64,
}

/// Rule-of-thumb geometry, see the Python floor `radial.pinch_geometry_estimate`.
#[must_use]
pub fn pinch_geometry_estimate(anode_radius_m: f64) -> PinchGeometryEstimate {
    PinchGeometryEstimate {
        minimum_radius_m: RULE_MIN_RADIUS_RATIO * anode_radius_m,
        maximum_length_m: RULE_MAX_LENGTH_RATIO * anode_radius_m,
        shock_transit_time_s: RULE_SHOCK_TRANSIT_S_PER_M * anode_radius_m,
        pinch_lifetime_s: RULE_PINCH_LIFETIME_S_PER_M * anode_radius_m,
    }
}

/// Pinch-phase closed forms (Lee 2014, eqs. 39–48).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct PinchRadiation {
    pub ion_density_per_m3: f64,
    pub bennett_temperature_k: f64,
    pub temperature_ev: f64,
    pub spitzer_resistance_ohm: f64,
    pub joule_power_w: f64,
    pub bremsstrahlung_power_w: f64,
    pub line_power_w: f64,
    pub photonic_excitation_number: f64,
    pub absorption_factor: f64,
    pub surface_line_power_w: f64,
    pub effective_line_power_w: f64,
    pub net_power_w: f64,
}

/// Pinch radiation, see the Python floor `pinch.pinch_radiation`.
///
/// # Errors
///
/// Returns [`PhysicsError`] only when a vendored kernel refuses an
/// argument (a non-normal absorption base).
#[allow(clippy::too_many_arguments)]
pub fn pinch_radiation(
    pinch_current_a: f64,
    pinch_radius_m: f64,
    pinch_length_m: f64,
    anode_radius_m: f64,
    molecule_density_per_m3: f64,
    axial_current_factor: f64,
    radial_mass_factor: f64,
    dissociation_number: f64,
    plasma_effective_charge: f64,
    atomic_number: f64,
) -> Result<PinchRadiation, PhysicsError> {
    let radius_ratio = anode_radius_m / pinch_radius_m;
    let density = molecule_density_per_m3 * radial_mass_factor * (radius_ratio * radius_ratio);
    let departure = dissociation_number * (1.0 + plasma_effective_charge);
    let sheath_current = pinch_current_a * axial_current_factor;
    let temperature = (MU0 * sheath_current * sheath_current)
        / (8.0
            * PI
            * PI
            * BOLTZMANN_J_PER_K
            * departure
            * molecule_density_per_m3
            * anode_radius_m
            * anode_radius_m
            * radial_mass_factor);
    let temperature_ev = temperature * (BOLTZMANN_J_PER_K / ELEMENTARY_CHARGE_C);
    let cross_section = PI * pinch_radius_m * pinch_radius_m;
    let sqrt_temperature = temperature.sqrt();
    let resistance = (SPITZER_COEFFICIENT * plasma_effective_charge * pinch_length_m)
        / (cross_section * (temperature * sqrt_temperature));
    let joule = resistance * sheath_current * sheath_current;
    let charge_cubed = plasma_effective_charge * plasma_effective_charge * plasma_effective_charge;
    let bremsstrahlung = 0.0
        - (BREMSSTRAHLUNG_COEFFICIENT
            * (density * density)
            * cross_section
            * pinch_length_m
            * sqrt_temperature
            * charge_cubed);
    let atomic_squared = atomic_number * atomic_number;
    let line = 0.0
        - (LINE_COEFFICIENT
            * (density * density)
            * plasma_effective_charge
            * (atomic_squared * atomic_squared)
            * cross_section
            * pinch_length_m
            / temperature);
    let sqrt_ev = temperature_ev.sqrt();
    let excitation = (EXCITATION_COEFFICIENT * pinch_radius_m * atomic_number.sqrt() * density)
        / (plasma_effective_charge * (temperature_ev * sqrt_ev));
    let ev_cubed = temperature_ev * temperature_ev * temperature_ev;
    let absorption_1 =
        1.0 + (ABSORPTION_COEFFICIENT * density * plasma_effective_charge) / (ev_cubed * sqrt_ev);
    let absorption_2 = 1.0 / absorption_1;
    let exponent = (1.0 + excitation) * natural_log(absorption_2)?;
    let absorption = if exponent < EXP_MIN {
        0.0
    } else {
        exponential(exponent)?
    };
    let surface = 0.0
        - (SURFACE_EMISSION_COEFFICIENT
            * plasma_effective_charge.sqrt()
            * (atomic_number * atomic_squared * atomic_number.sqrt())
            * pinch_radius_m
            * pinch_length_m
            * ((temperature * temperature) * (temperature * temperature)));
    let effective = if absorption > INV_E {
        absorption * line
    } else {
        surface
    };
    Ok(PinchRadiation {
        ion_density_per_m3: density,
        bennett_temperature_k: temperature,
        temperature_ev,
        spitzer_resistance_ohm: resistance,
        joule_power_w: joule,
        bremsstrahlung_power_w: bremsstrahlung,
        line_power_w: line,
        photonic_excitation_number: excitation,
        absorption_factor: absorption,
        surface_line_power_w: surface,
        effective_line_power_w: effective,
        net_power_w: joule + bremsstrahlung + effective,
    })
}

/// Fast-ion-beam chain (TECDOC-1829, eqs. 5–6 and items (a)–(k)).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct FastIonBeam {
    pub beam_speed_m_s: f64,
    pub flux_per_m2_s: f64,
    pub energy_flux_w_m2: f64,
    pub power_flow_w: f64,
    pub current_density_a_m2: f64,
    pub ion_current_a: f64,
    pub ions_per_s: f64,
    pub fluence_per_m2: f64,
    pub energy_fluence_j_m2: f64,
    pub ions_in_beam: f64,
    pub beam_energy_j: f64,
    pub damage_factor_w_m2_sqrt_s: f64,
}

/// Fast ion beam, see the Python floor `beam.fast_ion_beam`.
///
/// # Errors
///
/// Returns [`PhysicsError`] when the pinch radius is not smaller than the
/// cathode radius.
#[allow(clippy::too_many_arguments)]
pub fn fast_ion_beam(
    pinch_current_a: f64,
    pinch_radius_m: f64,
    cathode_radius_m: f64,
    diode_voltage_v: f64,
    pinch_duration_s: f64,
    beam_energy_fraction: f64,
    beam_ion_mass_number: f64,
    beam_effective_charge: f64,
) -> Result<FastIonBeam, PhysicsError> {
    if pinch_radius_m >= cathode_radius_m {
        return Err(PhysicsError {
            message: format!(
                "pinch_radius_m: must be smaller than cathode_radius_m, got {pinch_radius_m:?} >= {cathode_radius_m:?}"
            ),
        });
    }
    let speed = ((2.0 * ELEMENTARY_CHARGE_C * beam_effective_charge * diode_voltage_v)
        / (beam_ion_mass_number * PROTON_MASS_KG))
        .sqrt();
    let log_ratio = natural_log(cathode_radius_m / pinch_radius_m)?;
    let flux = (FLUX_COEFFICIENT * beam_energy_fraction)
        / (beam_ion_mass_number * beam_effective_charge).sqrt()
        * (log_ratio / (pinch_radius_m * pinch_radius_m))
        * ((pinch_current_a * pinch_current_a) / diode_voltage_v.sqrt());
    let ion_energy = beam_effective_charge * ELEMENTARY_CHARGE_C * diode_voltage_v;
    let cross_section = PI * pinch_radius_m * pinch_radius_m;
    let energy_flux = flux * ion_energy;
    let current_density = flux * ELEMENTARY_CHARGE_C * beam_effective_charge;
    let fluence = flux * pinch_duration_s;
    let ions = fluence * cross_section;
    Ok(FastIonBeam {
        beam_speed_m_s: speed,
        flux_per_m2_s: flux,
        energy_flux_w_m2: energy_flux,
        power_flow_w: energy_flux * cross_section,
        current_density_a_m2: current_density,
        ion_current_a: current_density * cross_section,
        ions_per_s: flux * cross_section,
        fluence_per_m2: fluence,
        energy_fluence_j_m2: fluence * ion_energy,
        ions_in_beam: ions,
        beam_energy_j: ions * ion_energy,
        damage_factor_w_m2_sqrt_s: energy_flux * pinch_duration_s.sqrt(),
    })
}

/// Beam-target yield, see the Python floor `neutron.beam_target_yield`.
///
/// # Errors
///
/// Returns [`PhysicsError`] when the radii are not ordered.
pub fn beam_target_yield(
    ion_density_per_m3: f64,
    pinch_current_a: f64,
    pinch_length_m: f64,
    cathode_radius_m: f64,
    pinch_radius_m: f64,
    cross_section_m2: f64,
    diode_voltage_v: f64,
) -> Result<f64, PhysicsError> {
    if pinch_radius_m >= cathode_radius_m {
        return Err(PhysicsError {
            message: format!(
                "pinch_radius_m: must be smaller than cathode_radius_m, got {pinch_radius_m:?} >= {cathode_radius_m:?}"
            ),
        });
    }
    Ok(BEAM_TARGET_CONSTANT
        * ion_density_per_m3
        * (pinch_current_a * pinch_current_a)
        * (pinch_length_m * pinch_length_m)
        * natural_log(cathode_radius_m / pinch_radius_m)?
        * cross_section_m2
        / diode_voltage_v.sqrt())
}

/// Scaling-law yield, see the Python floor `neutron.scaling_law_yield`.
///
/// # Errors
///
/// Returns [`PhysicsError`] when the current is outside the stated range.
pub fn scaling_law_yield(pinch_current_a: f64) -> Result<f64, PhysicsError> {
    let (low, high) = SCALING_RANGE_A;
    if pinch_current_a < low || pinch_current_a > high {
        return Err(PhysicsError {
            message: format!(
                "pinch_current_a: the scaling law is stated for [{low:?}, {high:?}] A, got {pinch_current_a:?}"
            ),
        });
    }
    Ok(SCALING_COEFFICIENT * power(pinch_current_a / 1.0e6, SCALING_EXPONENT)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bank_energy_and_quarter_period_match_the_closed_forms() {
        let b = bank_normalisation(1332.0e-6, 33.0e-9, 6.3e-3, 27.0e3, 0.116, 0.16, 0.60).unwrap();
        assert!((b.bank_energy_j - 485_514.0).abs() < 1.0);
        assert!((b.quarter_period_s - 10.414e-6).abs() < 1.0e-9);
        assert!(bank_normalisation(1.0, 1.0, 1.0, 1.0, 0.2, 0.1, 1.0).is_err());
    }

    #[test]
    fn slug_shock_is_inward_and_elongation_outward() {
        let s = slug_relations(8.62e5, 0.0223, 7.5e-4, 0.7, 0.35, 5.0 / 3.0, 4.0, 2.0, 1.0);
        assert!(s.shock_speed_m_s < 0.0);
        assert!(s.elongation_speed_m_s > 0.0);
        assert!(s.reflected_shock_speed_m_s > 0.0);
        assert!(s.shock_temperature_k > 0.0);
    }

    #[test]
    fn scaling_law_reproduces_its_calibration_point_within_ten_percent() {
        let y = scaling_law_yield(5.0e5).unwrap();
        assert!((y / 7.0e9 - 1.0).abs() < 0.1);
        assert!(scaling_law_yield(5.0e4).is_err());
    }

    #[test]
    fn beam_and_yield_refuse_unordered_radii() {
        assert!(fast_ion_beam(1.0e5, 0.2, 0.1, 1.0e5, 1.0e-7, 0.14, 2.0, 1.0).is_err());
        assert!(beam_target_yield(1.0e23, 1.0e5, 0.1, 0.1, 0.2, 1.0e-30, 1.0e5).is_err());
        assert!(
            pinch_radiation(8.62e5, 0.0223, 0.188, 0.116, 1.1e23, 0.7, 0.35, 2.0, 1.0, 1.0).is_ok()
        );
    }
}
