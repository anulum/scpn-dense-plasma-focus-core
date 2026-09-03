<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — Architecture summary
-->

# Architecture summary

`SCPN-DENSE-PLASMA-FOCUS-CORE` is the device-family owner for
dense-plasma-focus systems inside the SCPN Reactor Systems Research Group.
The repository holds four implemented capabilities at
`computational_prototype` — the device configuration model (ADR 0002),
the diagnostic and clock semantics model (ADR 0003), the level-0
device physics (ADR 0005; the closed forms of the Lee model on the pinned
shared numerics kernels, ADR 0006, with optional native kernels in
`rust/`), the device 3D model (ADR 0007 and ADR 0008; analytic bodies,
the rods of the squirrel-cage cathode included, tessellated and placed on
the geometry kernels of the same pinned library) and the device CAD model
(ADR 0009; the same bodies as B-rep solids on the CAD kernels of the same
pin, with a deterministic STEP export), all in
`src/scpn_dense_plasma_focus_core/` —
alongside the device boundary, its ecosystem contracts, and the validation
tooling that enforces them.

The authoritative architecture record is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The ownership decision and
its consequences are fixed in
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).

Boundary in one paragraph: this repository owns dense-plasma-focus plant
and experiment truth — configuration policy for coaxial-electrode devices
whose current sheath runs down the gap and collapses into a transient dense
pinch at the anode tip, phase-resolved lifecycle semantics (breakdown,
rundown, roll-over, collapse, focus, disruption) with declared separation
of thermal and internally generated beam-target yield, timing-anchored
diagnostic and clock declarations (the current-derivative focus dip),
actuator-response boundaries limited to shot-to-shot programming,
safety-envelope declarations, and the device-owned CONTROL adapter
specification. Generic Z-pinch physics stays with `SCPN-Z-PINCH-CORE`;
external beam-target systems with `SCPN-BEAM-TARGET-CORE`; solver
mathematics in `SCPN-FUSION-CORE`; typed semantics in
`SCPN-PHASE-ORCHESTRATOR` (review-only); admitted control actions are
formed only by `SCPN-CONTROL`; independent machine protection keeps the
final veto; portfolio presentation belongs to `SCPN-STUDIO`, towards which
this project is `not_federated`.
