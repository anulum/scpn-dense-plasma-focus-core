# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — parameter model tests

"""Every validation branch of the dense-plasma-focus parameter model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from scpn_dense_plasma_focus_core.errors import DeviceConfigurationError
from scpn_dense_plasma_focus_core.parameters import (
    BankAndFill,
    ElectrodeSet,
    require_finite,
    require_positive,
)


def synthetic_electrodes(**overrides: float) -> ElectrodeSet:
    """Build a valid synthetic electrode set with optional overrides."""
    values: dict[str, float] = {
        "anode_radius_m": 0.015,
        "cathode_radius_m": 0.03,
        "anode_length_m": 0.15,
    }
    values.update(overrides)
    return ElectrodeSet(**values)


def synthetic_bank(**overrides: Any) -> BankAndFill:
    """Build a valid synthetic bank/fill with optional overrides."""
    values: dict[str, Any] = {
        "bank_energy_kj": 3.0,
        "peak_current_ma": 0.3,
        "fill_pressure_torr": 4.0,
        "deuterium_fill": True,
    }
    values.update(overrides)
    return BankAndFill(**values)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


def test_valid_electrodes_construct() -> None:
    """A valid coaxial electrode set constructs unchanged."""
    assert synthetic_electrodes().anode_radius_m == 0.015


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"anode_radius_m": 0.0}, "anode_radius_m"),
        ({"cathode_radius_m": -1.0}, "cathode_radius_m"),
        ({"anode_length_m": 0.0}, "anode_length_m"),
        ({"anode_radius_m": 0.03}, "coaxial-gun geometry"),
        ({"anode_radius_m": 0.05}, "coaxial-gun geometry"),
    ],
)
def test_invalid_electrodes_are_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each electrode violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_electrodes(**overrides)


def test_drive_parameter_formula() -> None:
    """The drive parameter follows ``I / (a sqrt(p))`` exactly."""
    drive = synthetic_bank().drive_parameter(synthetic_electrodes())
    assert drive == pytest.approx(300.0 / (1.5 * math.sqrt(4.0)))


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"bank_energy_kj": 0.0}, "bank_energy_kj"),
        ({"peak_current_ma": -1.0}, "peak_current_ma"),
        ({"fill_pressure_torr": 0.0}, "fill_pressure_torr"),
        ({"fill_pressure_torr": math.inf}, "fill_pressure_torr"),
    ],
)
def test_invalid_bank_is_rejected(overrides: dict[str, Any], fragment: str) -> None:
    """Each bank/fill violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_bank(**overrides)
