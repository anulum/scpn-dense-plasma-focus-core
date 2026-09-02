<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ROADMAP
-->

# Roadmap

Planned work and implemented capability are kept strictly separate. Anything
listed under "Planned" carries no implementation, no code, and no claim in
this repository until it appears in the capability inventory with evidence.

## Implemented (repository infrastructure, not reactor capability)

- Domain manifest (`reactor-domain.json`) with validator.
- Derived Studio portfolio descriptor (`not_federated`) with drift check.
- Generated capability inventory (truthfully empty) with drift check.
- CONTROL adapter specification (contract only, no implementation).
- Local and workflow gate definitions (lint, typing, tests, coverage,
  REUSE, security audit, SBOM, documentation checks).

- **Device configuration model** (landed 2026-08-31) — validated
  electrode and bank/fill objects for `dense_plasma_focus` with the hard
  coaxial-geometry invariant (cathode outside anode), the Lee-Serban
  drive parameter `I / (a sqrt(p))` with its documented deuterium
  window advisory (Lee & Serban 1996), canonical digests, and the SPO
  registry data pin; `computational_prototype` (ADR 0002,
  `VALIDATION.md#device-configuration-model`). Insulator classes and
  scaling declarations remain future work under the same capability.
- **Diagnostic and clock semantics** (landed 2026-08-31) — synthetic
  diagnostic-channel and clock declarations aligned fail-closed with the
  pinned SPO observability-profile catalogue (release `1.0.0`): candidate
  applicability, carrier admissibility, exact evidence vocabularies,
  clock-kind compatibility, Nyquist and event-timing bounds, canonical
  digests; the reference plan mirrors canonical practice
  (discharge event train, neck-mode probe array, synthetic oscillator); `computational_prototype` (ADR 0003,
  `VALIDATION.md#diagnostic-and-clock-semantics`). No ingress is
  declared; the SPO semantic-profile state remains `not_declared`.
- **Level-0 device physics** (landed 2026-09-02) — the closed forms of
  the Lee model evaluated on the validated configuration and a declared
  pinch state: bank normalisation and scaling parameters, fill state,
  axial and radial characteristic quantities, slug relations, rule-of-thumb
  pinch geometry, pinch-phase density, Bennett temperature and power
  terms, the fast-ion-beam chain, beam-target and scaling-law neutron
  estimates; a canonical `Level0PhysicsRecord`, optional native kernels
  bit-exact with the Python floor, and a standard-conformant benchmark;
  `computational_prototype` (ADR 0005,
  `VALIDATION.md#level-0-device-physics`). Follow-ups under the same
  capability: the five-phase integration (level 1) once the shared
  integrator kernels exist, the thermonuclear term once the reactivity
  kernel exists, the corona-model charge state, and the family's 3D model
  once the shared kernel library is pinned.

## Planned (no implementation exists; ordering is not a commitment)
1. **Safety-envelope declaration** — machine-readable operational envelope
   (bank, current, pressure, repetition, electrode bounds) consumed by the
   CONTROL adapter contract.
2. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
3. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for sheath-dynamics and pinch surfaces,
   strictly after the family migration gate proves exact replacement; no
   solver code is copied.
4. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Generic Z-pinch and theta-pinch devices, external-accelerator beam-target
systems, magnetic-confinement devices, inertial and magneto-inertial liner
systems, generic controller mathematics, machine-protection logic, and any
direct actuation path.
