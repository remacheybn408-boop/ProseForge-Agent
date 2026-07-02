"""Shared helpers for OpenAI-shaped provider payloads."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator

from ...errors import ProviderError
from ..base import StreamChunk


def provider_error(message: str, code: str) -> ProviderError:
    error = ProviderError(message)
    error.code = code
    return error


def openai_message_text(payload: dict) -> str:
    """Return assistant text from an OpenAI-shaped chat completion payload."""
    message = payload["choices"][0]["message"]
    if not isinstance(message, dict):
        raise TypeError("message must be an object")
    return message.get("content") or ""


def add_openai_tools(body: dict, tools: list[dict]) -> None:
    if tools:
        body["tools"] = list(tools)


def anthropic_tools(tools: list[dict]) -> list[dict]:
    converted: list[dict] = []
    for tool in tools:
        if "name" in tool and "input_schema" in tool:
            converted.append(dict(tool))
            continue
        function = tool.get("function") if tool.get("type") == "function" else tool
        if not isinstance(function, dict):
            raise TypeError("tool must be an object")
        converted.append(
            {
                "name": function["name"],
                "description": function.get("description", ""),
                "input_schema": function.get("parameters")
                or function.get("input_schema")
                or {"type": "object", "properties": {}},
            }
        )
    return converted


def gemini_tools(tools: list[dict]) -> list[dict]:
    declarations: list[dict] = []
    for tool in tools:
        if "functionDeclarations" in tool:
            declarations.extend(tool["functionDeclarations"])
            continue
        if "function_declarations" in tool:
            declarations.extend(tool["function_declarations"])
            continue
        function = tool.get("function") if tool.get("type") == "function" else tool
        if not isinstance(function, dict):
            raise TypeError("tool must be an object")
        declarations.append(
            {
                "name": function["name"],
                "description": function.get("description", ""),
                "parameters": function.get("parameters")
                or function.get("input_schema")
                or {"type": "object"},
            }
        )
    return [{"functionDeclarations": declarations}] if declarations else []


def stream_openai_sse_lines(
    lines: Iterator[str],
    *,
    provider_name: str,
    extract_delta: Callable[[dict], str],
) -> Iterator[StreamChunk]:
    index = 0
    emitted = False
    try:
        for line in lines:
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                break
            obj = json.loads(data)
            content = extract_delta(obj)
            if content:
                emitted = True
                yield StreamChunk(text=content, done=False, index=index)
                index += 1
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise provider_error(
            f"provider {provider_name!r} returned an unparseable stream chunk",
            "invalid_response",
        ) from exc
    if emitted:
        yield StreamChunk(text="", done=True, index=index)


def stream_anthropic_sse_lines(lines: Iterator[str], *, provider_name: str) -> Iterator[StreamChunk]:
    index = 0
    emitted = False
    try:
        for line in lines:
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].strip()
            obj = json.loads(data)
            if obj.get("type") == "message_stop":
                break
            if obj.get("type") != "content_block_delta":
                continue
            delta = obj.get("delta", {})
            if delta.get("type") == "text_delta" and delta.get("text"):
                emitted = True
                yield StreamChunk(text=delta["text"], done=False, index=index)
                index += 1
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise provider_error(
            f"provider {provider_name!r} returned an unparseable stream chunk",
            "invalid_response",
        ) from exc
    if emitted:
        yield StreamChunk(text="", done=True, index=index)
