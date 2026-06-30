"""Provider-neutral structured function calling helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from ..errors import ConfigurationError
from ..llm import Message, ProviderRequest


@dataclass(frozen=True)
class ProviderToolCall:
    """One normalized tool call parsed from a provider response."""

    id: str
    name: str
    arguments: dict[str, Any]

    def __hash__(self) -> int:
        return hash((self.id, self.name, json.dumps(self.arguments, sort_keys=True)))


@dataclass(frozen=True)
class StructuredToolResult:
    """One normalized result from validating and invoking a tool call."""

    call_id: str
    name: str
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolLoopResult:
    """Final provider text plus all messages and tool results."""

    final_text: str
    messages: list[Message]
    tool_results: list[StructuredToolResult] = field(default_factory=list)


class StructuredToolAdapter:
    """Convert tool schemas and tool calls across provider wire formats."""

    def schema_for_provider(self, tool, provider_kind: str) -> dict[str, Any]:
        provider_kind = provider_kind.lower()
        if provider_kind == "openai":
            return {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
        if provider_kind == "anthropic":
            return {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
        if provider_kind == "gemini":
            return {
                "function_declarations": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    }
                ]
            }
        if provider_kind == "fake":
            return {
                "name": tool.name,
                "description": tool.description,
                "schema": tool.input_schema,
            }
        raise ConfigurationError(f"unsupported tool schema provider {provider_kind!r}")

    def parse_tool_calls(self, provider_kind: str, raw: dict[str, Any]) -> list[ProviderToolCall]:
        provider_kind = provider_kind.lower()
        if provider_kind == "openai":
            return _parse_openai(raw)
        if provider_kind == "anthropic":
            return _parse_anthropic(raw)
        if provider_kind == "gemini":
            return _parse_gemini(raw)
        if provider_kind == "fake":
            return _parse_fake(raw)
        raise ConfigurationError(f"unsupported tool call provider {provider_kind!r}")

    def validate(self, call: ProviderToolCall, registry) -> None:
        tool = registry.get(call.name)
        if tool is None:
            raise ConfigurationError(f"unknown tool {call.name!r}")
        schema = tool.input_schema or {}
        required = list(schema.get("required", []))
        missing = [name for name in required if name not in call.arguments]
        if missing:
            raise ConfigurationError(f"missing required field(s): {', '.join(missing)}")
        if schema.get("additionalProperties") is False:
            properties = set((schema.get("properties") or {}).keys())
            unknown = [name for name in call.arguments if name not in properties]
            if unknown:
                raise ConfigurationError(f"unknown field(s): {', '.join(unknown)}")

    def result_message(self, result: StructuredToolResult) -> Message:
        return Message(
            role="tool",
            content=json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True),
        )


class ToolCallLoop:
    """Run a small provider/tool loop until the provider stops requesting tools."""

    def __init__(
        self,
        *,
        provider,
        registry,
        provider_kind: str,
        adapter: StructuredToolAdapter | None = None,
        max_steps: int = 4,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.provider_kind = provider_kind
        self.adapter = adapter or StructuredToolAdapter()
        self.max_steps = max_steps

    def run(self, request: ProviderRequest) -> ToolLoopResult:
        messages = list(request.messages)
        results: list[StructuredToolResult] = []
        final_text = ""
        tools = [self.adapter.schema_for_provider(tool, self.provider_kind) for tool in self.registry.list()]
        for _step in range(self.max_steps):
            provider_request = ProviderRequest(
                role=request.role,
                messages=list(messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=tools,
            )
            provider_result = self.provider.generate(provider_request)
            calls = self.adapter.parse_tool_calls(self.provider_kind, provider_result.raw)
            if not calls:
                final_text = provider_result.text
                messages.append(Message(role="assistant", content=final_text))
                break
            for call in calls:
                result = self._invoke(call)
                results.append(result)
                messages.append(self.adapter.result_message(result))
        return ToolLoopResult(final_text=final_text, messages=messages, tool_results=results)

    def _invoke(self, call: ProviderToolCall) -> StructuredToolResult:
        try:
            self.adapter.validate(call, self.registry)
            output = self.registry.execute(call.name, call.arguments)
        except Exception as exc:  # noqa: BLE001 - convert to structured tool result
            return StructuredToolResult(
                call_id=call.id,
                name=call.name,
                status="invalid",
                error=str(exc),
            )
        return StructuredToolResult(
            call_id=call.id,
            name=call.name,
            status="ok",
            output=output if isinstance(output, dict) else {"value": output},
        )


def _parse_openai(raw: dict[str, Any]) -> list[ProviderToolCall]:
    message = (((raw.get("choices") or [{}])[0]).get("message") or {})
    calls = []
    for item in message.get("tool_calls") or []:
        function = item.get("function") or {}
        calls.append(
            ProviderToolCall(
                id=str(item.get("id") or ""),
                name=str(function.get("name") or ""),
                arguments=_arguments(function.get("arguments")),
            )
        )
    return calls


def _parse_anthropic(raw: dict[str, Any]) -> list[ProviderToolCall]:
    return [
        ProviderToolCall(
            id=str(item.get("id") or ""),
            name=str(item.get("name") or ""),
            arguments=_arguments(item.get("input")),
        )
        for item in raw.get("content") or []
        if item.get("type") == "tool_use"
    ]


def _parse_gemini(raw: dict[str, Any]) -> list[ProviderToolCall]:
    calls = []
    for candidate in raw.get("candidates") or []:
        for part in ((candidate.get("content") or {}).get("parts") or []):
            function = part.get("functionCall")
            if function:
                calls.append(
                    ProviderToolCall(
                        id=str(function.get("id") or f"call_{len(calls) + 1}"),
                        name=str(function.get("name") or ""),
                        arguments=_arguments(function.get("args")),
                    )
                )
    return calls


def _parse_fake(raw: dict[str, Any]) -> list[ProviderToolCall]:
    return [
        ProviderToolCall(
            id=str(item.get("id") or ""),
            name=str(item.get("name") or ""),
            arguments=_arguments(item.get("arguments")),
        )
        for item in raw.get("tool_calls") or []
    ]


def _arguments(value: Any) -> dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, str):
        parsed = json.loads(value)
        if not isinstance(parsed, dict):
            raise ConfigurationError("tool arguments must decode to an object")
        return parsed
    if not isinstance(value, dict):
        raise ConfigurationError("tool arguments must be an object")
    return dict(value)


__all__ = [
    "ProviderToolCall",
    "StructuredToolAdapter",
    "StructuredToolResult",
    "ToolCallLoop",
    "ToolLoopResult",
]
