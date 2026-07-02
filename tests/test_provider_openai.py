import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse, HttpTimeout
from proseforge_agent.llm.profiles import load_provider_profiles
from proseforge_agent.llm.providers.openai import (
    build_provider,
    real_smoke,
    shape_certification,
)
from proseforge_agent.llm.registry import build_provider_from_profile

FIXTURES = Path(__file__).parent / "fixtures" / "providers"
CONFIG = "configs/providers/openai.yaml"
SUCCESS = (FIXTURES / "openai_success.json").read_text(encoding="utf-8")
ERROR = (FIXTURES / "openai_error.json").read_text(encoding="utf-8")
STREAM = (FIXTURES / "openai_stream.txt").read_text(encoding="utf-8").splitlines()


def _profile(name="openai_main"):
    return load_provider_profiles(CONFIG)[name]


def _request(content="one line"):
    return ProviderRequest(role="drafter", messages=[Message(role="user", content=content)])


class CountingStreamTransport(FakeHttpTransport):
    def __init__(self, stream_lines: list[str]):
        super().__init__(stream_lines=stream_lines)
        self.consumed = 0

    def post_json_stream(self, request):
        self.requests.append(request)
        for line in self.stream_lines:
            self.consumed += 1
            yield line


@pytest.fixture
def fake_http():
    return FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])


def test_openai_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    profile = load_provider_profiles(CONFIG)["openai_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")])
    )
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])


def test_openai_request_forwards_tools(fake_http):
    tool = {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Lookup canon",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        },
    }
    provider = build_provider(_profile(), http=fake_http)
    provider.generate(
        ProviderRequest(
            role="drafter",
            messages=[Message(role="user", content="one line")],
            tools=[tool],
        )
    )
    assert fake_http.requests[0].json["tools"] == [tool]


def test_openai_parses_success_response_into_provider_result(fake_http):
    result = build_provider(_profile(), http=fake_http).generate(_request())
    assert result.text == "A single quiet line."
    assert result.usage.total_tokens > 0
    assert result.raw["id"] == "chatcmpl-openai-0001"
    assert result.raw["choices"][0]["message"]["tool_calls"]


def test_openai_parses_responses_output_text():
    payload = {
        "id": "resp-1",
        "model": "gpt-4o-mini",
        "output_text": "Normalized responses text.",
        "usage": {"input_tokens": 7, "output_tokens": 4},
    }
    http = FakeHttpTransport(
        responses=[HttpResponse(status_code=200, text=json.dumps(payload))]
    )
    provider = build_provider(_profile("openai_responses"), http=http)
    result = provider.generate(_request())
    assert result.text == "Normalized responses text."
    assert result.usage.total_tokens == 11


def test_openai_parses_stream_events_into_normalized_chunks():
    http = FakeHttpTransport(stream_lines=STREAM)
    chunks = list(build_provider(_profile(), http=http).generate_stream(_request()))
    assert "".join(c.text for c in chunks) == "Hello from OpenAI"
    assert chunks[-1].done is True


def test_openai_stream_yields_before_transport_is_exhausted():
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]
    http = CountingStreamTransport(lines)
    stream = build_provider(_profile(), http=http).generate_stream(_request())

    first = next(stream)

    assert first.text == "Hello"
    assert http.consumed == 1


def test_openai_maps_auth_rate_limit_timeout_and_invalid_response_errors():
    cases = {
        401: "auth",
        429: "rate_limit",
        500: "server_error",
    }
    for status, code in cases.items():
        http = FakeHttpTransport(responses=[HttpResponse(status_code=status, text=ERROR)])
        provider = build_provider(_profile(), http=http)
        with pytest.raises(ProviderError) as exc:
            provider.generate(_request())
        assert exc.value.code == code

    timed = build_provider(_profile(), http=FakeHttpTransport(raises=HttpTimeout("x")))
    with pytest.raises(ProviderError) as exc:
        timed.generate(_request())
    assert exc.value.code == "timeout"

    bad = build_provider(
        _profile(), http=FakeHttpTransport(responses=[HttpResponse(200, "not json")])
    )
    with pytest.raises(ProviderError) as exc:
        bad.generate(_request())
    assert exc.value.code == "invalid_response"


def test_openai_does_not_leak_key_in_errors(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-XYZ")
    http = FakeHttpTransport(responses=[HttpResponse(status_code=401, text=ERROR)])
    provider = build_provider(_profile(), http=http)
    with pytest.raises(ProviderError) as exc:
        provider.generate(_request())
    assert "secret-XYZ" not in str(exc.value)


def test_openai_missing_openai_api_key_skips_real_smoke(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = real_smoke(_profile())
    assert report["skipped"] is True
    assert "OPENAI_API_KEY" in report["reason"]


def test_openai_shape_certification_report_records_source_and_checked_date(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = shape_certification(_profile())
    assert report["source"]
    assert report["checked_date"]
    assert report["level"] == "shape_tested"
    assert set(report["capabilities"]) >= {"text", "streaming", "json", "tools", "vision"}


def test_registry_resolves_openai_aliases(fake_http):
    provider = build_provider_from_profile(_profile(), http=fake_http)
    result = provider.generate(_request())
    assert result.text == "A single quiet line."
