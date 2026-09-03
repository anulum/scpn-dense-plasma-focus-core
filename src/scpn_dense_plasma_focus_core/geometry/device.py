# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device geometry model

"""Validated device geometry of a Mather-type plasma-focus assembly.

The geometry complements the
:class:`~scpn_dense_plasma_focus_core.configuration.DeviceConfiguration`
(which carries the coaxial electrode pair and the bank and fill) with the
device-owned mechanical envelope: the insulator sleeve over the anode
base, the cathode wall and length, the vacuum chamber with its wall and
length, and the two closing walls. The layout is the qualitative
Mather-type arrangement of the plasma-focus literature on file — a
central anode bar, a cathode coaxial with it attached to the back-wall
plate, an insulator sleeve over the anode base whose length is a printed
device parameter, and the plasma chamber around them (IAEA-TECDOC-1829,
IAEA Vienna 2017) — with the electrode pair idealised as the coaxial
line of the model this repository implements (S. Lee, J. Fusion Energ. 33
(2014) 319). No dimension of any device is used, and every parameter set
is synthetic.

The anode radius, the cathode radius and the anode length are not
repeated here: they are the validated configuration's ``ElectrodeSet``,
checked against this geometry when the model is built. Validation is
fail-closed, serialisation is canonical, and the SHA-256 digest
identifies the exact geometry.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_dense_plasma_focus_core.errors import DeviceGeometryError
from scpn_dense_plasma_focus_core.parameters import require_positive

GEOMETRY_FIELDS: Final = (
    "insulator_sleeve_length_m",
    "insulator_sleeve_wall_thickness_m",
    "cathode_wall_thickness_m",
    "cathode_length_m",
    "chamber_inner_radius_m",
    "chamber_wall_thickness_m",
    "chamber_length_m",
    "back_wall_thickness_m",
    "end_wall_thickness_m",
)


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule with the geometry error type.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceGeometryError
        If the value is non-finite or not strictly positive.
    """
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceGeometry:
    """Validated plasma-focus geometry (SI units in the field names).

    Parameters
    ----------
    insulator_sleeve_length_m
        Axial length of the insulator sleeve over the anode base;
        strictly positive.
    insulator_sleeve_wall_thickness_m
        Radial wall thickness of the insulator sleeve; strictly positive.
    cathode_wall_thickness_m
        Radial wall thickness of the cathode drawn as the equivalent
        coaxial conductor; strictly positive.
    cathode_length_m
        Axial length of the cathode; strictly positive and at most the
        chamber length.
    chamber_inner_radius_m
        Bore radius of the vacuum chamber; strictly positive.
    chamber_wall_thickness_m
        Radial wall thickness of the chamber; strictly positive.
    chamber_length_m
        Axial length of the chamber bore; strictly positive.
    back_wall_thickness_m
        Axial thickness of the back wall closing the breech; strictly
        positive.
    end_wall_thickness_m
        Axial thickness of the downstream end wall; strictly positive.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive, or if the
        cathode is longer than the chamber.
    """

    insulator_sleeve_length_m: float
    insulator_sleeve_wall_thickness_m: float
    cathode_wall_thickness_m: float
    cathode_length_m: float
    chamber_inner_radius_m: float
    chamber_wall_thickness_m: float
    chamber_length_m: float
    back_wall_thickness_m: float
    end_wall_thickness_m: float

    def __post_init__(self) -> None:
        """Validate every value and the axial containment invariant.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        for name in GEOMETRY_FIELDS:
            _positive(name, getattr(self, name))
        if self.cathode_length_m > self.chamber_length_m:
            raise DeviceGeometryError(
                "cathode_length_m: must not exceed chamber_length_m, got "
                f"{self.cathode_length_m!r} > {self.chamber_length_m!r}"
            )

    @property
    def chamber_outer_radius_m(self) -> float:
        """Outer radius of the chamber (bore plus wall)."""
        return self.chamber_inner_radius_m + self.chamber_wall_thickness_m

    def to_record(self) -> dict[str, float]:
        """Project the geometry to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in GEOMETRY_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the geometry canonically.

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
        """Identify the exact geometry.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Decoded JSON object.
    field
        Field name to read.

    Returns
    -------
    float
        The field value as a float.

    Raises
    ------
    DeviceGeometryError
        If the field is missing or not a real number (booleans rejected).
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceGeometryError(f"{field}: must be a number, got {value!r}")
    return float(value)


def geometry_from_record(record: Any) -> DeviceGeometry:
    """Build a validated geometry from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceGeometry.to_record`.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the record shape or any value violates the model; unknown
        fields are refused.
    """
    if not isinstance(record, dict):
        raise DeviceGeometryError("record: must be an object")
    unknown = sorted(set(record) - set(GEOMETRY_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"record: unknown fields {unknown!r}")
    return DeviceGeometry(**{name: _number(record, name) for name in GEOMETRY_FIELDS})


def geometry_from_bytes(data: bytes) -> DeviceGeometry:
    """Build a validated geometry from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceGeometryError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceGeometryError(f"record: invalid JSON document: {exc}") from exc
    return geometry_from_record(record)
