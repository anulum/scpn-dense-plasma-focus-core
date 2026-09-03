# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device model parity against the library kernels

"""Bit-exact parity of the device model against the pinned library's native kernels.

The device model is composed on the Python floor of the shared kernel
library; this file proves that every body it builds agrees bit for bit
with the library's native tessellation and mesh measures, so the consumer
inherits the library's parity rather than re-proving the kernels. Skipped
hermetically when the library's optional native module is absent; when
present, every vertex coordinate, face index and measure is compared by
float64 bit pattern, never by tolerance. All inputs are synthetic.
"""

from __future__ import annotations

import pytest

from geometry_fixtures import (
    REFERENCE_PINCH_LENGTH_M,
    REFERENCE_PINCH_RADIUS_M,
    bits,
    reference_configuration,
    reference_geometry,
    stream_bits,
)
from scpn_dense_plasma_focus_core.geometry import build_device_model

native = pytest.importorskip("scpn_reactor_kernels_native")


def native_bodies(segments: int) -> list[tuple[list[float], list[int]]]:
    """Tessellate the seven device bodies through the library's native kernels."""
    geometry = reference_geometry()
    electrodes = reference_configuration().electrodes
    anode_radius = electrodes.anode_radius_m
    cathode_radius = electrodes.cathode_radius_m
    anode_length = electrodes.anode_length_m
    chamber_outer = geometry.chamber_outer_radius_m
    chamber_length = geometry.chamber_length_m
    rod_vertices, rod_faces = native.tessellate_cylinder(
        geometry.cathode_rod_radius_m, 0.0, geometry.cathode_length_m, segments
    )
    ring = native.ring_offsets(geometry.cathode_rod_count, cathode_radius)
    rods = tuple(
        (
            native.translate(rod_vertices, ring[2 * index], ring[2 * index + 1], 0.0),
            rod_faces,
        )
        for index in range(geometry.cathode_rod_count)
    )
    streams = (
        native.tessellate_cylinder(anode_radius, 0.0, anode_length, segments),
        native.tessellate_annular_tube(
            anode_radius,
            anode_radius + geometry.insulator_sleeve_wall_thickness_m,
            0.0,
            geometry.insulator_sleeve_length_m,
            segments,
        ),
        *rods,
        native.tessellate_annular_tube(
            geometry.chamber_inner_radius_m,
            chamber_outer,
            0.0,
            chamber_length,
            segments,
        ),
        native.tessellate_cylinder(
            chamber_outer, 0.0 - geometry.back_wall_thickness_m, 0.0, segments
        ),
        native.tessellate_cylinder(
            chamber_outer,
            chamber_length,
            chamber_length + geometry.end_wall_thickness_m,
            segments,
        ),
        native.tessellate_cylinder(
            REFERENCE_PINCH_RADIUS_M,
            anode_length,
            anode_length + REFERENCE_PINCH_LENGTH_M,
            segments,
        ),
    )
    return [(list(vertices), list(faces)) for vertices, faces in streams]


@pytest.mark.parametrize("segments", [8, 32, 64])
def test_every_body_is_bit_exact_with_the_library_native_kernels(
    segments: int,
) -> None:
    """Vertices, faces, volume and area of every body agree bit for bit."""
    model = build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
        segments,
    )
    bodies = native_bodies(segments)
    for mesh, (vertices, faces) in zip(model.meshes, bodies, strict=True):
        floor = [c for v in mesh.vertices for c in v]
        assert stream_bits(floor) == stream_bits(vertices)
        assert [i for f in mesh.faces for i in f] == faces
        volume = native.mesh_volume(vertices, faces)
        assert bits(volume) == bits(mesh.signed_volume_m3())
        assert bits(native.mesh_area(vertices, faces)) == bits(mesh.surface_area_m2())
