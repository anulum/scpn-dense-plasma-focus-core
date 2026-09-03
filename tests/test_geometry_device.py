# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device geometry model tests

"""Every invariant, derived quantity and codec branch of DeviceGeometry."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from typing import Any

import pytest

from geometry_fixtures import reference_geometry
from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.geometry import (
    GEOMETRY_FIELDS,
    RECORD_FIELDS,
    DeviceGeometry,
    geometry_from_bytes,
    geometry_from_record,
)


def test_derived_outer_radius() -> None:
    """The chamber outer radius is the bore plus the wall."""
    assert reference_geometry().chamber_outer_radius_m == 0.15 + 0.01


@pytest.mark.parametrize("field", GEOMETRY_FIELDS)
@pytest.mark.parametrize("value", [0.0, -1.0, math.nan, math.inf])
def test_every_field_must_be_finite_and_positive(field: str, value: float) -> None:
    """Non-finite and non-positive values fail closed on every field."""
    changes: dict[str, Any] = {field: value}
    with pytest.raises(DeviceGeometryError, match=field):
        dataclasses.replace(reference_geometry(), **changes)


def test_cathode_must_fit_the_chamber_length() -> None:
    """A cathode longer than the chamber bore is refused; flush is allowed."""
    with pytest.raises(DeviceGeometryError, match="cathode_length_m"):
        dataclasses.replace(reference_geometry(), cathode_length_m=0.6)
    flush = dataclasses.replace(reference_geometry(), cathode_length_m=0.5)
    assert flush.cathode_length_m == flush.chamber_length_m


def test_rod_count_must_be_an_integer_of_at_least_three() -> None:
    """Fewer than three rods cannot enclose the anode; booleans are not counts."""
    for count in (2, 1, 0, -4):
        with pytest.raises(DeviceGeometryError, match="cathode_rod_count"):
            dataclasses.replace(reference_geometry(), cathode_rod_count=count)
    record = reference_geometry().to_record()
    for value in (None, "12", True, 12.0):
        record["cathode_rod_count"] = value  # type: ignore[assignment]
        with pytest.raises(DeviceGeometryError, match="must be an integer"):
            geometry_from_record(record)


def test_record_round_trip_and_digest() -> None:
    """The canonical bytes are sorted JSON and the digest identifies them."""
    geometry = reference_geometry()
    record = geometry.to_record()
    assert tuple(record) == RECORD_FIELDS
    assert set(GEOMETRY_FIELDS) < set(RECORD_FIELDS)
    data = geometry.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == record
    assert list(json.loads(data)) == sorted(record)
    assert geometry.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert geometry_from_record(record) == geometry
    assert geometry_from_bytes(data) == geometry


def test_record_must_be_an_object() -> None:
    """Non-object records are refused."""
    with pytest.raises(DeviceGeometryError, match="record: must be an object"):
        geometry_from_record([1, 2, 3])


def test_unknown_fields_are_refused() -> None:
    """The parser refuses fields outside the declared set."""
    record = reference_geometry().to_record()
    record["port_count"] = 4
    with pytest.raises(DeviceGeometryError, match=r"unknown fields \['port_count'\]"):
        geometry_from_record(record)


@pytest.mark.parametrize("value", [None, "0.1", True])
def test_non_numeric_fields_are_refused(value: object) -> None:
    """Missing, string and boolean values are not numbers."""
    record = reference_geometry().to_record()
    record["end_wall_thickness_m"] = value  # type: ignore[assignment]
    with pytest.raises(DeviceGeometryError, match="end_wall_thickness_m: must be"):
        geometry_from_record(record)


def test_invalid_json_and_non_finite_literals_are_refused() -> None:
    """Malformed documents and NaN literals fail closed."""
    with pytest.raises(DeviceGeometryError, match="invalid JSON"):
        geometry_from_bytes(b"{")
    with pytest.raises(DeviceGeometryError, match="invalid JSON"):
        geometry_from_bytes(b"\xff\xfe")
    record = reference_geometry().to_record()
    text = json.dumps(record).replace("0.02", "NaN")
    with pytest.raises(DeviceGeometryError, match="non-finite JSON literal"):
        geometry_from_bytes(text.encode("utf-8"))


def test_geometry_is_frozen() -> None:
    """The dataclass is immutable."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        reference_geometry().end_wall_thickness_m = 1.0  # type: ignore[misc]
    assert isinstance(reference_geometry(), DeviceGeometry)
