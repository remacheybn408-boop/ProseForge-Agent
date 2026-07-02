from pathlib import Path

import yaml

from proseforge_agent.llm.policies import is_retryable_error
from proseforge_agent.llm.router import ProviderRouter, RouteDecision


ROUTE_MATRIX = Path(__file__).parent / "fixtures" / "providers" / "route_matrix.yaml"


def _route_matrix():
    return yaml.safe_load(ROUTE_MATRIX.read_text(encoding="utf-8"))


def test_privacy_strict_policy_blocks_remote_provider_for_sensitive_memory():
    decision = ProviderRouter(_route_matrix()).select(
        role="memory",
        policy="privacy_strict",
        privacy_class="local_only",
    )
    assert decision.selected.family == "fake"
    assert any(skip.reason == "privacy_policy" for skip in decision.skipped)


def test_domestic_only_policy_blocks_foreign_candidates():
    decision = ProviderRouter(_route_matrix()).select(role="drafter", policy="domestic_only")
    assert decision.selected.name == "domestic_writer"
    assert any(skip.provider == "cloud_writer" and skip.reason == "locality_policy" for skip in decision.skipped)


def test_missing_capability_and_missing_key_are_recorded_as_skips(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    decision = ProviderRouter(_route_matrix()).select(role="researcher", policy="high_quality")
    reasons = {skip.reason for skip in decision.skipped}
    assert "missing_capability" in reasons
    assert "missing_api_key" in reasons
    assert decision.selected.name == "fake_local"


def test_manual_override_selects_named_provider_and_audits_reason(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    decision = ProviderRouter(_route_matrix()).select(
        role="drafter",
        policy="manual_override",
        manual_provider="cloud_writer",
    )
    assert decision.selected.name == "cloud_writer"
    assert decision.audit["manual_override"] == "cloud_writer"
    assert any(skip.reason == "manual_override" for skip in decision.skipped)


def test_non_retryable_error_stops_without_fallback():
    decision = ProviderRouter(_route_matrix()).fallback_after(
        role="drafter",
        failed_provider="cloud_writer",
        error_kind="auth",
    )
    assert decision.selected is None
    assert decision.blocked_reason == "non_retryable_error"


def test_retryable_error_falls_back_to_next_candidate(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "present")
    decision = ProviderRouter(_route_matrix()).fallback_after(
        role="drafter",
        failed_provider="cloud_writer",
        error_kind="timeout",
    )
    assert decision.selected.name == "domestic_writer"
    assert any(skip.provider == "cloud_writer" and skip.reason == "retryable_failure" for skip in decision.skipped)


def test_invalid_response_error_falls_back_to_next_candidate(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "present")
    decision = ProviderRouter(_route_matrix()).fallback_after(
        role="drafter",
        failed_provider="cloud_writer",
        error_kind="invalid_response",
    )
    assert is_retryable_error("invalid_response") is True
    assert decision.selected.name == "domestic_writer"
    assert any(skip.provider == "cloud_writer" and skip.reason == "retryable_failure" for skip in decision.skipped)


def test_route_decision_builds_report():
    decision = ProviderRouter(_route_matrix()).select(role="memory", policy="local_only")
    report = decision.to_report()
    assert report.title == "Provider Route Decision"
    assert report.status == "ok"
    assert report.data["selected"]["name"] == decision.selected.name
    assert isinstance(decision, RouteDecision)
