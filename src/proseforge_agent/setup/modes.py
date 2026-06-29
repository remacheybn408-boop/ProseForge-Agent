"""Setup mode selection for the guided installer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SetupMode(str, Enum):
    """Supported guided setup modes."""

    QUICK = "quick"
    FULL = "full"
    MINIMAL = "minimal"
    NON_INTERACTIVE = "non_interactive"


@dataclass(frozen=True)
class SetupModeContract:
    """Operator-visible behavior for one setup mode."""

    mode: SetupMode
    label: str
    description: str
    provider_order: tuple[str, ...]
    steps: tuple[str, ...]
    requires_network: bool
    requires_api_key: bool


PROVIDER_ORDER: tuple[str, ...] = (
    "deepseek",
    "qwen",
    "glm",
    "doubao",
    "openai",
    "anthropic",
    "gemini",
    "fake",
)


SETUP_MODE_CONTRACTS: dict[SetupMode, SetupModeContract] = {
    SetupMode.QUICK: SetupModeContract(
        mode=SetupMode.QUICK,
        label="Quick",
        description="Fast setup for ordinary users with a recommended provider and fake fallback.",
        provider_order=PROVIDER_ORDER,
        steps=("workspace", "provider", "secret_reference", "doctor"),
        requires_network=False,
        requires_api_key=False,
    ),
    SetupMode.FULL: SetupModeContract(
        mode=SetupMode.FULL,
        label="Full",
        description="Guided configuration for workspace, provider, model, base URL, key storage, shell, and doctor.",
        provider_order=PROVIDER_ORDER,
        steps=(
            "workspace",
            "provider",
            "model",
            "base_url",
            "key_storage",
            "shell_completion",
            "doctor",
        ),
        requires_network=False,
        requires_api_key=False,
    ),
    SetupMode.MINIMAL: SetupModeContract(
        mode=SetupMode.MINIMAL,
        label="Minimal",
        description="Zero-key offline validation with only the fake provider enabled.",
        provider_order=("fake",),
        steps=("workspace", "fake_provider", "doctor"),
        requires_network=False,
        requires_api_key=False,
    ),
    SetupMode.NON_INTERACTIVE: SetupModeContract(
        mode=SetupMode.NON_INTERACTIVE,
        label="Non-interactive",
        description="Use environment/defaults without opening prompts.",
        provider_order=PROVIDER_ORDER,
        steps=("workspace", "provider", "secret_reference", "doctor"),
        requires_network=False,
        requires_api_key=False,
    ),
}


CHOICE_TO_MODE: dict[str, SetupMode] = {
    "1": SetupMode.QUICK,
    "quick": SetupMode.QUICK,
    "2": SetupMode.FULL,
    "full": SetupMode.FULL,
    "3": SetupMode.MINIMAL,
    "minimal": SetupMode.MINIMAL,
}


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


def resolve_mode_choice(choice: str) -> SetupMode:
    normalized = str(choice).strip().lower()
    if normalized not in CHOICE_TO_MODE:
        raise ValueError(f"unknown setup mode choice {choice!r}")
    return CHOICE_TO_MODE[normalized]


def mode_menu_lines() -> str:
    return "\n".join(
        [
            "[1] Quick",
            "[2] Full",
            "[3] Minimal",
        ]
    )


__all__ = [
    "PROVIDER_ORDER",
    "SETUP_MODE_CONTRACTS",
    "SetupMode",
    "SetupModeContract",
    "mode_from_flags",
    "mode_menu_lines",
    "resolve_mode_choice",
]
