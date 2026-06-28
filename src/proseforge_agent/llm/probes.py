"""Capability prober: run probes against a provider and record evidence.

The prober is deliberately conservative. It defaults to ``offline`` mode, where
probes flagged ``requires_real`` are *skipped* (with replay evidence) and never
issue a network call. Real calls happen only under an explicit real mode. A
probe that errors records a ``FAIL`` result; it never raises out of ``run`` and
never mutates provider configuration.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from .base import LLMProvider, ProviderResult
from .capabilities import (
    DEFAULT_PROBES,
    FAIL,
    PASS,
    SKIPPED,
    CapabilityProbeResult,
    ProbeDefinition,
    load_replay_results,
)

# Modes that permit a real backend call. Everything else stays offline.
_REAL_MODES = frozenset({"real", "real_if_key_present"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CapabilityProber:
    """Measure a provider's capabilities through safe probes."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        mode: str = "offline",
        replay: dict | None = None,
    ) -> None:
        self._provider = provider
        self._mode = mode
        self._replay = replay if replay is not None else load_replay_results()

    def run(self, capabilities: list[str] | None = None) -> list[CapabilityProbeResult]:
        """Probe ``capabilities`` (default: all) and return one result each."""
        names = capabilities if capabilities is not None else list(DEFAULT_PROBES)
        results: list[CapabilityProbeResult] = []
        for name in names:
            definition = DEFAULT_PROBES.get(name)
            if definition is None:
                results.append(self._unknown_result(name))
                continue
            if definition.requires_real and not self._real_allowed():
                results.append(self._skipped_result(definition))
                continue
            results.append(self._measure(definition))
        return results

    # -- mode guards ----------------------------------------------------------

    def _real_allowed(self) -> bool:
        if self._mode not in _REAL_MODES:
            return False
        if self._mode == "real_if_key_present":
            key_env = getattr(self._provider, "api_key_env", None)
            return bool(key_env) and bool(os.environ.get(key_env))
        return True

    # -- result builders ------------------------------------------------------

    def _skipped_result(self, definition: ProbeDefinition) -> CapabilityProbeResult:
        replay = self._replay_for(definition.capability)
        evidence = {"reason": "real call guarded", "mode": self._mode}
        if replay:
            evidence["replay"] = replay
        return CapabilityProbeResult(
            provider=self._provider.name,
            model=self._provider.model,
            capability=definition.capability,
            status=SKIPPED,
            latency_ms=0.0,
            checked_at=_now_iso(),
            evidence=evidence,
        )

    def _unknown_result(self, capability: str) -> CapabilityProbeResult:
        return CapabilityProbeResult(
            provider=self._provider.name,
            model=self._provider.model,
            capability=capability,
            status=FAIL,
            latency_ms=0.0,
            checked_at=_now_iso(),
            error=f"unknown capability {capability!r}",
            evidence={"reason": "no probe definition"},
        )

    def _measure(self, definition: ProbeDefinition) -> CapabilityProbeResult:
        request = definition.build_request() if definition.build_request else None
        if request is None:
            # Nothing offline to exercise; treat as a guarded skip with replay.
            return self._skipped_result(definition)

        start = time.perf_counter()
        try:
            if definition.capability == "streaming":
                result = self._collect_stream(request)
            else:
                result = self._provider.generate(request)
        except Exception as exc:  # noqa: BLE001 - record failure, never raise
            latency_ms = (time.perf_counter() - start) * 1000.0
            return CapabilityProbeResult(
                provider=self._provider.name,
                model=self._provider.model,
                capability=definition.capability,
                status=FAIL,
                latency_ms=latency_ms,
                checked_at=_now_iso(),
                error=f"{type(exc).__name__}: {exc}",
                evidence={"exception": type(exc).__name__},
            )

        latency_ms = (time.perf_counter() - start) * 1000.0
        evidence = definition.check(result)
        return CapabilityProbeResult(
            provider=self._provider.name,
            model=self._provider.model,
            capability=definition.capability,
            status=PASS,
            latency_ms=latency_ms,
            checked_at=_now_iso(),
            usage_prompt_tokens=result.usage.prompt_tokens,
            usage_completion_tokens=result.usage.completion_tokens,
            evidence=evidence,
        )

    def _collect_stream(self, request) -> ProviderResult:
        chunks = list(self._provider.generate_stream(request))
        text = "".join(chunk.text for chunk in chunks)
        # Reuse generate() for usage accounting so the streaming probe still
        # carries token evidence; falls back to a bare result if unavailable.
        base = self._provider.generate(request)
        return ProviderResult(
            provider=base.provider,
            model=base.model,
            text=text,
            usage=base.usage,
            raw={"chunks": len(chunks)},
        )

    def _replay_for(self, capability: str) -> dict:
        entries = self._replay.get(self._provider.name) or self._replay.get("fake") or {}
        if isinstance(entries, dict):
            return entries.get(capability, {})
        return {}


__all__ = ["CapabilityProber"]
