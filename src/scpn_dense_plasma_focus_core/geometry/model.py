# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device 3D model record

"""Tier-G1 device 3D model: analytic bodies of one validated design.

The model composes the validated configuration (coaxial electrode pair),
the validated device geometry (insulator sleeve, cathode, chamber,
closing walls) and the declared pinch column of the level-0 models into
seven named, closed, outward-oriented triangle meshes on the device axis,
regenerated deterministically from the records. Its canonical record
carries the schema identity, the units and axis convention, both source
digests, the pinch radius and length, the segment count, a summary of
every body and fixed non-claims; the SHA-256 of that record identifies
the exact model.

The meshes are analytic surfaces. The cathode is the squirrel cage it is:
one body per rod, the rods equally spaced on the coaxial circle of the
configuration's cathode radius through the shared placement kernel, and
the model refuses a rod set whose members would intersect each other, the
insulator sleeve or the chamber wall. The plasma body is the declared
pinch column at the anode tip, not a computed compression boundary, and
no body carries an engineering property. The unit circle,
the primitives and the mesh contract are consumed from the pinned shared
kernel library (``scpn_reactor_kernels.geometry``); this module owns only
the device composition.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    annular_tube,
    cylinder_solid,
    require_segments,
    ring_offsets,
    ring_separation_m,
    translate,
)

from scpn_dense_plasma_focus_core.configuration import DeviceConfiguration
from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.geometry.device import DeviceGeometry
from scpn_dense_plasma_focus_core.parameters import require_positive

MODEL_SCHEMA: Final = "scpn.dense-plasma-focus-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the device axis, increasing downstream",
    "origin": "inner face of the back wall at z = 0 on the axis",
}
MODEL_NON_CLAIMS: Final = (
    "analytic surfaces tessellated from a declared configuration and geometry",
    "no body is a compression boundary, a CAD solid or an engineering model",
    "the rods are straight cylinders; their mounting hardware is not modelled",
    "no material property, load, field or neutronic quantity is carried",
    (
        "a dimension reproduced from a published arrangement is an anchor,"
        " not a claim about that machine"
    ),
)

ROLE_ELECTRODE: Final = "electrode"
ROLE_INSULATOR: Final = "insulator"
ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_PLASMA: Final = "plasma"
MATERIAL_ELECTRODE_CONDUCTOR: Final = "electrode_conductor"
MATERIAL_INSULATOR_SLEEVE: Final = "insulator_sleeve"
MATERIAL_CHAMBER_WALL: Final = "chamber_wall"
MATERIAL_PLASMA: Final = "plasma"

BODY_ANODE: Final = "anode"
BODY_INSULATOR_SLEEVE: Final = "insulator_sleeve"
BODY_CATHODE_ROD_PREFIX: Final = "cathode_rod"
BODY_CHAMBER_WALL: Final = "chamber_wall"
BODY_BACK_WALL: Final = "back_wall"
BODY_END_WALL_DOWNSTREAM: Final = "end_wall_downstream"
BODY_PINCH_COLUMN: Final = "pinch_column"


def cathode_rod_names(rod_count: int) -> tuple[str, ...]:
    """Return the names of the cathode rods for a rod count.

    Parameters
    ----------
    rod_count
        Number of rods on the cage.

    Returns
    -------
    tuple of str
        ``cathode_rod_00`` upwards, zero-padded to the width of the last
        index so the names sort in ring order for any count.
    """
    width = len(str(rod_count - 1))
    return tuple(
        f"{BODY_CATHODE_ROD_PREFIX}_{index:0{width}d}" for index in range(rod_count)
    )


def body_names(rod_count: int) -> tuple[str, ...]:
    """Return the fixed body order of a model with ``rod_count`` rods.

    Parameters
    ----------
    rod_count
        Number of cathode rods.

    Returns
    -------
    tuple of str
        The anode, the insulator sleeve, every cathode rod in ring order,
        the chamber wall, both closing walls and the pinch column.
    """
    return (
        BODY_ANODE,
        BODY_INSULATOR_SLEEVE,
        *cathode_rod_names(rod_count),
        BODY_CHAMBER_WALL,
        BODY_BACK_WALL,
        BODY_END_WALL_DOWNSTREAM,
        BODY_PINCH_COLUMN,
    )


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    pinch_radius_m
        Declared pinch column radius the plasma body was built from.
    pinch_length_m
        Declared pinch column length the plasma body was built from.
    rod_count
        Number of cathode rods the model was built with.
    segments
        Circumferential segment count used for every body.
    meshes
        The bodies in the fixed order of :func:`body_names`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :func:`body_names`.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    pinch_radius_m: float
    pinch_length_m: float
    rod_count: int
    segments: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body inventory.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from :func:`body_names`.
        """
        expected = body_names(self.rod_count)
        names = tuple(mesh.name for mesh in self.meshes)
        if names != expected:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {expected!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, the pinch
            column, the segment count and every body summary.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "pinch_radius_m": self.pinch_radius_m,
            "pinch_length_m": self.pinch_length_m,
            "rod_count": self.rod_count,
            "segments": self.segments,
            "bodies": [mesh.summary_record() for mesh in self.meshes],
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


def build_device_model(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    pinch_radius_m: float,
    pinch_length_m: float,
    segments: int,
) -> DeviceModel3D:
    """Tessellate the seven bodies of a validated design.

    Parameters
    ----------
    configuration
        Validated plasma-focus configuration; its electrode set fixes the
        anode radius, the cathode radius and the anode length.
    geometry
        Validated device geometry (insulator sleeve, cathode, chamber,
        closing walls).
    pinch_radius_m
        Declared pinch column radius ``rp``; strictly positive and smaller
        than the anode radius, the same rule the level-0 record enforces.
    pinch_length_m
        Declared pinch column length ``zp``; strictly positive.
    segments
        Circumferential segments for every body; at least 8, multiple of 8.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid (the library's refusal is re-raised
        under the device error type with its message), if the insulator
        sleeve does not fit the electrode annulus, if a cathode rod reaches
        the sleeve, if the rods would intersect each other, if the cathode
        does not fit the chamber bore, if the sleeve is longer than the
        anode, if the anode is longer than the chamber, if the pinch column
        is not inside the anode radius, or if it leaves the chamber.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    try:
        require_positive("pinch_radius_m", pinch_radius_m)
        require_positive("pinch_length_m", pinch_length_m)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    electrodes = configuration.electrodes
    anode_radius = electrodes.anode_radius_m
    cathode_radius = electrodes.cathode_radius_m
    anode_length = electrodes.anode_length_m
    sleeve_outer = anode_radius + geometry.insulator_sleeve_wall_thickness_m
    if sleeve_outer >= cathode_radius:
        raise DeviceGeometryError(
            "insulator_sleeve_wall_thickness_m: the sleeve outer radius must stay "
            f"inside the cathode radius {cathode_radius!r}, got {sleeve_outer!r}"
        )
    rod_radius = geometry.cathode_rod_radius_m
    rod_count = geometry.cathode_rod_count
    if cathode_radius - rod_radius <= sleeve_outer:
        raise DeviceGeometryError(
            "cathode_rod_radius_m: the inner face of a rod must stay outside the "
            f"insulator sleeve at {sleeve_outer!r}, got "
            f"{cathode_radius - rod_radius!r}"
        )
    cathode_outer = cathode_radius + rod_radius
    if cathode_outer > geometry.chamber_inner_radius_m:
        raise DeviceGeometryError(
            "chamber_inner_radius_m: must be at least the cathode outer radius "
            f"{cathode_outer!r}, got {geometry.chamber_inner_radius_m!r}"
        )
    separation = ring_separation_m(rod_count, cathode_radius)
    if separation <= 2.0 * rod_radius:
        raise DeviceGeometryError(
            "cathode_rod_count: rods of radius "
            f"{rod_radius!r} would intersect on a ring whose neighbours are "
            f"{separation!r} apart"
        )
    if geometry.insulator_sleeve_length_m > anode_length:
        raise DeviceGeometryError(
            "insulator_sleeve_length_m: must not exceed anode_length_m, got "
            f"{geometry.insulator_sleeve_length_m!r} > {anode_length!r}"
        )
    if anode_length > geometry.chamber_length_m:
        raise DeviceGeometryError(
            "anode_length_m: must not exceed chamber_length_m, got "
            f"{anode_length!r} > {geometry.chamber_length_m!r}"
        )
    if pinch_radius_m >= anode_radius:
        raise DeviceGeometryError(
            "pinch_radius_m: must be smaller than anode_radius_m, got "
            f"{pinch_radius_m!r} >= {anode_radius!r}"
        )
    if anode_length + pinch_length_m > geometry.chamber_length_m:
        raise DeviceGeometryError(
            "pinch_length_m: the column must stay inside the chamber, got "
            f"{anode_length!r} + {pinch_length_m!r} > {geometry.chamber_length_m!r}"
        )
    chamber_outer = geometry.chamber_outer_radius_m
    chamber_length = geometry.chamber_length_m
    rod_vertices, rod_faces = cylinder_solid(
        rod_radius, 0.0, geometry.cathode_length_m, segments
    )
    rods = tuple(
        (
            name,
            ROLE_ELECTRODE,
            MATERIAL_ELECTRODE_CONDUCTOR,
            (translate(rod_vertices, offset_x, offset_y, 0.0), rod_faces),
        )
        for name, (offset_x, offset_y) in zip(
            cathode_rod_names(rod_count),
            ring_offsets(rod_count, cathode_radius),
            strict=True,
        )
    )
    bodies = (
        (
            BODY_ANODE,
            ROLE_ELECTRODE,
            MATERIAL_ELECTRODE_CONDUCTOR,
            cylinder_solid(anode_radius, 0.0, anode_length, segments),
        ),
        (
            BODY_INSULATOR_SLEEVE,
            ROLE_INSULATOR,
            MATERIAL_INSULATOR_SLEEVE,
            annular_tube(
                anode_radius,
                sleeve_outer,
                0.0,
                geometry.insulator_sleeve_length_m,
                segments,
            ),
        ),
        *rods,
        (
            BODY_CHAMBER_WALL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            annular_tube(
                geometry.chamber_inner_radius_m,
                chamber_outer,
                0.0,
                chamber_length,
                segments,
            ),
        ),
        (
            BODY_BACK_WALL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            cylinder_solid(
                chamber_outer, 0.0 - geometry.back_wall_thickness_m, 0.0, segments
            ),
        ),
        (
            BODY_END_WALL_DOWNSTREAM,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_CHAMBER_WALL,
            cylinder_solid(
                chamber_outer,
                chamber_length,
                chamber_length + geometry.end_wall_thickness_m,
                segments,
            ),
        ),
        (
            BODY_PINCH_COLUMN,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            cylinder_solid(
                pinch_radius_m, anode_length, anode_length + pinch_length_m, segments
            ),
        ),
    )
    meshes = tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        pinch_radius_m=pinch_radius_m,
        pinch_length_m=pinch_length_m,
        rod_count=rod_count,
        segments=segments,
        meshes=meshes,
    )
