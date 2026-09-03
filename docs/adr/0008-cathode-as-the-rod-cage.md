<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0008
-->

# ADR 0008 — The cathode is the rod cage, not an equivalent tube

Status: accepted (2026-09-03). Supersedes item 4 and the "Simplification
recorded on purpose" section of ADR 0007.

## Context

ADR 0007 drew the cathode as one annular tube: the equivalent coaxial
conductor of the model this repository implements. The reasoning recorded
there was that the shared kernel library had no way to place a body off the
axis, so a cage of rods could not be built without re-implementing geometry
locally.

The owner ruled that this is not acceptable: the model must carry what the
machine has. A squirrel cage of discrete rods and a solid tube are different
objects — different surface area, different volume, different sight lines,
different everything a later engineering lane would ask of the geometry — and
recording the difference in a non-claim does not make the geometry right.

## Decision

1. The missing capability was added where it belongs, in the shared library:
   `geometry_placement` (SCPN-REACTOR-KERNELS ADR 0007) provides an exact
   translation of a vertex stream, the centres of identical bodies equally
   spaced on a circle, and the neighbour separation of that ring. This
   repository re-pins to the library commit that carries it and adds the
   kernel to its `kernel_library` block.
2. `DeviceGeometry` replaces `cathode_wall_thickness_m` with
   `cathode_rod_radius_m` and `cathode_rod_count`. The rod count is an
   integer of at least three, validated through the library's own rule and
   re-raised under the device error type; the record parser refuses a
   non-integer count, booleans included.
3. The model builds one body per rod, named `cathode_rod_00` upwards with the
   index zero-padded to the width of the last index, placed on the coaxial
   circle of the configuration's cathode radius in ring order. The body
   inventory is therefore a function of the rod count, not a constant, and
   `body_names(rod_count)` is the contract.
4. Two invariants enter, both fail-closed: the inner face of a rod must stay
   outside the insulator sleeve (`cathode_radius - rod_radius > sleeve
   outer`), and neighbouring rods must not intersect (the library's ring
   separation must exceed twice the rod radius). The chamber-bore rule now
   uses the rod outer face `cathode_radius + rod_radius`.
5. The model record carries `rod_count`, and the export provenance carries it
   too, so a consumer reading a file knows how many rods the mesh set holds
   without counting nodes.

## Consequences

The reference model digest changes, and so do the manifest digest, the
descriptor, the inventory and the envelope fixture; all are regenerated in
the same landing. The pinned library commit and the kernel-inventory digest
move, which is a governed data change recorded in the re-intake note.

The model is larger: eighteen bodies instead of seven for a twelve-rod cage,
and the benchmark grows with it (327680 faces at 4096 segments against
163840). That cost is the price of the geometry being true, and the benchmark
records it rather than hiding it.

What is still not modelled is now a short and honest list: the rods are
straight cylinders, so their mounting into the back-wall plate, any taper or
chamfer, and the insulator end fittings are absent. Nothing in the model
stands in for something it is not.
