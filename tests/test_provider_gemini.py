import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse, HttpTimeout
from proseforge_agent.llm.profiles import load_provider_profiles
from proseforge_agent.llm.providers.gemini import (
    build_provider,
    real_smoke,
    shape_certification,
)
from proseforge_agent.llm.registry import build_provider_from_profile

FIXTURES = Path(__file__).parent / "fixtures" / "providers"
CONFIG = "configs/providers/gemini.yaml"
SUCCESS = (FIXTURES / "gemini_success.json").read_text(encoding="utf-8")
ERROR = (FIXTURES / "gemini_error.json").read_text(encoding="utf-8")
STREAM = (FIXTURES / "gemini_stream.txt").read_text(encoding="utf-8").splitlines()


def _profile(name="gemini_main"):
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


def test_gemini_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    profile = load_provider_profiles(CONFIG)["gemini_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")])
    )
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])


def test_gemini_parses_success_response_into_provider_result(fake_http):
    result = build_provider(_profile(), http=fake_http).generate(_request())
    assert result.text == "A single quiet line."
    assert result.usage.total_tokens > 0
    candidate = result.raw["candidates"][0]
    assert any("functionCall" in part for part in candidate["content"]["parts"])
    assert candidate["finishReason"] == "STOP"
    assert candidate["safetyRatings"]


def test_gemini_native_request_converts_function_declarations(fake_http):
    tool = {
        "function_declarations": [
            {
                "name": "lookup",
                "description": "Lookup canon",
                "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
            }
        ]
    }
    build_provider(_profile(), http=fake_http).generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")], tools=[tool])
    )
    assert fake_http.requests[0].json["tools"] == [
        {
            "functionDeclarations": [
                {
                    "name": "lookup",
                    "description": "Lookup canon",
                    "parameters": {
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                    },
                }
            ]
        }
    ]


def test_gemini_parses_stream_events_into_normalized_chunks():
    http = FakeHttpTransport(stream_lines=STREAM)
    chunks = list(build_provider(_profile(), http=http).generate_stream(_request()))
    assert "".join(c.text for c in chunks) == "Hello from Gemini"
    assert chunks[-1].done is True


def test_gemini_stream_yields_before_transport_is_exhausted():
    lines = [
        'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]}}]}',
        'data: {"candidates":[{"content":{"parts":[{"text":" Gemini"}]}}]}',
        "data: [DONE]",
    ]
    http = CountingStreamTransport(lines)
    stream = build_provider(_profile(), http=http).generate_stream(_request())

    first = next(stream)

    assert first.text == "Hello"
    assert http.consumed == 1


def test_gemini_maps_auth_rate_limit_timeout_and_invalid_response_errors():
    for status, code in {401: "auth", 429: "rate_limit", 500: "server_error"}.items():
        http = FakeHttpTransport(responses=[HttpResponse(status_code=status, text=ERROR)])
        with pytest.raises(ProviderError) as exc:
            build_provider(_profile(), http=http).generate(_request())
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


def test_gemini_does_not_leak_key_in_errors(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-XYZ")
    http = FakeHttpTransport(responses=[HttpResponse(status_code=401, text=ERROR)])
    with pytest.raises(ProviderError) as exc:
        build_provider(_profile(), http=http).generate(_request())
    assert "secret-XYZ" not in str(exc.value)


def test_gemini_missing_gemini_api_key_skips_real_smoke(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = real_smoke(_profile())
    assert report["skipped"] is True
    assert "GEMINI_API_KEY" in report["reason"]


def test_gemini_shape_certification_report_records_source_and_checked_date(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    report = shape_certification(_profile())
    assert report["source"]
    assert report["checked_date"]
    assert report["level"] == "shape_tested"
    assert set(report["capabilities"]) >= {"text", "streaming", "json", "tools", "vision"}


def test_gemini_openai_profile_parses_chat_completion(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = json.dumps(
        {
            "model": "gemini-2.0-flash",
            "choices": [{"message": {"role": "assistant", "content": "Bridge reply."}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        }
    )
    http = FakeHttpTransport(responses=[HttpResponse(status_code=200, text=payload)])
    provider = build_provider(_profile("gemini_openai"), http=http)
    result = provider.generate(_request())
    assert result.text == "Bridge reply."
    assert result.usage.total_tokens == 10
    assert "test-key" not in repr(http.requests[0])
    assert http.requests[0].url.endswith("/chat/completions")


def test_gemini_openai_profile_forwards_tools(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = json.dumps(
        {
            "model": "gemini-2.0-flash",
            "choices": [{"message": {"role": "assistant", "content": "Bridge reply."}}],
            "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        }
    )
    http = FakeHttpTransport(responses=[HttpResponse(status_code=200, text=payload)])
    tool = {
        "type": "function",
        "function": {"name": "lookup", "description": "Lookup", "parameters": {"type": "object"}},
    }
    provider = build_provider(_profile("gemini_openai"), http=http)
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")], tools=[tool])
    )
    assert http.requests[0].json["tools"] == [tool]


def test_registry_resolves_gemini_aliases(fake_http):
    provider = build_provider_from_profile(_profile(), http=fake_http)
    result = provider.generate(_request())
    assert result.text == "A single quiet line."
