# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — physical constants of the level-0 models

"""Physical constants shared by the level-0 models, in SI units.

The exact SI 2019 values are used where the sources round them (the
review writes the reciprocal proton mass as ``6e26`` and the molar gas
constant as ``8e3`` J kmol^-1 K^-1); each use site states the source's
rounding so the difference is visible. Nothing here describes a device.
"""

from __future__ import annotations

import math
from typing import Final

#: Vacuum permeability ``4e-7 pi`` (evaluated exactly as the native kernel does).
MU0: Final = 4.0e-7 * math.pi
#: Proton mass in kilograms; the sources scale ion and molecule masses by it.
PROTON_MASS_KG: Final = 1.67262192369e-27
#: Boltzmann constant in joules per kelvin (exact SI 2019 value).
BOLTZMANN_J_PER_K: Final = 1.380649e-23
#: Elementary charge in coulombs (exact SI 2019 value).
ELEMENTARY_CHARGE_C: Final = 1.602176634e-19
#: Molar gas constant in J kmol^-1 K^-1 (the review rounds it to ``8e3``).
MOLAR_GAS_CONSTANT_J_PER_KMOL_K: Final = 8314.462618
#: Pascals per torr as the exact quotient ``101325 / 760``.
PASCAL_PER_TORR: Final = 101325.0 / 760.0
#: ``pi`` as the correctly rounded double.
PI: Final = math.pi
#: ``1 / e`` as the correctly rounded double (the surface-emission threshold).
INV_E: Final = 0.36787944117144233
