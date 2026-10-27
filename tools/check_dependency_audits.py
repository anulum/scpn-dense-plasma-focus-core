# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — blocking dependency audit policy
"""Pin complete lock audits to unconditional required CI execution."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

import yaml
from audit_workflows import required_gate_errors

LOCK_PATH: Final = re.compile(
    r"(?:^|/)(?:[^/]+\.lock|[^/]*lock[^/]*\.(?:json|yaml|toml)|requirements[^/]*\.txt)$"
)
# The kernel-library lock pins first-party source by archive digest; it is not
# a PyPI distribution, so the PyPI audit below covers every third-party lock.
LOCKS: Final = frozenset(
    {
        "requirements-dev.txt",
        "requirements-cad.txt",
        "requirements-audit.txt",
        "requirements-kernels.txt",
        "rust/Cargo.lock",
    }
)
AUDITS: Final = {
    "Dependency vulnerability audit": (
        "pip-audit --strict --disable-pip -r requirements-dev.txt "
        "-r requirements-cad.txt -r requirements-audit.txt"
    ),
    "Rust dependency vulnerability audit": "cargo +1.98.0 audit --file rust/Cargo.lock",
    "Install pinned Rust audit tooling": (
        "rustup toolchain install 1.98.0 --profile minimal\n"
        "cargo +1.98.0 install cargo-audit --version 0.22.2 --locked"
    ),
}


def _workflow_errors(ci: dict[Any, Any], security: dict[str, Any]) -> list[str]:
    """Check event, required-gate and command semantics of parsed workflows.

    Parameters
    ----------
    ci, security
        YAML mappings from the maintained coordinator and audit category.

    Returns
    -------
    list[str]
        Violations of blocking, unfiltered dependency-audit execution.
    """
    errors: list[str] = []
    triggers = ci.get(True, ci.get("on"))
    if not isinstance(triggers, dict):
        return ["push and pull-request audit trigger mapping is required"]
    if any(triggers.get(event) is not None for event in ("push", "pull_request")):
        errors.append("main push and pull-request audits must not have trigger filters")
    if not {"push", "pull_request"}.issubset(triggers):
        errors.append("push and pull-request audit triggers are required")
    call = ci["jobs"]["security-audit"]
    if call["uses"] != "./.github/workflows/reusable-security-audit.yml" or {
        "if",
        "continue-on-error",
    }.intersection(call):
        errors.append(
            "security audit must be an unconditional required gate dependency"
        )
    errors.extend(
        required_gate_errors(ci["jobs"].get("gate"), set(ci["jobs"]) - {"gate"})
    )
    if {"env", "defaults"}.intersection(ci):
        errors.append("coordinator execution must not be overridden")
    job = security["jobs"]["audit"]
    if {"if", "continue-on-error", "env", "defaults"}.intersection(job) or {
        "env",
        "defaults",
    }.intersection(security):
        errors.append("audit execution must not be conditional or overridden")
    for name, command in AUDITS.items():
        steps = [step for step in job["steps"] if step.get("name") == name]
        if len(steps) != 1 or set(steps[0]) != {"name", "run"}:
            errors.append(f"{name}: exactly one unconditional audit step is required")
        elif steps[0]["run"].strip() != command:
            errors.append(f"{name}: pinned blocking audit command changed")
    return errors


def audit(root: Path) -> list[str]:
    """Verify every tracked lock and its unconditional required audit.

    Parameters
    ----------
    root
        Actual repository root holding the workflow and tracked lock files.

    Returns
    -------
    list[str]
        Policy violations. Empty means policy compliance, not a clean audit.
    """
    git = shutil.which("git")
    if git is None:
        return ["Git executable is unavailable for tracked-lock inventory"]
    try:
        # The executable resolves from PATH; Git arguments are fixed and no shell runs.
        tracked = (
            subprocess.check_output(  # noqa: S603
                [git, "ls-files", "-z"], cwd=root, stderr=subprocess.DEVNULL
            )
            .decode()
            .split("\0")
        )
        ci: dict[Any, Any] = yaml.safe_load(
            (root / ".github/workflows/ci.yml").read_text()
        )
        security: dict[str, Any] = yaml.safe_load(
            (root / ".github/workflows/reusable-security-audit.yml").read_text()
        )
        errors = _workflow_errors(ci, security)
    except (
        OSError,
        subprocess.CalledProcessError,
        yaml.YAMLError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        return ["dependency audit policy is unreadable or malformed"]
    if {path for path in tracked if LOCK_PATH.search(path)} != LOCKS:
        errors.append(
            "tracked dependency locks differ from the complete audit inventory"
        )
    if any(path.endswith("/audit.toml") for path in tracked):
        errors.append("Rust audit configuration requires reviewed policy enrollment")
    return errors


def main(argv: list[str]) -> int:
    """Check the current or explicitly supplied repository from the CLI.

    Parameters
    ----------
    argv
        Optional repository-root argument.

    Returns
    -------
    int
        Zero for compliant policy; one for any missing or weakened audit.
    """
    errors = audit(Path(argv[0]) if argv else Path.cwd())
    for error in errors:
        print(f"dependency-audit-policy: FAIL {error}")
    if errors:
        return 1
    print("dependency-audit-policy: PASS complete blocking lock audits required")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
