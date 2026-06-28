"""Shared Agent Kernel data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentIntent:
    """Kernel-facing intent metadata."""

    name: str
    confidence: float = 1.0
    reason: str = ""
    required_permission: str = "read_only"
    target_tool: str | None = None
    mode_after_turn: str | None = None


@dataclass(frozen=True)
class AgentTurnRequest:
    """Single input object for one agent turn."""

    session_id: str
    text: str
    mode: str
    project_slug: str | None
    permission_level: str


@dataclass(frozen=True)
class ToolCallResult:
    """Machine-readable record of a tool call."""

    name: str
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass(frozen=True)
class AgentTurnResult:
    """Single output object for one agent turn."""

    text: str
    intent: AgentIntent
    tool_calls: list[ToolCallResult] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    memory_candidate_ids: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    trace_id: str = ""


__all__ = [
    "AgentIntent",
    "AgentTurnRequest",
    "AgentTurnResult",
    "ToolCallResult",
]
