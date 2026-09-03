# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device configuration container tests

"""Every branch of the device configuration container and its parsers.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import pytest

from scpn_dense_plasma_focus_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import BankAndFill, ElectrodeSet

REGISTRY = RegistryBinding(version="1.0.0", digest_sha256="0" * 64)


def synthetic_configuration(
    identifier: str = "dense_plasma_focus",
    peak_current_ma: float = 0.3,
    *,
    deuterium_fill: bool = True,
) -> DeviceConfiguration:
    """Build a valid synthetic configuration with optional overrides."""
    return DeviceConfiguration(
        identifier=identifier,
        electrodes=ElectrodeSet(
            anode_radius_m=0.015,
            cathode_radius_m=0.03,
            anode_length_m=0.15,
        ),
        bank=BankAndFill(
            bank_energy_kj=3.0,
            peak_current_ma=peak_current_ma,
            fill_pressure_torr=4.0,
            deuterium_fill=deuterium_fill,
        ),
        registry=REGISTRY,
    )


def test_registry_binding_rejects_bad_pins() -> None:
    """Malformed registry pins are rejected."""
    with pytest.raises(DeviceConfigurationError, match=r"registry\.version"):
        RegistryBinding(version="", digest_sha256="0" * 64)
    with pytest.raises(DeviceConfigurationError, match=r"registry\.digest_sha256"):
        RegistryBinding(version="1.0.0", digest_sha256="ZZ")


def test_owned_identifier_constructs_and_derives_drive() -> None:
    """The owned identifier constructs and derives the drive parameter."""
    configuration = synthetic_configuration()
    assert configuration.identifier == "dense_plasma_focus"
    assert configuration.drive_parameter() == pytest.approx(
        300.0 / (1.5 * math.sqrt(4.0))
    )


def test_unowned_identifier_is_rejected() -> None:
    """Identifiers outside this repository's ownership are rejected."""
    with pytest.raises(DeviceConfigurationError, match="not owned"):
        synthetic_configuration("z_pinch")


def test_consistency_report_clean_and_findings() -> None:
    """The report is empty in-window and precise outside it."""
    assert synthetic_configuration().consistency_report() == ()
    weak = synthetic_configuration(peak_current_ma=0.1)
    findings = weak.consistency_report()
    assert len(findings) == 1
    assert "deuterium window" in findings[0].message
    non_deuterium = synthetic_configuration(peak_current_ma=0.1, deuterium_fill=False)
    assert non_deuterium.consistency_report() == ()


def test_canonical_round_trip_and_digest() -> None:
    """Canonical bytes round-trip losslessly and digest deterministically."""
    configuration = synthetic_configuration()
    data = configuration.canonical_bytes()
    assert data.endswith(b"\n")
    restored = configuration_from_bytes(data)
    assert restored == configuration
    expected = hashlib.sha256(data).hexdigest()
    assert configuration.digest_sha256() == expected


def test_from_record_round_trip() -> None:
    """The owned configuration round-trips through records."""
    configuration = synthetic_configuration()
    assert configuration_from_record(configuration.to_record()) == configuration


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda _: "not-a-dict", "record: must be an object"),
        (lambda r: {**r, "extra": 1}, "unknown fields"),
        (lambda r: {**r, "electrodes": None}, "electrodes: must be an object"),
        (lambda r: {**r, "bank": []}, "bank: must be an object"),
        (lambda r: {**r, "registry": 7}, "registry: must be an object"),
        (lambda r: {**r, "identifier": 3}, "identifier: must be a string"),
    ],
)
def test_from_record_shape_violations(mutate: Any, fragment: str) -> None:
    """Each record-shape violation is rejected with a precise message."""
    record = synthetic_configuration().to_record()
    with pytest.raises(DeviceConfigurationError, match=fragment):
        configuration_from_record(mutate(record))


def test_from_record_field_type_violations() -> None:
    """Nested field-type violations name the offending field."""
    record = synthetic_configuration().to_record()
    record["electrodes"]["anode_radius_m"] = "big"
    with pytest.raises(DeviceConfigurationError, match="anode_radius_m: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["bank"]["peak_current_ma"] = True
    with pytest.raises(DeviceConfigurationError, match="peak_current_ma: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["bank"]["deuterium_fill"] = "yes"
    with pytest.raises(DeviceConfigurationError, match="deuterium_fill: must be"):
        configuration_from_record(record)
    record = synthetic_configuration().to_record()
    record["registry"]["version"] = None
    with pytest.raises(DeviceConfigurationError, match="version: must be a string"):
        configuration_from_record(record)


def test_from_bytes_rejects_invalid_documents() -> None:
    """Invalid UTF-8, invalid JSON, and non-finite literals are rejected."""
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"\xff\xfe")
    with pytest.raises(DeviceConfigurationError, match="invalid JSON document"):
        configuration_from_bytes(b"{not json")
    record = synthetic_configuration().to_record()
    text = json.dumps(record).replace("0.015", "NaN", 1)
    with pytest.raises(DeviceConfigurationError, match="non-finite JSON literal"):
        configuration_from_bytes(text.encode("utf-8"))


def test_integer_accepted_where_number_expected() -> None:
    """Integral JSON numbers are accepted for real-valued fields."""
    record = synthetic_configuration().to_record()
    record["bank"]["fill_pressure_torr"] = 4
    restored = configuration_from_record(record)
    assert restored.bank.fill_pressure_torr == 4.0
