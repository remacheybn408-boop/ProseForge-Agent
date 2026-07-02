"""Provider route policy definitions.

Policies are intentionally small, serializable names. The router owns the
selection mechanics; this module centralizes the accepted policy and role names
so CLI, tests, and later workflow state recording use the same vocabulary.
"""

from __future__ import annotations

POLICY_DEFAULT = "default"
POLICY_DOMESTIC_ONLY = "domestic_only"
POLICY_FOREIGN_ONLY = "foreign_only"
POLICY_LOCAL_ONLY = "local_only"
POLICY_PRIVACY_STRICT = "privacy_strict"
POLICY_LOW_COST = "low_cost"
POLICY_HIGH_QUALITY = "high_quality"
POLICY_MANUAL_OVERRIDE = "manual_override"

POLICIES: tuple[str, ...] = (
    POLICY_DEFAULT,
    POLICY_DOMESTIC_ONLY,
    POLICY_FOREIGN_ONLY,
    POLICY_LOCAL_ONLY,
    POLICY_PRIVACY_STRICT,
    POLICY_LOW_COST,
    POLICY_HIGH_QUALITY,
    POLICY_MANUAL_OVERRIDE,
)

ROLES: tuple[str, ...] = (
    "planner",
    "drafter",
    "critic",
    "reviser",
    "memory",
    "embedding",
    "market_analyst",
    "researcher",
    "code_assistant",
)

RETRYABLE_ERRORS: frozenset[str] = frozenset(
    {"timeout", "rate_limit", "temporary", "network", "server_error", "invalid_response"}
)
NON_RETRYABLE_ERRORS: frozenset[str] = frozenset(
    {"auth", "permission", "policy", "invalid_request", "quota"}
)


def is_retryable_error(error_kind: str) -> bool:
    """Return whether a provider error should advance to fallback."""
    return error_kind in RETRYABLE_ERRORS


__all__ = [
    "POLICY_DEFAULT",
    "POLICY_DOMESTIC_ONLY",
    "POLICY_FOREIGN_ONLY",
    "POLICY_LOCAL_ONLY",
    "POLICY_PRIVACY_STRICT",
    "POLICY_LOW_COST",
    "POLICY_HIGH_QUALITY",
    "POLICY_MANUAL_OVERRIDE",
    "POLICIES",
    "ROLES",
    "RETRYABLE_ERRORS",
    "NON_RETRYABLE_ERRORS",
    "is_retryable_error",
]
