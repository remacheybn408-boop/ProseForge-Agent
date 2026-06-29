"""First-run setup guidance helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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


@dataclass(frozen=True)
class FirstRunVerdict:
    """Readiness verdict for commands that need a configured workspace."""

    ready: bool
    reasons: list[str] = field(default_factory=list)
    guidance: str = SETUP_GUIDANCE

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "reasons": list(self.reasons),
            "guidance": self.guidance,
        }


class FirstRunBootstrap:
    """Detect incomplete setup and return concrete recovery guidance."""

    def __init__(self, root: str | Path = ".pf-agent") -> None:
        self.root = Path(root)

    def check(self) -> FirstRunVerdict:
        config_path = self.root / "config.yaml"
        if not config_path.exists():
            return FirstRunVerdict(ready=False, reasons=["config missing"])

        config = _load_config(config_path)
        reasons: list[str] = []
        if not is_setup_complete(config):
            reasons.append("setup.completed is not true")

        workspace = _workspace_path(config, self.root)
        if not workspace.exists():
            reasons.append("workspace missing")

        if not _default_provider_available(config):
            reasons.append("default provider unavailable")

        return FirstRunVerdict(ready=not reasons, reasons=reasons)


def _load_config(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001 - corrupt config should produce setup guidance
        return {}
    return payload if isinstance(payload, dict) else {}


def _workspace_path(config: dict[str, Any], root: Path) -> Path:
    paths = config.get("paths") if isinstance(config.get("paths"), dict) else {}
    workspace = config.get("workspace") if isinstance(config.get("workspace"), dict) else {}
    raw = paths.get("workspace_root") or workspace.get("path")
    if not raw:
        return root / "workspace"
    return Path(str(raw))


def _default_provider_available(config: dict[str, Any]) -> bool:
    llm = config.get("llm") if isinstance(config.get("llm"), dict) else {}
    providers = llm.get("providers") if isinstance(llm.get("providers"), dict) else config.get("providers")
    providers = providers if isinstance(providers, dict) else {}
    default_provider = llm.get("default_provider") or config.get("default_provider") or "fake"
    provider = providers.get(default_provider)
    return isinstance(provider, dict) and bool(provider.get("enabled", True))


__all__ = [
    "FirstRunBootstrap",
    "FirstRunVerdict",
    "SETUP_GUIDANCE",
    "is_setup_complete",
    "setup_guidance",
]
