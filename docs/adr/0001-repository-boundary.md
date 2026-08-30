<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)  
**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. The dense plasma focus terminates in
a Z-pinch-like column and produces part of its yield through internal
beam-target reactions, bordering two other owners; a boundary decision was
needed on both edges.

## Decision

1. `SCPN-DENSE-PLASMA-FOCUS-CORE` owns exactly one registry configuration:
   `dense_plasma_focus` (coaxial plasma-focus pinch).
2. The repository owns device-level truth only: coaxial sheath-dynamics
   configuration policy (electrode and insulator classes, fill-gas and
   pressure programming), the phase-resolved lifecycle (breakdown,
   rundown, roll-over, collapse, focus, disruption), the declared
   separation of thermal and beam-target yield contributions,
   timing-anchored diagnostic and clock declarations, actuator-response
   model boundaries, the safety-envelope declaration, and the
   device-owned CONTROL adapter specification.
3. Generic Z-pinch physics stays with `SCPN-Z-PINCH-CORE`: the DPF's
   identity is the electrode-driven sheath lifecycle that creates the
   transient focus, not a preformed column.
4. External-accelerator beam-target fusion stays with
   `SCPN-BEAM-TARGET-CORE`: the DPF's beam component is internally
   generated device truth, not a beam-facility capability.
5. Solver mathematics remains in `SCPN-FUSION-CORE` until an exact surface
   passes the family migration gate. No solver code is copied here.
6. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only).
   Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation remains in `SCPN-STUDIO`; this project is
   `not_federated`.
7. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **Folding the DPF into the Z-pinch repository** (both end in an
  axial-current pinch): rejected — the DPF's defining surfaces are the
  coaxial rundown driver, the phase-structured lifecycle, and
  timing-anchored diagnostics; only the terminal instants resemble a
  Z-pinch (surfaces 2, 3, and 4 differ).
- **Classifying the DPF as a beam-target device** (beam component of the
  yield): rejected — the beam arises from internal pinch instability, not
  an external accelerator; the driver and lifecycle are pulsed-power
  sheath dynamics.
- **Absorbing solver code at scaffold time**: rejected — violates the
  migration gate.

## Consequences

- Downstream consumers get one stable identity for the dense-plasma-focus
  configuration and a manifest to bind against.
- The validator fails on any capability or claim entry while maturity is
  `architecture_only`.
- Boundary changes require a portfolio-level map change first; a future
  ADR records any such change here.
