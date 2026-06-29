"""Canonical, deterministic, network-free fakes shared across tests.

These are the single authoritative doubles for cross-module contract and golden
tests. They satisfy the same shapes as the real subsystems:

* :class:`FakeProvider` reuses the production :class:`proseforge_agent.llm.fake.FakeProvider`
  (so it can never drift from the real ``LLMProvider`` contract) and only adds
  zero-argument defaults.
* :class:`FakeTools`, :class:`FakeSessionStore`, :class:`FakeRetrieval`, and
  :class:`FakeKernel` mirror the registry / session / retrieval / kernel
  interfaces the Agent Kernel depends on.
* :class:`FakeHTTP` reuses the production :class:`FakeHttpTransport`.

Cards should import these instead of redefining their own.
"""

from __future__ import annotations

from typing import Any

from ..agent.types import AgentIntent, AgentTurnRequest, AgentTurnResult, ToolCallResult
from ..llm.fake import FakeProvider as _RealFakeProvider
from ..llm.http import FakeHttpTransport


class FakeProvider(_RealFakeProvider):
    """Deterministic provider with zero-argument construction for tests."""

    def __init__(self, name: str = "fake", model: str = "fake-novelist") -> None:
        super().__init__(name=name, model=model)


class FakeTools:
    """Canonical in-memory tool registry double."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.called: list[tuple[str, dict]] = []
        self.permissions = {
            "chapter.accept": "project_write",
            "chapter.run": "draft_write",
            "draft.note": "draft_write",
            "memory.search": "read_only",
        }

    def required_permission(self, name: str) -> str:
        return self.permissions[name]

    def execute(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.called.append((name, payload))
        if self.fail:
            raise RuntimeError("tool failed")
        return {"ok": True, "name": name}

    def list(self) -> list[str]:
        return sorted(self.permissions)


class FakeSessionStore:
    """Canonical session store double recording messages, events, and memory."""

    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []
        self.events: list[dict[str, Any]] = []
        self.memory_candidates: list[dict[str, str]] = []

    def ensure_session(self, session_id: str, mode: str, project_slug: str | None) -> dict:
        return {"session_id": session_id, "mode": mode, "project_slug": project_slug}

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.messages.append({"session_id": session_id, "role": role, "content": content})

    def record_event(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    def save_memory_candidate(self, session_id: str, text: str) -> str:
        memory_id = f"mem-{len(self.memory_candidates) + 1}"
        self.memory_candidates.append({"id": memory_id, "session_id": session_id, "text": text})
        return memory_id


class FakeRetrieval:
    """Canonical retrieval double returning deterministic evidence dicts."""

    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._items = items or [{"id": "ev-1", "text": "昨天写到第二章。"}]

    def retrieve(self, project_slug: str | None, text: str) -> list[dict[str, Any]]:
        self.calls.append({"project_slug": project_slug, "text": text})
        return list(self._items)


class FakeKernel:
    """Canonical single-turn kernel double.

    ``scripted`` supplies per-turn response text; once exhausted it echoes the
    request. ``done_marker`` lets a caller (e.g. the autonomous loop) detect goal
    satisfaction deterministically. The kernel never mutates itself between turns.
    """

    def __init__(
        self,
        scripted: list[str] | None = None,
        *,
        done_marker: str = "[[done]]",
    ) -> None:
        self._scripted = list(scripted or [])
        self.done_marker = done_marker
        self.calls: list[AgentTurnRequest] = []

    def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        index = len(self.calls)
        self.calls.append(request)
        if index < len(self._scripted):
            text = self._scripted[index]
        else:
            text = f"step {index + 1}: {request.text}"
        return AgentTurnResult(
            text=text,
            intent=AgentIntent(name="answer_directly", reason="fake kernel turn"),
            tool_calls=[ToolCallResult(name="noop", status="ok")],
            evidence_refs=[],
            events=[{"type": "turn_started", "trace_id": f"trace-{index + 1}"}],
            trace_id=f"trace-{index + 1}",
        )


# Reuse the production offline transport as the canonical HTTP fake.
FakeHTTP = FakeHttpTransport


__all__ = [
    "FakeProvider",
    "FakeTools",
    "FakeSessionStore",
    "FakeRetrieval",
    "FakeKernel",
    "FakeHTTP",
]
