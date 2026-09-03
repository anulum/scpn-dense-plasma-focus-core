<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN Dense Plasma Focus Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-DENSE-PLASMA-FOCUS-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`ElectrodeSet`, `BankAndFill`,
  `DeviceConfiguration`) rejecting non-finite values, non-positive
  extents, and an anode at or beyond the cathode radius (the hard
  coaxial-gun invariant of the Mather/Filippov family) — every rejection
  branch is tested.
- The Lee-Serban drive parameter `S = I_peak / (a sqrt(p))`
  (Lee & Serban, IEEE Trans. Plasma Sci. 24 (1996) 1101) as a
  documented derived quantity, with an advisory finding outside the
  documented deuterium window `[66, 108]` kA cm^-1 Torr^-1/2 (not
  applied to other fill gases), reported and never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are advisory regime checks, not pinch-dynamics or yield
  results; no benchmark, dataset, solver, controller, or experimental
  correlation exists in this repository.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design record: `docs/adr/0005-level0-device-physics.md`).
Sources: S. Lee, "Plasma Focus Radiative Model: Review of the Lee Model
Code", J. Fusion Energ. 33 (2014) 319–335; S. H. Saw and S. Lee,
"Investigation of Intense Fusion Pulses", in IAEA-TECDOC-1829 (2017)
pp. 84–86 (Table 1: twelve machines fitted with the code); S. Lee, "The
Plasma Focus: Scaling Properties to Scaling Laws", ICTP 2168-10 (2012).

What is exercised, all under the 100 % statement-and-branch coverage gate
(`src/scpn_dense_plasma_focus_core/physics/`):

- **Bank normalisation and fill state** (`bank.py`; Lee eqs. 4–6, 9, 43):
  `E0`, `t0`, `Z0`, `I0`, the quarter period, `delta`, `ln c`, `La`,
  `beta`, and the ideal-gas fill. Anchors: the `E0` and `trise` columns of
  Table 1 for PF1000, NX3, INTI and PF400J within 2.5 % and 2 % (the
  table's own rounding; the sub-kilojoule row prints one significant
  digit).
- **Axial characteristics** (`axial.py`; eqs. 5–7, eq. 1 at rest): the
  transit time, `alpha`, the characteristic speed and the terminal snowplow
  speed at a declared current. Anchor: the terminal speed at the peak
  current against the `peak va` column of the four rows within 15 %; it
  overestimates every row by 7–14 % and the tests assert that sign, so the
  deviation is evidence, not noise.
- **Radial characteristics, slug relations, rule-of-thumb geometry**
  (`radial.py`; eqs. 14, 15, 24–28, 32, 34; ICTP Tables 2–3): closed forms
  against their definitions to `1e-14`; the eq. (28) ratio at `c = 3.4`
  reproduces the printed "typically 2.5" (2.40, 5 %); the tabulated
  `rmin/a` of NX3 and PF400J and `zmax/a` of NX3 fall inside the ICTP
  Table 2 spread; sign and scaling identities of the slug relations;
  `gamma <= 1` and a negative effective charge are refused.
- **Pinch-phase closed forms** (`pinch.py`; eqs. 39–48): density, Bennett
  temperature, Spitzer resistance, Joule, bremsstrahlung, line and
  surface-emission terms against their definitions; both self-absorption
  branches (a fully absorbed dense column with `A` exactly zero and the
  surface term; a tenuous column with `A > 1/e` and the scaled volumetric
  term); `A` monotone in density; `T ∝ I^2`. No printed anchor: the
  tabulated `Tpinch` and `ni` are outputs of the integrated code and are
  not reproduced by eqs. (41) and (43) at the tabulated inputs (factors of
  about 3 and 5 in a hand check), which the record states.
- **Fast-ion-beam chain** (`beam.py`; TECDOC eqs. 5–6, items (a)–(k)):
  flux, beam speed, energy flux, power flow, ion current, fluence, energy
  fluence, ions, beam energy and damage factor against the PF1000, NX3 and
  INTI columns within 3 % and the PF400J column within 12 % (its two-digit
  pinch radius enters as `rp^-2`); `J_b ∝ I^2 / sqrt(M Z_eff)`.
- **Neutron estimates** (`neutron.py`; Lee eq. 50, TECDOC eqs. 1–2): the
  beam-target closed form with the declared cross-section; the source's
  own identity between its eq. (1) and eq. (2) reproduced to 1 % (the two
  printed constants differ by 0.5 %); the empirical scaling law reproduces
  its stated calibration point (`7e9` at 0.5 MA) within 10 % and is refused
  outside 0.1–1 MA (the record reports it as not applicable instead).
- **Numerics substrate** (`numerics.py`; ADR 0006): the natural logarithm,
  the exponential and the real power are the pinned shared kernel library's
  (`scpn-reactor-kernels`, kernel `numerics_transcendental`; commit and
  inventory digest in `reactor-domain.json`, `kernel_library`); tests prove
  each wrapper returns the library value bit for bit and re-raises the
  library's domain refusal as `NumericsError`; the library's accuracy
  evidence (logarithm and exponential within `1e-15` relative of the
  platform `math` module, power within `1e-13`) is the library's own. The
  manifest block is validated field by field and a contract test proves
  the manifest, the `pyproject.toml` dependency, the installed library
  version, `rust/Cargo.toml`, `rust/Cargo.lock` and the CI install steps
  name one commit.
- A composed `Level0PhysicsRecord` (`scpn.dense-plasma-focus-level0-physics.v1`
  `1.0.0`) with canonical bytes, SHA-256 digest and fixed non-claims, built
  from the validated configuration, explicit `ModelInputs` and a declared
  `PinchState`; every input rejects non-positive and non-finite values;
  three consistency checks (circuit energy within 5 % of the declared bank
  energy, pinch current not above the peak current, pinch radius inside
  the anode) refuse inconsistent declarations. The configuration's drive
  parameter reproduces the `SF` column for PF1000 and NX3 within 1 %; the
  INTI row is excluded because its printed `SF` does not follow from its
  own printed inputs.
- **Native parity**: the Rust crate in `rust/` mirrors every kernel with
  identical operation order; `tests/test_physics_native_parity.py`
  compares float64 bit patterns of every field of every model on the four
  anchor rows and on both self-absorption branches, plus the refusal paths.
- **Benchmark**: `benchmarks/level0_physics.py` per the ecosystem
  benchmark standard; results in `docs/benchmarks.md` and the committed
  local artefact `benchmarks/results/level0_physics.local.json`.

Bounded claims — what is NOT claimed:

- Every number is a closed-form evaluation of published relations on a
  synthetic configuration and a declared pinch state; no phase of the Lee
  model is integrated, no shot is simulated, no current waveform is fitted.
- The anchors reproduce numbers printed in the sources, which are
  themselves outputs of the source's fitted code; they are not correlations
  with experimental data.
- No yield, gain, reactivity, confinement or breakeven statement is made;
  the beam-target and scaling-law values are consistency instruments at
  the declared inputs, and the thermonuclear term is not implemented.
- No value describes, approximates or validates any real machine; the
  benchmark measures per-point evaluation cost of two implementations of
  the same closed forms.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, unresolvable event-timing bounds,
  and incomplete candidate coverage — every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- A reference plan mirroring canonical practice with synthetic
  declarations: discharge event train, neck-mode probe array, synthetic oscillator, each bound to its clock domain.
- Documented advisory band and timing checks with their sources stated
  in the code: m=0 necking bands of 1–1000 MHz and ns-scale pinch timing (Lee and Serban 1996); findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for this device family remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_dense_plasma_focus_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). The envelope is `1.1.0`, adding
`manifest_sha256` — the SHA-256 of the committed canonical
`reactor-domain.json` — verified in tests against the committed file.
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion;
`1.1.0` remains historical custody at the consumer) adds three typed
declaration surfaces, every branch under the 100 % statement-and-branch
gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; a `timing_marker` in `"s"` exactly for
  event-relative channels and forbidden otherwise; numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`): the frame kinds this
  repository may declare admit no transformation pair, so the
  transformation tuple must be empty and a second frame — which could
  never be connected — is refused. The model, its admissibility table
  and its declaration-only semantics (`evidence_claimed` always `False`)
  are shared with the portfolio.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.

## Device 3D model

Evidence record of the `device_3d_model` capability
(`computational_prototype`; design records `docs/adr/0007-device-3d-model.md`,
which amends `docs/adr/0006-shared-numerics-kernels.md`, and
`docs/adr/0008-cathode-as-the-rod-cage.md`, which supersedes its cathode
decision; consumer contract: `docs/DEVICE_3D_MODEL_CONTRACT.md`).

The unit circle, the tessellation primitives, the closed-mesh contract and
the STL/GLB serialisers are consumed from the shared kernel library
`scpn-reactor-kernels` at the commit this repository already pinned for the
numerics kernel; their evidence (polynomial accuracy against `libm`, exact
polygon-prism identities, quadratic convergence, closure and orientation,
export layouts, native parity) is the library's, at its
`VALIDATION.md#geometry-kernels`. What this repository exercises, all under
the coverage gate (`src/scpn_dense_plasma_focus_core/geometry/`):

