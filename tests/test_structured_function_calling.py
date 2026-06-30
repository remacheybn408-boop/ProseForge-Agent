"""Structured function calling protocol tests (Task 109)."""

from __future__ import annotations

from proseforge_agent.agent.function_calling import (
    StructuredToolAdapter,
    ToolCallLoop,
)
from proseforge_agent.agent.tools import AgentTool, ToolRegistry
from proseforge_agent.llm import Message, ProviderRequest, ProviderResult


def _registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        AgentTool(
            name="math.add",
            permission="read_only",
            input_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                "required": ["a", "b"],
                "additionalProperties": False,
            },
            output_schema={"type": "object", "required": ["sum"]},
            callable=lambda payload: {"sum": payload["a"] + payload["b"]},
            description="Add two numbers",
        )
    )
    return registry


def test_registered_tool_schema_converts_to_provider_shapes():
    tool = _registry().get("math.add")
    adapter = StructuredToolAdapter()

    assert adapter.schema_for_provider(tool, "openai") == {
        "type": "function",
        "function": {
            "name": "math.add",
            "description": "Add two numbers",
            "parameters": tool.input_schema,
        },
    }
    assert adapter.schema_for_provider(tool, "anthropic")["input_schema"] == tool.input_schema
    assert adapter.schema_for_provider(tool, "gemini")["function_declarations"][0]["name"] == "math.add"
    assert adapter.schema_for_provider(tool, "fake")["schema"] == tool.input_schema


def test_tool_call_parsing_normalizes_provider_shapes():
    adapter = StructuredToolAdapter()

    openai_call = adapter.parse_tool_calls(
        "openai",
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "math.add", "arguments": '{"a": 1, "b": 2}'},
                            }
                        ]
                    }
                }
            ]
        },
    )[0]
    anthropic_call = adapter.parse_tool_calls(
        "anthropic",
        {"content": [{"type": "tool_use", "id": "call_1", "name": "math.add", "input": {"a": 1, "b": 2}}]},
    )[0]
    gemini_call = adapter.parse_tool_calls(
        "gemini",
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"functionCall": {"name": "math.add", "args": {"a": 1, "b": 2}}}]
                    }
                }
            ]
        },
    )[0]
    fake_call = adapter.parse_tool_calls(
        "fake",
        {"tool_calls": [{"id": "call_1", "name": "math.add", "arguments": {"a": 1, "b": 2}}]},
    )[0]

    assert {openai_call, anthropic_call, gemini_call, fake_call} == {openai_call}
    assert openai_call.name == "math.add"
    assert openai_call.arguments == {"a": 1, "b": 2}


def test_tool_loop_executes_and_injects_result_into_message_history():
    registry = _registry()
    provider = _ScriptedToolProvider()
    request = ProviderRequest(role="planner", messages=[Message(role="user", content="add 1 and 2")])

    result = ToolCallLoop(provider=provider, registry=registry, provider_kind="fake").run(request)

    assert result.final_text == "done"
    assert result.tool_results[0].output == {"sum": 3}
    assert result.messages[-2].role == "tool"
    assert '"sum": 3' in result.messages[-2].content
    assert provider.requests[1].messages[-1].role == "tool"


def test_tool_loop_reports_schema_error_without_executing_tool():
    registry = _registry()
    provider = _BadToolProvider()
    request = ProviderRequest(role="planner", messages=[Message(role="user", content="add")])

    result = ToolCallLoop(provider=provider, registry=registry, provider_kind="fake").run(request)

    assert result.tool_results[0].status == "invalid"
    assert "missing required field" in result.tool_results[0].error
    assert result.messages[-2].role == "tool"
    assert "invalid" in result.messages[-2].content


class _ScriptedToolProvider:
    name = "fake"
    model = "fake"

    def __init__(self) -> None:
        self.requests = []

    def generate(self, request: ProviderRequest) -> ProviderResult:
        self.requests.append(request)
        if len(self.requests) == 1:
            return ProviderResult(
                provider="fake",
                model="fake",
                text="",
                raw={
                    "tool_calls": [
                        {"id": "call_1", "name": "math.add", "arguments": {"a": 1, "b": 2}}
                    ]
                },
            )
        return ProviderResult(provider="fake", model="fake", text="done", raw={})


class _BadToolProvider:
    name = "fake"
    model = "fake"

    def generate(self, request: ProviderRequest) -> ProviderResult:
        if not any(message.role == "tool" for message in request.messages):
            return ProviderResult(
                provider="fake",
                model="fake",
                text="",
                raw={"tool_calls": [{"id": "call_bad", "name": "math.add", "arguments": {"a": 1}}]},
            )
        return ProviderResult(provider="fake", model="fake", text="schema handled", raw={})
