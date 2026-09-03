# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN Dense Plasma Focus Core — device capability model errors

"""Error surface of the device capability models."""

from __future__ import annotations


class DeviceConfigurationError(ValueError):
    """Raised when a device configuration value violates a model invariant.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected.
    """


class DeviceGeometryError(ValueError):
    """Raised when a device geometry or 3D model invariant is violated.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected. Refusals raised
    by the shared kernel library are re-raised under this type with the
    library's message preserved.
    """


class DiagnosticPlanError(ValueError):
    """Raised when a diagnostic or clock declaration violates the model.

    Every rejection carries the offending field and the violated bound in
    its message; nothing is clamped or silently corrected.
    """


class NumericsError(DeviceConfigurationError):
    """Raised when a vendored numerical kernel input leaves its admissible range."""
