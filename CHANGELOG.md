<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — CHANGELOG
-->

# Changelog

## [Unreleased]

### Changed

- The temporary byte-identical copy of the shared library's transcendental
  kernel (`physics/_transcendental.py`, `rust/src/transcendental.rs`) is
  retired for the pinned library (ADR 0006): `scpn-reactor-kernels` is the
  one runtime dependency pinned to a commit object in `pyproject.toml`, the
  manifest records the same commit, the library's kernel-inventory digest
  and the consumed kernel in the optional `kernel_library` block enforced by
  the validator, and declares the excluded domain
  `shared_physics_geometry_and_numerics_kernels`; `physics/numerics.py`
  re-exports the library kernels and re-raises their refusals as
  `NumericsError`; the native crate depends on the library's Rust crate at
  the same commit. No level-0 value changes; the library's own tests no
  longer run here. CI installs the package with its pinned dependency;
  descriptor and inventory regenerated; the envelope fixture regenerated for
  the new `manifest_sha256` (plan bytes unchanged); the benchmark artefact
  regenerated on the pinned crate.

### Added

- Device CAD model (`src/scpn_dense_plasma_focus_core/geometry/cad.py`),
  the fifth implemented capability at `computational_prototype` (ADR
  0009): the same bodies as exact B-rep solids, with the cathode built as
  one solid per rod on the centres the tessellated model uses, so the two
  tiers sit on one circle by construction. The `DeviceModelCAD` record
  (`scpn.dense-plasma-focus-cad-model.v1`) carries both source digests,
  the declared pinch column, the rod count, the declared deflections and
  reference segment count, the back-end versions, the assembly manifest,
  the STEP digest and the per-body evidence; `write_step` writes exactly
  the digested bytes, and the STEP provenance carries the rod count and
  the ring separation so a reader of the file can see the cage. The
  per-body evidence is the shared library's, not this repository's. The
  build runs the tier-G1 build first, so one set of invariants governs
  both tiers — a rod set that would intersect itself is refused before any
  solid exists. The anchor fixture is exercised at this tier too: the
  anode radius and length, the cathode circle radius, the rod radius and
  count and the sleeve length printed for the NX3 assembly A20Z160 are all
  proven to appear in the built solids. The kernel-library pin moves to
  the commit carrying the CAD group, its placement and body-evidence
  kernels and its bounding-box correction, in the manifest, the
  dependency (with the `cad` extra), the crate and the lock; the CI gains
  a `cad` job that installs the system library the mesher's wheel links
  against before the extra; manifest, descriptor, inventory and envelope
  fixture regenerated; a standard-conformant benchmark with a committed
  local artefact is added.

- Device 3D model (`src/scpn_dense_plasma_focus_core/geometry/`), the fourth
  implemented capability at `computational_prototype` (ADR 0007, which amends
  ADR 0006, and ADR 0008): a validated `DeviceGeometry` of the Mather-type
  mechanical envelope (insulator-sleeve length and wall, cathode rod radius,
  rod count and cathode length, chamber bore, wall and length, back-wall and
  end-wall thickness — the anode radius, cathode radius and anode length stay
  in the configuration), and a `DeviceModel3D` record
  (`scpn.dense-plasma-focus-3d-model.v1`) composing `6 + N` closed,
  outward-oriented triangle bodies: anode, insulator sleeve, the `N` cathode
  rods of the squirrel cage placed on the coaxial circle of the cathode
  radius, chamber wall, back wall, downstream end wall and the declared pinch
  column standing on the anode tip. The layout follows the documents already
  on file for the level-0 models; every dimension is declared, and the
  cathode is built as the rod cage it is — a rod that would reach the
  insulator sleeve and a rod set whose members would intersect are both
  refused. Binary STL and glTF 2.0 binary exports carry the device
  provenance, the rod count included, in the document `extras`. The manifest
  block `kernel_library` gains the geometry kernels and the placement kernel
  and moves to the library commit that carries the latter, the capability and
  the owned domain `device_geometry_and_3d_model`; descriptor and inventory
  regenerated; the envelope fixture regenerated for the new
  `manifest_sha256` (plan bytes unchanged). Every body is proven bit-exact
  against the library's native module. A standard-conformant benchmark
  (`benchmarks/device_model_3d.py`) with a committed local artefact and a
  `docs/benchmarks.md` section; the native CI job additionally builds the
  library's native module so the geometry parity file never skips.

- Level-0 device physics (`src/scpn_dense_plasma_focus_core/physics/`), the
  third implemented capability at `computational_prototype` (ADR 0005):
  the closed forms of the Lee model (Lee 2014; Saw and Lee in
  IAEA-TECDOC-1829; Lee, ICTP 2012) — bank normalisation and scaling
  parameters, fill state, axial and radial characteristic quantities, slug
  relations, rule-of-thumb pinch geometry, pinch-phase density, Bennett
  temperature and power terms with both self-absorption branches, the
  fast-ion-beam chain, beam-target and scaling-law neutron estimates — with
  a canonical `Level0PhysicsRecord`, explicit `ModelInputs` and a declared
  `PinchState`, anchored to the printed table of twelve fitted machines with
  declared tolerances and three recorded source inconsistencies. A vendored
  byte-identical copy of the shared kernel library's deterministic
  logarithm, exponential and power (canonical: SCPN-REACTOR-KERNELS
  `799d44d3`) keeps the bit-exact rule; native kernels (`rust/`, crate
  `scpn-dense-plasma-focus-rs`, optional distribution
  `scpn-dense-plasma-focus-native`) reproduce every value bit for bit,
  proven by parity tests; a standard-conformant benchmark
  (`benchmarks/level0_physics.py`) with a committed local artefact and
  `docs/benchmarks.md`. The manifest declares the capability and the owned
  domain `analytic_device_physics_models`; descriptor and inventory
  regenerated; the envelope fixture regenerated for the new
  `manifest_sha256` (plan bytes unchanged). Gates extended: `mypy` scope
  includes `benchmarks/` and `make typecheck` now covers `src/`, a `rust`
  CI job runs the crate gates, parity and a benchmark smoke, `make rust`
  locally.

