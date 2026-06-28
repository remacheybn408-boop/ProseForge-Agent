"""Prompt protocol for chat turns."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..agent.modes import CONVERSATION_MODES
from ..errors import ConfigurationError


_MODE_SYSTEM = {
    "general_chat": "general_chat: answer directly with concise reasoning.",
    "project_chat": "project_chat: use project canon only when it is supplied.",
    "workflow_chat": "workflow_chat: explain workflow intent without starting side effects.",
    "operator_chat": "operator_chat: help diagnose setup, providers, and permissions.",
    "creative_chat": "creative_chat: generate ideas while separating suggestions from canon.",
}


@dataclass(frozen=True)
class PromptItem:
    """One evidence item included in a prompt section."""

    kind: str
    text: str
    id: str = ""
    source: str = ""


@dataclass(frozen=True)
class PromptPack:
    """Structured prompt components sent to a chat provider."""

    mode: str
    system: str
    user: str
    project_slug: str | None = None
    canon: list[PromptItem] = field(default_factory=list)
    suggestions: list[PromptItem] = field(default_factory=list)

    def render_markdown(self) -> str:
        """Render a human-readable prompt pack for CLI inspection."""
        lines = [
            "# Prompt Pack",
            "",
            f"- mode: {self.mode}",
            f"- project: {self.project_slug or '(none)'}",
            "",
            "## System",
            self.system,
            "",
            "## Canon",
            *self._render_items(self.canon),
            "",
            "## Suggestions",
            *self._render_items(self.suggestions),
            "",
            "## User",
            self.user,
        ]
        return "\n".join(lines).rstrip() + "\n"

    def to_dict(self) -> dict[str, Any]:
        """Return stable JSON-compatible prompt data."""
        return {
            "mode": self.mode,
            "system": self.system,
            "user": self.user,
            "project_slug": self.project_slug,
            "canon": [asdict(item) for item in self.canon],
            "suggestions": [asdict(item) for item in self.suggestions],
        }

    @staticmethod
    def _render_items(items: list[PromptItem]) -> list[str]:
        if not items:
            return ["_(none)_"]
        lines = []
        for item in items:
            prefix = f"[{item.id}] " if item.id else ""
            lines.append(f"- {prefix}{item.text}")
        return lines


class ChatPromptBuilder:
    """Build prompt packs from mode, user text, and optional evidence."""

    def build(
        self,
        *,
        text: str,
        mode: str,
        project_slug: str | None = None,
        evidence_pack: dict[str, Any] | None = None,
    ) -> PromptPack:
        if mode not in CONVERSATION_MODES:
            raise ConfigurationError(f"unknown conversation mode {mode!r}")
        evidence_pack = evidence_pack or {}
        return PromptPack(
            mode=mode,
            system=_MODE_SYSTEM[mode],
            user=text,
            project_slug=project_slug,
            canon=self._items(evidence_pack.get("canon", []), kind="canon"),
            suggestions=self._items(evidence_pack.get("suggestions", []), kind="suggestion"),
        )

    @staticmethod
    def _items(raw_items: list[Any], *, kind: str) -> list[PromptItem]:
        items: list[PromptItem] = []
        for raw in raw_items:
            if isinstance(raw, str):
                items.append(PromptItem(kind=kind, text=raw))
                continue
            if isinstance(raw, dict):
                items.append(
                    PromptItem(
                        kind=kind,
                        id=str(raw.get("id", "")),
                        text=str(raw.get("text", "")),
                        source=str(raw.get("source", "")),
                    )
                )
        return items


__all__ = ["ChatPromptBuilder", "PromptItem", "PromptPack"]
