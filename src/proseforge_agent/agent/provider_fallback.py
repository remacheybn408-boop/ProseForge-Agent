"""Provider fallback chain execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..errors import ProviderError
from ..llm import ProviderRequest, ProviderResult


FALLBACK_ERROR_CODES = {
    "timeout",
    "rate_limit",
    "invalid_response",
    "unavailable",
    "provider_unavailable",
    "quota",
    "insufficient_quota",
    "context_too_large",
    "model_missing",
    "model_not_found",
}


@dataclass(frozen=True)
class ProviderFallbackAttempt:
    """One provider attempt in a fallback chain."""

    provider: str
    status: str
    fallback_reason: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderFallbackResult:
    """Result selected from a fallback chain."""

    result: ProviderResult
    attempts: list[ProviderFallbackAttempt] = field(default_factory=list)
    selected_provider: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": {
                "provider": self.result.provider,
                "model": self.result.model,
                "text": self.result.text,
                "usage": self.result.usage.__dict__,
                "raw": self.result.raw,
            },
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "selected_provider": self.selected_provider,
        }


class ProviderFallbackChain:
    """Try providers in order when failures are explicitly fallback-safe."""

    def __init__(self, providers: list[Any]) -> None:
        self.providers = providers

    def generate(self, request: ProviderRequest) -> ProviderFallbackResult:
        attempts: list[ProviderFallbackAttempt] = []
        last_error: ProviderError | None = None
        for provider in self.providers:
            name = str(getattr(provider, "name", "provider"))
            try:
                result = provider.generate(request)
            except ProviderError as exc:
                reason = fallback_reason(exc)
                attempts.append(
                    ProviderFallbackAttempt(
                        provider=name,
                        status="fallback" if reason else "failed",
                        fallback_reason=reason,
                        error=str(exc),
                    )
                )
                if not reason:
                    raise
                last_error = exc
                continue
            if not result.text:
                error = ProviderError("provider returned an empty response")
                error.code = "invalid_response"
                attempts.append(
                    ProviderFallbackAttempt(
                        provider=name,
                        status="fallback",
                        fallback_reason="invalid_response",
                        error=str(error),
                    )
                )
                last_error = error
                continue
            attempts.append(ProviderFallbackAttempt(provider=name, status="ok"))
            return ProviderFallbackResult(result=result, attempts=attempts, selected_provider=name)
        if last_error is not None:
            raise last_error
        raise ProviderError("provider fallback chain is empty")


def fallback_reason(error: Exception) -> str:
    code = str(getattr(error, "code", "") or "").lower().replace("-", "_")
    if code in FALLBACK_ERROR_CODES:
        return _canonical_reason(code)
    message = str(error).lower()
    for code_candidate in FALLBACK_ERROR_CODES:
        if code_candidate.replace("_", " ") in message or code_candidate in message:
            return _canonical_reason(code_candidate)
    return ""


def _canonical_reason(code: str) -> str:
    if code in {"provider_unavailable"}:
        return "unavailable"
    if code in {"insufficient_quota"}:
        return "quota"
    if code in {"model_not_found"}:
        return "model_missing"
    return code


__all__ = [
    "FALLBACK_ERROR_CODES",
    "ProviderFallbackAttempt",
    "ProviderFallbackChain",
    "ProviderFallbackResult",
    "fallback_reason",
]