- Diagnostic-plan depth: per-channel signal inventories, frame
  transformations with a fixed kind-admissibility table and connectivity
  rule, and a clock topology partitioning the physical clocks into rooted
  domains with a star of relations to the reference root. Envelope
  `scpn.reactor-diagnostic-plan-envelope.v1` bumped to `1.2.0`; the
  fixture is regenerated from the public surface and re-pinned. All new
  members are declarations: no observation, phase, mapping, or control
  authority is created.
- Local gate parity with the wider ecosystem: the pre-commit chain now
  also runs REUSE licensing compliance and a typographical checker
  (`_typos.toml` carries the deliberate reactor vocabulary), and adds
  the upstream YAML, TOML, large-file and private-key guards. Licensing
  and spelling were previously verified only in hosted CI, so a broken
  REUSE annotation — including the aggregate annotation that covers the
  binary header images — could reach a push before being caught.
- Generated repository header artwork: `docs/assets/generate_header.py`
  renders three deterministic 1280x640 images from the repository's own
  domain surface (the coaxial device view used by the README, the
  three discharge phases, and the drive-parameter window).
- Modular hosted-workflow surface per the ecosystem workflow-modularity
  standard: `ci.yml` reduced to a coordinator with a stable fail-closed
  `gate` job, single-responsibility reusable workflows for static
  analysis/repository policy and for tests, a versioned machine-readable
  inventory (`.github/workflow-inventory.json`,
  `scpn.workflow-inventory.v1` `1.0.0`), and a fail-closed modularity
  guard (`tools/audit_workflows.py`) enforced locally (preflight gate,
  pre-commit hook) and in hosted CI. The duplicate documentation-links
  step was removed from the CI chain; `docs.yml` remains the single
  owner of documentation validation.

- Typed reference frames, clock synchronisation relations (synthetic
  bounds only; no correlation evidence claimed), and per-channel
  acquisition windows and element counts in the diagnostic model;
  hardened decoders (recursive exact-key, duplicate-member, and
  byte-canonical refusal in both codecs); envelope `1.1.0` adding
  `manifest_sha256` over the committed canonical `reactor-domain.json`
  (fixture regenerated; byte hash re-pinned in tests).

- Portable diagnostic-plan envelope
  (`src/scpn_dense_plasma_focus_core/plan_envelope.py`,
  `scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): a
  producer-owned, canonically serialised wrapper carrying project
  identity, exact owned configurations, capability and maturity,
  synthetic/review-only/non-actuating statements, both SPO registry
  pins, the inner plan's SHA-256, the producer revision, and fixed
  no-observation/no-control non-claims; strict parsers refuse unknown,
  duplicate, and non-finite members, and an immutable committed fixture
  exercises the exchange end to end.

- Diagnostic and clock semantics model
  (`src/scpn_dense_plasma_focus_core/observability.py`), the second implemented
  capability at `computational_prototype`: frozen clock, channel,
  deferral, and plan objects aligned fail-closed with the pinned SPO
  observability-profile catalogue (candidate applicability, carrier
  admissibility, exact class-fixed evidence vocabularies, clock-kind
  compatibility, Nyquist and event-timing bounds); cited advisory band
  and timing checks; canonical serialisation with SHA-256 digests and
  strict NaN-rejecting round-trip parsing (design record
  `docs/adr/0003-diagnostic-clock-semantics.md`).

- Device configuration model (`src/scpn_dense_plasma_focus_core/`), the first implemented
  capability at `computational_prototype`: validated frozen parameter
  objects with device-specific invariants and documented, cited
  consistency estimates; canonical serialisation with SHA-256 digests
  and strict NaN-rejecting round-trip parsing; a data-only pin to the
  SPO reactor registry; and the reactor-domain validator branch
  enforcing populated capability inventories with the ADR 0002
  evidence-maturity ceiling rule (design record
  `docs/adr/0002-device-configuration-model.md`).

- Architecture-only repository scaffold: governance, security, licensing,
  REUSE metadata, contribution and support policies, and citation metadata.
- Machine-readable domain manifest `reactor-domain.json` binding the project
  to SCPN Phase Orchestrator reactor registry `1.0.0`
  (configuration `dense_plasma_focus`).
- Device-owned CONTROL adapter specification and threat model.
- Derived Studio portfolio descriptor (`not_federated`) and generated
  capability inventory (zero implemented capabilities).
- Validation tooling: domain-manifest validator, descriptor derivation and
  inventory generation with drift checks, and a fail-closed preflight
  orchestrator, each with statement- and branch-complete tests.
- Continuous-integration, code-scanning, security-audit, documentation,
  SBOM, pre-commit, and Scorecard workflow definitions (read-only
  permissions; no publication or deployment workflows).

### Changed

- Studio portfolio descriptor schema ratified at version 1.1.0 after
  downstream review, before any consumer adoption (1.0.0 superseded
  unconsumed): canonical JSON Schema published in-repository with a strict
  unknown-field policy, explicit source repository, nullable lifecycle
  evidence pointer, nullable versioned control-intent reference, ratified
  capability item shape, and a machine-protection object (independent
  final-veto owner with availability `not_assessed`) replacing the former
  boolean flag.
