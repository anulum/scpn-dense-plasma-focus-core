<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — Device 3D model contract
-->

# Device 3D model contract

Producer-owned contract of the `device_3d_model` and `device_cad_model`
capabilities (`computational_prototype`; design records ADR 0006, ADR
0007, ADR 0008 and ADR 0009). It
states exactly what the exported files contain so that a consumer — the
portfolio presentation layer, an engineering tool, a reviewer — can read
them without importing this package. Nothing in the files or in this
contract creates a federation, a claim, or an engineering statement.

## Records

| Record | Schema | Identity |
|---|---|---|
| Device configuration | package `DeviceConfiguration` record | `configuration_digest_sha256` |
| Device geometry | package `DeviceGeometry` record (nine SI fields and the rod count) | `geometry_digest_sha256` |
| Device model | `scpn.dense-plasma-focus-3d-model.v1` version `1.0.0` | `model_sha256` = SHA-256 of the canonical model record |
| Body mesh | little-endian `uint32 vertex_count, uint32 face_count, float64 x y z per vertex, uint32 i j k per face` | `mesh_sha256` |

The model record carries: `schema`, `schema_version`, `units`,
`non_claims`, `configuration_digest_sha256`, `geometry_digest_sha256`,
`pinch_radius_m`, `pinch_length_m`, `rod_count`, `segments`, and `bodies` (one summary per body: `name`,
`role`, `material_identifier`, `vertex_count`, `face_count`, `volume_m3`,
`surface_area_m2`, `bounding_box_min_m`, `bounding_box_max_m`,
`mesh_sha256`). Canonical bytes are UTF-8 JSON with sorted keys, minimal
separators and a trailing newline; NaN and infinity are never emitted.

## Units and axes

- Length unit: metre, in every record and in both export formats.
- Right-handed Cartesian frame; `z` is the device axis, increasing
  downstream; the origin is the inner face of the back wall on the axis.
  The back wall therefore occupies negative `z`.
- Float64 in the records and the canonical mesh bytes; float32 in STL and
  GLB because both containers require it (the canonical digests are taken
  on the float64 bytes, never on the exports).

## Bodies (fixed order, fixed names)

`a`, `b` and `L_a` are the configuration's anode radius, cathode radius and
anode length; `t_ins`/`L_ins` the insulator sleeve wall and length, `r_rod`/
`N`/`L_cat` the cathode rod radius, rod count and cathode length,
`r_ch`/`t_ch`/`L_ch` the chamber bore, wall and length, `t_bw`/`t_ew` the
back-wall and end-wall thickness, and `rp`/`zp` the declared pinch column.
The body count is `6 + N`.

| Node name | Role | Material token | Analytic body |
|---|---|---|---|
| `anode` | `electrode` | `electrode_conductor` | solid cylinder of radius `a`, `z in [0, L_a]` |
| `insulator_sleeve` | `insulator` | `insulator_sleeve` | annular tube `a` to `a + t_ins`, `z in [0, L_ins]` |
| `cathode_rod_00` … `cathode_rod_<N-1>` | `electrode` | `electrode_conductor` | `N` solid cylinders of radius `r_rod`, `z in [0, L_cat]`, centres equally spaced on the circle of radius `b`, the first on the positive `x` axis and the rest in increasing angle |
| `chamber_wall` | `vacuum_boundary` | `chamber_wall` | annular tube `r_ch` to `r_ch + t_ch`, `z in [0, L_ch]` |
| `back_wall` | `vacuum_boundary` | `chamber_wall` | solid cylinder of the chamber outer radius, `z in [-t_bw, 0]` |
| `end_wall_downstream` | `vacuum_boundary` | `chamber_wall` | solid cylinder of the chamber outer radius, `z in [L_ch, L_ch + t_ew]` |
| `pinch_column` | `plasma` | `plasma` | solid cylinder of radius `rp`, `z in [L_a, L_a + zp]` |

The rod index is zero-padded to the width of `N - 1`, so the node names sort
in ring order for any count.

Material tokens are declarations only; no density, composition,
conductivity or nuclear property is carried anywhere.

