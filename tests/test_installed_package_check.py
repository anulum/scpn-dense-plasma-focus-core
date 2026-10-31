# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — installed-wheel contract check tests

"""Every finding of the installed-wheel check fires on its fault.

The hosted installed-wheel job runs the check against a real wheel in clean
base and CAD environments. These tests prove, in the development
environment, that each check reports its fault: a package imported from
the checkout, a missing ``py.typed`` marker, absent or mismatched metadata,
a CAD back-end present where it must be absent, and that an absent CAD
back-end surfaces as the documented ``CadUnavailableError``.
"""

from __future__ import annotations

import dataclasses
import importlib.metadata
import sys
from pathlib import Path

import pytest
from installed_package_check import (
    CONFIGURATION_DOCUMENT,
    GEOMETRY_DOCUMENT,
    PHYSICS_CONFIGURATION_DOCUMENT,
    PHYSICS_INPUTS,
    PINCH_LENGTH_M,
    PINCH_RADIUS_M,
    PINCH_STATE,
    check_installed,
    failed,
    layout_findings,
    main,
    metadata_findings,
    public_path_findings,
    report,
)
from scpn_reactor_kernels.errors import CadUnavailableError

from geometry_fixtures import (
    REFERENCE_PINCH_LENGTH_M,
    REFERENCE_PINCH_RADIUS_M,
    reference_configuration,
    reference_geometry,
)
from scpn_dense_plasma_focus_core import configuration_from_bytes
from scpn_dense_plasma_focus_core.geometry import build_device_cad

REPO = Path(__file__).resolve().parents[1]


def test_layout_accepts_an_installed_package_with_its_marker(tmp_path: Path) -> None:
    """A package outside the checkout that ships py.typed passes."""
    package = tmp_path / "site-packages" / "scpn_dense_plasma_focus_core"
    package.mkdir(parents=True)
    (package / "py.typed").write_text("", encoding="utf-8")
    assert layout_findings(package, REPO) == []


def test_layout_rejects_checkout_import_and_omitted_marker(tmp_path: Path) -> None:
    """A checkout import and a wheel without py.typed are both findings."""
    package = tmp_path / "scpn_dense_plasma_focus_core"
    package.mkdir()
    findings = layout_findings(package, tmp_path)
    assert any("imported from the checkout" in item for item in findings)
    assert any("no py.typed" in item for item in findings)


def test_metadata_reports_a_missing_distribution() -> None:
    """An absent distribution is a finding, not an exception."""
    assert metadata_findings("1", "no-such-distribution-for-this-test") == [
        "no-such-distribution-for-this-test is not installed"
    ]


def test_metadata_checks_version_and_requirement() -> None:
    """A real installed distribution passes or fails on exact metadata."""
    version = importlib.metadata.version("scpn-reactor-kernels")
    assert metadata_findings(version, "scpn-reactor-kernels", "cadquery") == []
    findings = metadata_findings("0.0.0", "scpn-reactor-kernels", "absent-package")
    assert any("installed version" in item for item in findings)
    assert any("does not require absent-package" in item for item in findings)


def test_failed_keeps_only_false_checks_in_order() -> None:
    """Only the messages of failed checks are returned."""
    assert failed([(True, "a"), (False, "b"), (False, "c")]) == ["b", "c"]


def test_configuration_document_is_canonical() -> None:
    """The embedded document is the canonical form of a valid configuration."""
    configuration = configuration_from_bytes(CONFIGURATION_DOCUMENT)
    assert configuration.canonical_bytes() == CONFIGURATION_DOCUMENT


def test_cad_mode_builds_a_model_where_the_back_end_exists() -> None:
    """With the CAD extra installed, the cad mode has no findings."""
    assert public_path_findings("cad") == []


def test_base_mode_reports_a_present_cad_back_end() -> None:
    """The base environment must not carry the CAD extra."""
    assert public_path_findings("base") == [
        "CAD back-end present in the base environment"
    ]


def test_base_mode_passes_when_the_back_end_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without cadquery the CAD request fails as documented and base passes."""
    monkeypatch.setitem(sys.modules, "cadquery", None)
    assert public_path_findings("base") == []


def test_absent_cad_back_end_raises_the_documented_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """build_device_cad lets CadUnavailableError through, as documented."""
    monkeypatch.setitem(sys.modules, "cadquery", None)
    with pytest.raises(CadUnavailableError, match="optional CAD back-end"):
        build_device_cad(
            reference_configuration(),
            reference_geometry(),
            REFERENCE_PINCH_RADIUS_M,
            REFERENCE_PINCH_LENGTH_M,
        )


def test_check_from_the_checkout_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """Run from the source tree, the check refuses the checkout import."""
    findings = check_installed("cad", REPO)
    assert any("imported from the checkout" in item for item in findings)
    assert main(["--mode", "cad", "--checkout", str(REPO)]) == 1
    assert "installed-package: FAIL cad" in capsys.readouterr().err


def test_report_exit_status(capsys: pytest.CaptureFixture[str]) -> None:
    """No findings is a pass; any finding is a failure with its reasons."""
    assert report("base", []) == 0
    assert "installed-package: PASS base" in capsys.readouterr().out
    assert report("base", ["x"]) == 1
    assert "  - x" in capsys.readouterr().err


def test_embedded_documents_are_the_test_suite_fixtures() -> None:
    """The installed check serves exactly the fixtures the suite validates."""
    import physics_fixtures

    assert reference_configuration().canonical_bytes() == CONFIGURATION_DOCUMENT
    assert reference_geometry().canonical_bytes() == GEOMETRY_DOCUMENT
    assert (PINCH_RADIUS_M, PINCH_LENGTH_M) == (
        REFERENCE_PINCH_RADIUS_M,
        REFERENCE_PINCH_LENGTH_M,
    )
    anchor = physics_fixtures.configuration()
    assert anchor.canonical_bytes() == PHYSICS_CONFIGURATION_DOCUMENT
    assert dataclasses.asdict(physics_fixtures.inputs()) == PHYSICS_INPUTS
    assert dataclasses.asdict(physics_fixtures.pinch_state()) == PINCH_STATE
