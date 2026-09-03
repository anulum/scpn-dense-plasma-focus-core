<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-DENSE-PLASMA-FOCUS-CORE` is the device-family owner for
dense-plasma-focus systems in the SCPN Reactor Systems Research Group
portfolio. The
repository owns four implemented capabilities at
`computational_prototype` in `src/scpn_dense_plasma_focus_core/`: the device
configuration model (design record ADR 0002, evidence record
`VALIDATION.md#device-configuration-model`), the diagnostic and
clock semantics model (design record ADR 0003, evidence record
`VALIDATION.md#diagnostic-and-clock-semantics`) and the level-0 device
physics (design record ADR 0005, evidence record
`VALIDATION.md#level-0-device-physics`; owned domain
`analytic_device_physics_models`, disjoint from solver mathematics) and the
device 3D model (design records ADR 0007 and ADR 0008, evidence record
`VALIDATION.md#device-3d-model`; owned domain
`device_geometry_and_3d_model`, built on the geometry kernels of the pinned
library). Every other
section below describes boundaries and contracts. The claim inventory is
empty; capability and claim inventories are generated and drift-checked.

## The five-surface boundary

1. **Governing confinement physics** — the `dense_plasma_focus` (coaxial
   plasma-focus pinch, `self_magnetic` registry family): a discharge
   across a coaxial electrode pair breaks down over the insulator, forms a
   current sheath, accelerates it axially down the gap (rundown), rolls it
   over the anode tip, and collapses it radially into a short-lived dense
   pinch column. Neutron production combines thermal fusion in the hot
   column with a substantial instability-driven ion-beam-on-target
   component; declaring the two contributions separately is a first-class
   device requirement. The static or flow-stabilised Z-pinch (preformed
   column), the theta pinch, and external-accelerator beam-target
   facilities fail this sharing test and are excluded.
2. **Primary driver and energy delivery** — capacitor-bank pulsed-power
   drive across the coaxial electrodes, with fill-gas selection and
   pressure programming; repetition-capable operation is a configuration
   facet.
3. **Plant and shot lifecycle** — single-shot lifecycle: charge, breakdown
   over the insulator, axial rundown, roll-over, radial collapse, focus
   (pinch) phase with beam and hot-spot activity, disruption, and
   disassembly. Sheath symmetry and timing quality are device-truth
   declarations for each phase; hazards cover insulator failure, restrike,
   asymmetric sheath formation, and electrode erosion.
4. **Diagnostic, reference-frame, and clock model** — electrode-relative
   coordinates (insulator, rundown gap, anode tip), current and
   current-derivative monitors (the focus dip as timing anchor), imaging
   of sheath and pinch, neutron time-of-flight and yield diagnostics with
   the thermal/beam separation declared, and nanosecond-resolved
   shot-relative clock identities.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE`, review-only semantics towards
   `SCPN-PHASE-ORCHESTRATOR`, and the device-owned CONTROL adapter
   specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-DENSE-PLASMA-FOCUS-CORE (device truth: sheath/focus policy, pulsed
                              lifecycle, timing diagnostics, safety
                              envelope, adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   └──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated inventory of the four implemented capabilities |
| `src/scpn_dense_plasma_focus_core/physics/` | level-0 device physics (Lee model closed forms, composed record) |
| `src/scpn_dense_plasma_focus_core/geometry/` | device geometry and the tier-G1 3D model on the pinned shared kernels |
| `docs/DEVICE_3D_MODEL_CONTRACT.md` | producer-owned contract of the exported meshes |
| `reactor-domain.json` → `kernel_library` | exact pin of `scpn-reactor-kernels` (commit object, kernel-inventory digest, consumed kernels; ADR 0006 and ADR 0007) |
| `rust/` | optional native kernels (`scpn-dense-plasma-focus-rs`, depending on the library's Rust crate at the pinned commit), bit-exact with the Python floor |
| `benchmarks/` | standard-conformant benchmark and committed local artefact |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `src/` and `tools/`, native parity tests |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`; unknown
  schemas are rejected by consumers.
- The Studio descriptor is derived deterministically and embeds the
  manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at `0.1.0-spec`.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`.

## What would change this architecture

Acceptance of a FUSION solver seam through the family migration gate,
ratification of an SPO `ControlIntent`-class contract, or Studio federation
after a real capability passes producer and consumer gates — each recorded
as a versioned contract change in a new ADR.
