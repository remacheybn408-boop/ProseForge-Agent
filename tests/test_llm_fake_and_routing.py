from proseforge_agent.llm import FakeProvider, Message, ProviderRequest


def _request():
    return ProviderRequest(role="drafter", messages=[Message(role="user", content="chapter")])


def test_fake_provider_returns_deterministic_result():
    provider = FakeProvider(name="fake_main", model="fake-novelist")
    result = provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="chapter")])
    )
    assert result.provider == "fake_main"
    assert "fake-novelist" in result.text
    assert result.usage.total_tokens >= 0


def test_fake_provider_is_deterministic_across_calls():
    provider = FakeProvider(name="fake_main", model="fake-novelist")
    first = provider.generate(_request())
    second = provider.generate(_request())
    assert first.text == second.text
    assert first.usage.total_tokens == second.usage.total_tokens


def test_fake_provider_stream_aggregates_to_generate_text():
    provider = FakeProvider(name="fake_main", model="fake-novelist")
    chunks = list(provider.generate_stream(_request()))
    aggregated = "".join(chunk.text for chunk in chunks)
    assert aggregated == provider.generate(_request()).text
    assert chunks[-1].done is True


def test_fake_usage_total_equals_prompt_plus_completion():
    provider = FakeProvider(name="fake_main", model="fake-novelist")
    usage = provider.generate(_request()).usage
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens
