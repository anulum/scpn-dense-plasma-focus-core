# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — level-0 device physics package

"""Level-0 device physics of the dense-plasma-focus family.

The closed forms of the Lee model (Lee 2014; Saw and Lee in
IAEA-TECDOC-1829; Lee, ICTP 2012) evaluated on the validated device
configuration: bank normalisation and scaling parameters, fill state,
axial and radial characteristic quantities, slug relations, rule-of-thumb
pinch geometry, pinch-phase density, Bennett temperature and power terms,
the fast-ion-beam chain, the beam-target yield and the empirical scaling
law. Every function is a closed-form evaluation; no phase is integrated
and no value describes a real machine. Design record: ADR 0005.
"""

from __future__ import annotations

from scpn_dense_plasma_focus_core.physics._transcendental import (
    exponential,
    natural_log,
    power,
)
from scpn_dense_plasma_focus_core.physics.axial import (
    AxialCharacteristics,
    axial_characteristics,
)
from scpn_dense_plasma_focus_core.physics.bank import (
    BankNormalisation,
    FillState,
    bank_normalisation,
    fill_state,
)
from scpn_dense_plasma_focus_core.physics.beam import (
    FLUX_COEFFICIENT,
    FastIonBeam,
    fast_ion_beam,
)
from scpn_dense_plasma_focus_core.physics.constants import (
    BOLTZMANN_J_PER_K,
    ELEMENTARY_CHARGE_C,
    MU0,
    PASCAL_PER_TORR,
    PROTON_MASS_KG,
)
from scpn_dense_plasma_focus_core.physics.level0 import (
    BANK_ENERGY_CONSISTENCY,
    LEVEL0_NON_CLAIMS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    level0_physics,
    require_fraction,
)
from scpn_dense_plasma_focus_core.physics.neutron import (
    BEAM_TARGET_CONSTANT,
    SCALING_COEFFICIENT,
    SCALING_EXPONENT,
    SCALING_RANGE_A,
    NeutronEstimates,
    beam_target_yield,
    scaling_law_applies,
    scaling_law_yield,
)
from scpn_dense_plasma_focus_core.physics.pinch import (
    PinchRadiation,
    PinchState,
    diode_voltage_rule,
    pinch_radiation,
)
from scpn_dense_plasma_focus_core.physics.radial import (
    REFLECTED_SHOCK_FRACTION,
    RULE_MAX_LENGTH_RATIO,
    RULE_MAX_LENGTH_RATIO_BOUNDS,
    RULE_MIN_RADIUS_RATIO,
    RULE_MIN_RADIUS_RATIO_BOUNDS,
    RULE_PINCH_DURATION_BOUNDS_S_PER_M,
    PinchGeometryEstimate,
    RadialCharacteristics,
    SlugRelations,
    pinch_geometry_estimate,
    radial_characteristics,
    require_specific_heat_ratio,
    slug_relations,
)

__all__ = [
    "BANK_ENERGY_CONSISTENCY",
    "BEAM_TARGET_CONSTANT",
    "BOLTZMANN_J_PER_K",
    "ELEMENTARY_CHARGE_C",
    "FLUX_COEFFICIENT",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "MU0",
    "PASCAL_PER_TORR",
    "PROTON_MASS_KG",
    "REFLECTED_SHOCK_FRACTION",
    "RULE_MAX_LENGTH_RATIO",
    "RULE_MAX_LENGTH_RATIO_BOUNDS",
    "RULE_MIN_RADIUS_RATIO",
    "RULE_MIN_RADIUS_RATIO_BOUNDS",
    "RULE_PINCH_DURATION_BOUNDS_S_PER_M",
    "SCALING_COEFFICIENT",
    "SCALING_EXPONENT",
    "SCALING_RANGE_A",
    "AxialCharacteristics",
    "BankNormalisation",
    "FastIonBeam",
    "FillState",
    "Level0PhysicsRecord",
    "ModelInputs",
    "NeutronEstimates",
    "PinchGeometryEstimate",
    "PinchRadiation",
    "PinchState",
    "RadialCharacteristics",
    "SlugRelations",
    "axial_characteristics",
    "bank_normalisation",
    "beam_target_yield",
    "diode_voltage_rule",
    "exponential",
    "fast_ion_beam",
    "fill_state",
    "level0_physics",
    "natural_log",
    "pinch_geometry_estimate",
    "pinch_radiation",
    "power",
    "radial_characteristics",
    "require_fraction",
    "require_specific_heat_ratio",
    "scaling_law_applies",
    "scaling_law_yield",
    "slug_relations",
]
