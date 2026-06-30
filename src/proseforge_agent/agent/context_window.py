"""Context window token budgeting and compaction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..llm import Message


DEFAULT_PROVIDER_LIMITS = {
    "fake": 4096,
    "openai": 128000,
    "anthropic": 200000,
    "gemini": 1000000,
}


@dataclass(frozen=True)
class ContextUsageReport:
    """Token budget report before constructing a provider prompt."""

    provider: str
    max_context_tokens: int
    prompt_tokens: int
    evidence_tokens: int
    reserve_tokens: int
    evidence_budget_tokens: int
    remaining_tokens: int
    truncated_evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContextWindowManager:
    """Estimate prompt usage, truncate evidence, and summarize old messages."""

    def __init__(self, provider_limits: dict[str, int] | None = None) -> None:
        self.provider_limits = {**DEFAULT_PROVIDER_LIMITS, **dict(provider_limits or {})}

    def estimate_tokens(self, text: str) -> int:
        return len(str(text).split())

    def status(
        self,
        *,
        provider: str,
        messages: list[Message],
        evidence: list[dict[str, Any]] | None = None,
        reserve_tokens: int = 256,
        max_context_tokens: int | None = None,
    ) -> ContextUsageReport:
        max_tokens = max_context_tokens or self.provider_limits.get(provider, DEFAULT_PROVIDER_LIMITS["fake"])
        prompt_tokens = sum(self.estimate_tokens(message.content) for message in messages)
        evidence_budget = max(0, max_tokens - prompt_tokens - reserve_tokens)
        included_evidence = 0
        truncated: list[str] = []
        for item in evidence or []:
            item_tokens = self.estimate_tokens(str(item.get("text", "")))
            if included_evidence + item_tokens > evidence_budget:
                truncated.append(str(item.get("id") or "evidence"))
                continue
            included_evidence += item_tokens
        remaining = max(0, max_tokens - prompt_tokens - included_evidence - reserve_tokens)
        return ContextUsageReport(
            provider=provider,
            max_context_tokens=max_tokens,
            prompt_tokens=prompt_tokens,
            evidence_tokens=included_evidence,
            reserve_tokens=reserve_tokens,
            evidence_budget_tokens=evidence_budget,
            remaining_tokens=remaining,
            truncated_evidence_ids=truncated,
        )

    def compact_messages(self, messages: list[Message], *, keep_last: int = 6) -> list[Message]:
        if keep_last < 0:
            keep_last = 0
        if len(messages) <= keep_last:
            return list(messages)
        early = messages[: len(messages) - keep_last]
        tail = messages[-keep_last:] if keep_last else []
        summary_text = "summary: " + " | ".join(
            f"{message.role}: {message.content}" for message in early
        )
        return [Message(role="system", content=summary_text), *tail]


__all__ = ["ContextUsageReport", "ContextWindowManager", "DEFAULT_PROVIDER_LIMITS"]
