# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — shared synthetic fixtures of the geometry tests

"""Synthetic configuration and geometry shared by the geometry tests.

Every value is a test fixture; none describes a real machine. The
level-0 fixtures anchor on parameter columns printed by the source, but
the geometry tier declares synthetic dimensions only, so this module
builds its own configuration instead of reusing an anchor row.
"""

from __future__ import annotations

import struct

from scpn_dense_plasma_focus_core.configuration import (
    DeviceConfiguration,
    RegistryBinding,
)
from scpn_dense_plasma_focus_core.geometry import DeviceGeometry
from scpn_dense_plasma_focus_core.parameters import BankAndFill, ElectrodeSet

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
REFERENCE_PINCH_RADIUS_M = 0.006
REFERENCE_PINCH_LENGTH_M = 0.08


def reference_configuration() -> DeviceConfiguration:
    """Return the synthetic plasma-focus configuration of these tests."""
    return DeviceConfiguration(
        identifier="dense_plasma_focus",
        electrodes=ElectrodeSet(
            anode_radius_m=0.05,
            cathode_radius_m=0.1,
            anode_length_m=0.3,
        ),
        bank=BankAndFill(
            bank_energy_kj=20.0,
            peak_current_ma=0.5,
            fill_pressure_torr=4.0,
            deuterium_fill=True,
        ),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def reference_geometry() -> DeviceGeometry:
    """Return the synthetic plasma-focus geometry of these tests."""
    return DeviceGeometry(
        insulator_sleeve_length_m=0.06,
        insulator_sleeve_wall_thickness_m=0.008,
        cathode_rod_radius_m=0.006,
        cathode_rod_count=12,
        cathode_length_m=0.32,
        chamber_inner_radius_m=0.15,
        chamber_wall_thickness_m=0.01,
        chamber_length_m=0.5,
        back_wall_thickness_m=0.02,
        end_wall_thickness_m=0.02,
    )


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


def stream_bits(values: list[float]) -> bytes:
    """Return the concatenated bit patterns of a float stream."""
    return b"".join(bits(value) for value in values)
