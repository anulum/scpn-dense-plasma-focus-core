# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device CAD model tests (tier G2)

"""B-rep agreement, the rod cage, faceting bounds, STEP and record identity.

The reference pair is synthetic and describes no machine. The anchor pair
carries the electrode dimensions IAEA-TECDOC-1829 prints for the NX3
assembly A20Z160, and the anchor test proves each printed dimension
appears in the B-rep bodies; a dimension reproduced from a published
arrangement is an anchor, not a claim about that machine. The cathode is
the cage of rods it is, on the same centres the tier-G1 model uses. The
B-rep measures come from the pinned third-party OpenCASCADE kernel and are
checked against the analytic closed forms within the library's declared
tolerance; the reference mesh, the polygon-deficit bound, the placement
and the per-body evidence come from the shared kernel library.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from pathlib import Path

import pytest

pytest.importorskip("cadquery")

from scpn_reactor_kernels.cad import MANIFEST_SCHEMA, MEASURE_TOLERANCE
from scpn_reactor_kernels.errors import CadError
from scpn_reactor_kernels.geometry import ring_offsets

from geometry_fixtures import (
    ANCHOR_ANODE_LENGTH_M,
    ANCHOR_ANODE_RADIUS_M,
    ANCHOR_CATHODE_RADIUS_M,
    ANCHOR_ROD_COUNT,
    ANCHOR_ROD_RADIUS_M,
    ANCHOR_SLEEVE_LENGTH_M,
    REFERENCE_PINCH_LENGTH_M,
    REFERENCE_PINCH_RADIUS_M,
    anchor_configuration,
    anchor_geometry,
    reference_configuration,
    reference_geometry,
)
from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.geometry import (
    CAD_MODEL_NON_CLAIMS,
    CAD_MODEL_SCHEMA,
    CAD_MODEL_SCHEMA_VERSION,
    DEFAULT_ANGULAR_DEFLECTION_RAD,
    DEFAULT_LINEAR_DEFLECTION_M,
    DEFAULT_REFERENCE_MESH_SEGMENTS,
    DeviceModel3D,
    DeviceModelCAD,
    body_names,
    build_device_cad,
    build_device_model,
    cathode_rod_names,
    write_step,
)

#: Digest of the reference CAD model record in the pinned back-end
#: environment (cadquery 2.8.0, OCP 7.9.3.1); a back-end bump re-pins it
#: as a governed data change (ADR 0009).
REFERENCE_CAD_MODEL_SHA256 = (
    "9dee37544eb8dd98dcc21da138a4a0455722f7ff39e271185f9bca213631936b"
)


def reference_cad_model() -> DeviceModelCAD:
    """Build the synthetic CAD model of the tests."""
    return build_device_cad(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
    )


def reference_g1_model() -> DeviceModel3D:
    """Build the tier-G1 model of the same design at the reference segments."""
    return build_device_model(
        reference_configuration(),
        reference_geometry(),
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
        DEFAULT_REFERENCE_MESH_SEGMENTS,
    )


def analytic_volumes() -> tuple[float, ...]:
    """Return the closed-form volume of every body of the reference design.

    The expressions are the closed forms of the primitives in the shared
    library's operation order, evaluated on the same fixture values the
    build reads, so the comparison is an exact equality rather than an
    approximation against a decimal literal.
    """
    configuration = reference_configuration()
    geometry = reference_geometry()
    electrodes = configuration.electrodes
    anode_radius = electrodes.anode_radius_m
    anode_length = electrodes.anode_length_m
    sleeve_outer = anode_radius + geometry.insulator_sleeve_wall_thickness_m
    rod_radius = geometry.cathode_rod_radius_m
    chamber_inner = geometry.chamber_inner_radius_m
    chamber_outer = geometry.chamber_outer_radius_m
    chamber_length = geometry.chamber_length_m
    rod = math.pi * rod_radius * rod_radius * geometry.cathode_length_m
    return (
        math.pi * anode_radius * anode_radius * anode_length,
        math.pi
        * (sleeve_outer * sleeve_outer - anode_radius * anode_radius)
        * geometry.insulator_sleeve_length_m,
        *(rod for _ in range(geometry.cathode_rod_count)),
        math.pi
        * (chamber_outer * chamber_outer - chamber_inner * chamber_inner)
        * chamber_length,
        math.pi
        * chamber_outer
        * chamber_outer
        * (0.0 - (0.0 - geometry.back_wall_thickness_m)),
        math.pi
        * chamber_outer
        * chamber_outer
        * (chamber_length + geometry.end_wall_thickness_m - chamber_length),
        math.pi
        * REFERENCE_PINCH_RADIUS_M
        * REFERENCE_PINCH_RADIUS_M
        * (anode_length + REFERENCE_PINCH_LENGTH_M - anode_length),
    )


def test_bodies_match_the_g1_inventory_roles_and_materials() -> None:
    """The CAD bodies are the G1 bodies: same names, roles, materials."""
    model = reference_cad_model()
    reference = reference_g1_model()
    expected = body_names(reference_geometry().cathode_rod_count)
    assert tuple(body.name for body in model.bodies) == expected
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.role == mesh.role
        assert body.material_identifier == mesh.material_identifier


def test_brep_measures_agree_with_the_analytic_closed_forms() -> None:
    """Every body volume and area matches the analytic form within 1e-9."""
    model = reference_cad_model()
    for body, analytic in zip(model.bodies, analytic_volumes(), strict=True):
        assert body.analytic_volume_m3 == analytic
        assert 0.0 <= body.volume_relative_error <= MEASURE_TOLERANCE
        assert 0.0 <= body.surface_area_relative_error <= MEASURE_TOLERANCE


def test_the_cathode_is_a_cage_of_rods_on_the_configuration_circle() -> None:
    """One solid per rod, on the tier-G1 centres, all of one size.

    The rods are the reason the placement kernel exists. This test proves
    the cage is a cage: as many solids as the geometry declares, named in
    ring order, each centred on the configuration's cathode circle at the
    centre the tier-G1 model uses, and all of the same declared radius.
    """
    geometry = reference_geometry()
    cathode_radius = reference_configuration().electrodes.cathode_radius_m
    rod_count = geometry.cathode_rod_count
    model = reference_cad_model()
    boxes = {
        body["name"]: (body["bounding_box_min_m"], body["bounding_box_max_m"])
        for body in model.assembly_manifest["bodies"]
    }
    names = cathode_rod_names(rod_count)
    assert len(names) == rod_count
    centres = ring_offsets(rod_count, cathode_radius)
    for name, (centre_x, centre_y) in zip(names, centres, strict=True):
        low, high = boxes[name]
        assert math.isclose(0.5 * (low[0] + high[0]), centre_x, abs_tol=1.0e-12)
        assert math.isclose(0.5 * (low[1] + high[1]), centre_y, abs_tol=1.0e-12)
        assert math.isclose(
            0.5 * (high[0] - low[0]), geometry.cathode_rod_radius_m, abs_tol=1.0e-12
        )
        assert math.isclose(low[2], 0.0, abs_tol=1.0e-12)
        assert math.isclose(high[2], geometry.cathode_length_m, abs_tol=1.0e-12)


def test_faceted_volumes_stay_within_the_deflection_deficit_bound() -> None:
    """The faceted body underestimates the analytic volume within 2 d / r."""
    model = reference_cad_model()
    for body in model.bodies:
        assert body.faceted_volume_relative_deficit >= 0.0
        assert body.faceted_volume_relative_deficit <= body.faceted_volume_deficit_bound
        assert body.faceted_volume_m3 < body.analytic_volume_m3


def test_faceted_meshes_are_closed_and_outward_oriented() -> None:
    """Every faceted mesh satisfies the G1 closed-mesh contract."""
    model = reference_cad_model()
    assert len(model.faceted_meshes) == len(model.bodies)
    for mesh in model.faceted_meshes:
        assert mesh.signed_volume_m3() > 0.0
        assert mesh.face_count > 0


def test_faceted_volumes_track_the_reference_mesh_within_the_polygon_bound() -> None:
    """Faceted and G1 volumes agree within the exact polygon-deficit bound."""
    model = reference_cad_model()
    reference = reference_g1_model()
    for body, mesh in zip(model.bodies, reference.meshes, strict=True):
        assert body.reference_mesh_volume_m3 == mesh.signed_volume_m3()
        assert body.mesh_volume_relative_difference >= 0.0
        assert body.mesh_volume_relative_difference <= body.mesh_volume_difference_bound


def test_anchor_dimensions_appear_in_the_brep_bodies() -> None:
    """Every dimension the filed source prints is in the built solids.

    The anode radius and length, the cathode circle radius, the rod radius
    and count, and the insulator-sleeve length are the printed values of
    the NX3 assembly A20Z160; the test proves the built solids carry them.
    Reproducing a printed dimension is an anchor, not a claim about that
    machine.
    """
    model = build_device_cad(anchor_configuration(), anchor_geometry(), 0.003, 0.02)
    boxes = {
        body["name"]: (body["bounding_box_min_m"], body["bounding_box_max_m"])
        for body in model.assembly_manifest["bodies"]
    }
    anode_low, anode_high = boxes["anode"]
    assert math.isclose(anode_high[0], ANCHOR_ANODE_RADIUS_M, abs_tol=1.0e-12)
    assert math.isclose(
        anode_high[2] - anode_low[2], ANCHOR_ANODE_LENGTH_M, abs_tol=1.0e-12
    )
    sleeve_low, sleeve_high = boxes["insulator_sleeve"]
    assert math.isclose(
        sleeve_high[2] - sleeve_low[2], ANCHOR_SLEEVE_LENGTH_M, abs_tol=1.0e-12
    )
    names = cathode_rod_names(ANCHOR_ROD_COUNT)
    assert model.rod_count == ANCHOR_ROD_COUNT
    for name in names:
        low, high = boxes[name]
        centre_x = 0.5 * (low[0] + high[0])
        centre_y = 0.5 * (low[1] + high[1])
        assert math.isclose(
            math.hypot(centre_x, centre_y), ANCHOR_CATHODE_RADIUS_M, abs_tol=1.0e-12
        )
        assert math.isclose(
            0.5 * (high[0] - low[0]), ANCHOR_ROD_RADIUS_M, abs_tol=1.0e-12
        )


def test_step_export_is_byte_deterministic() -> None:
    """Two builds of the same design give byte-identical STEP documents."""
    first = reference_cad_model()
    second = reference_cad_model()
    assert first.step_data == second.step_data
    assert first.step_sha256 == second.step_sha256
    assert len(first.step_sha256) == 64
    assert first.digest_sha256() == second.digest_sha256()


def test_step_round_trip_reproduces_the_volumes(tmp_path: Path) -> None:
    """Re-importing the written STEP gives the bodies' volumes within 1e-9.

    The re-import runs in a subprocess, which is how a consumer reads the
    file: a separate reader process.
    """
    import subprocess
    import sys

    model = reference_cad_model()
    target = tmp_path / "device.step"
    written = write_step(target, model)
    assert written == len(model.step_data)
    assert target.read_bytes() == model.step_data
    assert hashlib.sha256(target.read_bytes()).hexdigest() == model.step_sha256
    script = (
        "import json, sys;"
        "import cadquery;"
        "solids = cadquery.importers.importStep(sys.argv[1]).solids().vals();"
        "print(json.dumps(sorted(float(s.Volume()) for s in solids)))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(target)],
        capture_output=True,
        text=True,
        check=True,
    )
    got = json.loads(completed.stdout)
    assert len(got) == len(model.bodies)
    expected = sorted(body.analytic_volume_m3 for body in model.bodies)
    for value, reference in zip(got, expected, strict=True):
        assert math.isclose(value, reference, rel_tol=MEASURE_TOLERANCE)


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_cad(
        configuration, geometry, REFERENCE_PINCH_RADIUS_M, REFERENCE_PINCH_LENGTH_M
    )
    record = model.to_record()
    assert record["schema"] == CAD_MODEL_SCHEMA
    assert record["schema_version"] == CAD_MODEL_SCHEMA_VERSION
    assert record["non_claims"] == list(CAD_MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["pinch_radius_m"] == REFERENCE_PINCH_RADIUS_M
    assert record["pinch_length_m"] == REFERENCE_PINCH_LENGTH_M
    assert record["rod_count"] == geometry.cathode_rod_count
    assert record["reference_mesh_segments"] == DEFAULT_REFERENCE_MESH_SEGMENTS
    assert record["linear_deflection_m"] == DEFAULT_LINEAR_DEFLECTION_M
    assert record["angular_deflection_rad"] == DEFAULT_ANGULAR_DEFLECTION_RAD
    assert record["backend_versions"]["cadquery"] != "unavailable"
    assert record["backend_versions"]["ocp"] != "unavailable"
    assert record["assembly_manifest"]["schema"] == MANIFEST_SCHEMA
    assert record["assembly_manifest"]["body_count"] == len(model.bodies)
    assert [body["name"] for body in record["bodies"]] == list(
        body_names(geometry.cathode_rod_count)
    )
    data = model.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_CAD_MODEL_SHA256


def test_invalid_segments_are_refused() -> None:
    """The reference mesh segment rule is enforced by the build."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            20,
        )


