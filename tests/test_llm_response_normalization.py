"""Regression tests for LLM provider response normalization."""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse
from proseforge_agent.llm.openai_compatible import OpenAICompatibleProvider
from proseforge_agent.llm.providers.deepseek import DeepSeekProvider
from proseforge_agent.llm.providers.doubao import DoubaoProvider
from proseforge_agent.llm.providers.gemini import GeminiProvider
from proseforge_agent.llm.providers.glm import GLMProvider
from proseforge_agent.llm.providers.grok import GrokProvider
from proseforge_agent.llm.providers.minimax import MiniMaxProvider
from proseforge_agent.llm.providers.mimo import MiMoProvider
from proseforge_agent.llm.providers.openai import OpenAIProvider
from proseforge_agent.llm.providers.qwen import QwenProvider


def _request() -> ProviderRequest:
    return ProviderRequest(role="drafter", messages=[Message(role="user", content="hello")])


def _payload(*, content: str | None, usage: dict | None = None) -> str:
    return json.dumps(
        {
            "model": "model-a",
            "choices": [{"message": {"role": "assistant", "content": content}}],
            "usage": usage or {"prompt_tokens": 1, "completion_tokens": 1},
        }
    )


ProviderFactory = Callable[[FakeHttpTransport], object]


@pytest.mark.parametrize(
    "factory",
    [
        lambda http: OpenAIProvider("openai", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: DeepSeekProvider("deepseek", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: QwenProvider("qwen", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: DoubaoProvider("doubao", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: GLMProvider("glm", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: GrokProvider("grok", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: MiniMaxProvider("minimax", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: MiMoProvider("mimo", "https://example.test/v1", "key", "model-a", http=http),
        lambda http: GeminiProvider(
            "gemini",
            "https://example.test/v1beta",
            "key",
            "model-a",
            protocol="gemini_openai",
            http=http,
        ),
        lambda http: OpenAICompatibleProvider(
            "compat", "https://example.test/v1", "key", "model-a", http=http
        ),
    ],
)
def test_openai_shaped_providers_normalize_null_content_to_empty_text(factory):
    http = FakeHttpTransport(responses=[HttpResponse(status_code=200, text=_payload(content=None))])
    provider = factory(http)

    result = provider.generate(_request())

    assert result.text == ""
    assert isinstance(result.text, str)


def test_openai_compatible_null_usage_tokens_are_zero():
    http = FakeHttpTransport(
        responses=[
            HttpResponse(
                status_code=200,
                text=_payload(
                    content="ok",
                    usage={"prompt_tokens": None, "completion_tokens": None},
                ),
            )
        ]
    )
    provider = OpenAICompatibleProvider(
        "compat", "https://example.test/v1", "key", "model-a", http=http
    )

    result = provider.generate(_request())

    assert result.text == "ok"
    assert result.usage.prompt_tokens == 0
    assert result.usage.completion_tokens == 0
