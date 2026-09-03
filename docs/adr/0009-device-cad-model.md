<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0009
-->

# ADR 0009 — Device CAD model: B-rep solids, the rod cage, and a deterministic STEP export

Status: accepted (2026-09-03). Adds the fifth implemented capability,
`device_cad_model`, at `computational_prototype`. Extends ADR 0008 (the
cathode is the rod cage) to the solid tier.

## Context

The tier-G1 model (ADR 0007, ADR 0008) produces analytic triangle meshes,
with the cathode as the cage of discrete rods it is. The solid tier was
blocked on the same gap that had blocked tier G1 before ADR 0008: the
shared library's CAD group offered only axis-centred constructors, so a
cage of rods could not be built without drawing an axisymmetric substitute
or reaching into the back-end from this repository. Both are refused by
the rule that produced ADR 0008 — when the shared library cannot express a
part, the library gains the capability. It now has `cad_placement` (the
library's ADR 0008), the solid counterpart of the placement kernel tier G1
uses, and this record consumes it.

## Decision

1. `src/scpn_dense_plasma_focus_core/geometry/cad.py` builds the same
   bodies as `build_device_model` — anode, insulator sleeve, one solid per
   cathode rod in ring order, chamber wall, both closing walls and the
   declared pinch column — with the library's B-rep constructors and its
   placement kernel, at the same names, roles, material tokens and extents
   as tier G1.
2. The rods are placed on the centres the tier-G1 model uses, from the
   library's `ring_offsets`. Both tiers therefore sit on one circle by
   construction rather than by coincidence, and a test proves each rod's
   box centre is that centre, each rod carries the declared radius, and
   each spans the declared cathode length.
3. The build's refusals are the tier-G1 refusals: it runs the tier-G1
   build first, so a rod set that would intersect itself, a rod that would
   reach the insulator sleeve, a cathode that would not fit the chamber
   bore, a sleeve longer than the anode, an anode longer than the chamber
   and a pinch column outside the anode or outside the chamber are all
   refused before any solid is built. One set of invariants, not two.
4. The per-body evidence is the shared library's (`cad_evidence`, the
   library's ADR 0009), not this repository's. What this module owns is
   the schema identity (`scpn.dense-plasma-focus-cad-model.v1`, version
   `1.0.0`), the composition of the bodies, this family's build invariants
   and its non-claims. A violated bound raises the library's `CadError`,
   which the build re-raises as `DeviceGeometryError`; nothing is clamped.
5. The record carries the rod count, so the body inventory it validates
   against is the inventory of that count — a record built for twelve rods
   cannot be re-labelled as one built for sixteen. The STEP provenance
   extras additionally carry the rod count and the ring separation, so a
   reader of the exported file can see the cage the assembly is.
6. The kernel library pin moves to the commit carrying the CAD group, the
   CAD placement kernel, the body-evidence kernel and the bounding-box
   correction; the crate pin and the lock move with it. The library's `cad`
   extra is NOT a dependency of this package: every other capability works
   without a B-rep kernel, so declaring it as one would overstate what the
   package needs and would pull a roughly one-gigabyte back-end into every
   environment that installs it. It is an optional extra here too —
   `[project.optional-dependencies] cad` naming the same commit — and only
   the two CI jobs that need it install it: the coverage job, because the
   CAD module is covered like every other module, and the `cad` job. A
   contract test proves the plain dependency, the extra, the crate and the
   lock all name one commit. The CI gains a `cad` job that installs the system
   library the mesher's wheel links against before the extra.
7. The anchor fixture is exercised at this tier too: a test proves that
   the anode radius and length, the cathode circle radius, the rod radius
   and count, and the insulator-sleeve length that IAEA-TECDOC-1829 prints
   for the NX3 assembly A20Z160 all appear in the built solids.
   Reproducing a printed dimension is an anchor, not a claim about that
   machine, and the fields the source does not print stay declared as
   declared.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty; no material property, load, field or neutronic quantity is
carried by any body. The STEP file is an export of the record, never its
source.

The assembly is now the largest in the group — eighteen bodies at twelve
rods — and the faceting and record-build costs scale with it. That is a
per-design cost and it is measured, not assumed.

The rods are straight cylinders: their mounting hardware, the flanges that
hold them and any taper are not modelled at either tier, and that stays in
the non-claims.
