"""Capability probe data contracts and probe definitions.

Routing should depend on *observed* model behavior, not static profile claims
alone. This module defines the result record a probe writes, the declarative
probe definitions for each capability, and a helper that collapses results into
a capability matrix the fallback router (Task 29) can consume.

This module is pure data plus definitions; the running of probes lives in
:mod:`proseforge_agent.llm.probes`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .base import Message, ProviderRequest, ProviderResult

# Probe outcomes. A probe always writes one of these; it never mutates config.
PASS = "pass"
FAIL = "fail"
SKIPPED = "skipped"
UNSUPPORTED = "unsupported"

# Offline replay fixture: canned evidence for capabilities that cannot be
# exercised offline (e.g. tool calling, embeddings).
PROBE_RESULTS_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "providers"
    / "probe_results.json"
)


@dataclass(frozen=True)
class CapabilityProbeResult:
    """One capability measurement with evidence.

    Records the provider/model probed, the capability, the outcome status,
    latency, token usage (when a call was made), an ISO timestamp, an error
    string for failures, and an evidence mapping that explains the verdict.
    """

    provider: str
    model: str
    capability: str
    status: str
    latency_ms: float
    checked_at: str
    usage_prompt_tokens: int | None = None
    usage_completion_tokens: int | None = None
    error: str | None = None
    evidence: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ProbeDefinition:
    """Declarative description of how to exercise one capability.

    ``requires_real`` marks probes that need a real backend; in offline mode
    those are skipped (with replay evidence) rather than called. ``build_request``
    constructs the request to send; ``check`` turns a result into evidence.
    """

    capability: str
    requires_real: bool
    build_request: Callable[[], ProviderRequest] | None
    check: Callable[[ProviderResult], dict]


def _user_request(content: str, role: str = "drafter") -> ProviderRequest:
    return ProviderRequest(role=role, messages=[Message(role="user", content=content)])


def _text_check(result: ProviderResult) -> dict:
    sample = result.text[:80]
    return {"sample": sample, "length": len(result.text)}


def _json_check(result: ProviderResult) -> dict:
    try:
        json.loads(result.text)
        parsed = True
    except (ValueError, TypeError):
        parsed = False
    return {"parsed": parsed, "sample": result.text[:80]}


def _long_context_check(result: ProviderResult) -> dict:
    return {
        "prompt_tokens": result.usage.prompt_tokens,
        "returned_text": bool(result.text),
    }


# Probe registry. Text-shaped capabilities are verifiable offline against the
# deterministic fake provider; backend-specific capabilities require real mode.
DEFAULT_PROBES: dict[str, ProbeDefinition] = {
    "text": ProbeDefinition(
        capability="text",
        requires_real=False,
        build_request=lambda: _user_request("Write one sentence."),
        check=_text_check,
    ),
    "streaming": ProbeDefinition(
        capability="streaming",
        requires_real=False,
        build_request=lambda: _user_request("Stream one sentence."),
        check=_text_check,
    ),
    "json_mode": ProbeDefinition(
        capability="json_mode",
        requires_real=False,
        build_request=lambda: _user_request('Return JSON: {"ok": true}'),
        check=_json_check,
    ),
    "long_context": ProbeDefinition(
        capability="long_context",
        requires_real=False,
        build_request=lambda: _user_request("context probe " * 64),
        check=_long_context_check,
    ),
    "tool_calling": ProbeDefinition(
        capability="tool_calling",
        requires_real=True,
        build_request=lambda: _user_request("Call the get_time tool."),
        check=_text_check,
    ),
    "reasoning_controls": ProbeDefinition(
        capability="reasoning_controls",
        requires_real=True,
        build_request=lambda: _user_request("Think step by step, then answer."),
        check=_text_check,
    ),
    "embeddings": ProbeDefinition(
        capability="embeddings",
        requires_real=True,
        build_request=None,
        check=_text_check,
    ),
    "safety_behavior": ProbeDefinition(
        capability="safety_behavior",
        requires_real=True,
        build_request=lambda: _user_request("Refuse politely if unsafe."),
        check=_text_check,
    ),
}


def capability_matrix(results: list[CapabilityProbeResult]) -> dict[str, str]:
    """Collapse probe results into a ``{capability: status}`` map.

    This is the consumption surface for the fallback router (Task 29): later
    results win, so a re-probe of the same capability overrides earlier ones.
    """
    return {result.capability: result.status for result in results}


def load_replay_results(path: str | Path | None = None) -> dict:
    """Load the offline replay fixture, or an empty mapping if absent."""
    fixture = Path(path) if path is not None else PROBE_RESULTS_FIXTURE
    if not fixture.exists():
        return {}
    return json.loads(fixture.read_text(encoding="utf-8"))


__all__ = [
    "PASS",
    "FAIL",
    "SKIPPED",
    "UNSUPPORTED",
    "PROBE_RESULTS_FIXTURE",
    "CapabilityProbeResult",
    "ProbeDefinition",
    "DEFAULT_PROBES",
    "capability_matrix",
    "load_replay_results",
]
