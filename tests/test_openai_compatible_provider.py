import json
from pathlib import Path

import pytest

from proseforge_agent.errors import ProviderError
from proseforge_agent.llm import Message, ProviderRequest
from proseforge_agent.llm.http import FakeHttpTransport, HttpResponse, HttpTimeout
from proseforge_agent.llm.openai_compatible import OpenAICompatibleProvider

FIXTURES = Path(__file__).parent / "fixtures" / "providers"
SUCCESS = (FIXTURES / "openai_chat_success.json").read_text(encoding="utf-8")
ERROR = (FIXTURES / "openai_chat_error.json").read_text(encoding="utf-8")


def _request(content="Hi"):
    return ProviderRequest(role="drafter", messages=[Message(role="user", content=content)])


@pytest.fixture
def fake_http():
    return FakeHttpTransport(responses=[HttpResponse(status_code=200, text=SUCCESS)])


def _provider(http, **kwargs):
    params = dict(
        name="compat",
        base_url="https://example.test/v1",
        api_key="key",
        model="model-a",
        http=http,
    )
    params.update(kwargs)
    return OpenAICompatibleProvider(**params)


def test_chat_request_shape_uses_configured_base_url(fake_http):
    provider = OpenAICompatibleProvider(
        name="compat",
        base_url="https://example.test/v1",
        api_key="key",
        model="model-a",
        http=fake_http,
    )
    provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="Hi")])
    )
    assert fake_http.requests[0].url == "https://example.test/v1/chat/completions"
    assert fake_http.requests[0].json["model"] == "model-a"


def test_authorization_header_uses_bearer_api_key(fake_http):
    _provider(fake_http).generate(_request())
    assert fake_http.requests[0].headers["Authorization"] == "Bearer key"


def test_success_response_maps_to_provider_result(fake_http):
    result = _provider(fake_http).generate(_request())
    assert result.provider == "compat"
    assert result.model == "model-a"
    assert result.text == "Hello from the model."
    assert result.usage.total_tokens > 0
    assert result.raw["id"] == "chatcmpl-test-0001"


def test_extra_body_is_merged_into_request_json(fake_http):
    provider = _provider(fake_http, extra_body={"top_p": 0.5})
    provider.generate(_request())
    assert fake_http.requests[0].json["top_p"] == 0.5


def test_temperature_is_passed_through(fake_http):
    provider = _provider(fake_http)
    provider.generate(
        ProviderRequest(
            role="drafter",
            messages=[Message(role="user", content="Hi")],
            temperature=0.2,
        )
    )
    assert fake_http.requests[0].json["temperature"] == 0.2


def test_401_raises_auth_error_without_leaking_key():
    http = FakeHttpTransport(responses=[HttpResponse(status_code=401, text=ERROR)])
    provider = _provider(http, api_key="secret-XYZ")
    with pytest.raises(ProviderError) as exc:
        provider.generate(_request())
    assert exc.value.code == "auth"
    assert "secret-XYZ" not in str(exc.value)


def test_429_raises_rate_limit():
    http = FakeHttpTransport(responses=[HttpResponse(status_code=429, text=ERROR)])
    with pytest.raises(ProviderError) as exc:
        _provider(http).generate(_request())
    assert exc.value.code == "rate_limit"


def test_500_raises_server_error():
    http = FakeHttpTransport(responses=[HttpResponse(status_code=500, text=ERROR)])
    with pytest.raises(ProviderError) as exc:
        _provider(http).generate(_request())
    assert exc.value.code == "server_error"


def test_timeout_raises_timeout_error():
    http = FakeHttpTransport(raises=HttpTimeout("timed out"))
    with pytest.raises(ProviderError) as exc:
        _provider(http).generate(_request())
    assert exc.value.code == "timeout"


def test_malformed_json_becomes_invalid_response():
    http = FakeHttpTransport(responses=[HttpResponse(status_code=200, text="not json")])
    with pytest.raises(ProviderError) as exc:
        _provider(http).generate(_request())
    assert exc.value.code == "invalid_response"


def test_streaming_aggregates_to_text():
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]
    http = FakeHttpTransport(stream_lines=lines)
    chunks = list(_provider(http).generate_stream(_request()))
    aggregated = "".join(chunk.text for chunk in chunks)
    assert aggregated == "Hello world"
    assert chunks[-1].done is True