- **Device geometry** (`DeviceGeometry`): nine SI parameters of the
  mechanical envelope (insulator-sleeve length and wall, cathode rod radius
  and cathode length, chamber bore, wall and length, back-wall and end-wall
  thickness) plus the integer rod count, with fail-closed positivity, the
  rule that at least three rods are declared, the axial rule that the
  cathode fits the chamber length, canonical bytes, a SHA-256 digest and a
  strict parser refusing unknown fields, non-finite literals and a
  non-integer rod count; every rejection branch is tested. The anode radius, the cathode radius and the anode length stay in
  the configuration's `ElectrodeSet`. The layout is the qualitative
  Mather-type arrangement of the documents already on file for the level-0
  models (IAEA-TECDOC-1829; S. Lee, J. Fusion Energ. 33 (2014) 319). The
  reference fixtures are synthetic; one anchor fixture carries the
  dimensions IAEA-TECDOC-1829 p. 231 prints for the NX3 assembly A20Z160
  (anode radius 20 mm and length 160 mm, twelve rods of 12 mm diameter on a
  circle of radius 51 mm, insulator-sleeve length 30 mm) and a test proves
  the model reproduces every one of them. Reproducing a printed dimension is
  an anchor, never a claim about that machine.
- **Kernel library pin**: the manifest block `kernel_library` lists the four
  geometry kernels, the placement kernel and the numerics kernel at one
  commit and inventory digest; the contract test proves the manifest, the
  `pyproject.toml` dependency, the Rust crate revision, the lock file, the
  installed library version and the CI install steps name one commit.
- **Device model** (`DeviceModel3D`, `scpn.dense-plasma-focus-3d-model.v1`
  `1.0.0`): `6 + N` bodies in the fixed order of `body_names(N)` with
  declared roles and materials; every cathode rod is a cylinder whose centre
  lies on the cathode circle to `1e-12`, whose axial extent is the cathode
  length and whose neighbours are further apart than twice its radius;
  refusal of a rod that reaches the insulator sleeve and of a rod set that
  would intersect; the sleeve starts at the anode surface, stays inside the
  cathode radius and ends before the anode does; the rod cage fits the
  chamber bore;
  the back wall and the end wall cap the chamber at both ends; the pinch
  column stands exactly where the anode ends and stays inside the chamber;
  every body volume converges on its analytic cylinder or tube; refusal of a
  sleeve that reaches the cathode, a cathode wider than the chamber bore, a
  sleeve longer than the anode, an anode longer than the chamber, a column
  not inside the anode radius, a column leaving the chamber, and non-finite
  or non-positive column dimensions; the fixed body inventory; determinism;
  canonical bytes with one pinned reference digest (segments = 8).
- **Exports**: the device-side provenance record (`glb_extras`: schema, both
  source digests, model digest, pinch radius and length, rod count, segment
  count, units, non-claims) is exactly what the library's GLB carries as document
  `extras`; the bytes are proven identical to the library serialisers called
  directly; the binary STL and glTF 2.0 binary layouts are read back with
  minimal specification-level readers; determinism; the file writers.
- **Native parity**: `tests/test_geometry_native_parity.py` builds every
  device body, rods included, on the library's Python floor and compares float64 bit
  patterns of every vertex coordinate, the face index streams, the signed
  volume and the surface area against the library's native module
  (`scpn_reactor_kernels_native`); the consumer inherits the library's parity
  rather than re-proving the kernels. The crate in `rust/` carries physics
  only and is unchanged by this capability.
- **Benchmark**: `benchmarks/device_model_3d.py` per the ecosystem benchmark
  standard, measuring the library's Python floor (through the validated
  device build) against the library's native kernels; results in
  `docs/benchmarks.md` and the committed local artefact
  `benchmarks/results/device_model_3d.local.json`.

Bounded claims — what is NOT claimed:

- The bodies are analytic surfaces of a declared design: no B-rep solid, no
  compression boundary, no engineering model. The plasma body is the declared
  pinch column of the level-0 models standing on the anode tip, not a
  computed compression boundary, and it is drawn at one instant, not swept
  through the phases the model integrates.
- The rods are straight cylinders: their mounting into the back-wall plate,
  any taper or chamfer, and the insulator end fittings are not modelled, and
  neither are gas ports, diagnostic windows, the collector plate or supports.
- No material property, load, field, thermal or neutronic quantity is
  carried; the material tokens are declarations only.
- The tessellation is exact only as an inscribed polygonal prism: every
  volume and area is below the analytic value by the declared deficit, and
  that deficit is measured, not assumed.
- No value describes, approximates or validates any real machine; the
  benchmark measures tessellation cost of two implementations of the same
  kernels, not physics.
- Maturity stays `computational_prototype`.
