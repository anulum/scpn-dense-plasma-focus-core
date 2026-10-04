// SPDX-License-Identifier: AGPL-3.0-or-later
// Commercial license available
// © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
// © Code 2020–2026 Miroslav Šotek. All rights reserved.
// ORCID: 0009-0009-3560-0851
// Contact: www.anulum.li | protoscience@anulum.li
// SCPN Dense Plasma Focus Core — public Rust axial geometry contracts

//! Direct consumer tests of the fallible public axial API, not private helpers.

use scpn_dense_plasma_focus_native::physics::{
    axial_characteristics, bank_normalisation, AxialCharacteristics, PhysicsError,
};

/// Published-scale bank-derived argument declaration in SI units.
fn arguments() -> [f64; 10] {
    let bank = bank_normalisation(1332e-6, 33e-9, 6.3e-3, 27e3, 0.116, 0.16, 0.6).unwrap();
    [
        6.6e-6,
        5.4e6,
        0.116,
        0.16,
        0.6,
        bank.log_radius_ratio,
        7.5e-4,
        0.14,
        0.7,
        1.8e6,
    ]
}

/// Invoke the actual exported ten-argument equation owner.
fn evaluate(a: [f64; 10]) -> Result<AxialCharacteristics, PhysicsError> {
    axial_characteristics(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9])
}

#[test]
fn axial_valid_outputs_obey_scaling_and_transit_definitions() {
    let a = arguments();
    let result = evaluate(a).unwrap();
    assert_eq!(result.alpha, a[0] / result.axial_transit_time_s);
    assert_eq!(
        result.characteristic_axial_speed_m_s,
        a[4] / result.axial_transit_time_s
    );
    let mut double = a;
    double[9] *= 2.0;
    let scaled = evaluate(double).unwrap();
    assert_eq!(
        scaled.terminal_sheath_speed_m_s,
        2.0 * result.terminal_sheath_speed_m_s
    );
    assert_eq!(scaled.axial_transit_time_s, result.axial_transit_time_s);
    assert!(result.axial_transit_time_s > 0.0);
    assert!(result.terminal_sheath_speed_m_s.is_finite());
}

#[test]
fn axial_invalid_scalars_are_named_domain_errors() {
    let fields = [
        "characteristic_time_s",
        "characteristic_current_a",
        "anode_radius_m",
        "cathode_radius_m",
        "anode_length_m",
        "log_radius_ratio",
        "mass_density_kg_m3",
        "axial_mass_factor",
        "axial_current_factor",
        "drive_current_a",
    ];
    for (index, field) in fields.into_iter().enumerate() {
        for value in [0.0, -1.0, f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            let mut a = arguments();
            a[index] = value;
            assert!(evaluate(a).unwrap_err().message.starts_with(field));
        }
    }
}

#[test]
fn axial_equal_and_reversed_electrodes_are_refused() {
    for cathode in [0.116, 0.05] {
        let mut a = arguments();
        a[3] = cathode;
        assert!(evaluate(a)
            .unwrap_err()
            .message
            .starts_with("cathode_radius_m: must be strictly greater than anode_radius_m"));
    }
}

#[test]
fn axial_logarithm_is_exactly_bank_derived() {
    let a = arguments();
    for log in [1.5, f64::from_bits(a[5].to_bits() + 1)] {
        let mut changed = a;
        changed[5] = log;
        assert!(evaluate(changed)
            .unwrap_err()
            .message
            .starts_with("log_radius_ratio: must equal"));
    }
}

#[test]
fn axial_finite_inputs_refuse_unrepresentable_equation_terms() {
    let cases = [
        ("radius_ratio", vec![(2, 1e-308), (3, 1e308)]),
        ("terminal_geometry_denominator", vec![(6, 1e308)]),
        ("terminal_geometry_factor", vec![(6, f64::from_bits(1))]),
        ("characteristic_current_per_radius", vec![(1, 1e308)]),
        ("axial_drive", vec![(1, 1e-300), (6, 1e200)]),
        ("axial_mass_current_factor", vec![(8, 1e-320)]),
        ("axial_transit_time_s", vec![(4, f64::from_bits(1))]),
        ("axial_transit_time_s", vec![(4, 1e308)]),
        ("terminal_current_mass_factor", vec![(8, 1e200)]),
        ("terminal_current_mass_factor", vec![(8, 1e-200)]),
        (
            "terminal_speed_squared_factor",
            vec![(8, 1e-150), (6, 1e200)],
        ),
        ("drive_current_per_radius", vec![(9, 1e308)]),
        ("terminal_sheath_speed_m_s", vec![(8, 1e50), (9, 1e300)]),
        ("alpha", vec![(0, 1e308)]),
        (
            "characteristic_axial_speed_m_s",
            vec![(7, 1e-300), (1, 1e160)],
        ),
    ];
    for (field, updates) in cases {
        let mut a = arguments();
        for (index, value) in updates {
            a[index] = value;
        }
        assert!(a.into_iter().all(|value| value.is_finite() && value > 0.0));
        assert!(
            evaluate(a).unwrap_err().message.starts_with(field),
            "{field}"
        );
    }
    for (radius, field) in [
        (1e200, "radius_squared_ratio_minus_one"),
        (1e153, "axial_geometry_factor"),
    ] {
        let mut a = arguments();
        let bank = bank_normalisation(1e-6, 1e-8, 1e-3, 1e4, 1.0, radius, 0.6).unwrap();
        a[2] = 1.0;
        a[3] = radius;
        a[5] = bank.log_radius_ratio;
        assert!(evaluate(a).unwrap_err().message.starts_with(field));
    }
}
