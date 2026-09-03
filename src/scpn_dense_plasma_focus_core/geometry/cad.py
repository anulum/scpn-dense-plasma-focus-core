# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device CAD model record (tier G2)

"""Tier-G2 device CAD model: B-rep solids of one validated design.

The model composes the validated configuration (coaxial electrode pair),
the validated device geometry (insulator sleeve, cathode cage, chamber,
closing walls) and the declared pinch column of the level-0 models into
the same named bodies as the tier-G1 model (:func:`build_device_model`),
built as exact B-rep solids by the pinned third-party OpenCASCADE kernel
through the shared kernel library (``scpn_reactor_kernels.cad``, kernels
``cad_brep_solids``, ``cad_placement``, ``cad_step_export``,
``cad_faceting``, ``cad_evidence``).

The cathode is the squirrel cage it is at this tier as well: one solid per
rod, placed on the coaxial circle of the configuration's cathode radius by
the library's placement kernel, on the same centres the tessellated model
uses — so the two tiers sit on one circle by construction rather than by
coincidence. The build refuses a rod set whose members would intersect
each other, the insulator sleeve or the chamber wall, on the same
invariants as tier G1.

OpenCASCADE is not the bit-exact floor: every body is checked fail-closed
by the library's evidence kernel against its analytic closed form (volume
and surface area within the declared relative tolerance ``1e-9``), the
faceted volume is checked against the declared deflection deficit bound
and against the tier-G1 mesh at the declared reference segment count
within the exact polygon-deficit bound, and the STEP export is the
library's normalised deterministic writer. This module owns only what is
device knowledge: the schema identity, the composition of the bodies, the
build invariants of this family and its non-claims. No body carries an
engineering property and no value describes a real machine.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Final

from scpn_reactor_kernels.cad import (
    MANIFEST_SCHEMA,
    BodyEvidence,
    BrepAssembly,
    annular_tube_brep,
    assembly_evidence,
    backend_versions,
    cylinder_solid_brep,
    facet_assembly,
    ring_brep_bodies,
)
from scpn_reactor_kernels.cad import (
    step_bytes as _normalised_step_bytes,
)
from scpn_reactor_kernels.cad import (
    step_sha256 as _step_bytes_sha256,
)
from scpn_reactor_kernels.errors import CadError, GeometryError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    require_segments,
    ring_offsets,
    ring_separation_m,
)

from scpn_dense_plasma_focus_core.configuration import DeviceConfiguration
from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.geometry.device import DeviceGeometry
from scpn_dense_plasma_focus_core.geometry.model import (
    BODY_ANODE,
    BODY_BACK_WALL,
    BODY_CHAMBER_WALL,
    BODY_END_WALL_DOWNSTREAM,
    BODY_INSULATOR_SLEEVE,
    BODY_PINCH_COLUMN,
    MATERIAL_CHAMBER_WALL,
    MATERIAL_ELECTRODE_CONDUCTOR,
    MATERIAL_INSULATOR_SLEEVE,
    MATERIAL_PLASMA,
    MODEL_UNITS,
    ROLE_ELECTRODE,
    ROLE_INSULATOR,
    ROLE_PLASMA,
    ROLE_VACUUM_BOUNDARY,
    body_names,
    build_device_model,
    cathode_rod_names,
)

CAD_MODEL_SCHEMA: Final = "scpn.dense-plasma-focus-cad-model.v1"
CAD_MODEL_SCHEMA_VERSION: Final = "1.0.0"
CAD_MODEL_NON_CLAIMS: Final = (
    (
        "B-rep solids of the same declared design, built by the pinned "
        "third-party OpenCASCADE kernel and checked against the analytic closed "
        "forms; not an engineering model"
    ),
    "no material property, load, field or neutronic quantity is carried",
    "the rods are straight cylinders; their mounting hardware is not modelled",
    (
        "STEP bytes are deterministic only within one pinned back-end "
        "environment; identity across OpenCASCADE or gmsh versions is not claimed"
    ),
    (
        "a dimension reproduced from a published arrangement is an anchor,"
        " not a claim about that machine"
    ),
)

#: Reference segment count of the tier-G1 mesh the faceted B-rep is
#: compared against.
DEFAULT_REFERENCE_MESH_SEGMENTS: Final = 8
#: Declared mesher deflections of the reference record.
DEFAULT_LINEAR_DEFLECTION_M: Final = 1.0e-4
DEFAULT_ANGULAR_DEFLECTION_RAD: Final = 0.1


@dataclass(frozen=True, slots=True)
class DeviceModelCAD:
    """The B-rep device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    pinch_radius_m, pinch_length_m
        Declared pinch column the plasma body was built from.
    rod_count
        Number of cathode rods the model was built with.
    reference_mesh_segments
        Segment count of the tier-G1 reference mesh of the comparison.
    linear_deflection_m, angular_deflection_rad
        Declared mesher deflections of the faceting evidence.
    backend_versions
        Versions of the pinned CAD back-ends (``cadquery``, ``ocp``,
        ``gmsh``) as reported by the library.
    assembly_manifest
        The library's B-rep assembly manifest record.
    step_sha256
        SHA-256 of the normalised STEP export of the assembly.
    bodies
        Per-body evidence in the fixed order of :func:`body_names`, as
        checked by the library's evidence kernel.
    step_data
        The normalised STEP bytes (the digested export).
    faceted_meshes
        The faceted closed meshes, one per body, in the fixed order.

    Raises
    ------
    DeviceGeometryError
        If the body inventory differs from :func:`body_names`, the segment
        rule or the deflection rule is violated, the manifest is foreign,
        or the STEP digest is not a 64-hex value.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    pinch_radius_m: float
    pinch_length_m: float
    rod_count: int
    reference_mesh_segments: int
    linear_deflection_m: float
    angular_deflection_rad: float
    backend_versions: dict[str, str]
    assembly_manifest: dict[str, Any]
    step_sha256: str
    bodies: tuple[BodyEvidence, ...]
    step_data: bytes = field(compare=False, repr=False)
    faceted_meshes: tuple[TriangleMesh, ...] = field(
        compare=False, repr=False, default=()
    )

    def __post_init__(self) -> None:
        """Validate the model inventory and declared parameters.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        expected = body_names(self.rod_count)
        names = tuple(body.name for body in self.bodies)
        if names != expected:
            raise DeviceGeometryError(
                f"bodies: bodies must be exactly {expected!r} in order, got {names!r}"
            )
        try:
            require_segments(self.reference_mesh_segments)
        except GeometryError as exc:
            raise DeviceGeometryError(str(exc)) from exc
        for name, value in (
            ("linear_deflection_m", self.linear_deflection_m),
            ("angular_deflection_rad", self.angular_deflection_rad),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise DeviceGeometryError(
                    f"{name}: must be finite and strictly positive, got {value!r}"
                )
        if self.assembly_manifest.get("schema") != MANIFEST_SCHEMA:
            raise DeviceGeometryError(
                f"assembly_manifest.schema: must be {MANIFEST_SCHEMA!r}"
            )
        if self.assembly_manifest.get("body_count") != len(expected):
            raise DeviceGeometryError(
                f"assembly_manifest.body_count: must be {len(expected)}, got "
                f"{self.assembly_manifest.get('body_count')!r}"
            )
        if len(self.step_sha256) != 64 or not all(
            character in "0123456789abcdef" for character in self.step_sha256
        ):
            raise DeviceGeometryError(
                "step_sha256: must be 64 lowercase hexadecimal characters"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, the pinch
            column, the rod count, the declared deflections and reference
            segment count, back-end versions, the assembly manifest, the
            STEP digest and every body evidence.
        """
        return {
            "schema": CAD_MODEL_SCHEMA,
            "schema_version": CAD_MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(CAD_MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "pinch_radius_m": self.pinch_radius_m,
            "pinch_length_m": self.pinch_length_m,
            "rod_count": self.rod_count,
            "reference_mesh_segments": self.reference_mesh_segments,
            "linear_deflection_m": self.linear_deflection_m,
            "angular_deflection_rad": self.angular_deflection_rad,
            "backend_versions": dict(self.backend_versions),
            "assembly_manifest": self.assembly_manifest,
            "step_sha256": self.step_sha256,
            "bodies": [body.to_record() for body in self.bodies],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def build_device_cad(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    pinch_radius_m: float,
    pinch_length_m: float,
    segments: int = DEFAULT_REFERENCE_MESH_SEGMENTS,
    linear_deflection_m: float = DEFAULT_LINEAR_DEFLECTION_M,
    angular_deflection_rad: float = DEFAULT_ANGULAR_DEFLECTION_RAD,
) -> DeviceModelCAD:
    """Build the B-rep device model of a validated design.

    Parameters
    ----------
    configuration
        Validated plasma-focus configuration; its electrode set fixes the
        anode radius, the cathode radius and the anode length.
    geometry
        Validated device geometry (insulator sleeve, cathode cage,
        chamber, closing walls).
    pinch_radius_m
        Declared pinch column radius; strictly positive and smaller than
        the anode radius, the same rule the level-0 record enforces.
    pinch_length_m
        Declared pinch column length; strictly positive.
    segments
        Segment count of the tier-G1 reference mesh of the faceting
        comparison; at least 8, multiple of 8.
    linear_deflection_m
        Largest chord distance of the faceting to the true surface;
        strictly positive.
    angular_deflection_rad
        Largest angle between adjacent facet normals; strictly positive.

    Returns
    -------
    DeviceModelCAD
        The composed, fail-closed checked model with its STEP export.

    Raises
    ------
    DeviceGeometryError
        If the tier-G1 build refuses the design (segment rule, sleeve fit,
        rod clearance, rod intersection, chamber fit, lengths, column
        containment), if a deflection is invalid, or if a body violates a
        declared evidence bound (the library's refusals are re-raised
        under the device error type with their messages);
        :class:`~scpn_reactor_kernels.errors.CadUnavailableError` if the
        optional CAD back-end is absent.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    reference = build_device_model(
        configuration, geometry, pinch_radius_m, pinch_length_m, segments
    )
    electrodes = configuration.electrodes
    anode_radius = electrodes.anode_radius_m
    cathode_radius = electrodes.cathode_radius_m
    anode_length = electrodes.anode_length_m
    sleeve_outer = anode_radius + geometry.insulator_sleeve_wall_thickness_m
    rod_radius = geometry.cathode_rod_radius_m
    rod_count = geometry.cathode_rod_count
    chamber_outer = geometry.chamber_outer_radius_m
    chamber_length = geometry.chamber_length_m
    try:
        rod = cylinder_solid_brep(
            rod_radius,
            0.0,
            geometry.cathode_length_m,
            "cathode_rod",
            ROLE_ELECTRODE,
            MATERIAL_ELECTRODE_CONDUCTOR,
        )
        rods = ring_brep_bodies(
            rod,
            cathode_rod_names(rod_count),
            ring_offsets(rod_count, cathode_radius),
        )
        assembly = BrepAssembly(
            (
                cylinder_solid_brep(
                    anode_radius,
                    0.0,
                    anode_length,
                    BODY_ANODE,
                    ROLE_ELECTRODE,
                    MATERIAL_ELECTRODE_CONDUCTOR,
                ),
                annular_tube_brep(
                    anode_radius,
                    sleeve_outer,
                    0.0,
                    geometry.insulator_sleeve_length_m,
                    BODY_INSULATOR_SLEEVE,
                    ROLE_INSULATOR,
                    MATERIAL_INSULATOR_SLEEVE,
                ),
                *rods,
                annular_tube_brep(
                    geometry.chamber_inner_radius_m,
                    chamber_outer,
                    0.0,
                    chamber_length,
                    BODY_CHAMBER_WALL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    chamber_outer,
                    0.0 - geometry.back_wall_thickness_m,
                    0.0,
                    BODY_BACK_WALL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    chamber_outer,
                    chamber_length,
                    chamber_length + geometry.end_wall_thickness_m,
                    BODY_END_WALL_DOWNSTREAM,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_CHAMBER_WALL,
                ),
                cylinder_solid_brep(
                    pinch_radius_m,
                    anode_length,
                    anode_length + pinch_length_m,
                    BODY_PINCH_COLUMN,
                    ROLE_PLASMA,
                    MATERIAL_PLASMA,
                ),
            )
        )
        faceted = facet_assembly(assembly, linear_deflection_m, angular_deflection_rad)
        smallest_radii = (
            anode_radius,
            anode_radius,
            *(rod_radius for _ in range(rod_count)),
            geometry.chamber_inner_radius_m,
            chamber_outer,
            chamber_outer,
            pinch_radius_m,
        )
        bodies = assembly_evidence(
            assembly.bodies,
            smallest_radii,
            faceted,
            reference.meshes,
            linear_deflection_m,
            segments,
        )
    except CadError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    manifest = assembly.manifest()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "cathode_rod_count": rod_count,
        "cathode_ring_separation_m": ring_separation_m(rod_count, cathode_radius),
        "units": dict(MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }
    step_data = _normalised_step_bytes(assembly, extras)
    return DeviceModelCAD(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        pinch_radius_m=pinch_radius_m,
        pinch_length_m=pinch_length_m,
        rod_count=rod_count,
        reference_mesh_segments=segments,
        linear_deflection_m=linear_deflection_m,
        angular_deflection_rad=angular_deflection_rad,
        backend_versions=backend_versions(),
        assembly_manifest=manifest,
        step_sha256=_step_bytes_sha256(step_data),
        bodies=bodies,
        step_data=step_data,
        faceted_meshes=faceted,
    )
