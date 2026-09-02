// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Dense Plasma Focus Core — native level-0 physics kernels

//! Native level-0 device-physics kernels of SCPN Dense Plasma Focus Core.
//!
//! Every function mirrors one closed-form evaluation of the pure-Python
//! floor in `scpn_dense_plasma_focus_core.physics` with the identical
//! operation order, so the IEEE-754 double results agree bit for bit. The
//! kernels use only `+`, `-`, `*`, `/` and `sqrt` (all correctly rounded)
//! plus the vendored deterministic logarithm, exponential and power of the
//! shared kernel library crate (`scpn-reactor-kernels-rs`, pinned by
//! commit in `Cargo.toml` and in the manifest, ADR 0006); no `libm`
//! transcendental is called on either side.
//! Nothing here integrates an equation and no value describes a real
//! machine; the design record is ADR 0005 of the repository.

pub mod physics;

pub use scpn_reactor_kernels_native::numerics::transcendental::NumericsError;

/// Vacuum permeability `mu0 = 4e-7 pi`, evaluated as the Python floor does.
pub const MU0: f64 = 4.0e-7 * std::f64::consts::PI;
/// Proton mass in kilograms.
pub const PROTON_MASS_KG: f64 = 1.672_621_923_69e-27;
/// Boltzmann constant in joules per kelvin (exact SI 2019 value).
pub const BOLTZMANN_J_PER_K: f64 = 1.380_649e-23;
/// Elementary charge in coulombs (exact SI 2019 value).
pub const ELEMENTARY_CHARGE_C: f64 = 1.602_176_634e-19;
/// Molar gas constant in J kmol^-1 K^-1.
pub const MOLAR_GAS_CONSTANT_J_PER_KMOL_K: f64 = 8314.462618;
/// Pascals per torr as the exact quotient `101325 / 760`.
pub const PASCAL_PER_TORR: f64 = 101_325.0 / 760.0;
/// `pi` as the correctly rounded double.
pub const PI: f64 = std::f64::consts::PI;
/// `1 / e` as the correctly rounded double.
pub const INV_E: f64 = 0.367_879_441_171_442_33;

#[cfg(feature = "python")]
mod python {
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;

    use crate::physics;

    /// Bank normalisation tuple, see `physics::bank_normalisation`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments, clippy::type_complexity)]
    fn bank_normalisation(
        capacitance_f: f64,
        inductance_h: f64,
        resistance_ohm: f64,
        charge_voltage_v: f64,
        anode_radius_m: f64,
        cathode_radius_m: f64,
        anode_length_m: f64,
    ) -> PyResult<(f64, f64, f64, f64, f64, f64, f64, f64, f64)> {
        let b = physics::bank_normalisation(
            capacitance_f,
            inductance_h,
            resistance_ohm,
            charge_voltage_v,
            anode_radius_m,
            cathode_radius_m,
            anode_length_m,
        )
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok((
            b.bank_energy_j,
            b.characteristic_time_s,
            b.surge_impedance_ohm,
            b.characteristic_current_a,
            b.quarter_period_s,
            b.damping_ratio,
            b.log_radius_ratio,
            b.axial_inductance_h,
            b.inductance_ratio,
        ))
    }

    /// Fill state tuple, see `physics::fill_state`.
    #[pyfunction]
    fn fill_state(
        pressure_torr: f64,
        molecular_mass_amu: f64,
        temperature_k: f64,
    ) -> (f64, f64, f64, f64) {
        let f = physics::fill_state(pressure_torr, molecular_mass_amu, temperature_k);
        (
            f.pressure_pa,
            f.molecular_mass_kg,
            f.molecule_density_per_m3,
            f.mass_density_kg_m3,
        )
    }

