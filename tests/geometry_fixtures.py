# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — shared synthetic fixtures of the geometry tests

"""Configurations and geometries shared by the geometry tests.

Two fixtures, and the difference between them is the point.

The *reference* pair is synthetic: round numbers chosen to exercise the
model, describing no machine.

The *anchor* pair carries the electrode dimensions printed in
IAEA-TECDOC-1829 (IAEA Vienna, 2017), section 3.1.2 "Optimization
configurations used on NX3 device", p. 231, for the electrode assembly
the source names A20Z160: an anode of length 160 mm and radius 20 mm, and
a squirrel-cage cathode of twelve brass rods of 12 mm diameter uniformly
spaced on a coaxial circle of radius 51 mm; the insulator-sleeve length
of 30 mm is the value printed for the same device in Table 1, p. 228. It
exists so the geometry tier can be checked against a published
arrangement the way the level-0 models are checked against published
numbers. The fields the source does not print — the chamber bore, wall
and length, the cathode length, the sleeve wall thickness and the two
closing walls — are declared here and marked as declared; reproducing a
printed dimension is an anchor, never a claim about the machine.
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


#: Values printed in IAEA-TECDOC-1829 for the NX3 assembly A20Z160.
ANCHOR_ANODE_RADIUS_M = 0.020
ANCHOR_ANODE_LENGTH_M = 0.160
ANCHOR_CATHODE_RADIUS_M = 0.051
ANCHOR_ROD_RADIUS_M = 0.006
ANCHOR_ROD_COUNT = 12
ANCHOR_SLEEVE_LENGTH_M = 0.030
#: Bank energy printed for the same device; the remaining bank fields are
#: declared and do not enter the geometry.
ANCHOR_BANK_ENERGY_KJ = 20.0


def anchor_configuration() -> DeviceConfiguration:
    """Return the configuration of the printed NX3 electrode assembly A20Z160."""
    return DeviceConfiguration(
        identifier="dense_plasma_focus",
        electrodes=ElectrodeSet(
            anode_radius_m=ANCHOR_ANODE_RADIUS_M,
            cathode_radius_m=ANCHOR_CATHODE_RADIUS_M,
            anode_length_m=ANCHOR_ANODE_LENGTH_M,
        ),
        bank=BankAndFill(
            bank_energy_kj=ANCHOR_BANK_ENERGY_KJ,
            peak_current_ma=0.4,
            fill_pressure_torr=4.0,
            deuterium_fill=True,
        ),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def anchor_geometry() -> DeviceGeometry:
    """Return the geometry of the printed NX3 electrode assembly A20Z160.

    The rod radius, the rod count and the insulator-sleeve length are the
    printed values; the remaining fields are declared because the source
    does not print them.
    """
    return DeviceGeometry(
        insulator_sleeve_length_m=ANCHOR_SLEEVE_LENGTH_M,
        insulator_sleeve_wall_thickness_m=0.004,
        cathode_rod_radius_m=ANCHOR_ROD_RADIUS_M,
        cathode_rod_count=ANCHOR_ROD_COUNT,
        cathode_length_m=0.170,
        chamber_inner_radius_m=0.100,
        chamber_wall_thickness_m=0.006,
        chamber_length_m=0.300,
        back_wall_thickness_m=0.015,
        end_wall_thickness_m=0.015,
    )


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


def stream_bits(values: list[float]) -> bytes:
    """Return the concatenated bit patterns of a float stream."""
    return b"".join(bits(value) for value in values)
