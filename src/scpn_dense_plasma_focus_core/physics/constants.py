# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — physical constants of the level-0 models

"""Physical constants shared by the level-0 models, in SI units.

Each constant states its edition. The Boltzmann constant and the
elementary charge are exact 2019 SI values. The vacuum permeability is the
pre-2019 convention ``4 pi x 10^-7`` H/m, which CODATA 2018 exceeds by
about ``5.4 x 10^-10`` relative and CODATA 2022 undercuts by about
``1.3 x 10^-10``. The proton mass is the CODATA 2018 value; CODATA 2022 is
about ``1.4 x 10^-9`` relative higher. The molar gas constant is the exact
product ``N_A k`` rounded to ten significant figures, about
``1.8 x 10^-11`` relative below it. The sources round much further (the
review writes the reciprocal proton mass as ``6e26`` and the molar gas
constant as ``8e3`` J kmol^-1 K^-1); each use site states the source's
rounding so the difference is visible. Nothing here describes a device.
"""

from __future__ import annotations

import math
from typing import Final

#: Vacuum permeability ``4e-7 pi``: the pre-2019 SI convention (see the module text).
MU0: Final = 4.0e-7 * math.pi
#: Proton mass in kilograms (CODATA 2018); the sources scale ion masses by it.
PROTON_MASS_KG: Final = 1.67262192369e-27
#: Boltzmann constant in joules per kelvin (exact SI 2019 value).
BOLTZMANN_J_PER_K: Final = 1.380649e-23
#: Elementary charge in coulombs (exact SI 2019 value).
ELEMENTARY_CHARGE_C: Final = 1.602176634e-19
#: Molar gas constant in J kmol^-1 K^-1, ``N_A k`` to ten figures (review: ``8e3``).
MOLAR_GAS_CONSTANT_J_PER_KMOL_K: Final = 8314.462618
#: Pascals per torr as the exact quotient ``101325 / 760``.
PASCAL_PER_TORR: Final = 101325.0 / 760.0
#: ``pi`` as the correctly rounded double.
PI: Final = math.pi
#: ``1 / e`` as the correctly rounded double (the surface-emission threshold).
INV_E: Final = 0.36787944117144233