def test_column_violations_are_refused() -> None:
    """The pinch containment invariant holds for the CAD build."""
    with pytest.raises(DeviceGeometryError, match="pinch_radius_m"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            0.06,
            REFERENCE_PINCH_LENGTH_M,
        )


def test_intersecting_rods_are_refused() -> None:
    """A rod set whose members would overlap is refused before any solid."""
    geometry = dataclasses.replace(reference_geometry(), cathode_rod_count=64)
    with pytest.raises(DeviceGeometryError, match="cathode_rod_count"):
        build_device_cad(
            reference_configuration(),
            geometry,
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
        )


def test_invalid_deflections_are_refused() -> None:
    """Non-positive deflections are refused by the build."""
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
            linear_deflection_m=0.0,
        )


def test_body_evidence_refuses_out_of_bound_values() -> None:
    """The library's evidence record fails closed when a bound is violated.

    The per-body check belongs to the shared library (its ADR 0009), so a
    violated bound surfaces as the library's error type; a build re-raises
    it under the device error type, which the build refusal tests cover.
    """
    model = reference_cad_model()
    body = model.bodies[0]
    with pytest.raises(CadError, match="volume_relative_error"):
        dataclasses.replace(body, volume_relative_error=1.0)
    with pytest.raises(CadError, match="surface_area_relative_error"):
        dataclasses.replace(body, surface_area_relative_error=1.0)
    with pytest.raises(CadError, match="faceted_volume_relative_deficit"):
        dataclasses.replace(body, faceted_volume_relative_deficit=1.0)
    with pytest.raises(CadError, match="mesh_volume_relative_difference"):
        dataclasses.replace(body, mesh_volume_relative_difference=1.0)


