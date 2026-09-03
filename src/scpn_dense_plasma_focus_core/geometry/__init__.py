# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device geometry and 3D model

"""Device geometry and tier-G1 3D model of the plasma-focus family.

A validated device geometry, the composed device model record of the
anode, the insulator sleeve, every cathode rod, the chamber and the pinch
column, and the device-side provenance of the open-format
exports (binary STL, glTF 2.0 binary). The unit circle, the tessellation
primitives, the closed-mesh contract and the serialisers are consumed
from the pinned shared kernel library ``scpn_reactor_kernels``; the mesh
type of every body is that library's ``TriangleMesh``. Every body is an
analytic surface of a synthetic design; nothing here is a CAD solid, a
compression boundary or an engineering model, and no value describes a
real machine. Design records: ADR 0006, ADR 0007.
"""

from __future__ import annotations

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
    "body_names",
    "build_device_model",
    "cathode_rod_names",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "stl_bytes",
    "write_glb",
    "write_stl",
]
