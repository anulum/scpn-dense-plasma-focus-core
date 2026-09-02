# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — shared numerics kernels and physical constants

"""Physical constants and the transcendental kernels of the shared library.

The level-0 models use only ``+ - * /`` and ``sqrt`` plus the deterministic
natural logarithm, exponential and real power of the pinned shared kernel
library (``scpn_reactor_kernels.numerics``, kernel
``numerics_transcendental``), never the platform ``math`` module, so the
Python floor and the native crate (which depends on the same library's
Rust crate) agree bit for bit. A domain refusal of the library is
re-raised as :class:`~scpn_dense_plasma_focus_core.errors.NumericsError` with the
library's message. The admissible window of the exponential (``EXP_MIN``,
``EXP_MAX``) is re-exported for the pinch absorption factor. This module
replaces the temporary byte-identical copy that the first level-0 landing
carried (ADR 0006).
"""

from __future__ import annotations

from typing import Final

from scpn_reactor_kernels.errors import NumericsError as LibraryNumericsError
from scpn_reactor_kernels.numerics import EXP_MAX, EXP_MIN
from scpn_reactor_kernels.numerics import exponential as _exponential
from scpn_reactor_kernels.numerics import natural_log as _natural_log
from scpn_reactor_kernels.numerics import power as _power

from scpn_dense_plasma_focus_core.errors import NumericsError

__all__: Final = ["EXP_MAX", "EXP_MIN", "exponential", "natural_log", "power"]


def natural_log(x: float) -> float:
    """Return ``ln x`` by the library kernel.

    Parameters
    ----------
    x
        Positive normal double.

    Returns
    -------
    float
        The natural logarithm.

    Raises
    ------
    NumericsError
        If the library refuses the argument.
    """
    try:
        return _natural_log(x)
    except LibraryNumericsError as exc:
        raise NumericsError(str(exc)) from exc


def exponential(y: float) -> float:
    """Return ``exp y`` by the library kernel.

    Parameters
    ----------
    y
        Argument inside the library's normal-result window.

    Returns
    -------
    float
        The exponential.

    Raises
    ------
    NumericsError
        If the library refuses the argument.
    """
    try:
        return _exponential(y)
    except LibraryNumericsError as exc:
        raise NumericsError(str(exc)) from exc


def power(base: float, exponent: float) -> float:
    """Return ``base ** exponent`` by the library kernel.

    Parameters
    ----------
    base
        Positive normal double.
    exponent
        Real exponent.

    Returns
    -------
    float
        The real power ``exp(exponent ln base)``.

    Raises
    ------
    NumericsError
        If the library refuses the arguments.
    """
    try:
        return _power(base, exponent)
    except LibraryNumericsError as exc:
        raise NumericsError(str(exc)) from exc
