from pathlib import Path

import pytest

from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse, HttpTimeout
from proseforge_agent.llm.profiles import load_provider_profiles
from proseforge_agent.llm.providers.qwen import (
    build_provider,
    real_smoke,
    shape_certification,
    tool_calls,
)
from proseforge_agent.llm.registry import build_provider_from_profile

FIXTURES = Path(__file__).parent / "fixtures" / "providers"
CONFIG = "configs/providers/qwen.yaml"
SUCCESS = (FIXTURES / "qwen_success.json").read_text(encoding="utf-8")
ERROR = (FIXTURES / "qwen_error.json").read_text(encoding="utf-8")
STREAM = (FIXTURES / "qwen_stream.txt").read_text(encoding="utf-8").splitlines()


def _profile(name="qwen_main"):
    return load_provider_profiles(CONFIG)[name]


def _request(content="one line"):
    return ProviderRequest(role="drafter", messages=[Message(role="user", content=content)])


@pytest.fixture
def fake_http():
    return FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])


def test_qwen_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    profile = load_provider_profiles(CONFIG)["qwen_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")])
    )
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])


def test_qwen_parses_success_response_into_provider_result(fake_http):
    result = build_provider(_profile(), http=fake_http).generate(_request())
    assert result.text == "A single quiet line."
    assert result.usage.total_tokens > 0
    assert result.raw["id"] == "chatcmpl_qwen_0001"
    assert result.raw["choices"][0]["finish_reason"] == "stop"


def test_qwen_parses_tool_calls_metadata(fake_http):
    result = build_provider(_profile(), http=fake_http).generate(_request())
    calls = tool_calls(result)
    assert calls and calls[0]["function"]["name"] == "noop"
    assert result.text == "A single quiet line."


def test_qwen_includes_workspace_header_when_env_set(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_WORKSPACE_ID", raising=False)
    http_off = FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])
    build_provider(_profile(), http=http_off).generate(_request())
    assert "X-DashScope-WorkSpace" not in http_off.requests[0].headers

    monkeypatch.setenv("DASHSCOPE_WORKSPACE_ID", "ws-123")
    http_on = FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])
    build_provider(_profile(), http=http_on).generate(_request())
    assert http_on.requests[0].headers["X-DashScope-WorkSpace"] == "ws-123"


def test_qwen_parses_stream_events_into_normalized_chunks():
    http = FakeHttpTransport(stream_lines=STREAM)
    chunks = list(build_provider(_profile(), http=http).generate_stream(_request()))
    assert "".join(c.text for c in chunks) == "Hello from Qwen"
    assert chunks[-1].done is True


def test_qwen_maps_auth_rate_limit_timeout_and_invalid_response_errors():
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


def test_qwen_does_not_leak_key_in_errors(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "secret-XYZ")
    http = FakeHttpTransport(responses=[HttpResponse(status_code=401, text=ERROR)])
    with pytest.raises(ProviderError) as exc:
        build_provider(_profile(), http=http).generate(_request())
    assert "secret-XYZ" not in str(exc.value)


def test_qwen_missing_dashscope_api_key_skips_real_smoke(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    report = real_smoke(_profile())
    assert report["skipped"] is True
    assert "DASHSCOPE_API_KEY" in report["reason"]


def test_qwen_shape_certification_report_records_source_and_checked_date(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    report = shape_certification(_profile())
    assert report["source"]
    assert report["checked_date"]
    assert report["level"] == "shape_tested"
    assert set(report["capabilities"]) >= {"text", "streaming", "json", "tools", "vision"}


def test_registry_resolves_qwen_aliases(fake_http):
    provider = build_provider_from_profile(_profile(), http=fake_http)
    result = provider.generate(_request())
    assert result.text == "A single quiet line."
