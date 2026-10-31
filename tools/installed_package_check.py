# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — installed-wheel contract check

"""Exercise the installed package from outside the source checkout.

The installed-wheel workflow builds the wheel, installs it into a clean
environment and runs this script with ``python -I`` from a directory
outside the checkout. The script fails closed unless the package was
imported from the environment rather than the checkout, ships its
``py.typed`` marker, reports matching installed metadata with the pinned
kernel dependency, and serves the public path from canonical configuration
and geometry documents through level-0 physics to the tessellated device
model. In ``base`` mode the optional CAD back-end must be absent and a CAD
request must raise the documented ``CadUnavailableError``; in ``cad`` mode
one B-rep model must be built and exported.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from pathlib import Path
from typing import Final

DISTRIBUTION: Final = "scpn-dense-plasma-focus-core"
PACKAGE: Final = "scpn_dense_plasma_focus_core"
KERNEL_REQUIREMENT: Final = "scpn-reactor-kernels"
MODES: Final = ("base", "cad")

CONFIGURATION_DOCUMENT: Final = (
    b'{"bank":{"bank_energy_kj":20.0,"deuterium_fill":true,"fill_pressure_torr":4.0,'
    b'"peak_current_ma":0.5},"electrodes":{"anode_length_m":0.3,"anode_radius_m":0.05,'
    b'"cathode_radius_m":0.1},"identifier":"dense_plasma_focus","registry":'
    b'{"digest_sha256":'
    b'"786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090",'
    b'"version":"1.0.0"}}\n'
)
"""A synthetic canonical configuration for the device models; no real machine."""

GEOMETRY_DOCUMENT: Final = (
    b'{"back_wall_thickness_m":0.02,"cathode_length_m":0.32,"cathode_rod_count":12,'
    b'"cathode_rod_radius_m":0.006,"chamber_inner_radius_m":0.15,'
    b'"chamber_length_m":0.5,"chamber_wall_thickness_m":0.01,'
    b'"end_wall_thickness_m":0.02,"insulator_sleeve_length_m":0.06,'
    b'"insulator_sleeve_wall_thickness_m":0.008}\n'
)
"""A synthetic canonical device geometry in metres."""

PINCH_RADIUS_M: Final = 0.006
"""Declared pinch-column radius of the synthetic model, in metres."""

PINCH_LENGTH_M: Final = 0.08
"""Declared pinch-column length of the synthetic model, in metres."""

PHYSICS_CONFIGURATION_DOCUMENT: Final = (
    b'{"bank":{"bank_energy_kj":486.0,"deuterium_fill":true,"fill_pressure_torr":3.5,'
    b'"peak_current_ma":1.846},"electrodes":{"anode_length_m":0.6,'
    b'"anode_radius_m":0.116,"cathode_radius_m":0.16},"identifier":'
    b'"dense_plasma_focus","registry":{"digest_sha256":'
    b'"786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090",'
    b'"version":"1.0.0"}}\n'
)
"""The PF1000 row of the source's fitted-machine table, the test suite's anchor.