def test_model_refuses_a_foreign_body_inventory() -> None:
    """A record with the wrong body order is refused."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        dataclasses.replace(model, bodies=model.bodies[::-1])


def test_model_refuses_invalid_declared_parameters() -> None:
    """The record refuses invalid segments, deflections and digests."""
    model = reference_cad_model()
    with pytest.raises(DeviceGeometryError, match="multiple"):
        dataclasses.replace(model, reference_mesh_segments=20)
    with pytest.raises(DeviceGeometryError, match="linear_deflection_m"):
        dataclasses.replace(model, linear_deflection_m=math.nan)
    with pytest.raises(DeviceGeometryError, match="angular_deflection_rad"):
        dataclasses.replace(model, angular_deflection_rad=-1.0)
    with pytest.raises(DeviceGeometryError, match="step_sha256"):
        dataclasses.replace(model, step_sha256="not-a-digest")
    with pytest.raises(DeviceGeometryError, match="assembly_manifest"):
        dataclasses.replace(model, assembly_manifest={"schema": "foreign"})
    manifest = dict(model.assembly_manifest)
    manifest["body_count"] = 1
    with pytest.raises(DeviceGeometryError, match="body_count"):
        dataclasses.replace(model, assembly_manifest=manifest)


def test_evidence_projection_is_json_serialisable() -> None:
    """The per-body evidence projects to JSON with every declared bound."""
    model = reference_cad_model()
    record = model.bodies[0].to_record()
    assert record["name"] == "anode"
    assert record["volume_relative_error"] <= MEASURE_TOLERANCE
    assert (
        record["faceted_volume_relative_deficit"]
        <= record["faceted_volume_deficit_bound"]
    )
    json.dumps(record, allow_nan=False)
