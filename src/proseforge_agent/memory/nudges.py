"""Memory nudge generation from user model candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .user_model import UserModelStore


@dataclass(frozen=True)
class MemoryNudge:
    """Prompt for reviewing a memory candidate without auto-accepting it."""

    candidate_id: str
    reason: str
    suggested_scope: str
    action_choices: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "reason": self.reason,
            "suggested_scope": self.suggested_scope,
            "action_choices": self.action_choices,
        }


class MemoryNudgeGenerator:
    """Generate review prompts for pending user-model candidates."""

    def __init__(self, store: UserModelStore) -> None:
        self.store = store

    def generate(self) -> list[MemoryNudge]:
        nudges: list[MemoryNudge] = []
        for candidate in self.store.candidates():
            reason = "candidate preference may be worth remembering"
            if _has_contradiction(candidate.text, [fact.text for fact in self.store.facts(scope=candidate.scope)]):
                reason = "contradiction with existing user model fact"
            nudges.append(
                MemoryNudge(
                    candidate_id=candidate.id,
                    reason=reason,
                    suggested_scope=candidate.scope,
                    action_choices=["accept", "reject", "keep_pending"],
                )
            )
        return nudges


def _has_contradiction(candidate: str, facts: list[str]) -> bool:
    text = candidate.lower()
    if "english" in text:
        return any("chinese" in fact.lower() for fact in facts)
    if "chinese" in text:
        return any("english" in fact.lower() for fact in facts)
    return False


__all__ = ["MemoryNudge", "MemoryNudgeGenerator"]
