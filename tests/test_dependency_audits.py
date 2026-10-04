# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — dependency audit policy CLI tests
"""Exercise actual audit policy through real Git/workflow trees and its CLI."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from check_dependency_audits import main

REPO = Path(__file__).resolve().parents[1]


def repository(tmp_path: Path) -> Path:
    """Create a real Git fixture from the current maintained policy surface.

    Parameters
    ----------
    tmp_path
        Owned test allocation.

    Returns
    -------
    Path
        Root containing exact copied workflows and staged dependency locks.
    """
    root = tmp_path / "repository"
    root.mkdir()
    shutil.copytree(REPO / ".github", root / ".github")
    (root / "rust").mkdir()
    for name in ("requirements-dev.txt", "rust/Cargo.lock"):
        shutil.copyfile(REPO / name, root / name)
    subprocess.run(
        ["/usr/bin/git", "init", "-q", "--initial-branch=main"], cwd=root, check=True
    )
    subprocess.run(
        [
            "/usr/bin/git",
            "add",
            "--",
            ".github",
            "requirements-dev.txt",
            "rust/Cargo.lock",
        ],
        cwd=root,
        check=True,
    )
    return root


@pytest.mark.parametrize("explicit", [True, False])
def test_actual_policy_is_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *,
    explicit: bool,
) -> None:
    """The real whole workflow chain passes through both CLI entry forms."""
    root = repository(tmp_path)
    monkeypatch.chdir(root)
    assert main([str(root)] if explicit else []) == 0
    assert "PASS complete blocking lock audits" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("file", "before", "after"),
    [
        ("ci.yml", "  push:", "  push:\n    paths: [rust/**]"),
        ("ci.yml", "  push:", "  workflow_call:"),
        ("ci.yml", "  security-audit:\n", "  security-audit:\n    if: false\n"),
        ("ci.yml", "static-policy, tests, security-audit", "static-policy, tests"),
        ("ci.yml", "if: always()", "if: success()"),
        ("ci.yml", "exit 1", "exit 0"),
        ("ci.yml", "needs: [static-policy, tests, security-audit]", "needs: [null]"),
        (
            "ci.yml",
            "permissions: {}\n",
            "permissions: {}\ndefaults:\n  run:\n    shell: sh\n",
        ),
        (
            "reusable-security-audit.yml",
            "  audit:\n",
            "  audit:\n    continue-on-error: true\n",
        ),
        ("reusable-security-audit.yml", "jobs:\n", "env:\n  AUDIT: advisory\njobs:\n"),
        (
            "reusable-security-audit.yml",
            "pip-audit --strict -r requirements-dev.txt",
            "pip-audit --strict -r requirements-dev.txt || true",
        ),
        (
            "reusable-security-audit.yml",
            "pip-audit --strict -r requirements-dev.txt",
            "pip-audit -r requirements-dev.txt",
        ),
        (
            "reusable-security-audit.yml",
            "cargo +1.98.0 audit --file rust/Cargo.lock",
            "cargo +1.98.0 audit --file rust/Cargo.lock --ignore RUSTSEC-2020-0071",
        ),
        ("reusable-security-audit.yml", "--version 0.22.2", "--version 0.22.1"),
        (
            "reusable-security-audit.yml",
            "      - name: Rust dependency vulnerability audit\n",
            (
                "      - name: Rust dependency vulnerability audit\n"
                "        continue-on-error: true\n"
            ),
        ),
        (
            "reusable-security-audit.yml",
            "      - name: Rust dependency vulnerability audit\n",
            "      - name: Absent Rust audit\n",
        ),
    ],
)
def test_weakened_real_workflow_is_refused(
    tmp_path: Path, file: str, before: str, after: str
) -> None:
    """Missing audits, trigger filters, suppressions and bypasses fail the CLI."""
    root = repository(tmp_path)
    path = root / ".github/workflows" / file
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after, 1))
    assert main([str(root)]) == 1


@pytest.mark.parametrize("name", ["package-lock.json", "rust/.cargo/audit.toml"])
def test_unenrolled_lock_or_rust_configuration_is_refused(
    tmp_path: Path, name: str
) -> None:
    """A newly tracked ecosystem or suppression file cannot silently escape."""
    root = repository(tmp_path)
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}\n")
    subprocess.run(["/usr/bin/git", "add", "--all"], cwd=root, check=True)
    assert main([str(root)]) == 1


def test_missing_workflow_is_refused(tmp_path: Path) -> None:
    """An unreadable required audit definition is a refusal rather than a pass."""
    root = repository(tmp_path)
    (root / ".github/workflows/reusable-security-audit.yml").unlink()
    assert main([str(root)]) == 1


def test_missing_git_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An environment with no Git cannot report a complete tracked-lock audit."""
    root = repository(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "absent-bin"))
    assert main([str(root)]) == 1


@pytest.mark.parametrize("content", ["jobs: [", "jobs: null", "on: push"])
def test_malformed_or_missing_trigger_mapping_is_refused(
    tmp_path: Path, content: str
) -> None:
    """Malformed YAML or scalar/missing trigger policy refuses the public CLI."""
    root = repository(tmp_path)
    (root / ".github/workflows/ci.yml").write_text(content)
    assert main([str(root)]) == 1


