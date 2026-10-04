// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Dense Plasma Focus Core — validated axial Lee-model characteristics

//! Axial snowplow closed forms with the Python floor's binary64 domain.
//! Lee2014 p322 defines c=b/a; equations1 and5–7 use its logarithm, not
//! an independent fit. Evaluation order matches the floor for bit parity.

use crate::physics::PhysicsError;
use crate::{MU0, PI};
use scpn_reactor_kernels_native::numerics::transcendental::natural_log;

/// Axial-phase characteristic quantities (Lee2014, eqs.5–7 and eq.1 at rest).
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct AxialCharacteristics {
    /// Characteristic transit time ta of equation5, in seconds.
    pub axial_transit_time_s: f64,
    /// Characteristic circuit time divided by ta (equation6).
    pub alpha: f64,
    /// Anode length divided by ta (equation7), in metres per second.
    pub characteristic_axial_speed_m_s: f64,
    /// Terminal snowplow speed at the declared drive current, in metres per second.
    pub terminal_sheath_speed_m_s: f64,
}

/// Require a finite positive binary64 input or intermediate.
fn positive(name: &str, value: f64) -> Result<f64, PhysicsError> {
    if !value.is_finite() {
        return Err(PhysicsError {
            message: format!("{name}: must be finite, got {value:?}"),
        });
    }
    if value <= 0.0 {
        return Err(PhysicsError {
            message: format!("{name}: must be strictly positive, got {value:?}"),
        });
    }
    Ok(value)
}

/// Check coaxial/logarithmic consistency and evaluate equation geometry factors.
fn geometry_factors(a: f64, b: f64, log: f64, density: f64) -> Result<(f64, f64), PhysicsError> {
    if b <= a {
        return Err(PhysicsError {
            message: format!(
                "cathode_radius_m: must be strictly greater than anode_radius_m, got {b:?} <= {a:?}"
            ),
        });
    }
    let ratio = positive("radius_ratio", b / a)?;
    if log != natural_log(ratio)? {
        return Err(PhysicsError {
            message: "log_radius_ratio: must equal deterministic ln(cathode_radius_m / anode_radius_m) from bank_normalisation".into(),
        });
    }
    let difference = positive("radius_squared_ratio_minus_one", ratio * ratio - 1.0)?;
    let magnetic_factor = positive("magnetic_log_factor", MU0 * log)?;
    let geometry = positive(
        "axial_geometry_factor",
        (4.0 * PI * PI * difference) / magnetic_factor,
    )?;
    let denominator = positive(
        "terminal_geometry_denominator",
        4.0 * PI * PI * density * difference,
    )?;
    Ok((
        geometry,
        positive("terminal_geometry_factor", magnetic_factor / denominator)?,
    ))
}

/// Evaluate the closed-form axial transit, scaling parameter and sheath speeds.
///
/// All ten arguments must be finite and positive. The cathode radius must
/// exceed the anode radius. `log_radius_ratio` must exactly equal the shared
/// deterministic logarithm of their ratio, as returned by
/// [`crate::physics::bank_normalisation`]. It is not an independent parameter.
/// Valid evaluation retains the original equation order and output bit patterns.
///
/// # Errors
///
/// Returns [`PhysicsError`] naming the field/relation when an input is
/// inadmissible or an intermediate/output is not finite and strictly positive.
/// Underflow, overflow and zero denominators are refused without clamping.
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
) -> Result<AxialCharacteristics, PhysicsError> {
    for (name, value) in [
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
    ] {
        positive(name, value)?;
    }
    let (geometry, terminal_geometry) = geometry_factors(
        anode_radius_m,
        cathode_radius_m,
        log_radius_ratio,
        mass_density_kg_m3,
    )?;
    let current_per_radius = positive(
        "characteristic_current_per_radius",
        characteristic_current_a / anode_radius_m,
    )?;
    let drive = positive(
        "axial_drive",
        current_per_radius / mass_density_kg_m3.sqrt(),
    )?;
    let mass_current_factor = positive(
        "axial_mass_current_factor",
        axial_mass_factor.sqrt() / axial_current_factor,
    )?;
    let transit = positive(
        "axial_transit_time_s",
        geometry.sqrt() * mass_current_factor * anode_length_m / drive,
    )?;
    let current_mass_factor = positive(
        "terminal_current_mass_factor",
        (axial_current_factor * axial_current_factor) / axial_mass_factor,
    )?;
    let radicand = positive(
        "terminal_speed_squared_factor",
        current_mass_factor * terminal_geometry,
    )?;
    let drive_per_radius = positive("drive_current_per_radius", drive_current_a / anode_radius_m)?;
    let terminal = positive(
        "terminal_sheath_speed_m_s",
        radicand.sqrt() * drive_per_radius,
    )?;
    Ok(AxialCharacteristics {
        axial_transit_time_s: transit,
        alpha: positive("alpha", characteristic_time_s / transit)?,
        characteristic_axial_speed_m_s: positive(
            "characteristic_axial_speed_m_s",
            anode_length_m / transit,
        )?,
        terminal_sheath_speed_m_s: terminal,
    })
}
