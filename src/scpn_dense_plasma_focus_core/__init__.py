# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device capability package

"""Device capability models of the SCPN dense-plasma-focus family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics``, ``level0_device_physics``,
``device_3d_model`` and ``device_cad_model`` capabilities
at ``computational_prototype`` maturity: validated parameter objects,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, the closed forms of the Lee model evaluated on
the validated configuration, documented consistency estimates, a validated
device geometry with a deterministic tier-G1 3D model built on the pinned
shared kernel library and open-format exports, the tier-G2 B-rep CAD model
of the same design — cathode rod cage included — with a normalised
deterministic STEP export, canonical serialisation with SHA-256 digests,
and data-only pins to the SPO registries. No claim about any real machine
or diagnostic is made anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_dense_plasma_focus_core.configuration import (
    DEUTERIUM_DRIVE_WINDOW,
    OWNED_CONFIGURATIONS,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_dense_plasma_focus_core.errors import (
    DeviceConfigurationError,
    DeviceGeometryError,
    DiagnosticPlanError,
    NumericsError,
)
from scpn_dense_plasma_focus_core.geometry import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    GEOMETRY_FIELDS,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceGeometry,
    DeviceModel3D,
    DeviceModelCAD,
    body_names,
    build_device_cad,
    build_device_model,
    cathode_rod_names,
    geometry_from_bytes,
    geometry_from_record,
    glb_bytes,
    glb_extras,
    stl_bytes,
    write_glb,
    write_step,
    write_stl,
)
from scpn_dense_plasma_focus_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    CandidateProfile,
    ClockKind,
    ClockModel,
    ClockRelation,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    ObservabilityBinding,
    ObservabilityClass,
    ReferenceFrame,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)
from scpn_dense_plasma_focus_core.parameters import BankAndFill, ElectrodeSet
from scpn_dense_plasma_focus_core.physics import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    PinchState,
    level0_physics,
)
from scpn_dense_plasma_focus_core.plan_envelope import (
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

__version__: Final = "0.1.0.dev0"

__all__ = [
    "APPLICABLE_CANDIDATES",
    "CAD_MODEL_NON_CLAIMS",
    "CAD_MODEL_SCHEMA",
    "CAD_MODEL_SCHEMA_VERSION",
    "CATALOGUE_BINDING",
    "DEFAULT_ANGULAR_DEFLECTION_RAD",
    "DEFAULT_LINEAR_DEFLECTION_M",
    "DEFAULT_REFERENCE_MESH_SEGMENTS",
    "DEUTERIUM_DRIVE_WINDOW",
    "GEOMETRY_FIELDS",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "MODEL_NON_CLAIMS",
    "MODEL_SCHEMA",
    "MODEL_SCHEMA_VERSION",
    "MODEL_UNITS",
    "OWNED_CONFIGURATIONS",
    "BankAndFill",
    "CandidateProfile",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DeviceGeometry",
    "DeviceGeometryError",
    "DeviceModel3D",
    "DeviceModelCAD",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "DiagnosticPlanError",
    "ElectrodeSet",
    "FrameKind",
    "Level0PhysicsRecord",
    "ModelInputs",
    "NumericsError",
    "ObservabilityBinding",
    "ObservabilityClass",
    "PinchState",
    "PlanEnvelope",
    "ReferenceFrame",
    "RegistryBinding",
    "SemanticCarrier",
    "__version__",
    "body_names",
    "build_device_cad",
    "build_device_model",
    "cathode_rod_names",
    "configuration_from_bytes",
    "configuration_from_record",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "geometry_from_bytes",
    "geometry_from_record",
    "glb_bytes",
    "glb_extras",
    "level0_physics",
    "plan_from_bytes",
    "plan_from_record",
    "stl_bytes",
    "verify_envelope",
    "write_glb",
    "write_step",
    "write_stl",
]
