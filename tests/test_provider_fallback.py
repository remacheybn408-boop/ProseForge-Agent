"""Provider fallback tests (Task 123)."""

from __future__ import annotations

import pytest

from proseforge_agent.agent.provider_fallback import ProviderFallbackChain
from proseforge_agent.cli import main
from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest, ProviderResult


class FailingProvider:
    def __init__(self, name: str, code: str) -> None:
        self.name = name
        self.model = name
        self.code = code

    def generate(self, request: ProviderRequest) -> ProviderResult:
        error = ProviderError(f"{self.name} failed")
        error.code = self.code
        raise error


class SucceedingProvider:
    def __init__(self, name: str) -> None:
        self.name = name
        self.model = name

    def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(provider=self.name, model=self.model, text=f"ok from {self.name}")


def test_provider_fallback_tries_chain_until_success():
    request = ProviderRequest(role="drafter", messages=[Message(role="user", content="hello")])
    chain = ProviderFallbackChain(
        [
            FailingProvider("deepseek", "timeout"),
            FailingProvider("qwen", "quota"),
            SucceedingProvider("fake"),
        ]
    )

    result = chain.generate(request)

    assert result.result.text == "ok from fake"
    assert [attempt.provider for attempt in result.attempts] == ["deepseek", "qwen", "fake"]
    assert result.attempts[0].fallback_reason == "timeout"
    assert result.attempts[1].fallback_reason == "quota"


def test_provider_fallback_stops_on_non_fallback_error():
    request = ProviderRequest(role="drafter", messages=[Message(role="user", content="hello")])
    chain = ProviderFallbackChain([FailingProvider("deepseek", "auth"), SucceedingProvider("fake")])

    with pytest.raises(ProviderError):
        chain.generate(request)


def test_provider_fallback_cli_status_and_test_chain(capsys):
    assert main(["provider", "fallback-status"]) == 0
    assert main(["provider", "test-chain"]) == 0

    out = capsys.readouterr().out
    assert "Provider Fallback" in out
    assert "deepseek -> qwen -> openai -> fake" in out
    assert "selected=fake" in out