Every body is a closed triangle surface with outward orientation
(counter-clockwise vertex order seen from outside), no degenerate face,
every directed edge appearing exactly once together with its reverse.
Segment counts are multiples of eight (at least eight).

## Files

- **Binary STL** (`stl_bytes`, `write_stl`): 80-byte header written by the
  shared library kernel, `uint32` triangle count, then per triangle a
  float32 unit normal, three float32 vertices and a zero `uint16`
  attribute. All bodies are concatenated in the fixed order; STL carries
  no names, so the GLB is the file for body identity.
- **glTF 2.0 binary** (`glb_bytes`, `write_glb`): header (magic `glTF`,
  version 2, total length), one JSON chunk (space-padded to four bytes),
  one binary chunk (zero-padded). One `mesh` and one `node` per body, the
  node named as in the table above, with `node.extras` = `{role,
  material_identifier, mesh_sha256}`. Each primitive has a float32 `VEC3`
  `POSITION` accessor with `min`/`max` and a `uint32` `SCALAR` index
  accessor, mode `TRIANGLES`; buffer views are four-byte aligned. The
  document `extras` carry `schema`, `schema_version`,
  `configuration_digest_sha256`, `geometry_digest_sha256`, `model_sha256`,
  `pinch_radius_m`, `pinch_length_m`, `rod_count`, `segments`, `units` and
  `non_claims`. No materials,
  textures, animations or extensions are used.
- **STEP** (`write_step`, capability `device_cad_model`, ADR 0009): an ISO
  10303-21 (AP214) export of the B-rep assembly of the SAME bodies — the
  cathode included as one solid per rod on the same ring centres — built
  by the pinned OpenCASCADE kernel through the shared library's `cad`
  group. The header is normalised by the library: the `FILE_NAME` name and
  time stamp are fixed literals, the assembly usage-occurrence identifiers
  are renumbered from one, the writer's continuation lines are unfolded,
  and `FILE_DESCRIPTION` carries the generator name and the provenance
  extras (record schema, both source digests, the assembly manifest
  digest, the cathode rod count and ring separation, the back-end
  versions, the units and the non-claims) as a JSON string. The file
  written is exactly the byte string whose SHA-256 the CAD model record
  carries as `step_sha256`; the bytes are deterministic within one pinned
  back-end environment and no identity across OpenCASCADE versions is
  claimed. The CAD model record
  (`scpn.dense-plasma-focus-cad-model.v1` version `1.0.0`) additionally
  carries, per body, the B-rep volume and area against the analytic closed
  form within `1e-9` relative, the faceted volume deficit within the
  declared bound `2 d / r`, and the faceted volume against the tier-G1
  mesh at the declared reference segment count within the exact
  polygon-deficit bound. Bounding boxes in the assembly manifest are the
  exact boxes of the geometry: they do not depend on whether the bodies
  have been faceted.

## Determinism

The same configuration, geometry, pinch column and segment count always
yield the same records, the same mesh bytes and the same export bytes, on
every backend: the vertex coordinates are computed by the polynomial unit
circle of the shared kernel library `scpn-reactor-kernels` (pinned by
commit object and kernel-inventory digest in `reactor-domain.json`,
`kernel_library`) with fixed operation order, proven bit-exact between
that library's Python floor and its native kernels, and this device model
is proven bit-exact against the library's native module body by body. The
serialisers are the library's kernel `geometry_exports`: the binary STL
header and the glTF `asset.generator` name that kernel, while the document
`extras` carry this repository's provenance. A change of the library pin
is a governed data change of this repository.

## What is not modelled

The rods are straight cylinders: their mounting into the back-wall plate,
any taper or chamfer, and the insulator end fittings are absent. Gas ports,
diagnostic windows, the collector plate and supports are absent too. Nothing
in the model stands in for something it is not.

## Non-claims

- The bodies are analytic surfaces of a synthetic design: no CAD solid,
  no compression boundary, no engineering model. The plasma body is the
  declared pinch column standing on the anode tip, not a computed
  compression boundary.
- No material property, load, field or neutronic quantity is carried.
- No value describes or validates any real machine.
- Providing these files does not federate the repository, present it, or
  gate its execution anywhere; those remain the portfolio layer's domain.
