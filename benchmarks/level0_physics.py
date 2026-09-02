# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — level-0 physics benchmark

"""Benchmark the level-0 physics kernels: Python floor versus native.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per (operation, backend), unavailable backends marked
explicitly, full provenance in the artefact. The operation is one pass over
a synthetic grid of pinch states (current, radius) evaluating, per point,
the slug relations, the pinch-phase closed forms, the fast-ion-beam chain
and the beam-target yield; each sample times one full grid pass and the
time is reported per grid point. Both backends are called per point (the
native one through its bindings), so the row measures call-through cost,
not a vectorised scan; the grids are built outside the timed region.
Nothing measured here is a physics claim.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scpn_dense_plasma_focus_core.physics import (  # noqa: E402
    beam_target_yield,
    fast_ion_beam,
    pinch_radiation,
    slug_relations,
)

SCHEMA: Final = "scpn-dense-plasma-focus-core.level0-physics-benchmark.v1"
ANODE_RADIUS_M: Final = 0.05
CATHODE_RADIUS_M: Final = 0.10
PINCH_LENGTH_M: Final = 0.075
MOLECULE_DENSITY_PER_M3: Final = 1.0e23
MASS_DENSITY_KG_M3: Final = 7.5e-4
GAMMA: Final = 5.0 / 3.0
DIODE_VOLTAGE_V: Final = 8.0e4
PINCH_DURATION_S: Final = 5.0e-8
CROSS_SECTION_M2: Final = 1.5e-30
Pass = Callable[[], float]


def grid(points: int) -> list[tuple[float, float]]:
    """Build a deterministic synthetic grid of pinch states.

    Parameters
    ----------
    points
        Number of grid points.

    Returns
    -------
    list of (float, float)
        (pinch_current_a, pinch_radius_m) tuples spanning 0.1–1 MA and
        0.1–0.3 of the anode radius.
    """
    return [
        (
            1.0e5 + 9.0e5 * (index % 97) / 96.0,
            ANODE_RADIUS_M * (0.1 + 0.2 * (index % 89) / 88.0),
        )
        for index in range(points)
    ]


def floor_pass_factory(points: int) -> Pass:
    """Return one grid pass on the Python floor over a precomputed grid.

    Parameters
    ----------
    points
        Number of grid points.

    Returns
    -------
    callable
        Pass returning a checksum of the results, so the work cannot be
        optimised away.
    """
    sample_grid = grid(points)

    def floor_pass() -> float:
        total = 0.0
        for current, radius in sample_grid:
            slug = slug_relations(
                current, radius, MASS_DENSITY_KG_M3, 0.7, 0.35, GAMMA, 4.0, 2.0, 1.0
            )
            pinch = pinch_radiation(
                current,
                radius,
                PINCH_LENGTH_M,
                ANODE_RADIUS_M,
                MOLECULE_DENSITY_PER_M3,
                0.7,
                0.35,
                2.0,
                1.0,
                1.0,
            )
            beam = fast_ion_beam(
                current,
                radius,
                CATHODE_RADIUS_M,
                DIODE_VOLTAGE_V,
                PINCH_DURATION_S,
                0.14,
                2.0,
                1.0,
            )
            total += slug.shock_temperature_k + pinch.net_power_w * 1e-9
            total += beam.damage_factor_w_m2_sqrt_s * 1e-10
            total += (
                beam_target_yield(
                    pinch.ion_density_per_m3,
                    current,
                    PINCH_LENGTH_M,
                    CATHODE_RADIUS_M,
                    radius,
                    CROSS_SECTION_M2,
                    DIODE_VOLTAGE_V,
                )
                * 1e-9
            )
        return total

    return floor_pass


def native_pass_factory(points: int) -> Pass | None:
    """Return the native grid pass when the native module is importable.

    Parameters
    ----------
    points
        Number of grid points.

    Returns
    -------
    callable or None
        The pass function, or None when the native module is absent.
    """
    try:
        native = importlib.import_module("scpn_dense_plasma_focus_native")
    except ImportError:
        return None
    sample_grid = grid(points)

    def native_pass() -> float:
        total = 0.0
        for current, radius in sample_grid:
            slug = native.slug_relations(
                current, radius, MASS_DENSITY_KG_M3, 0.7, 0.35, GAMMA, 4.0, 2.0, 1.0
            )
            pinch = native.pinch_radiation(
                current,
                radius,
                PINCH_LENGTH_M,
                ANODE_RADIUS_M,
                MOLECULE_DENSITY_PER_M3,
                0.7,
                0.35,
                2.0,
                1.0,
                1.0,
            )
            beam = native.fast_ion_beam(
                current,
                radius,
                CATHODE_RADIUS_M,
                DIODE_VOLTAGE_V,
                PINCH_DURATION_S,
                0.14,
                2.0,
                1.0,
            )
            total += slug[2] + pinch[11] * 1e-9 + beam[11] * 1e-10
            total += (
                native.beam_target_yield(
                    pinch[0],
                    current,
                    PINCH_LENGTH_M,
                    CATHODE_RADIUS_M,
                    radius,
                    CROSS_SECTION_M2,
                    DIODE_VOLTAGE_V,
                )
                * 1e-9
            )
        return total

    return native_pass


def measure(run: Pass, points: int, warmup: int, repeats: int) -> dict[str, float]:
    """Time repeated passes and summarise them.

    Parameters
    ----------
    run
        Pass to time.
    points
        Number of grid points per pass.
    warmup
        Discarded leading passes.
    repeats
        Timed passes.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min, max in microseconds per grid point and the
        throughput in points per second (P50-based).
    """
    for _ in range(warmup):
        run()
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        run()
        samples.append((time.perf_counter_ns() - start) / 1e3 / points)
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    p50 = percentile(0.5)
    return {
        "points_per_pass": float(points),
        "p50_us_per_point": p50,
        "p95_us_per_point": percentile(0.95),
        "p99_us_per_point": percentile(0.99),
        "mean_us_per_point": statistics.fmean(samples),
        "min_us_per_point": ordered[0],
        "max_us_per_point": ordered[-1],
        "throughput_points_per_s": 1e6 / p50,
    }


def provenance() -> dict[str, Any]:
    """Collect the environment provenance of a run.

    Returns
    -------
    dict[str, Any]
        Interpreter, platform, CPU model, commit and host-load context.
    """
    cpu_model = "unknown"
    with contextlib.suppress(OSError):
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    load = "unavailable"
    with contextlib.suppress(OSError):
        load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[0]
    commit = "unknown"
    git = shutil.which("git")
    if git is not None:
        with contextlib.suppress(OSError):
            commit = subprocess.run(
                [git, "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "load_average_1min_at_start": load,
        "commit": commit,
        "isolated_cores": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark command-line interface.

    Parameters
    ----------
    argv
        Argument vector; None reads sys.argv.

    Returns
    -------
    int
        0 on completion.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=100000)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    results: list[dict[str, Any]] = [
        {
            "name": "level0_pinch_beam_yield_grid_pass",
            "backend": "python_floor",
            "stats": measure(
                floor_pass_factory(args.points), args.points, args.warmup, args.repeats
            ),
            "status": "measured",
        }
    ]
    native_pass = native_pass_factory(args.points)
    if native_pass is None:
        results.append(
            {
                "name": "level0_pinch_beam_yield_grid_pass",
                "backend": "rust_native",
                "stats": None,
                "status": "unavailable: scpn_dense_plasma_focus_native not installed",
            }
        )
    else:
        stats = measure(native_pass, args.points, args.warmup, args.repeats)
        results.append(
            {
                "name": "level0_pinch_beam_yield_grid_pass",
                "backend": "rust_native",
                "stats": stats,
                "status": "measured",
                "requires": "optional native build (rust/, maturin)",
            }
        )
        floor_p50 = results[0]["stats"]["p50_us_per_point"]
        results[1]["speedup_p50_vs_python_floor"] = (
            floor_p50 / stats["p50_us_per_point"]
        )
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {
            "points": args.points,
            "warmup": args.warmup,
            "repeats": args.repeats,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"level0_physics.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['backend']}: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
