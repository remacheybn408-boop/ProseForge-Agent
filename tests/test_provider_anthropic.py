from pathlib import Path

import pytest

from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse, HttpTimeout
from proseforge_agent.llm.profiles import load_provider_profiles
from proseforge_agent.llm.providers.anthropic import (
    build_provider,
    real_smoke,
    shape_certification,
)
from proseforge_agent.llm.registry import build_provider_from_profile

FIXTURES = Path(__file__).parent / "fixtures" / "providers"
CONFIG = "configs/providers/anthropic.yaml"
SUCCESS = (FIXTURES / "anthropic_success.json").read_text(encoding="utf-8")
ERROR = (FIXTURES / "anthropic_error.json").read_text(encoding="utf-8")
STREAM = (FIXTURES / "anthropic_stream.txt").read_text(encoding="utf-8").splitlines()


def _profile(name="anthropic_main"):
    return load_provider_profiles(CONFIG)[name]


def _request(content="one line"):
    return ProviderRequest(role="drafter", messages=[Message(role="user", content=content)])


@pytest.fixture
def fake_http():
    return FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])


def test_anthropic_request_shape_uses_profile_config(fake_http, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    profile = load_provider_profiles(CONFIG)["anthropic_main"]
    provider = build_provider(profile, http=fake_http)
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="one line")])
    )
    assert fake_http.requests[0].json["model"] == profile.model
    assert "test-key" not in repr(fake_http.requests[0])


def test_anthropic_request_includes_max_tokens(fake_http):
    build_provider(_profile(), http=fake_http).generate(_request())
    assert fake_http.requests[0].json["max_tokens"] > 0


def test_anthropic_parses_success_response_into_provider_result(fake_http):
    result = build_provider(_profile(), http=fake_http).generate(_request())
    assert result.text == "A single quiet line."
    assert result.usage.total_tokens > 0
    assert result.raw["id"] == "msg_anthropic_0001"
    assert any(b["type"] == "tool_use" for b in result.raw["content"])
    assert result.raw["stop_reason"] == "end_turn"


def test_anthropic_parses_stream_events_into_normalized_chunks():
    http = FakeHttpTransport(stream_lines=STREAM)
    chunks = list(build_provider(_profile(), http=http).generate_stream(_request()))
    assert "".join(c.text for c in chunks) == "Hello from Claude"
    assert chunks[-1].done is True


def test_anthropic_maps_auth_rate_limit_timeout_and_invalid_response_errors():
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


def test_anthropic_does_not_leak_key_in_errors(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-XYZ")
    http = FakeHttpTransport(responses=[HttpResponse(status_code=401, text=ERROR)])
    with pytest.raises(ProviderError) as exc:
        build_provider(_profile(), http=http).generate(_request())
    assert "secret-XYZ" not in str(exc.value)


def test_anthropic_missing_anthropic_api_key_skips_real_smoke(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = real_smoke(_profile())
    assert report["skipped"] is True
    assert "ANTHROPIC_API_KEY" in report["reason"]


def test_anthropic_shape_certification_report_records_source_and_checked_date(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = shape_certification(_profile())
    assert report["source"]
    assert report["checked_date"]
    assert report["level"] == "shape_tested"
    assert set(report["capabilities"]) >= {"text", "streaming", "json", "tools", "vision"}


def test_registry_resolves_anthropic_aliases(fake_http):
    provider = build_provider_from_profile(_profile(), http=fake_http)
    result = provider.generate(_request())
    assert result.text == "A single quiet line."
