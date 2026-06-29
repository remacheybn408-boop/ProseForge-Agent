"""Setup mode selection for the guided installer."""

from __future__ import annotations

from enum import Enum


class SetupMode(str, Enum):
    """Supported guided setup modes."""

    QUICK = "quick"
    FULL = "full"
    MINIMAL = "minimal"
    NON_INTERACTIVE = "non_interactive"


def mode_from_flags(
    *,
    quick: bool = False,
    full: bool = False,
    minimal: bool = False,
    non_interactive: bool = False,
) -> SetupMode:
    if minimal:
        return SetupMode.MINIMAL
    if full:
        return SetupMode.FULL
    if non_interactive:
        return SetupMode.NON_INTERACTIVE
    if quick:
        return SetupMode.QUICK
    return SetupMode.QUICK


__all__ = ["SetupMode", "mode_from_flags"]
