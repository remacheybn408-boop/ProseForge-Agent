from collections.abc import Iterator

import pytest

from proseforge_agent.llm import (
    CapabilityProbeResult,
    CapabilityProber,
    FakeProvider,
    ProviderRequest,
    StreamChunk,
)
from proseforge_agent.llm.capabilities import (
    FAIL,
    SKIPPED,
    capability_matrix,
)


@pytest.fixture
def fake_provider():
    return FakeProvider(name="fake", model="fake-novelist")


class _BrokenProvider:
    """A provider whose generate() always raises, to prove FAIL is recorded."""

    name = "broken"
    model = "broken-model"

    def generate(self, request: ProviderRequest):
        raise RuntimeError("backend exploded")

    def generate_stream(self, request: ProviderRequest) -> Iterator[StreamChunk]:
        raise RuntimeError("backend exploded")


def test_fake_provider_text_and_json_probes_record_evidence(fake_provider):
    results = CapabilityProber(fake_provider).run(["text", "json_mode"])
    assert {r.capability for r in results} == {"text", "json_mode"}
    assert all(r.evidence for r in results)


def test_requires_real_capabilities_skipped_in_offline_mode(fake_provider):
    results = CapabilityProber(fake_provider).run(["tool_calling", "embeddings"])
    assert {r.capability for r in results} == {"tool_calling", "embeddings"}
    assert all(r.status == SKIPPED for r in results)
    # Skipped probes still carry evidence and never mutate config.
    assert all(r.evidence for r in results)


def test_capability_matrix_collapses_results(fake_provider):
    results = CapabilityProber(fake_provider).run(["text", "tool_calling"])
    matrix = capability_matrix(results)
    assert set(matrix) == {"text", "tool_calling"}
    assert matrix["tool_calling"] == SKIPPED


def test_probe_records_failure_instead_of_raising():
    results = CapabilityProber(_BrokenProvider()).run(["text"])
    assert len(results) == 1
    result = results[0]
    assert result.status == FAIL
    assert result.error
    assert result.evidence  # failure still records evidence


def test_results_are_capability_probe_results_with_timestamps(fake_provider):
    results = CapabilityProber(fake_provider).run(["text"])
    result = results[0]
    assert isinstance(result, CapabilityProbeResult)
    assert result.provider == "fake"
    assert result.model == "fake-novelist"
    assert result.checked_at
    assert result.latency_ms >= 0.0


def test_default_run_covers_full_capability_set(fake_provider):
    results = CapabilityProber(fake_provider).run()
    capabilities = {r.capability for r in results}
    assert {"text", "streaming", "json_mode", "tool_calling", "embeddings"} <= capabilities
