"""Middleware hooks for Agent runtime (Task 182).

Middleware CAN change runtime behavior (unlike observer hooks). Middleware is
opt-in per hook, ordered deterministically by registration order, and fails
open: a middleware exception is recorded and the chain continues.

Kinds:
- ``llm_request`` and ``tool_request``: transform *request*/args before policy.
- ``llm_execution`` and ``tool_execution``: wrap the underlying call with
  ``next_call`` semantics.

Downstream policy MUST re-check any rewritten request or tool args — this
module records what was rewritten so the caller can prove the re-check ran.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from .events import _redact
from .tools import ToolResult


MIDDLEWARE_KIND_LLM_REQUEST = "llm_request"
MIDDLEWARE_KIND_LLM_EXECUTION = "llm_execution"
MIDDLEWARE_KIND_TOOL_REQUEST = "tool_request"
MIDDLEWARE_KIND_TOOL_EXECUTION = "tool_execution"

_KINDS = frozenset(
    {
        MIDDLEWARE_KIND_LLM_REQUEST,
        MIDDLEWARE_KIND_LLM_EXECUTION,
        MIDDLEWARE_KIND_TOOL_REQUEST,
        MIDDLEWARE_KIND_TOOL_EXECUTION,
    }
)


@dataclass(frozen=True)
class LLMRequest:
    """Mutable-by-copy LLM request seen by ``llm_request`` middleware."""

    model: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def with_messages(self, messages: list[dict[str, Any]]) -> "LLMRequest":
        return replace(self, messages=list(messages))

    def with_parameters(self, parameters: dict[str, Any]) -> "LLMRequest":
        return replace(self, parameters=dict(parameters))


@dataclass(frozen=True)
class ToolRequest:
    """Mutable-by-copy tool request seen by ``tool_request`` middleware."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def with_arguments(self, arguments: dict[str, Any]) -> "ToolRequest":
        return replace(self, arguments=dict(arguments))

    def with_tool_name(self, tool_name: str) -> "ToolRequest":
        return replace(self, tool_name=tool_name)


@dataclass(frozen=True)
class LLMExecutionContext:
    """Context passed into ``llm_execution`` middleware wrappers."""

    request: LLMRequest


@dataclass(frozen=True)
class ToolExecutionContext:
    """Context passed into ``tool_execution`` middleware wrappers."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MiddlewareTrace:
    """One recorded middleware invocation."""

    kind: str
    name: str
    rewritten: bool
    error: str = ""


@dataclass
class _Entry:
    kind: str
    name: str
    callback: Callable[..., Any]
    enabled: bool


class MiddlewareRegistry:
    """Register ordered middleware and apply them with fail-open semantics."""

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._traces: list[MiddlewareTrace] = []
        self._failures: list[dict[str, str]] = []

    def register(
        self,
        kind: str,
        name: str,
        callback: Callable[..., Any],
        *,
        enabled: bool = False,
    ) -> None:
        if kind not in _KINDS:
            raise ValueError(f"unknown middleware kind {kind!r}")
        self._entries.append(_Entry(kind=kind, name=name, callback=callback, enabled=enabled))

    def enable(self, name: str) -> None:
        for entry in self._entries:
            if entry.name == name:
                entry.enabled = True

    def disable(self, name: str) -> None:
        for entry in self._entries:
            if entry.name == name:
                entry.enabled = False

    def middleware_names(self, kind: str) -> list[str]:
        return [entry.name for entry in self._entries if entry.kind == kind]

    def traces(self) -> list[MiddlewareTrace]:
        return list(self._traces)

    def failures(self) -> list[dict[str, str]]:
        return list(self._failures)

    def apply_llm_request(self, request: LLMRequest) -> LLMRequest:
        current = request
        for entry in self._entries:
            if entry.kind != MIDDLEWARE_KIND_LLM_REQUEST or not entry.enabled:
                continue
            before = current
            try:
                current = entry.callback(before)
            except Exception as exc:
                self._record_failure(entry, exc)
                self._traces.append(MiddlewareTrace(entry.kind, entry.name, rewritten=False, error=str(exc)))
                continue
            self._traces.append(
                MiddlewareTrace(entry.kind, entry.name, rewritten=current != before)
            )
        return current

    def apply_tool_request(self, request: ToolRequest) -> ToolRequest:
        current = request
        for entry in self._entries:
            if entry.kind != MIDDLEWARE_KIND_TOOL_REQUEST or not entry.enabled:
                continue
            before = current
            try:
                current = entry.callback(before)
            except Exception as exc:
                self._record_failure(entry, exc)
                self._traces.append(MiddlewareTrace(entry.kind, entry.name, rewritten=False, error=str(exc)))
                continue
            self._traces.append(
                MiddlewareTrace(entry.kind, entry.name, rewritten=current != before)
            )
        return current

    def apply_llm_execution(
        self,
        context: LLMExecutionContext,
        base_call: Callable[[LLMExecutionContext], Any],
    ) -> Any:
        return self._apply_execution(MIDDLEWARE_KIND_LLM_EXECUTION, context, base_call)

    def apply_tool_execution(
        self,
        context: ToolExecutionContext,
        base_call: Callable[[ToolExecutionContext], ToolResult],
    ) -> ToolResult:
        return self._apply_execution(MIDDLEWARE_KIND_TOOL_EXECUTION, context, base_call)

    def _apply_execution(
        self,
        kind: str,
        context: Any,
        base_call: Callable[[Any], Any],
    ) -> Any:
        wrappers = [entry for entry in self._entries if entry.kind == kind and entry.enabled]

        def build(index: int) -> Callable[[Any], Any]:
            if index >= len(wrappers):
                return base_call
            entry = wrappers[index]

            def call(ctx: Any) -> Any:
                next_call = build(index + 1)
                try:
                    result = entry.callback(ctx, next_call)
                except Exception as exc:
                    self._record_failure(entry, exc)
                    self._traces.append(MiddlewareTrace(entry.kind, entry.name, rewritten=False, error=str(exc)))
                    return next_call(ctx)
                self._traces.append(MiddlewareTrace(entry.kind, entry.name, rewritten=True))
                return result

            return call

        return build(0)(context)

    def _record_failure(self, entry: _Entry, exc: Exception) -> None:
        self._failures.append(
            {"kind": entry.kind, "name": entry.name, "error": str(exc)}
        )


def sanitize_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convenience for callers that persist middleware payloads to disk."""
    return _redact(payload)


__all__ = [
    "LLMExecutionContext",
    "LLMRequest",
    "MIDDLEWARE_KIND_LLM_EXECUTION",
    "MIDDLEWARE_KIND_LLM_REQUEST",
    "MIDDLEWARE_KIND_TOOL_EXECUTION",
    "MIDDLEWARE_KIND_TOOL_REQUEST",
    "MiddlewareRegistry",
    "MiddlewareTrace",
    "ToolExecutionContext",
    "ToolRequest",
    "sanitize_trace_payload",
]
