"""Per-turn Agent Kernel.

The kernel is deliberately dependency-injected. It orchestrates providers,
tools, retrieval, sessions, and memory candidates without importing concrete
workflow or tool implementations.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from ..llm import Message, ProviderRequest, StreamChunk
from ..llm.streaming import iter_stream
from .types import AgentIntent, AgentTurnRequest, AgentTurnResult, ToolCallResult


_PERMISSION_ORDER = {
    "read_only": 0,
    "draft_write": 1,
    "project_write": 2,
    "engine_write": 3,
    "system_write": 4,
}


class AgentKernel:
    """Run one agent turn through classification, retrieval, tools, and provider."""

    def __init__(
        self,
        *,
        provider,
        tools=None,
        session_store=None,
        retrieval=None,
        intent_router=None,
        safety=None,
    ) -> None:
        self._provider = provider
        self._tools = tools
        self._session_store = session_store
        self._retrieval = retrieval
        self._intent_router = intent_router
        self._safety = safety

    def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        trace_id = f"trace-{uuid4().hex[:12]}"
        events: list[dict[str, Any]] = [
            {
                "type": "turn_started",
                "trace_id": trace_id,
                "session_id": request.session_id,
                "mode": request.mode,
            }
        ]
        self._ensure_session(request)
        self._append_message(request.session_id, "user", request.text)

        intent = self._classify(request)
        evidence = self._retrieve_if_needed(request, intent, events, trace_id)
        evidence_refs = [item["id"] for item in evidence if "id" in item]

        effective_ceiling = self._assess_safety(request, evidence, events, trace_id)

        memory_ids = self._save_memory_if_needed(
            request, intent, events, trace_id, effective_ceiling
        )

        if intent.target_tool:
            return self._run_tool(
                request=request,
                intent=intent,
                events=events,
                trace_id=trace_id,
                evidence_refs=evidence_refs,
                memory_ids=memory_ids,
                permission_level=effective_ceiling,
            )

        text = self._call_provider(request, intent, events, trace_id, evidence_refs)
        self._append_message(request.session_id, "assistant", text)
        self._record_events(events)
        return AgentTurnResult(
            text=text,
            intent=intent,
            evidence_refs=evidence_refs,
            memory_candidate_ids=memory_ids,
            events=events,
            trace_id=trace_id,
        )

    def run_turn_stream(self, request: AgentTurnRequest) -> "Iterator[StreamChunk]":
        """Yield a turn's answer incrementally as :class:`StreamChunk` pieces.

        Classification, retrieval, safety, and memory behave exactly as in
        :meth:`run_turn`. Tool turns yield their result as one terminal chunk.
        Provider answers stream chunk-by-chunk; the joined text is saved to the
        transcript exactly as the non-streaming path would (with the trace line).
        If the stream is interrupted, the partial response is saved with a marker.
        """
        trace_id = f"trace-{uuid4().hex[:12]}"
        events: list[dict[str, Any]] = [
            {
                "type": "turn_started",
                "trace_id": trace_id,
                "session_id": request.session_id,
                "mode": request.mode,
            }
        ]
        self._ensure_session(request)
        self._append_message(request.session_id, "user", request.text)

        intent = self._classify(request)
        evidence = self._retrieve_if_needed(request, intent, events, trace_id)
        evidence_refs = [item["id"] for item in evidence if "id" in item]
        effective_ceiling = self._assess_safety(request, evidence, events, trace_id)
        self._save_memory_if_needed(request, intent, events, trace_id, effective_ceiling)

        if intent.target_tool:
            result = self._run_tool(
                request=request,
                intent=intent,
                events=events,
                trace_id=trace_id,
                evidence_refs=evidence_refs,
                memory_ids=[],
                permission_level=effective_ceiling,
            )
            yield StreamChunk(text=result.text, done=True, index=0)
            return

        content = request.text
        if evidence_refs:
            content = f"{request.text}\nEvidence refs: {', '.join(evidence_refs)}"
        provider_request = ProviderRequest(
            role="planner" if intent.name == "retrieve_context" else "drafter",
            messages=[Message(role="user", content=content)],
        )

        pieces: list[str] = []
        index = 0
        try:
            for chunk in iter_stream(self._provider, provider_request):
                pieces.append(chunk.text)
                index = chunk.index
                yield chunk
        except Exception as exc:  # noqa: BLE001 - save partial, never crash the turn
            marker = f"\n[stream-interrupted: {exc}]"
            pieces.append(marker)
            events.append(
                {"type": "stream_interrupted", "trace_id": trace_id, "error": str(exc)}
            )
            saved = "".join(pieces) + f"\nTrace: {trace_id}"
            self._append_message(request.session_id, "assistant", saved)
            self._record_events(events)
            yield StreamChunk(text=marker, done=True, index=index + 1)
            return

        events.append(
            {
                "type": "provider_call",
                "trace_id": trace_id,
                "provider": getattr(self._provider, "name", ""),
                "model": getattr(self._provider, "model", ""),
            }
        )
        saved = "".join(pieces) + f"\nTrace: {trace_id}"
        self._append_message(request.session_id, "assistant", saved)
        self._record_events(events)

    # -- classification -------------------------------------------------

    def _classify(self, request: AgentTurnRequest) -> AgentIntent:
        if self._intent_router is not None:
            return self._intent_router.classify(request.text, mode=request.mode)
        lowered = request.text.lower()
        if "accept chapter" in lowered:
            return AgentIntent(
                name="accept_chapter",
                reason="chapter accept command",
                required_permission="project_write",
                target_tool="chapter.accept",
            )
        if "draft note" in lowered:
            return AgentIntent(
                name="draft_note",
                reason="draft note command",
                required_permission="draft_write",
                target_tool="draft.note",
            )
        if request.project_slug and request.mode == "project_chat" and (
            "today" in lowered or "今天" in request.text or "昨天" in request.text
        ):
            return AgentIntent(
                name="retrieve_context",
                reason="project question needs context",
                required_permission="read_only",
            )
        if "remember" in lowered or "i prefer" in lowered:
            return AgentIntent(
                name="update_memory_candidate",
                reason="durable user preference",
                required_permission="draft_write",
            )
        return AgentIntent(
            name="answer_directly",
            reason="general direct answer",
            required_permission="read_only",
        )

    # -- retrieval / memory --------------------------------------------

    def _retrieve_if_needed(
        self,
        request: AgentTurnRequest,
        intent: AgentIntent,
        events: list[dict[str, Any]],
        trace_id: str,
    ) -> list[dict[str, Any]]:
        if intent.name != "retrieve_context" or self._retrieval is None:
            return []
        evidence = self._retrieval.retrieve(request.project_slug, request.text)
        refs = [item["id"] for item in evidence if "id" in item]
        events.append({"type": "retrieval", "trace_id": trace_id, "refs": refs})
        return list(evidence)

    def _assess_safety(
        self,
        request: AgentTurnRequest,
        evidence: list[dict[str, Any]],
        events: list[dict[str, Any]],
        trace_id: str,
    ) -> str:
        """Return the effective permission ceiling for this turn.

        Retrieved evidence is untrusted: the guard scans it for prompt-injection
        and can only lower the ceiling, never raise it above the session grant.
        With no guard configured the session ceiling is used unchanged.
        """
        if self._safety is None:
            return request.permission_level
        untrusted_text = "\n".join(
            str(item.get("text", "")) for item in evidence if isinstance(item, dict)
        )
        verdict = self._safety.assess(
            untrusted_text,
            provenance="untrusted",
            session_ceiling=request.permission_level,
        )
        events.append(
            {
                "type": "safety_assessment",
                "trace_id": trace_id,
                "provenance": verdict.provenance,
                "allowed_ceiling": verdict.allowed_ceiling,
                "flags": list(verdict.flags),
                "reason": verdict.reason,
            }
        )
        return verdict.allowed_ceiling

    def _save_memory_if_needed(
        self,
        request: AgentTurnRequest,
        intent: AgentIntent,
        events: list[dict[str, Any]],
        trace_id: str,
        permission_level: str,
    ) -> list[str]:
        if intent.name != "update_memory_candidate":
            return []
        if not self._permission_allows(permission_level, "draft_write"):
            events.append({"type": "memory_skipped", "trace_id": trace_id, "reason": "permission"})
            return []
        if self._session_store is None or not hasattr(self._session_store, "save_memory_candidate"):
            return []
        memory_id = self._session_store.save_memory_candidate(request.session_id, request.text)
        events.append({"type": "memory_candidate", "trace_id": trace_id, "id": memory_id})
        return [memory_id]

    # -- execution ------------------------------------------------------

    def _run_tool(
        self,
        *,
        request: AgentTurnRequest,
        intent: AgentIntent,
        events: list[dict[str, Any]],
        trace_id: str,
        evidence_refs: list[str],
        memory_ids: list[str],
        permission_level: str | None = None,
    ) -> AgentTurnResult:
        permission_level = permission_level or request.permission_level
        required = self._tool_permission(intent.target_tool) or intent.required_permission
        if not self._permission_allows(permission_level, required):
            events.append(
                {
                    "type": "permission_denied",
                    "trace_id": trace_id,
                    "tool": intent.target_tool,
                    "required_permission": required,
                }
            )
            text = f"Permission denied for {intent.target_tool}; requires {required}. Trace {trace_id}."
            self._append_message(request.session_id, "assistant", text)
            self._record_events(events)
            return AgentTurnResult(
                text=text,
                intent=intent,
                evidence_refs=evidence_refs,
                memory_candidate_ids=memory_ids,
                events=events,
                trace_id=trace_id,
            )
        try:
            output = self._tools.execute(intent.target_tool, {"text": request.text})
        except Exception as exc:  # noqa: BLE001 - turn should recover with trace id
            events.append(
                {
                    "type": "tool_error",
                    "trace_id": trace_id,
                    "tool": intent.target_tool,
                    "error": str(exc),
                }
            )
            text = f"Tool {intent.target_tool} failed. Trace {trace_id}."
            self._append_message(request.session_id, "assistant", text)
            self._record_events(events)
            return AgentTurnResult(
                text=text,
                intent=intent,
                tool_calls=[
                    ToolCallResult(
                        name=intent.target_tool or "",
                        status="failed",
                        error=str(exc),
                    )
                ],
                evidence_refs=evidence_refs,
                memory_candidate_ids=memory_ids,
                events=events,
                trace_id=trace_id,
            )
        events.append({"type": "tool_call", "trace_id": trace_id, "tool": intent.target_tool})
        text = f"Tool {intent.target_tool} completed. Trace {trace_id}."
        self._append_message(request.session_id, "assistant", text)
        self._record_events(events)
        return AgentTurnResult(
            text=text,
            intent=intent,
            tool_calls=[
                ToolCallResult(
                    name=intent.target_tool or "",
                    status="ok",
                    output=output,
                )
            ],
            evidence_refs=evidence_refs,
            memory_candidate_ids=memory_ids,
            events=events,
            trace_id=trace_id,
        )

    def _call_provider(
        self,
        request: AgentTurnRequest,
        intent: AgentIntent,
        events: list[dict[str, Any]],
        trace_id: str,
        evidence_refs: list[str],
    ) -> str:
        content = request.text
        if evidence_refs:
            content = f"{request.text}\nEvidence refs: {', '.join(evidence_refs)}"
        provider_request = ProviderRequest(
            role="planner" if intent.name == "retrieve_context" else "drafter",
            messages=[Message(role="user", content=content)],
        )
        try:
            result = self._provider.generate(provider_request)
        except Exception as exc:  # noqa: BLE001 - preserve turn with trace id
            events.append(
                {
                    "type": "provider_error",
                    "trace_id": trace_id,
                    "provider": getattr(self._provider, "name", ""),
                    "error": str(exc),
                }
            )
            return f"Provider failed; trace {trace_id}."
        events.append(
            {
                "type": "provider_call",
                "trace_id": trace_id,
                "provider": result.provider,
                "model": result.model,
            }
        )
        return f"{result.text}\nTrace: {trace_id}"

    # -- persistence helpers -------------------------------------------

    def _ensure_session(self, request: AgentTurnRequest) -> None:
        if self._session_store is not None and hasattr(self._session_store, "ensure_session"):
            self._session_store.ensure_session(request.session_id, request.mode, request.project_slug)

    def _append_message(self, session_id: str, role: str, content: str) -> None:
        if self._session_store is not None and hasattr(self._session_store, "append_message"):
            self._session_store.append_message(session_id, role, content)

    def _record_events(self, events: list[dict[str, Any]]) -> None:
        if self._session_store is None or not hasattr(self._session_store, "record_event"):
            return
        for event in events:
            try:
                self._session_store.record_event(event)
            except Exception:  # noqa: BLE001 - event persistence must not crash the turn
                continue

    def _tool_permission(self, tool_name: str | None) -> str | None:
        if tool_name and self._tools is not None and hasattr(self._tools, "required_permission"):
            return self._tools.required_permission(tool_name)
        return None

    @staticmethod
    def _permission_allows(actual: str, required: str) -> bool:
        return _PERMISSION_ORDER.get(actual, -1) >= _PERMISSION_ORDER.get(required, 0)


__all__ = ["AgentKernel"]
