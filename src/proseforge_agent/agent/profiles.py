"""Agent profile and persona registry."""

from __future__ import annotations

from dataclasses import replace, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..errors import ConfigurationError
from .permissions import PERMISSION_LEVELS


_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


@dataclass(frozen=True)
class AgentProfile:
    """Persona, mode, routing, memory, and permission defaults for chat."""

    name: str
    mode: str
    tone: str
    provider_roles: dict[str, str] = field(default_factory=dict)
    memory_scope: str = "global"
    permission_ceiling: str = "read_only"
    prompt_pack: dict[str, Any] = field(default_factory=dict)
    source_permission_ceiling: str = ""

    def clamped(self, session_permission_max: str) -> "AgentProfile":
        """Return this profile with permission no higher than the session max."""
        source = self.permission_ceiling
        profile_index = _ORDER.get(self.permission_ceiling, 0)
        session_index = _ORDER.get(session_permission_max, 0)
        ceiling = self.permission_ceiling
        if session_index < profile_index:
            ceiling = session_permission_max
        return replace(self, permission_ceiling=ceiling, source_permission_ceiling=source)


class AgentProfileRegistry:
    """Registry for built-in and YAML-defined agent profiles."""

    def __init__(self, profiles: dict[str, AgentProfile]) -> None:
        self._profiles = dict(profiles)

    @classmethod
    def builtins(cls) -> "AgentProfileRegistry":
        return cls(
            {
                "writer": AgentProfile(
                    name="writer",
                    mode="creative_chat",
                    tone="generative, concrete, canon-aware",
                    provider_roles={"draft": "drafter", "review": "reviewer"},
                    memory_scope="project",
                    permission_ceiling="draft_write",
                    prompt_pack={"persona": "writer", "focus": "draft"},
                ),
                "editor": AgentProfile(
                    name="editor",
                    mode="project_chat",
                    tone="precise, critical, concise",
                    provider_roles={"review": "reviewer", "plan": "planner"},
                    memory_scope="project",
                    permission_ceiling="project_write",
                    prompt_pack={"persona": "editor", "focus": "revision"},
                ),
                "operator": AgentProfile(
                    name="operator",
                    mode="operator_chat",
                    tone="diagnostic, direct, procedural",
                    provider_roles={"diagnose": "planner", "verify": "reviewer"},
                    memory_scope="global",
                    permission_ceiling="engine_write",
                    prompt_pack={"persona": "operator", "focus": "diagnostics"},
                ),
                "general": AgentProfile(
                    name="general",
                    mode="general_chat",
                    tone="concise, helpful",
                    provider_roles={"chat": "drafter"},
                    memory_scope="global",
                    permission_ceiling="read_only",
                    prompt_pack={"persona": "general", "focus": "answer"},
                ),
            }
        )

    @classmethod
    def from_yaml(cls, path: Path | str) -> "AgentProfileRegistry":
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        raw_profiles = payload.get("profiles") or {}
        profiles: dict[str, AgentProfile] = {}
        for name, data in raw_profiles.items():
            data = data or {}
            profiles[str(name)] = AgentProfile(
                name=str(name),
                mode=str(data.get("mode", "general_chat")),
                tone=str(data.get("tone", "")),
                provider_roles=dict(data.get("provider_roles") or {}),
                memory_scope=str(data.get("memory_scope", "global")),
                permission_ceiling=str(data.get("permission_ceiling", "read_only")),
                prompt_pack=dict(data.get("prompt_pack") or {}),
            )
        return cls(profiles)

    def get(self, name: str) -> AgentProfile:
        try:
            return self._profiles[name]
        except KeyError as exc:
            raise ConfigurationError(f"unknown agent profile: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._profiles)

    def resolve(self, name: str, *, session_permission_max: str) -> AgentProfile:
        return self.get(name).clamped(session_permission_max)


__all__ = ["AgentProfile", "AgentProfileRegistry"]