    /// Axial characteristics tuple, see `physics::axial_characteristics`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn axial_characteristics(
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
    ) -> (f64, f64, f64, f64) {
        let a = physics::axial_characteristics(
            characteristic_time_s,
            characteristic_current_a,
            anode_radius_m,
            cathode_radius_m,
            anode_length_m,
            log_radius_ratio,
            mass_density_kg_m3,
            axial_mass_factor,
            axial_current_factor,
            drive_current_a,
        );
        (
            a.axial_transit_time_s,
            a.alpha,
            a.characteristic_axial_speed_m_s,
            a.terminal_sheath_speed_m_s,
        )
    }

    /// Radial characteristics tuple, see `physics::radial_characteristics`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn radial_characteristics(
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
    ) -> (f64, f64, f64, f64, f64, f64) {
        let r = physics::radial_characteristics(
            axial_transit_time_s,
            characteristic_current_a,
            anode_radius_m,
            cathode_radius_m,
            anode_length_m,
            log_radius_ratio,
            inductance_ratio,
            mass_density_kg_m3,
            axial_current_factor,
            radial_mass_factor,
            specific_heat_ratio,
        );
        (
            r.radial_transit_time_s,
            r.characteristic_radial_speed_m_s,
            r.alpha1,
            r.aspect_ratio,
            r.beta1,
            r.geometric_speed_ratio,
        )
    }

    /// Slug relations tuple, see `physics::slug_relations`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn slug_relations(
        current_a: f64,
        piston_radius_m: f64,
        mass_density_kg_m3: f64,
        axial_current_factor: f64,
        radial_mass_factor: f64,
        specific_heat_ratio: f64,
        molecular_mass_amu: f64,
        dissociation_number: f64,
        plasma_effective_charge: f64,
    ) -> (f64, f64, f64, f64) {
        let s = physics::slug_relations(
            current_a,
            piston_radius_m,
            mass_density_kg_m3,
            axial_current_factor,
            radial_mass_factor,
            specific_heat_ratio,
            molecular_mass_amu,
            dissociation_number,
            plasma_effective_charge,
        );
        (
            s.shock_speed_m_s,
            s.elongation_speed_m_s,
            s.shock_temperature_k,
            s.reflected_shock_speed_m_s,
        )
    }

    /// Rule-of-thumb geometry tuple, see `physics::pinch_geometry_estimate`.
    #[pyfunction]
    fn pinch_geometry_estimate(anode_radius_m: f64) -> (f64, f64, f64, f64) {
        let g = physics::pinch_geometry_estimate(anode_radius_m);
        (
            g.minimum_radius_m,
            g.maximum_length_m,
            g.shock_transit_time_s,
            g.pinch_lifetime_s,
        )
    }

    /// Pinch radiation tuple, see `physics::pinch_radiation`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments, clippy::type_complexity)]
    fn pinch_radiation(
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
    ) -> PyResult<(f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64)> {
        let p = physics::pinch_radiation(
            pinch_current_a,
            pinch_radius_m,
            pinch_length_m,
            anode_radius_m,
            molecule_density_per_m3,
            axial_current_factor,
            radial_mass_factor,
            dissociation_number,
            plasma_effective_charge,
            atomic_number,
        )
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok((
            p.ion_density_per_m3,
            p.bennett_temperature_k,
            p.temperature_ev,
            p.spitzer_resistance_ohm,
            p.joule_power_w,
            p.bremsstrahlung_power_w,
            p.line_power_w,
            p.photonic_excitation_number,
            p.absorption_factor,
            p.surface_line_power_w,
            p.effective_line_power_w,
            p.net_power_w,
        ))
    }

    /// Fast ion beam tuple, see `physics::fast_ion_beam`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments, clippy::type_complexity)]
    fn fast_ion_beam(
        pinch_current_a: f64,
        pinch_radius_m: f64,
        cathode_radius_m: f64,
        diode_voltage_v: f64,
        pinch_duration_s: f64,
        beam_energy_fraction: f64,
        beam_ion_mass_number: f64,
        beam_effective_charge: f64,
    ) -> PyResult<(f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64)> {
        let b = physics::fast_ion_beam(
            pinch_current_a,
            pinch_radius_m,
            cathode_radius_m,
            diode_voltage_v,
            pinch_duration_s,
            beam_energy_fraction,
            beam_ion_mass_number,
            beam_effective_charge,
        )
        .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok((
            b.beam_speed_m_s,
            b.flux_per_m2_s,
            b.energy_flux_w_m2,
            b.power_flow_w,
            b.current_density_a_m2,
            b.ion_current_a,
            b.ions_per_s,
            b.fluence_per_m2,
            b.energy_fluence_j_m2,
            b.ions_in_beam,
            b.beam_energy_j,
            b.damage_factor_w_m2_sqrt_s,
        ))
    }

    /// Beam-target yield, see `physics::beam_target_yield`.
    #[pyfunction]
    #[allow(clippy::too_many_arguments)]
    fn beam_target_yield(
        ion_density_per_m3: f64,
        pinch_current_a: f64,
        pinch_length_m: f64,
        cathode_radius_m: f64,
        pinch_radius_m: f64,
        cross_section_m2: f64,
        diode_voltage_v: f64,
    ) -> PyResult<f64> {
        physics::beam_target_yield(
            ion_density_per_m3,
            pinch_current_a,
            pinch_length_m,
            cathode_radius_m,
            pinch_radius_m,
            cross_section_m2,
            diode_voltage_v,
        )
        .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Scaling-law yield, see `physics::scaling_law_yield`.
    #[pyfunction]
    fn scaling_law_yield(pinch_current_a: f64) -> PyResult<f64> {
        physics::scaling_law_yield(pinch_current_a)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Python module `scpn_dense_plasma_focus_native`.
    #[pymodule]
    fn scpn_dense_plasma_focus_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(bank_normalisation, m)?)?;
        m.add_function(wrap_pyfunction!(fill_state, m)?)?;
        m.add_function(wrap_pyfunction!(axial_characteristics, m)?)?;
        m.add_function(wrap_pyfunction!(radial_characteristics, m)?)?;
        m.add_function(wrap_pyfunction!(slug_relations, m)?)?;
        m.add_function(wrap_pyfunction!(pinch_geometry_estimate, m)?)?;
        m.add_function(wrap_pyfunction!(pinch_radiation, m)?)?;
        m.add_function(wrap_pyfunction!(fast_ion_beam, m)?)?;
        m.add_function(wrap_pyfunction!(beam_target_yield, m)?)?;
        m.add_function(wrap_pyfunction!(scaling_law_yield, m)?)?;
        Ok(())
    }
}
