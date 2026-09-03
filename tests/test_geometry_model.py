# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device 3D model tests

"""Body inventory, placement, invariants, record identity and the pinned digest."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math

import pytest

from geometry_fixtures import (
    REFERENCE_PINCH_LENGTH_M,
    REFERENCE_PINCH_RADIUS_M,
    reference_configuration,
    reference_geometry,
)
from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.geometry import (
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    body_names,
    build_device_model,
    cathode_rod_names,
)
from scpn_dense_plasma_focus_core.parameters import ElectrodeSet

REFERENCE_MODEL_SHA256 = (
    "ee3de2ec8afc9cccd767fedc4df8b5679b380db3cf1d6843881654ce5cee7a62"
)
REFERENCE_ROD_COUNT = 12


def reference_model(segments: int = 16) -> DeviceModel3D:
    """Build the reference model of these tests at a segment count."""
    return build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
        segments,
    )


def test_bodies_roles_and_materials() -> None:
    """Every body in the fixed order with the declared roles and materials."""
    model = reference_model()
    names = body_names(REFERENCE_ROD_COUNT)
    assert tuple(mesh.name for mesh in model.meshes) == names
    assert len(model.meshes) == 6 + REFERENCE_ROD_COUNT
    rods = cathode_rod_names(REFERENCE_ROD_COUNT)
    assert rods[0] == "cathode_rod_00"
    assert rods[-1] == "cathode_rod_11"
    assert [mesh.role for mesh in model.meshes] == (
        ["electrode", "insulator"]
        + ["electrode"] * REFERENCE_ROD_COUNT
        + ["vacuum_boundary", "vacuum_boundary", "vacuum_boundary", "plasma"]
    )
    assert [mesh.material_identifier for mesh in model.meshes] == (
        ["electrode_conductor", "insulator_sleeve"]
        + ["electrode_conductor"] * REFERENCE_ROD_COUNT
        + ["chamber_wall", "chamber_wall", "chamber_wall", "plasma"]
    )
    for mesh in model.meshes:
        assert mesh.signed_volume_m3() > 0.0


def test_rods_stand_on_the_cathode_circle_and_clear_each_other() -> None:
    """Every rod is a cylinder on the cathode circle, clear of its neighbours."""
    geometry = reference_geometry()
    electrodes = reference_configuration().electrodes
    model = reference_model(64)
    rods = model.meshes[2 : 2 + REFERENCE_ROD_COUNT]
    radius = geometry.cathode_rod_radius_m
    centres = []
    for rod in rods:
        low, high = rod.bounding_box()
        assert low[2] == 0.0
        assert high[2] == geometry.cathode_length_m
        centre_x = (low[0] + high[0]) / 2.0
        centre_y = (low[1] + high[1]) / 2.0
        centres.append((centre_x, centre_y))
        assert math.hypot(centre_x, centre_y) == pytest.approx(
            electrodes.cathode_radius_m, abs=1.0e-12
        )
        assert (high[0] - low[0]) == pytest.approx(2.0 * radius, rel=1.0e-3)
    for index, (x_a, y_a) in enumerate(centres):
        x_b, y_b = centres[(index + 1) % REFERENCE_ROD_COUNT]
        assert math.hypot(x_b - x_a, y_b - y_a) > 2.0 * radius
    inner = electrodes.cathode_radius_m - radius
    assert inner > (
        electrodes.anode_radius_m + geometry.insulator_sleeve_wall_thickness_m
    )
    assert electrodes.cathode_radius_m + radius <= geometry.chamber_inner_radius_m


def test_sleeve_sits_in_the_electrode_annulus_and_covers_only_the_base() -> None:
    """The sleeve starts at the anode surface, stays inside the cathode, ends early."""
    geometry = reference_geometry()
    electrodes = reference_configuration().electrodes
    anode, sleeve, cathode, *_ = reference_model().meshes
    assert sleeve.bounding_box()[0][2] == anode.bounding_box()[0][2] == 0.0
    assert sleeve.bounding_box()[1][2] == geometry.insulator_sleeve_length_m
    assert sleeve.bounding_box()[1][2] < anode.bounding_box()[1][2]
    assert sleeve.bounding_box()[1][0] == (
        electrodes.anode_radius_m + geometry.insulator_sleeve_wall_thickness_m
    )
    assert sleeve.bounding_box()[1][0] < electrodes.cathode_radius_m
    assert cathode.bounding_box()[1][0] == pytest.approx(
        electrodes.cathode_radius_m + geometry.cathode_rod_radius_m, abs=1.0e-12
    )
    assert cathode.bounding_box()[1][0] <= geometry.chamber_inner_radius_m


def test_walls_close_the_chamber_and_the_column_stands_on_the_anode_tip() -> None:
    """The two walls cap the chamber; the column starts where the anode ends."""
    geometry = reference_geometry()
    electrodes = reference_configuration().electrodes
    meshes = reference_model().meshes
    anode = meshes[0]
    chamber, back, end, column = meshes[-4:]
    assert chamber.bounding_box()[0][2] == 0.0
    assert chamber.bounding_box()[1][2] == geometry.chamber_length_m
    assert back.bounding_box()[1][2] == chamber.bounding_box()[0][2]
    assert back.bounding_box()[0][2] == -geometry.back_wall_thickness_m
    assert end.bounding_box()[0][2] == chamber.bounding_box()[1][2]
    assert end.bounding_box()[1][2] == pytest.approx(
        geometry.chamber_length_m + geometry.end_wall_thickness_m
    )
    for wall in (back, end):
        assert wall.bounding_box()[1][0] == geometry.chamber_outer_radius_m
    assert column.bounding_box()[0][2] == anode.bounding_box()[1][2]
    assert column.bounding_box()[0][2] == electrodes.anode_length_m
    assert column.bounding_box()[1][2] == pytest.approx(
        electrodes.anode_length_m + REFERENCE_PINCH_LENGTH_M
    )
    assert column.bounding_box()[1][2] < geometry.chamber_length_m
    assert column.bounding_box()[1][0] == REFERENCE_PINCH_RADIUS_M


def test_volumes_follow_the_analytic_bodies() -> None:
    """Each body volume converges on the analytic cylinder or tube volume."""
    model = reference_model(1024)
    analytic = (
        [
            math.pi * 0.05**2 * 0.3,
            math.pi * (0.058**2 - 0.05**2) * 0.06,
        ]
        + [math.pi * 0.006**2 * 0.32] * REFERENCE_ROD_COUNT
        + [
            math.pi * (0.16**2 - 0.15**2) * 0.5,
            math.pi * 0.16**2 * 0.02,
            math.pi * 0.16**2 * 0.02,
            math.pi * REFERENCE_PINCH_RADIUS_M**2 * REFERENCE_PINCH_LENGTH_M,
        ]
    )
    for mesh, exact in zip(model.meshes, analytic, strict=True):
        assert 0.0 < (exact - mesh.signed_volume_m3()) / exact < 1.0e-5


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_model(
        configuration,
        geometry,
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
        8,
    )
    record = model.to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["units"] == MODEL_UNITS
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["pinch_radius_m"] == REFERENCE_PINCH_RADIUS_M
    assert record["pinch_length_m"] == REFERENCE_PINCH_LENGTH_M
    assert record["rod_count"] == REFERENCE_ROD_COUNT
    assert record["segments"] == 8
    assert [body["name"] for body in record["bodies"]] == list(
        body_names(REFERENCE_ROD_COUNT)
    )
    data = model.canonical_bytes()
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_MODEL_SHA256


def test_model_is_deterministic() -> None:
    """Two builds of the same inputs are equal and share every digest."""
    first = reference_model(32)
    second = reference_model(32)
    assert first == second
    assert first.digest_sha256() == second.digest_sha256()
    assert [m.digest_sha256() for m in first.meshes] == [
        m.digest_sha256() for m in second.meshes
    ]


def test_rods_must_clear_the_sleeve_and_each_other() -> None:
    """A rod reaching the sleeve, or rods that would intersect, are refused."""
    geometry = dataclasses.replace(reference_geometry(), cathode_rod_radius_m=0.043)
    with pytest.raises(DeviceGeometryError, match="cathode_rod_radius_m"):
        build_device_model(
            reference_configuration(),
            geometry,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )
    crowded = dataclasses.replace(
        reference_geometry(), cathode_rod_count=64, cathode_rod_radius_m=0.02
    )
    with pytest.raises(DeviceGeometryError, match="would intersect"):
        build_device_model(
            reference_configuration(),
            crowded,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


def test_sleeve_must_stay_inside_the_cathode() -> None:
    """A sleeve as wide as the cathode bore is refused."""
    geometry = dataclasses.replace(
        reference_geometry(), insulator_sleeve_wall_thickness_m=0.05
    )
    with pytest.raises(DeviceGeometryError, match="insulator_sleeve_wall_thickness_m"):
        build_device_model(
            reference_configuration(),
            geometry,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


def test_cathode_must_fit_the_chamber_bore() -> None:
    """A cathode wider than the chamber bore is refused."""
    geometry = dataclasses.replace(reference_geometry(), chamber_inner_radius_m=0.105)
    with pytest.raises(DeviceGeometryError, match="chamber_inner_radius_m"):
        build_device_model(
            reference_configuration(),
            geometry,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


def test_sleeve_must_not_be_longer_than_the_anode() -> None:
    """A sleeve longer than the anode is refused."""
    geometry = dataclasses.replace(reference_geometry(), insulator_sleeve_length_m=0.4)
    with pytest.raises(DeviceGeometryError, match="insulator_sleeve_length_m"):
        build_device_model(
            reference_configuration(),
            geometry,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


def test_anode_must_fit_the_chamber_length() -> None:
    """An anode longer than the chamber is refused."""
    configuration = dataclasses.replace(
        reference_configuration(),
        electrodes=ElectrodeSet(
            anode_radius_m=0.05, cathode_radius_m=0.1, anode_length_m=0.6
        ),
    )
    with pytest.raises(DeviceGeometryError, match="anode_length_m"):
        build_device_model(
            configuration,
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


def test_pinch_column_must_fit_the_anode_radius_and_the_chamber() -> None:
    """A column as wide as the anode or leaving the chamber is refused."""
    with pytest.raises(DeviceGeometryError, match="pinch_radius_m"):
        build_device_model(
            reference_configuration(),
            reference_geometry(),
            0.05,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )
    with pytest.raises(DeviceGeometryError, match="pinch_length_m"):
        build_device_model(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            0.25,
            8,
        )


@pytest.mark.parametrize("radius", [0.0, -0.001, math.nan, math.inf])
def test_pinch_radius_must_be_finite_and_positive(radius: float) -> None:
    """A non-finite or non-positive column radius fails closed."""
    with pytest.raises(DeviceGeometryError, match="pinch_radius_m"):
        build_device_model(
            reference_configuration(),
            reference_geometry(),
            radius,
            REFERENCE_PINCH_LENGTH_M,
            8,
        )


@pytest.mark.parametrize("length", [0.0, -0.001, math.nan, math.inf])
def test_pinch_length_must_be_finite_and_positive(length: float) -> None:
    """A non-finite or non-positive column length fails closed."""
    with pytest.raises(DeviceGeometryError, match="pinch_length_m"):
        build_device_model(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            length,
            8,
        )


def test_invalid_segments_are_refused_before_tessellation() -> None:
    """The segment rule is checked first."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_model(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            20,
        )


def test_body_inventory_is_enforced() -> None:
    """A model with the wrong bodies or order is refused."""
    model = reference_model(8)
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        DeviceModel3D(
            configuration_digest_sha256=model.configuration_digest_sha256,
            geometry_digest_sha256=model.geometry_digest_sha256,
            pinch_radius_m=model.pinch_radius_m,
            pinch_length_m=model.pinch_length_m,
            rod_count=model.rod_count,
            segments=8,
            meshes=model.meshes[::-1],
        )
