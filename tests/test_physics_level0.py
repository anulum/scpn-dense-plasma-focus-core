# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — level-0 record tests

"""Composition, identity, consistency checks and refusals of the level-0 record."""

from __future__ import annotations

import hashlib
import json

import pytest

from physics_fixtures import (
    NX3,
    PF1000,
    ROWS,
    AnchorRow,
    configuration,
    inputs,
    pinch_state,
)
from scpn_dense_plasma_focus_core import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    level0_physics,
)
from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.physics import (
    BANK_ENERGY_CONSISTENCY,
    require_fraction,
)

RECORD_KEYS = {
    "schema",
    "schema_version",
    "non_claims",
    "configuration_digest_sha256",
    "inputs",
    "pinch_state",
    "drive_parameter_ka_per_cm_sqrt_torr",
    "bank",
    "fill",
    "axial",
    "radial",
    "geometry",
    "slug",
    "pinch",
    "beam",
    "neutron",
}


def test_record_composes_every_model_and_is_canonical() -> None:
    """The record carries the configuration digest and every model record."""
    config = configuration()
    record = level0_physics(config, inputs(), pinch_state())
    assert isinstance(record, Level0PhysicsRecord)
    projected = record.to_record()
    assert projected["schema"] == LEVEL0_SCHEMA
    assert projected["schema_version"] == LEVEL0_SCHEMA_VERSION
    assert projected["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert projected["configuration_digest_sha256"] == config.digest_sha256()
    assert set(projected) == RECORD_KEYS
    data = record.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == projected
    assert record.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert level0_physics(config, inputs(), pinch_state()).digest_sha256() == (
        record.digest_sha256()
    )


@pytest.mark.parametrize("row", ROWS, ids=[row.name for row in ROWS])
def test_every_anchor_row_builds_a_consistent_record(row: AnchorRow) -> None:
    """Each Table 1 row passes the consistency checks and wires the models."""
    record = level0_physics(configuration(row), inputs(row), pinch_state(row))
    assert record.axial.drive_current_a == row.peak_current_a
    assert record.slug.current_a == row.pinch_current_a
    assert record.slug.piston_radius_m == row.minimum_radius_m
    assert record.geometry.anode_radius_m == row.anode_radius_m
    assert record.radial.alpha1 == record.axial.axial_transit_time_s / (
        record.radial.radial_transit_time_s
    )
    if row.pinch_current_a >= 1.0e5:
        assert record.neutron.scaling_law_yield is not None
        assert record.neutron.scaling_law_yield > 0.0
    else:
        assert record.neutron.scaling_law_yield is None
        assert record.to_record()["neutron"]["scaling_law_applicable"] is False
    assert record.neutron.beam_target_yield > 0.0
    assert record.pinch.ion_density_per_m3 > record.fill.molecule_density_per_m3


@pytest.mark.parametrize("row", [PF1000, NX3], ids=["PF1000", "NX3"])
def test_drive_parameter_reproduces_the_printed_speed_factor(row: AnchorRow) -> None:
    """The configuration's drive parameter matches the table's ``SF`` to 1 %.

    The INTI row is excluded on purpose: its printed ``SF`` (102) does not
    follow from its own printed ``I_peak`` and ``a`` (96), a rounding or
    typographical inconsistency of the source recorded in the evidence.
    """
    record = level0_physics(configuration(row), inputs(row), pinch_state(row))
    assert (
        abs(record.drive_parameter_ka_per_cm_sqrt_torr - row.drive_factor)
        / (row.drive_factor)
        <= 0.01
    )


def test_inputs_record_and_validation() -> None:
    """Every declared input is projected and validated."""
    model = inputs()
    record = model.to_record()
    assert len(record) == 14
    for field in record:
        with pytest.raises(DeviceConfigurationError, match=field):
            inputs(**{field: 0.0})
    for field in (
        "axial_mass_factor",
        "axial_current_factor",
        "radial_mass_factor",
        "radial_current_factor",
    ):
        with pytest.raises(DeviceConfigurationError, match="must not exceed 1"):
            inputs(**{field: 1.2})
    with pytest.raises(DeviceConfigurationError, match="specific_heat_ratio"):
        inputs(specific_heat_ratio=1.0)
    assert isinstance(inputs(axial_mass_factor=1.0), ModelInputs)
    assert require_fraction("f", 0.5) == 0.5


def test_bank_energy_consistency_is_enforced() -> None:
    """``C0 V0^2 / 2`` must agree with the declared bank energy within 2 %."""
    with pytest.raises(DeviceConfigurationError, match="bank_energy_kj"):
        level0_physics(configuration(), inputs(charge_voltage_v=30.0e3), pinch_state())
    tolerant = inputs(charge_voltage_v=27.0e3 * (1.0 + 0.4 * BANK_ENERGY_CONSISTENCY))
    assert (
        level0_physics(configuration(), tolerant, pinch_state()).bank.bank_energy_j
        > 0.0
    )


def test_pinch_state_consistency_is_enforced() -> None:
    """The pinch current cannot exceed the peak current; ``rp < a``."""
    with pytest.raises(DeviceConfigurationError, match="peak current"):
        level0_physics(configuration(), inputs(), pinch_state(pinch_current_a=2.0e6))
    with pytest.raises(DeviceConfigurationError, match="smaller than anode_radius_m"):
        level0_physics(configuration(), inputs(), pinch_state(pinch_radius_m=0.116))
