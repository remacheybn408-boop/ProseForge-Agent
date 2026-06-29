"""First-run setup guidance helpers."""

from __future__ import annotations


SETUP_GUIDANCE = """ProseForge Agent has not been initialized.
Recommended:
  pf-agent setup --quick

Zero-config validation:
  pf-agent setup --minimal

Manual check:
  pf-agent doctor
"""


def setup_guidance() -> str:
    return SETUP_GUIDANCE


def is_setup_complete(config: dict | None) -> bool:
    return bool((config or {}).get("setup", {}).get("completed"))


__all__ = ["SETUP_GUIDANCE", "is_setup_complete", "setup_guidance"]
