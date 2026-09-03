# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device geometry and 3D model

"""Device geometry, tier-G1 3D model and tier-G2 CAD model of the family.

A validated device geometry, the composed device model record of the
anode, the insulator sleeve, every cathode rod, the chamber and the pinch
column, the composed device CAD model record of the same bodies as B-rep
solids on the pinned third-party OpenCASCADE kernel, and the device-side
provenance of the open-format exports (binary STL, glTF 2.0 binary,
STEP). The unit circle, the tessellation primitives, the closed-mesh
contract, the placement of bodies off the axis, the serialisers and the
B-rep, STEP, faceting and body-evidence kernels are consumed from the
pinned shared kernel library ``scpn_reactor_kernels``; the mesh type of
every body is that library's ``TriangleMesh`` and the per-body evidence
is its ``BodyEvidence``. The cathode is the cage of rods it is at both
tiers, on one set of centres. Every tier-G1 body is an analytic surface
and every tier-G2 body is a B-rep solid of the same declared design;
nothing here is a compression boundary or an engineering model, and no
value describes a real machine. Design records: ADR 0006, ADR 0007, ADR
0008, ADR 0009.
"""

from __future__ import annotations

from scpn_dense_plasma_focus_core.geometry.cad import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModelCAD,
    build_device_cad,
)
from scpn_dense_plasma_focus_core.geometry.device import (
    GEOMETRY_COUNT_FIELDS,
    GEOMETRY_FIELDS,
    RECORD_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)
from scpn_dense_plasma_focus_core.geometry.export import (
    GLTF_GENERATOR,
    STL_HEADER,
    glb_bytes,
    glb_extras,
    stl_bytes,
    write_glb,
    write_step,
    write_stl,
)
from scpn_dense_plasma_focus_core.geometry.model import (
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    body_names,
    build_device_model,
    cathode_rod_names,
)

__all__ = [
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "GEOMETRY_COUNT_FIELDS",
    "GEOMETRY_FIELDS",
    "GLTF_GENERATOR",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "RECORD_FIELDS",
    "STL_HEADER",
    "DeviceGeometry",
    "DeviceModel3D",
    "DeviceModelCAD",
    "body_names",
    "build_device_cad",
    "build_device_model",
    "cathode_rod_names",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "stl_bytes",
    "write_glb",
    "write_step",
    "write_stl",
]
