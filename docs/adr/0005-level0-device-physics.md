<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: the closed forms of the Lee model with native parity

Status: accepted (2026-09-02). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

Until this record the repository carried no physics beyond the Lee–Serban
drive parameter of the configuration model. Every device manifest excludes
`solver_mathematics_and_validation_evidence` (owner SCPN-FUSION-CORE), and
no FUSION seam covers the dense-plasma-focus family. The device owner
therefore needs its own bounded, exercised, published physics: closed-form
relations from the device's own literature, evaluated on the validated
configuration, without integrating any phase. Three sources carry a
complete, internally consistent set of such relations with printed
reference numbers: the review of the Lee model code (S. Lee, J. Fusion
Energ. 33 (2014) 319–335, all fifty-five equations of the five-phase model),
the IAEA technical document on intense fusion pulses (IAEA-TECDOC-1829
(2017), the chapter by Saw and Lee with the ion-beam relations and a table
of twelve machines fitted with the code) and the same author's ICTP lecture
on scaling properties (ICTP 2168-10 (2012), the rule-of-thumb pinch
geometry).

## Decision

1. A new owned domain `analytic_device_physics_models` is declared in
   `reactor-domain.json`: device-owned closed-form and 0-D models from the
   device literature. It is disjoint from solver mathematics: no solver
   code is copied, no phase of the Lee model is integrated (that is the
   family's level 1, waiting for the shared integrator kernels), and no
   FUSION seam is implied or consumed.
2. Eight modules under `src/scpn_dense_plasma_focus_core/physics/`, each
   citing the equation or table it evaluates: bank normalisation and
   scaling parameters with the fill state (Lee eqs. 4–6, 9, 43), the axial
   characteristic quantities and the terminal snowplow speed (eqs. 5–7 and
   eq. 1 at zero acceleration), the radial characteristic quantities, slug
   relations and rule-of-thumb geometry (eqs. 14, 15, 24–28, 32, 34; ICTP
   Table 3), the pinch-phase closed forms (eqs. 39–48), the fast-ion-beam
   chain (TECDOC eqs. 5–6 and items (a)–(k)), and the neutron estimates
   (Lee eq. 50 with the TECDOC constant, the empirical scaling law with its
   calibration point). A composed `Level0PhysicsRecord` serialises
   canonically with a SHA-256 digest and carries fixed non-claims.
3. Inputs the configuration does not carry are declared explicitly and
   validated fail-closed: `ModelInputs` (bank circuit values, fill gas and
   temperature, dissociation number, specific heat ratio, the four model
   factors, plasma charge state) and `PinchState` (pinch current, radius,
   length, duration, diode voltage, beam energy fraction, beam ion mass and
   charge, the D–D neutron cross-section). The record enforces three
   consistency checks between the configuration and the declarations: the
   circuit energy `C0 V0^2 / 2` against the declared bank energy (5 %), the
   pinch current against the peak current, and the pinch radius against
   the anode radius.
4. Three honest limits are recorded in the evidence record rather than
   hidden: the tabulated pinch temperature and density are outputs of the
   integrated code and are not reproduced by the Bennett and compression
   closed forms at the tabulated inputs, so those quantities carry no
   anchor; the table prints the diode voltage equal to its `V_max` column
   whereas the text states `U = 3 V_max`, so `U` is a declared input and
   the rule is a separate helper; the INTI row's printed speed factor does
   not follow from its own printed inputs, so it is excluded from that
   anchor. The scaling law is reported as not applicable, instead of
   refusing the record, when the pinch current lies outside its stated
   range.
5. The bit-exact rule forbids platform logarithms, exponentials and
   powers. The repository vendors a byte-identical copy of the shared
   kernel library's deterministic transcendental kernel
   (`physics/_transcendental.py`, canonical: SCPN-REACTOR-KERNELS commit
   `799d44d3`, ADR 0003 there) with the library's own tests; the copy is
   retired for the pinned library exactly as the geometry copies of the
   Z-pinch family. Native kernels (`rust/`, crate
   `scpn-dense-plasma-focus-rs`, optional distribution
   `scpn-dense-plasma-focus-native` via maturin) mirror every evaluation
   with identical operation order using only `+ - * /`, `sqrt` and the
   vendored kernel; parity tests compare float64 bit patterns on the four
   anchor rows and on both self-absorption branches. The pure-Python floor
   remains the public API and the default.
6. Performance numbers follow the ecosystem benchmark standard; the local
   artefact is committed and labelled non-isolated.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. VALIDATION states per model what is exercised, what is
anchored and what is not claimed; the anchors reproduce numbers printed in
the sources, which are themselves outputs of the source's fitted code, not
correlations with data. The five-phase integration (level 1), the
thermonuclear yield term and the corona-model charge state wait for the
shared kernel library's integrator and reactivity increments. The family's
3D model waits for the kernel library pin. The manifest change alters
`manifest_sha256` inside the plan envelope, so the envelope fixture is
regenerated from the public surface and re-pinned; the plan bytes and
`plan_sha256` are unchanged.
