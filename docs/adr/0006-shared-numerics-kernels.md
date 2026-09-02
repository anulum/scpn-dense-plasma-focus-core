<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — ADR 0006
-->

# ADR 0006 — Retire the transcendental copy: consume the shared numerics kernels

Status: accepted (2026-09-02). Amends ADR 0005 item 5: the byte-identical
copy of the library's transcendental kernel is retired.

## Context

ADR 0005 vendored `physics/_transcendental.py` and `rust/src/transcendental.rs`
as byte-identical copies of the shared kernel library's `numerics_transcendental`
(SCPN-REACTOR-KERNELS commit 799d44d3) because the library could not yet be
pinned. The library is now public and pinnable by commit and inventory
digest, and two sibling repositories (Z-PINCH for the geometry kernels,
MIRROR for the numerics kernel) already consume it. Two copies of the same
series would drift; the copy carried the library's own tests, re-proving
what the library proves.

## Decision

1. `scpn-reactor-kernels` is the one runtime dependency, pinned to commit
   `6f574bfdddadf24c6a4c0a020c0a257fec38231a` in `pyproject.toml`; the
   manifest records the pin in the optional `kernel_library` block
   (distribution, version, source commit, inventory digest
   `b065c46b…`, kernels `[numerics_transcendental]`) enforced by the
   validator; a contract test proves manifest, `pyproject.toml`, the
   installed version, `rust/Cargo.toml`, `rust/Cargo.lock` and the CI
   install steps name one commit.
2. `physics/numerics.py` replaces the copy: it re-exports the library's
   `natural_log`, `exponential`, `power`, `EXP_MIN` and `EXP_MAX`, and
   re-raises the library's domain refusal as the device `NumericsError`;
   the physics modules import from it. The library's accuracy, exactness
   and refusal evidence is the library's (its `VALIDATION.md#numerics-kernels`).
3. The native crate depends on `scpn-reactor-kernels-rs` as a git
   dependency at the same commit (no default features) and uses its
   `numerics::transcendental` functions; `Cargo.lock` records the source.
4. The manifest adds the excluded domain
   `shared_physics_geometry_and_numerics_kernels` (owner SCPN-REACTOR-KERNELS).

## Consequences

Every level-0 value is unchanged (the series and the operation order are
identical); the reference digests and the parity tests stay green. A change
of the pin is a governed data change (manifest, descriptor, inventory,
envelope fixture, Cargo re-lock, SPO re-intake). The library's consumer
table gains this repository.
