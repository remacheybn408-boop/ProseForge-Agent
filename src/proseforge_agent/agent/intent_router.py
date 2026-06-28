"""Deterministic intent router for chat modes."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import ConfigurationError
from .modes import CONVERSATION_MODES


@dataclass(frozen=True)
class IntentDecision:
    """Intent metadata returned to the Agent Kernel."""

    name: str
    confidence: float
    reason: str
    required_permission: str
    target_tool: str | None = None
    mode_after_turn: str | None = None


class IntentRouter:
    """Classify user text into stable agent intents without side effects."""

    def classify(
        self,
        text: str,
        *,
        mode: str,
        project_slug: str | None = None,
    ) -> IntentDecision:
        if mode not in CONVERSATION_MODES:
            raise ConfigurationError(f"unknown conversation mode {mode!r}")

        normalized = " ".join(text.lower().split())

        if "switch" in normalized and "project" in normalized:
            if not project_slug:
                return IntentDecision(
                    name="ask_clarifying_question",
                    confidence=0.9,
                    reason="project slug required before switching to project_chat",
                    required_permission="read_only",
                )
            return IntentDecision(
                name="switch_mode",
                confidence=0.95,
                reason="user requested project chat mode",
                required_permission="read_only",
                mode_after_turn="project_chat",
            )

        if mode == "operator_chat":
            if self._mentions_provider_diagnosis(normalized, text):
                return IntentDecision(
                    name="diagnose_installation",
                    confidence=0.95,
                    reason="provider or key installation diagnosis requested",
                    required_permission="read_only",
                    target_tool="install.doctor",
                )
            if "configure provider" in normalized or "setup provider" in normalized:
                return IntentDecision(
                    name="configure_provider",
                    confidence=0.9,
                    reason="provider configuration requested",
                    required_permission="draft_write",
                    target_tool="provider.configure",
                )

        if mode == "workflow_chat":
            if "continue" in normalized or "resume" in normalized or "继续" in text:
                return IntentDecision(
                    name="continue_workflow",
                    confidence=0.95,
                    reason="workflow continuation requested",
                    required_permission="project_write",
                    target_tool="workflow.continue",
                )
            if "start" in normalized or "run workflow" in normalized:
                return IntentDecision(
                    name="start_workflow",
                    confidence=0.9,
                    reason="workflow start requested",
                    required_permission="draft_write",
                    target_tool="workflow.start",
                )

        if mode == "project_chat" and self._needs_project_context(normalized, text):
            return IntentDecision(
                name="retrieve_context",
                confidence=0.9,
                reason="project question needs context",
                required_permission="read_only",
            )

        if mode == "creative_chat" and self._mentions_memory_candidate(normalized):
            return IntentDecision(
                name="update_memory_candidate",
                confidence=0.9,
                reason="creative preference should become a memory candidate",
                required_permission="draft_write",
                target_tool="memory.add_candidate",
            )

        if "explain" in normalized and ("report" in normalized or "artifact" in normalized):
            return IntentDecision(
                name="explain_artifact",
                confidence=0.85,
                reason="artifact explanation requested",
                required_permission="read_only",
            )

        if self._ambiguous_write(normalized):
            return IntentDecision(
                name="ask_clarifying_question",
                confidence=0.7,
                reason="ambiguous write request needs target and permission",
                required_permission="read_only",
            )

        return IntentDecision(
            name="answer_directly",
            confidence=0.8,
            reason="safe direct answer fallback",
            required_permission="read_only",
        )

    @staticmethod
    def _mentions_provider_diagnosis(normalized: str, original: str) -> bool:
        return (
            "provider" in normalized
            and ("key" in normalized or "install" in normalized or "读不到" in original)
        )

    @staticmethod
    def _needs_project_context(normalized: str, original: str) -> bool:
        return any(token in normalized for token in ("today", "yesterday", "where did")) or any(
            token in original for token in ("今天", "昨天", "写到")
        )

    @staticmethod
    def _mentions_memory_candidate(normalized: str) -> bool:
        return "remember" in normalized or "prefer" in normalized or "style preference" in normalized

    @staticmethod
    def _ambiguous_write(normalized: str) -> bool:
        return normalized in {"write it", "write"} or normalized.startswith("write ")


__all__ = ["IntentDecision", "IntentRouter"]
