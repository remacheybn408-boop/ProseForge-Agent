"""Capability-aware provider fallback routing.

The router consumes a matrix shaped for automation and returns an explainable
decision: one selected provider, a list of skipped candidates with reasons, and
audit metadata suitable for workflow state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ..errors import ConfigurationError
from ..reports import Report, ReportSection
from .capabilities import PASS
from .policies import (
    POLICIES,
    POLICY_DOMESTIC_ONLY,
    POLICY_FOREIGN_ONLY,
    POLICY_HIGH_QUALITY,
    POLICY_LOCAL_ONLY,
    POLICY_LOW_COST,
    POLICY_MANUAL_OVERRIDE,
    POLICY_PRIVACY_STRICT,
    is_retryable_error,
)


@dataclass(frozen=True)
class RouteProvider:
    """Provider entry normalized from the route matrix."""

    name: str
    family: str
    model: str
    locality: str
    privacy: str
    cost: str
    quality: str
    reliability: float
    certified: bool
    capabilities: dict[str, str]
    api_key_env: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteProvider":
        return cls(
            name=data["name"],
            family=data.get("family", data.get("kind", "")),
            model=data.get("model", ""),
            locality=data.get("locality", "foreign"),
            privacy=data.get("privacy", "remote"),
            cost=data.get("cost", "medium"),
            quality=data.get("quality", "medium"),
            reliability=float(data.get("reliability", 0.0)),
            certified=bool(data.get("certified", False)),
            capabilities=dict(data.get("capabilities") or {}),
            api_key_env=data.get("api_key_env"),
        )

    def to_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "model": self.model,
            "locality": self.locality,
            "privacy": self.privacy,
            "cost": self.cost,
            "quality": self.quality,
            "reliability": self.reliability,
            "certified": self.certified,
        }


@dataclass(frozen=True)
class RouteSkip:
    """A candidate provider skipped during route selection."""

    provider: str
    reason: str
    detail: str = ""

    def to_line(self) -> str:
        suffix = f": {self.detail}" if self.detail else ""
        return f"{self.provider} -> {self.reason}{suffix}"

    def to_data(self) -> dict[str, str]:
        return {"provider": self.provider, "reason": self.reason, "detail": self.detail}


@dataclass(frozen=True)
class RouteDecision:
    """Explainable provider routing result."""

    role: str
    policy: str
    selected: RouteProvider | None
    skipped: list[RouteSkip] = field(default_factory=list)
    blocked_reason: str = ""
    audit: dict[str, Any] = field(default_factory=dict)

    def to_report(self) -> Report:
        selected_line = (
            f"{self.selected.name} ({self.selected.family}/{self.selected.model})"
            if self.selected
            else f"blocked: {self.blocked_reason}"
        )
        return Report(
            title="Provider Route Decision",
            status="ok" if self.selected else "blocked",
            next_action="Record this provider attempt in workflow state",
            sections=[
                ReportSection("Selected", [selected_line]),
                ReportSection("Skipped", [skip.to_line() for skip in self.skipped]),
            ],
            data={
                "role": self.role,
                "policy": self.policy,
                "selected": self.selected.to_data() if self.selected else None,
                "skipped": [skip.to_data() for skip in self.skipped],
                "blocked_reason": self.blocked_reason,
                "audit": dict(self.audit),
            },
        )


class ProviderRouter:
    """Select providers by policy, capabilities, certification, and fallback."""

    def __init__(self, route_matrix: dict[str, Any]) -> None:
        self._providers = {
            provider.name: provider
            for provider in (
                RouteProvider.from_dict(entry)
                for entry in route_matrix.get("providers", [])
            )
        }
        self._roles = dict(route_matrix.get("roles") or {})

    def select(
        self,
        *,
        role: str,
        policy: str = "default",
        privacy_class: str = "standard",
        manual_provider: str | None = None,
        exclude: set[str] | None = None,
        audit: dict[str, Any] | None = None,
    ) -> RouteDecision:
        if policy not in POLICIES:
            raise ConfigurationError(f"unknown provider route policy {policy!r}")

        skips: list[RouteSkip] = []
        audit_data = dict(audit or {})

        if policy == POLICY_MANUAL_OVERRIDE:
            return self._select_manual(
                role=role,
                provider_name=manual_provider,
                skipped=skips,
                audit=audit_data,
            )

        candidates = self._candidates_for(role)
        ranked = self._rank(candidates, policy)
        required = self._required_capabilities(role)
        excluded = exclude or set()
        for provider in ranked:
            skip = self._skip_reason(provider, required, policy, privacy_class, excluded)
            if skip is not None:
                skips.append(skip)
                continue
            return RouteDecision(
                role=role,
                policy=policy,
                selected=provider,
                skipped=skips,
                audit=audit_data,
            )
        return RouteDecision(
            role=role,
            policy=policy,
            selected=None,
            skipped=skips,
            blocked_reason="no_provider_available",
            audit=audit_data,
        )

    def fallback_after(
        self,
        *,
        role: str,
        failed_provider: str,
        error_kind: str,
        policy: str = "default",
    ) -> RouteDecision:
        audit = {"failed_provider": failed_provider, "error_kind": error_kind}
        if not is_retryable_error(error_kind):
            return RouteDecision(
                role=role,
                policy=policy,
                selected=None,
                skipped=[
                    RouteSkip(
                        provider=failed_provider,
                        reason="non_retryable_error",
                        detail=error_kind,
                    )
                ],
                blocked_reason="non_retryable_error",
                audit=audit,
            )
        decision = self.select(
            role=role,
            policy=policy,
            exclude={failed_provider},
            audit=audit,
        )
        return RouteDecision(
            role=decision.role,
            policy=decision.policy,
            selected=decision.selected,
            skipped=[
                RouteSkip(
                    provider=failed_provider,
                    reason="retryable_failure",
                    detail=error_kind,
                ),
                *decision.skipped,
            ],
            blocked_reason=decision.blocked_reason,
            audit=decision.audit,
        )

    def decisions_for_all_policies(self, role: str = "drafter") -> list[RouteDecision]:
        """Build one decision per policy, excluding manual override."""
        return [
            self.select(role=role, policy=policy)
            for policy in POLICIES
            if policy != POLICY_MANUAL_OVERRIDE
        ]

    def _select_manual(
        self,
        *,
        role: str,
        provider_name: str | None,
        skipped: list[RouteSkip],
        audit: dict[str, Any],
    ) -> RouteDecision:
        if not provider_name or provider_name not in self._providers:
            return RouteDecision(
                role=role,
                policy=POLICY_MANUAL_OVERRIDE,
                selected=None,
                skipped=skipped,
                blocked_reason="manual_provider_missing",
                audit=audit,
            )
        provider = self._providers[provider_name]
        for candidate in self._candidates_for(role):
            if candidate.name != provider_name:
                skipped.append(RouteSkip(candidate.name, "manual_override"))
        audit["manual_override"] = provider_name
        return RouteDecision(
            role=role,
            policy=POLICY_MANUAL_OVERRIDE,
            selected=provider,
            skipped=skipped,
            audit=audit,
        )

    def _candidates_for(self, role: str) -> list[RouteProvider]:
        spec = self._roles.get(role) or {}
        names = spec.get("candidates") or list(self._providers)
        return [self._providers[name] for name in names if name in self._providers]

    def _required_capabilities(self, role: str) -> list[str]:
        spec = self._roles.get(role) or {}
        return list(spec.get("required_capabilities") or ["text"])

    def _rank(self, candidates: list[RouteProvider], policy: str) -> list[RouteProvider]:
        if policy == POLICY_LOW_COST:
            cost_rank = {"low": 0, "medium": 1, "high": 2}
            return sorted(candidates, key=lambda p: (cost_rank.get(p.cost, 1), -p.reliability))
        if policy == POLICY_HIGH_QUALITY:
            quality_rank = {"low": 0, "medium": 1, "high": 2}
            return sorted(candidates, key=lambda p: (-quality_rank.get(p.quality, 1), -p.reliability))
        return list(candidates)

    def _skip_reason(
        self,
        provider: RouteProvider,
        required: list[str],
        policy: str,
        privacy_class: str,
        exclude: set[str],
    ) -> RouteSkip | None:
        if provider.name in exclude:
            return RouteSkip(provider.name, "excluded")
        if policy == POLICY_DOMESTIC_ONLY and provider.locality != "domestic":
            return RouteSkip(provider.name, "locality_policy", "domestic_only")
        if policy == POLICY_FOREIGN_ONLY and provider.locality != "foreign":
            return RouteSkip(provider.name, "locality_policy", "foreign_only")
        if policy == POLICY_LOCAL_ONLY and provider.locality != "local":
            return RouteSkip(provider.name, "locality_policy", "local_only")
        if policy == POLICY_PRIVACY_STRICT and (
            privacy_class == "local_only" and provider.privacy != "local"
        ):
            return RouteSkip(provider.name, "privacy_policy", privacy_class)
        missing = [
            cap for cap in required if provider.capabilities.get(cap) != PASS
        ]
        if missing:
            return RouteSkip(provider.name, "missing_capability", ",".join(missing))
        if not provider.certified:
            return RouteSkip(provider.name, "not_certified")
        if provider.api_key_env and not os.environ.get(provider.api_key_env):
            return RouteSkip(provider.name, "missing_api_key", provider.api_key_env)
        return None


__all__ = [
    "ProviderRouter",
    "RouteDecision",
    "RouteProvider",
    "RouteSkip",
]
