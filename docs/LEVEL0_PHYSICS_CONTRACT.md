<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — axial level-0 physics contract
-->

# Axial characteristics input and native contract

`scpn_dense_plasma_focus_core.physics.axial_characteristics` evaluates the
published closed forms of the axial snowplow phase. All ten arguments are
finite positive SI quantities; the mass and current factors are dimensionless.
The cathode radius `b` must be strictly greater than the anode radius `a`.
Lee defines `c = b/a` on page322 and uses `ln(c)` in equation1 and equation5
([Lee2014, DOI10.1007/s10894-014-9683-8](https://doi.org/10.1007/s10894-014-9683-8)).

`log_radius_ratio` is a derived quantity, not a fitting parameter. Supply
`bank_normalisation(...).log_radius_ratio`, or the exact result of the pinned
shared deterministic logarithm of `b/a`. Rounded approximations and an altered
binary64 value are refused. This avoids an invented tolerance and preserves the
operation order and bit patterns of the bank-to-axial composition.

Every divisor and square-root argument is checked before use. Derived factors,
transit time, scaling parameter and speeds must be representable as finite
positive binary64 values. Finite inputs can still overflow or underflow a
published equation term: those declarations are refused, without clamping or
rearranging the equation to manufacture a result. There is no arbitrary
minimum electrode separation; adjacent ordered radii remain admissible when
their derived terms are representable.

Python raises `DeviceConfigurationError` naming the offending field or
relation. `scpn_dense_plasma_focus_native.axial_characteristics` enforces the
same domain and raises the existing binding's `ValueError`. Its successful
four-tuple remains `(transit_time, alpha, axial_speed, terminal_speed)`.
The Python result also records the declared drive current. Its field names,
float values, complete level-0 canonical serialisation and schema are unchanged
for the published valid rows.

The Rust public path `scpn_dense_plasma_focus_native::physics::axial_characteristics`
remains available. It now returns `Result<AxialCharacteristics, PhysicsError>`:
native consumers must handle the domain refusal rather than accepting NaN,
infinity or a zero transit time. Both the Rust core and PyO3 binding are tested
through their actual public interfaces. The implementation lives in the axial
module and is re-exported through the existing physics namespace.

The composition API `level0_physics` propagates a refused axial declaration
before constructing its canonical record. Successful published-anchor records
retain their byte identities. Other level-0 kernels retain their documented
contracts; this correction does not qualify their entire direct native domain.

Dedicated tests cover each invalid scalar, equal/reversed electrodes, altered
logarithms, finite overflow/underflow, representable adjacent radii, current
scaling, the published terminal-speed anchors and exact native field parity.
The existing benchmark measures the pinch/beam/yield grid through both
backends; it does not measure axial evaluation. Timing is computational cost,
not experimental correlation, physical validity or permission to actuate.
