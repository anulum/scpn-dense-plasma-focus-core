<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0007
-->

# ADR 0007 — Device 3D model on the shared geometry kernels

Status: accepted (2026-09-03); item 4 and the simplification section are
superseded by `docs/adr/0008-cathode-as-the-rod-cage.md` (the cathode is
built as the rod cage it is, not as an equivalent tube). Adds the fourth
implemented capability, `device_3d_model`, at `computational_prototype`, and
amends ADR 0006 (the shared numerics kernels) by extending the same library
pin with the geometry kernels.

## Context

The device repository owns device geometry (ADR 0001 boundary). Until this
record the repository carried the coaxial electrode pair as numbers only;
there was no mechanical envelope and no way to present, measure or hand a
design to downstream tooling. A three-dimensional model is the substrate for
every later engineering lane (surface loading, neutronics geometry,
pulsed-power layout) and for portfolio presentation. It must regenerate
exactly from the validated records, must not need a heavy CAD kernel in every
gate, and must never overstate what an analytic surface is.

ADR 0006 already made this repository a consumer of the shared kernel library
`scpn-reactor-kernels`, pinned to one commit object with the kernel-inventory
digest recorded in the manifest. The geometry substrate lives in the same
library and at the same pinned commit, so this capability adds no new
dependency and no new pin — only four kernel identifiers to the block.

## Decision

1. A new owned domain `device_geometry_and_3d_model` is declared: device-owned
   geometry parameters and the 3D model derived from them. It is disjoint
   from solver mathematics, from portfolio presentation (the exported files
   are an offer, `docs/DEVICE_3D_MODEL_CONTRACT.md`) and from any engineering
   lane.
2. `DeviceGeometry` (`src/scpn_dense_plasma_focus_core/geometry/device.py`)
   carries the mechanical envelope — insulator-sleeve length and wall,
   cathode wall and length, chamber bore, wall and length, back-wall and
   end-wall thickness — with fail-closed positivity, the axial containment
   rule `cathode_length_m <= chamber_length_m`, canonical bytes, a SHA-256
   digest and a strict record parser. The anode radius, the cathode radius
   and the anode length are NOT repeated: they are the validated
   configuration's `ElectrodeSet`.
3. The layout is the qualitative Mather-type arrangement of the sources
   already on file for ADR 0005: a central anode bar, a cathode coaxial with
   it attached to the back-wall plate, an insulator sleeve over the anode
   base whose length is a printed device parameter, and the plasma chamber
   (IAEA-TECDOC-1829, IAEA Vienna 2017), with the electrode pair idealised as
   the coaxial line of the model this repository implements (S. Lee, J. Fusion
   Energ. 33 (2014) 319). No dimension of any device is used; every parameter
   set is synthetic.
4. The model is tier G1: analytic bodies (solid cylinders and annular tubes)
   tessellated into closed, outward-oriented triangle meshes with fixed vertex
   and face order. Seven bodies in a fixed order: anode, insulator sleeve,
   cathode, chamber wall, back wall, downstream end wall, and the pinch column
   standing on the anode tip (the declared `rp` and `zp` of the level-0 pinch
   state — an analytic surface, not a computed compression boundary). B-rep
   CAD (tier G2) is a separate, later decision.
5. `DeviceModel3D` (`scpn.dense-plasma-focus-3d-model.v1` `1.0.0`) records
   both source digests, the pinch radius and length, the segment count, the
   units and axis convention (metre, right-handed, z along the device axis
   increasing downstream, origin at the inner face of the back wall), every
   body summary and fixed non-claims; one reference digest (segments = 8) is
   pinned in the tests as an immutability fixture.
6. Build invariants fail closed, never clamp: the sleeve must stay inside the
   cathode radius and must not be longer than the anode; the cathode must fit
   the chamber bore; the anode must fit the chamber length; the pinch column
   must be inside the anode radius and must not leave the chamber; the segment
   count must satisfy the library rule (its refusal is re-raised as
   `DeviceGeometryError`).
7. Exports are pure serialisations of the validated meshes through the
   library's kernel `geometry_exports`: binary STL and glTF 2.0 binary, one
   named node per body, document `extras` carrying schema, both digests, the
   model digest, the pinch column, the segment count, units and non-claims.
8. The native crate carries physics only. Parity of the device model is proven
   against the library's native module: every vertex coordinate, face index,
   volume and area of the seven bodies agrees bit for bit.
9. A standard-conformant benchmark (`benchmarks/device_model_3d.py`) times one
   full device tessellation on both backends of the pinned library; the local
   artefact is committed and labelled non-isolated.

## Simplification recorded on purpose

The cathode is drawn as the equivalent coaxial conductor of the Lee model —
the model computes the tube inductance from `ln(b/a)` — and not as the
squirrel cage of discrete rods a real assembly carries. The rod count, spacing
and diameter are not modelled at this tier, and the kernel library has no
off-axis placement primitive. Insulator end fittings, gas ports, diagnostic
windows and supports are likewise not modelled.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory stays
empty. `VALIDATION.md#device-3d-model` states what is exercised and what is
not claimed. The manifest change alters `manifest_sha256` inside the plan
envelope, so the envelope fixture is regenerated and re-pinned; the plan bytes
and `plan_sha256` are unchanged. Continuous integration additionally builds
the library's native module in the native job so the geometry parity file
never silently skips. The exported GLB and its node contract are offered to
the portfolio layer; federation state remains `not_federated`.
