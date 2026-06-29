"""Guided product setup for ProseForge Agent."""

from .config_generator import SetupConfigGenerator, redact_config_text
from .first_run import FirstRunBootstrap, FirstRunVerdict, SETUP_GUIDANCE, is_setup_complete, setup_guidance
from .modes import SETUP_MODE_CONTRACTS, SetupMode, SetupModeContract, mode_from_flags, mode_menu_lines, resolve_mode_choice
from .summary import render_setup_lines
from .wizard import ProviderSetupResult, SetupResult, SetupWizard

__all__ = [
    "ProviderSetupResult",
    "FirstRunBootstrap",
    "FirstRunVerdict",
    "SETUP_GUIDANCE",
    "SETUP_MODE_CONTRACTS",
    "SetupConfigGenerator",
    "SetupMode",
    "SetupModeContract",
    "SetupResult",
    "SetupWizard",
    "is_setup_complete",
    "mode_from_flags",
    "mode_menu_lines",
    "redact_config_text",
    "render_setup_lines",
    "setup_guidance",
    "resolve_mode_choice",
]