The level-0 inputs below are the same row's bank and fill values. They are
used only as a regression anchor for determinism of the installed package;
nothing is asserted about the machine.
"""

PHYSICS_INPUTS: Final = {
    "bank_capacitance_f": 0.001332,
    "bank_inductance_h": 3.3e-08,
    "bank_resistance_ohm": 0.0063,
    "charge_voltage_v": 27000.0,
    "fill_molecular_mass_amu": 4.0,
    "fill_temperature_k": 300.0,
    "dissociation_number": 2.0,
    "specific_heat_ratio": 5.0 / 3.0,
    "axial_mass_factor": 0.14,
    "axial_current_factor": 0.7,
    "radial_mass_factor": 0.35,
    "radial_current_factor": 0.7,
    "plasma_effective_charge": 1.0,
    "atomic_number": 1.0,
}
"""Level-0 model inputs of the anchor row."""

PINCH_STATE: Final = {
    "pinch_current_a": 862000.0,
    "pinch_radius_m": 0.0223,
    "pinch_length_m": 0.188,
    "pinch_duration_s": 2.55e-07,
    "diode_voltage_v": 126000.0,
    "beam_energy_fraction": 0.14,
    "beam_ion_mass_number": 2.0,
    "beam_effective_charge": 1.0,
    "dd_neutron_cross_section_m2": 1.5e-30,
}
"""Declared pinch state of the anchor row."""


def layout_findings(package_dir: Path, checkout: Path) -> list[str]:
    """Check where the package was imported from and what it ships.

    Parameters
    ----------
    package_dir
        Directory of the imported package.
    checkout
        Source checkout the installed package must not come from.

    Returns
    -------
    list[str]
        Findings; empty when the package lies outside the checkout and
        carries its ``py.typed`` marker.
    """
    return failed(
        [
            (
                not package_dir.resolve().is_relative_to(checkout.resolve()),
                f"{PACKAGE} imported from the checkout: {package_dir}",
            ),
            (
                (package_dir / "py.typed").is_file(),
                f"{PACKAGE} ships no py.typed marker",
            ),
        ]
    )


def failed(checks: list[tuple[bool, str]]) -> list[str]:
    """Return the messages of the checks that did not hold.

    Parameters
    ----------
    checks
        Pairs of an outcome and the finding reported when it is false.

    Returns
    -------
    list[str]
        Findings in check order.
    """
    return [message for holds, message in checks if not holds]


def metadata_findings(
    version: str,
    distribution_name: str = DISTRIBUTION,
    required: str = KERNEL_REQUIREMENT,
) -> list[str]:
    """Check the installed distribution metadata.

    Parameters
    ----------
    version
        ``__version__`` of the imported package.
    distribution_name
        Installed distribution to read.
    required
        Requirement the distribution must declare.

    Returns
    -------
    list[str]
        Findings; empty when the distribution is installed with the same
        version and declares the required dependency.
    """
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return [f"{distribution_name} is not installed"]
    requirements = distribution.requires or []
    return failed(
        [
            (
                distribution.version == version,
                f"installed version {distribution.version} != package {version}",
            ),
            (
                any(item.startswith(required) for item in requirements),
                f"{distribution_name} does not require {required}",
            ),
        ]
    )


def public_path_findings(mode: str) -> list[str]:
    """Serve the public path through the installed package.

    Parameters
    ----------
    mode
        ``base`` when the CAD back-end must be absent, ``cad`` when it must
        build a model.

    Returns
    -------
    list[str]
        Findings; empty when every promised capability of the mode works
        and the absent one fails as documented.
    """
    from scpn_reactor_kernels.errors import CadUnavailableError

    from scpn_dense_plasma_focus_core import configuration_from_bytes
    from scpn_dense_plasma_focus_core.geometry import (
        DEFAULT_REFERENCE_MESH_SEGMENTS,
        build_device_cad,
        build_device_model,
        geometry_from_bytes,
    )
    from scpn_dense_plasma_focus_core.physics import (
        ModelInputs,
        PinchState,
        level0_physics,
    )

    configuration = configuration_from_bytes(CONFIGURATION_DOCUMENT)
    physics_configuration = configuration_from_bytes(PHYSICS_CONFIGURATION_DOCUMENT)
    geometry = geometry_from_bytes(GEOMETRY_DOCUMENT)
    inputs = ModelInputs(**PHYSICS_INPUTS)
    pinch = PinchState(**PINCH_STATE)
    segments = DEFAULT_REFERENCE_MESH_SEGMENTS
    record = level0_physics(physics_configuration, inputs, pinch).canonical_bytes()
    model = build_device_model(
        configuration, geometry, PINCH_RADIUS_M, PINCH_LENGTH_M, segments
    ).digest_sha256()
    findings = failed(
        [
            (
                configuration.canonical_bytes() == CONFIGURATION_DOCUMENT,
                "configuration did not round-trip byte for byte",
            ),
            (
                geometry.canonical_bytes() == GEOMETRY_DOCUMENT,
                "geometry did not round-trip byte for byte",
            ),
            (
                physics_configuration.canonical_bytes()
                == PHYSICS_CONFIGURATION_DOCUMENT,
                "physics configuration did not round-trip byte for byte",
            ),
            (
                record
                == level0_physics(
                    physics_configuration, inputs, pinch
                ).canonical_bytes(),
                "level-0 record is not deterministic",
            ),
            (
                model
                == build_device_model(
                    configuration, geometry, PINCH_RADIUS_M, PINCH_LENGTH_M, segments
                ).digest_sha256(),
                "tessellated model is not deterministic",
            ),
        ]
    )
    if mode == "base":
        try:
            build_device_cad(configuration, geometry, PINCH_RADIUS_M, PINCH_LENGTH_M)
        except CadUnavailableError:
            return findings
        return [*findings, "CAD back-end present in the base environment"]
    cad = build_device_cad(configuration, geometry, PINCH_RADIUS_M, PINCH_LENGTH_M)
    return findings + failed(
        [
            (bool(cad.step_data), "CAD model exported no STEP data"),
            (
                cad.configuration_digest_sha256 == configuration.digest_sha256(),
                "CAD model is bound to another configuration",
            ),
        ]
    )


def check_installed(mode: str, checkout: Path) -> list[str]:
    """Run every installed-package check for one environment.

    Parameters
    ----------
    mode
        One of :data:`MODES`.
    checkout
        Source checkout the package must not be imported from.

    Returns
    -------
    list[str]
        All findings; empty when the installed package meets its contract.
    """
    package = importlib.import_module(PACKAGE)
    package_dir = Path(package.__file__ or "").parent
    findings = layout_findings(package_dir, checkout)
    findings += metadata_findings(str(package.__version__))
    findings += public_path_findings(mode)
    return findings


def report(mode: str, findings: list[str]) -> int:
    """Print the outcome of one environment and return its exit status.

    Parameters
    ----------
    mode
        Environment mode that was checked.
    findings
        Findings of :func:`check_installed`.

    Returns
    -------
    int
        ``0`` without findings, else ``1``.
    """
    if findings:
        print(f"installed-package: FAIL {mode}", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print(f"installed-package: PASS {mode}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the installed-package check from the command line.

    Parameters
    ----------
    argv
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` when the installed package meets its contract, else ``1``.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args(argv)
    return report(args.mode, check_installed(args.mode, args.checkout))


if __name__ == "__main__":
    sys.exit(main())
