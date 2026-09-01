# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the coaxial electrode set with its sweeping
current sheath and focus, the three declared discharge phases, and the
Lee-Serban drive-parameter window the configuration model checks. The
right-hand text panel states only facts backed by the repository
itself.

Outputs (written next to this script):

- ``repo_header.png`` — the coaxial device view with the rundown
  sheath and the dense focus at the anode tip (used by ``README.md``).
- ``repo_header_discharge_phases.png`` — breakdown, axial rundown and
  radial focus as a sequence.
- ``repo_header_drive_window.png`` — the drive-parameter window of
  optimised machines with flagged outliers.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, no random input).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"
RED = "#ff3366"
GREEN = "#3ddc84"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configuration", "dense_plasma_focus · coaxial pinch"),
    ("Hard Invariant", "coaxial electrode ordering"),
    ("Drive Parameter", "Lee-Serban window flagged (D fills)"),
    ("Reference", "Lee-Serban, IEEE TPS 24 (1996) 1101"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.75,
        "DENSE PLASMA",
        color="white",
        fontsize=24,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.705,
        "FOCUS CORE",
        color="white",
        fontsize=24,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.645,
        subtitle,
        color=CYAN,
        fontsize=11,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.605, 0.605], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.545
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def generate_coaxial_device() -> None:
    """Generate ``repo_header.png``: the coaxial device view."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-2.6, 2.6)

    for rail_y in (1.75, -1.75):
        ax.plot([0.9, 7.6], [rail_y, rail_y], color=STEEL, lw=5.0, alpha=0.85)
    ax.text(
        4.2,
        2.02,
        "cathode (outer)",
        color="#667799",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.add_patch(
        plt.Rectangle(
            (0.9, -0.45),
            5.4,
            0.9,
            fill=False,
            ec=MAGENTA,
            lw=2.0,
            alpha=0.9,
        )
    )
    ax.text(
        3.4,
        -0.02,
        "anode (inner)",
        color=MAGENTA,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
    )

    ax.add_patch(
        plt.Rectangle(
            (0.9, -0.85),
            0.45,
            1.7,
            fill=True,
            fc="#223355",
            ec=PROBE,
            lw=1.2,
            alpha=0.65,
        )
    )
    ax.text(
        1.12,
        -1.2,
        "insulator",
        color=PROBE,
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    sheaths = ((2.1, 0.35), (3.4, 0.5), (4.7, 0.7), (5.9, 0.9))
    for sheath_x, alpha in sheaths:
        along = np.linspace(-1, 1, 100)
        ax.plot(
            sheath_x + 0.35 * (1 - along**2),
            along * 1.6,
            color=CYAN,
            lw=1.6,
            alpha=alpha,
        )
    ax.annotate(
        "",
        xy=(6.1, 2.15),
        xytext=(2.4, 2.15),
        arrowprops={"arrowstyle": "->", "color": CYAN, "lw": 1.1, "alpha": 0.7},
    )
    ax.text(
        4.25,
        2.32,
        "rundown sheath",
        color=CYAN,
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    grid_x = np.linspace(6.0, 8.4, 120)
    grid_z = np.linspace(-1.0, 1.0, 100)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    rho = np.sqrt(((mesh_x - 6.9) / 0.45) ** 2 + (mesh_z / 0.55) ** 2)
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 1.6),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.95,
    )
    ax.plot(6.9, 0, "o", color="white", ms=5, alpha=0.95)
    ax.annotate(
        "focus · dense pinch",
        xy=(6.9, 0.15),
        xytext=(7.7, 1.55),
        color="white",
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.95,
        arrowprops={"arrowstyle": "->", "color": "white", "lw": 0.9, "alpha": 0.6},
    )

    ax.text(
        5.0,
        -2.35,
        "coaxial discharge · breakdown, rundown, radial focus",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Coaxial Drive, Focused Pinch")
    _save(fig, plt, "repo_header.png")


def generate_discharge_phases() -> None:
    """Generate ``repo_header_discharge_phases.png``: the sequence."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    panels = [
        (1.85, "breakdown", "along the insulator"),
        (5.0, "axial rundown", "sheath swept by J x B"),
        (8.15, "radial focus", "dense pinch at the tip"),
    ]
    for centre_x, title, sub in panels:
        for rail_y in (1.3, -1.3):
            ax.plot(
                [centre_x - 1.25, centre_x + 1.05],
                [rail_y, rail_y],
                color=STEEL,
                lw=3.2,
                alpha=0.8,
            )
        ax.add_patch(
            plt.Rectangle(
                (centre_x - 1.25, -0.32),
                1.8,
                0.64,
                fill=False,
                ec=MAGENTA,
                lw=1.4,
                alpha=0.85,
            )
        )
        if title == "breakdown":
            along = np.linspace(-1, 1, 80)
            ax.plot(
                centre_x - 1.12 + 0.10 * (1 - along**2),
                along * 1.25,
                color=CYAN,
                lw=2.0,
                alpha=0.95,
            )
        if title == "axial rundown":
            for offset, alpha in ((-0.55, 0.45), (0.0, 0.7), (0.5, 0.95)):
                along = np.linspace(-1, 1, 80)
                ax.plot(
                    centre_x + offset + 0.28 * (1 - along**2),
                    along * 1.25,
                    color=CYAN,
                    lw=1.7,
                    alpha=alpha,
                )
            ax.annotate(
                "",
                xy=(centre_x + 0.85, 1.55),
                xytext=(centre_x - 0.75, 1.55),
                arrowprops={"arrowstyle": "->", "color": CYAN, "lw": 1.0, "alpha": 0.7},
            )
        if title == "radial focus":
            grid_x = np.linspace(centre_x + 0.2, centre_x + 1.35, 80)
            grid_z = np.linspace(-0.75, 0.75, 80)
            mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
            rho = np.sqrt(
                ((mesh_x - centre_x - 0.72) / 0.32) ** 2 + (mesh_z / 0.42) ** 2
            )
            ax.contourf(
                mesh_x,
                mesh_z,
                np.exp(-rho * 1.6),
                levels=24,
                cmap=_glow_cmap(),
                alpha=0.95,
            )
            ax.plot(
                centre_x + 0.72,
                0,
                "o",
                color="white",
                ms=4,
                alpha=0.95,
            )
        ax.text(
            centre_x,
            -1.85,
            title,
            color="#99bbdd",
            fontsize=8.5,
            fontfamily="monospace",
            ha="center",
            alpha=0.95,
        )
        ax.text(
            centre_x,
            -2.2,
            sub,
            color="#445566",
            fontsize=7.5,
            fontfamily="monospace",
            ha="center",
        )

    ax.annotate(
        "",
        xy=(6.5, 2.45),
        xytext=(3.5, 2.45),
        arrowprops={"arrowstyle": "->", "color": STEEL, "lw": 1.2, "alpha": 0.7},
    )
    ax.text(
        5.0,
        2.67,
        "time",
        color="#667799",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.text(
        5.0,
        -2.85,
        "one bank discharge, three declared phases",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "Breakdown, Rundown, Focus")
    _save(fig, plt, "repo_header_discharge_phases.png")


def generate_drive_window() -> None:
    """Generate ``repo_header_drive_window.png``: the checked window."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    ax.plot([1.0, 9.2], [1.7, 1.7], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([1.0, 1.0], [1.7, 9.1], color=STEEL, lw=1.0, alpha=0.7)
    ax.text(
        8.85,
        1.25,
        "machine scale",
        color="#8899bb",
        fontsize=9.5,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(
        1.15,
        8.85,
        "S = I / (a · √p)",
        color="#8899bb",
        fontsize=9.5,
        fontfamily="monospace",
    )

    y_low, y_high = 4.6, 6.2
    ax.fill_between([1.0, 9.0], y_low, y_high, color=GREEN, alpha=0.08)
    for level in (y_low, y_high):
        ax.plot(
            [1.0, 9.0],
            [level, level],
            color=GREEN,
            lw=1.0,
            alpha=0.6,
            ls=(0, (5, 3)),
        )
    ax.text(
        5.0,
        (y_low + y_high) / 2,
        "documented window of optimised machines",
        color=GREEN,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        va="center",
        alpha=0.95,
    )

    points = [
        (1.8, 5.4, True),
        (2.9, 5.1, True),
        (4.1, 5.7, True),
        (5.3, 4.9, True),
        (6.5, 5.5, True),
        (7.7, 5.2, True),
        (3.5, 7.8, False),
        (6.0, 2.9, False),
    ]
    for mark_x, mark_y, inside in points:
        if inside:
            ax.plot(mark_x, mark_y, "o", color=CYAN, ms=6, alpha=0.9)
        else:
            ax.plot(
                mark_x,
                mark_y,
                "x",
                color=RED,
                ms=9,
                mew=2.2,
                alpha=0.95,
            )
    ax.text(
        3.5,
        8.15,
        "flagged",
        color=RED,
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )
    ax.text(
        6.0,
        2.45,
        "flagged",
        color=RED,
        fontsize=8,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.text(
        5.0,
        0.75,
        "deuterium-fill drive parameter checked · Lee-Serban, IEEE TPS 24 (1996) 1101",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "A Drive Parameter With A Window")
    _save(fig, plt, "repo_header_drive_window.png")


if __name__ == "__main__":
    generate_coaxial_device()
    generate_discharge_phases()
    generate_drive_window()