@pytest.mark.parametrize(
    "checker", ["audit_workflows.py", "check_dependency_audits.py"]
)
@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("  gate:\n", "  gate:\n    continue-on-error: true\n"),
        ("  gate:\n", "  gate:\n    env:\n      RESULTS: success\n"),
        (
            "    timeout-minutes: 5\n",
            "    timeout-minutes: 5\n    defaults:\n      run:\n        shell: sh\n",
        ),
        (
            "      - name: Fail closed on any category result\n",
            "      - name: Fail closed on any category result\n        if: false\n",
        ),
        (
            "      - name: Fail closed on any category result\n",
            (
                "      - name: Fail closed on any category result\n"
                "        continue-on-error: true\n"
            ),
        ),
        (
            "RESULTS: ${{ join(needs.*.result, ' ') }}",
            "RESULTS: 'success success success'",
        ),
        ("RESULTS: ${{", "OMITTED_RESULTS: ${{"),
        ("        run: |\n", "        run: |\n          RESULTS=success\n"),
        (
            "        run: |\n",
            "        run: |\n          RESULTS='success success success'\n",
        ),
        ("        run: |\n", "        run: |\n          exit 0\n"),
        (
            "    steps:\n",
            "    steps:\n      - run: echo 'unreviewed extra gate step'\n",
        ),
        (
            "static-policy, tests, security-audit]",
            "static-policy, tests, security-audit, tests]",
        ),
        ("needs: [static-policy, tests, security-audit]", "needs: null"),
        ("needs: [static-policy, tests, security-audit]", "needs: [null]"),
        ("shell: bash", "shell: sh"),
        (
            "permissions: {}\n",
            "permissions: {}\ndefaults:\n  run:\n    shell: sh\n",
        ),
    ],
)
def test_public_guard_clis_refuse_gate_overrides(
    tmp_path: Path, checker: str, before: str, after: str
) -> None:
    """Both real CLIs reject complete gate semantics that can hide failures."""
    root = repository(tmp_path)
    path = root / ".github/workflows/ci.yml"
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after, 1))
    # Only the maintained guard names and this interpreter form the argv; no shell.
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-B", str(REPO / "tools" / checker), str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert "FAIL" in completed.stdout


@pytest.mark.parametrize(
    "checker", ["audit_workflows.py", "check_dependency_audits.py"]
)
def test_public_guard_clis_accept_actual_gate(tmp_path: Path, checker: str) -> None:
    """Both executable guards accept the same maintained full workflow tree."""
    root = repository(tmp_path)
    # The parametrized entry points are the two maintained guard files; no shell.
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-B", str(REPO / "tools" / checker), str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_both_clis_refuse_a_script_that_forces_shell_success(tmp_path: Path) -> None:
    """The actual overwritten-result shell succeeds but both guards refuse it."""
    root = repository(tmp_path)
    path = root / ".github/workflows/ci.yml"
    text = path.read_text()
    path.write_text(
        text.replace(
            "        run: |\n",
            "        run: |\n          RESULTS='success success success'\n",
            1,
        )
    )
    workflow = yaml.safe_load(path.read_text())
    # Execute the task-owned YAML block with fixed Bash flags in the owned fixture.
    shell = subprocess.run(  # noqa: S603
        [
            "/usr/bin/bash",
            "--noprofile",
            "--norc",
            "-e",
            "-o",
            "pipefail",
            "-c",
            workflow["jobs"]["gate"]["steps"][0]["run"],
        ],
        env={"RESULTS": "success failure success"},
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert shell.returncode == 0
    for checker in ("audit_workflows.py", "check_dependency_audits.py"):
        # These are the two maintained guard files, using this interpreter directly.
        checked = subprocess.run(  # noqa: S603
            [sys.executable, "-B", str(REPO / "tools" / checker), str(root)],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert checked.returncode == 1, checked.stdout + checked.stderr


def test_guard_accepts_dependency_order_without_losing_categories(
    tmp_path: Path,
) -> None:
    """An equivalent result ordering keeps all three required categories."""
    root = repository(tmp_path)
    path = root / ".github/workflows/ci.yml"
    path.write_text(
        path.read_text().replace(
            "static-policy, tests, security-audit]",
            "security-audit, tests, static-policy]",
        )
    )
    assert main([str(root)]) == 0


@pytest.mark.parametrize(
    ("results", "expected"),
    [
        ("success success success", 0),
        ("failure success success", 1),
        ("success failure success", 1),
        ("success success failure", 1),
        ("success cancelled success", 1),
        ("success skipped success", 1),
        ("success neutral success", 1),
        ("success unknown success", 1),
        ("success success", 1),
        ("success success success success", 1),
        ("", 1),
        ("   ", 1),
        ("success success success\nfailure", 1),
    ],
)
def test_actual_bash_gate_requires_every_category_success(
    results: str, expected: int
) -> None:
    """Execute the actual maintained run block with GitHub's Bash error flags."""
    workflow = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    script = workflow["jobs"]["gate"]["steps"][0]["run"]
    # The command is the maintained YAML run block, never user-supplied shell text.
    completed = subprocess.run(  # noqa: S603
        [
            "/usr/bin/bash",
            "--noprofile",
            "--norc",
            "-e",
            "-o",
            "pipefail",
            "-c",
            script,
        ],
        env={"RESULTS": results},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == expected, completed.stdout + completed.stderr
