# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device 3D model benchmark

"""Benchmark the device 3D model: library Python floor versus library native.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per (operation, backend), unavailable backends marked
explicitly, full provenance in the artefact. The operation is one full
device tessellation (the anode, the sleeve, every cathode rod, the
chamber and the pinch column) at a declared segment count followed by
the signed volume and surface area of every body; each sample times one
full pass and the cost is reported per generated face. Both backends are
the pinned shared kernel library's: the floor row builds the validated
device model on its Python kernels, the native row calls its native
kernels per body through the binding (call-through cost, not a vectorised
pipeline). Nothing measured here is a physics or engineering claim.
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

from scpn_dense_plasma_focus_core.configuration import (  # noqa: E402
    DeviceConfiguration,
    RegistryBinding,
)
from scpn_dense_plasma_focus_core.geometry import (  # noqa: E402
    DeviceGeometry,
    build_device_model,
)
from scpn_dense_plasma_focus_core.parameters import (  # noqa: E402
    BankAndFill,
    ElectrodeSet,
)

SCHEMA: Final = "scpn-dense-plasma-focus-core.device-model-3d-benchmark.v1"
PINCH_RADIUS_M: Final = 0.006
PINCH_LENGTH_M: Final = 0.08
REGISTRY_DIGEST: Final = (
    "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"
)


def synthetic_design() -> tuple[DeviceConfiguration, DeviceGeometry]:
    """Build the synthetic configuration and geometry of the benchmark.

    Returns
    -------
    (DeviceConfiguration, DeviceGeometry)
        Synthetic values; nothing describes a real machine.
    """
    configuration = DeviceConfiguration(
        identifier="dense_plasma_focus",
        electrodes=ElectrodeSet(
            anode_radius_m=0.05, cathode_radius_m=0.1, anode_length_m=0.3
        ),
        bank=BankAndFill(
            bank_energy_kj=20.0,
            peak_current_ma=0.5,
            fill_pressure_torr=4.0,
            deuterium_fill=True,
        ),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )
    geometry = DeviceGeometry(
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
    return configuration, geometry


def floor_pass(segments: int) -> tuple[float, int]:
    """Run one full device pass on the Python floor.

    Parameters
    ----------
    segments
        Circumferential segments per body.

    Returns
    -------
    (float, int)
        Checksum of the measures (so the work cannot be optimised away)
        and the number of generated faces.
    """
    configuration, geometry = synthetic_design()
    model = build_device_model(
        configuration, geometry, PINCH_RADIUS_M, PINCH_LENGTH_M, segments
    )
    total = 0.0
    faces = 0
    for mesh in model.meshes:
        total += mesh.signed_volume_m3() + mesh.surface_area_m2()
        faces += mesh.face_count
    return total, faces


def native_pass_factory() -> Callable[[int], tuple[float, int]] | None:
    """Return the native device pass when the library's native module imports.

    Returns
    -------
    callable or None
        The pass function, or None when scpn_reactor_kernels_native is absent.
    """
    try:
        native = importlib.import_module("scpn_reactor_kernels_native")
    except ImportError:
        return None

    def native_pass(segments: int) -> tuple[float, int]:
        configuration, geometry = synthetic_design()
        electrodes = configuration.electrodes
        anode_radius = electrodes.anode_radius_m
        cathode_radius = electrodes.cathode_radius_m
        anode_length = electrodes.anode_length_m
        chamber_outer = geometry.chamber_outer_radius_m
        chamber_length = geometry.chamber_length_m
        rod_vertices, rod_faces = native.tessellate_cylinder(
            geometry.cathode_rod_radius_m, 0.0, geometry.cathode_length_m, segments
        )
        ring = native.ring_offsets(geometry.cathode_rod_count, cathode_radius)
        rods = tuple(
            (
                native.translate(
                    rod_vertices, ring[2 * index], ring[2 * index + 1], 0.0
                ),
                rod_faces,
            )
            for index in range(geometry.cathode_rod_count)
        )
        bodies = (
            native.tessellate_cylinder(anode_radius, 0.0, anode_length, segments),
            native.tessellate_annular_tube(
                anode_radius,
                anode_radius + geometry.insulator_sleeve_wall_thickness_m,
                0.0,
                geometry.insulator_sleeve_length_m,
                segments,
            ),
            *rods,
            native.tessellate_annular_tube(
                geometry.chamber_inner_radius_m,
                chamber_outer,
                0.0,
                chamber_length,
                segments,
            ),
            native.tessellate_cylinder(
                chamber_outer, 0.0 - geometry.back_wall_thickness_m, 0.0, segments
            ),
            native.tessellate_cylinder(
                chamber_outer,
                chamber_length,
                chamber_length + geometry.end_wall_thickness_m,
                segments,
            ),
            native.tessellate_cylinder(
                PINCH_RADIUS_M,
                anode_length,
                anode_length + PINCH_LENGTH_M,
                segments,
            ),
        )
        total = 0.0
        faces = 0
        for vertices, indices in bodies:
            total += native.mesh_volume(vertices, indices)
            total += native.mesh_area(vertices, indices)
            faces += len(indices) // 3
        return total, faces

    return native_pass


def measure(
    run: Callable[[int], tuple[float, int]],
    segments: int,
    warmup: int,
    repeats: int,
) -> dict[str, float]:
    """Time repeated device passes and summarise them.

    Parameters
    ----------
    run
        Device pass to time.
    segments
        Circumferential segments per body.
    warmup
        Discarded leading passes.
    repeats
        Timed passes.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min, max in microseconds per generated face and
        the throughput in faces per second (P50-based).
    """
    faces = 1
    for _ in range(warmup):
        _, faces = run(segments)
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        _, faces = run(segments)
        samples.append((time.perf_counter_ns() - start) / 1e3 / faces)
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    p50 = percentile(0.5)
    return {
        "faces_per_pass": float(faces),
        "p50_us_per_face": p50,
        "p95_us_per_face": percentile(0.95),
        "p99_us_per_face": percentile(0.99),
        "mean_us_per_face": statistics.fmean(samples),
        "min_us_per_face": ordered[0],
        "max_us_per_face": ordered[-1],
        "throughput_faces_per_s": 1e6 / p50,
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
    parser.add_argument("--segments", type=int, default=4096)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    results: list[dict[str, Any]] = [
        {
            "name": "device_tessellation_and_measures",
            "backend": "python_floor",
            "stats": measure(floor_pass, args.segments, args.warmup, args.repeats),
            "status": "measured",
        }
    ]
    native_pass = native_pass_factory()
    if native_pass is None:
        results.append(
            {
                "name": "device_tessellation_and_measures",
                "backend": "rust_native",
                "stats": None,
                "status": "unavailable: scpn_reactor_kernels_native not installed",
            }
        )
    else:
        stats = measure(native_pass, args.segments, args.warmup, args.repeats)
        results.append(
            {
                "name": "device_tessellation_and_measures",
                "backend": "rust_native",
                "stats": stats,
                "status": "measured",
                "requires": (
                    "optional native build of the pinned kernel library "
                    "(its rust/, maturin)"
                ),
            }
        )
        floor_p50 = results[0]["stats"]["p50_us_per_face"]
        results[1]["speedup_p50_vs_python_floor"] = floor_p50 / stats["p50_us_per_face"]
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {
            "segments": args.segments,
            "warmup": args.warmup,
            "repeats": args.repeats,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"device_model_3d.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['backend']}: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
