"""Capability flags and safe-mode boot.

Every optional subsystem (chat, service API, local models, planning, providers,
memory, retrieval, workflow) is gated here. At boot, :class:`CapabilityRegistry`
reads capability flags from config, runs a lightweight self-check per subsystem,
and produces a resolved :class:`CapabilityMap`. A subsystem whose self-check
raises is auto-disabled with a reason and a safe-mode event — boot never crashes,
so the rest of the product keeps running (degraded, not down).

Calling a disabled capability through :meth:`CapabilityMap.require` returns a
readable :class:`ConfigurationError` with a recovery command and a trace id,
never a stack trace. Core capabilities can never be disabled.

This implements the Blast-Radius Contract in
``architecture/10-modularity-and-recovery.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import uuid4

from .errors import ConfigurationError

# Core capabilities are load-bearing and can never be disabled.
CORE_CAPABILITIES: tuple[str, ...] = ("config", "cli", "capabilities", "concurrency", "errors")

# Every non-core subsystem that may be gated off.
NON_CORE_CAPABILITIES: tuple[str, ...] = (
    "chat",
    "service",
    "local_models",
    "planning",
    "providers",
    "memory",
    "retrieval",
    "workflow",
)

ENABLED = "enabled"
DEGRADED = "degraded"
DISABLED = "disabled"


@dataclass(frozen=True)
class CapabilityState:
    """Resolved status of one capability."""

    name: str
    status: str
    reason: str = ""
    core: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "reason": self.reason, "core": self.core}


@dataclass(frozen=True)
class CapabilityMap:
    """Resolved capability statuses; callers gate features through :meth:`require`."""

    states: dict[str, CapabilityState] = field(default_factory=dict)

    def status(self, name: str) -> str:
        state = self.states.get(name)
        return state.status if state is not None else DISABLED

    def reason(self, name: str) -> str:
        state = self.states.get(name)
        return state.reason if state is not None else f"unknown capability {name!r}"

    def require(self, name: str) -> None:
        """Raise :class:`ConfigurationError` with recovery guidance if disabled."""
        state = self.states.get(name)
        if state is not None and state.status != DISABLED:
            return
        trace_id = f"trace-{uuid4().hex[:12]}"
        reason = state.reason if state is not None else f"unknown capability {name!r}"
        raise ConfigurationError(
            f"capability '{name}' is disabled: {reason}. "
            f"Recovery: re-enable it in config or run `pf-agent status --capabilities` "
            f"to inspect health (trace {trace_id})."
        )

    def disabled(self) -> list[str]:
        return sorted(n for n, s in self.states.items() if s.status == DISABLED)

    def to_dict(self) -> dict[str, Any]:
        return {name: state.to_dict() for name, state in sorted(self.states.items())}


class CapabilityRegistry:
    """Resolve capability flags and self-checks into a :class:`CapabilityMap`."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        checks: dict[str, Callable[[], Any]] | None = None,
        *,
        cli_overrides: dict[str, bool] | None = None,
        event_bus: Any = None,
    ) -> None:
        self._config = config or {}
        self._checks = checks or {}
        self._cli_overrides = cli_overrides or {}
        self._event_bus = event_bus

    def _flags(self) -> dict[str, bool]:
        flags = self._config.get("capabilities")
        if not isinstance(flags, dict):
            flags = {}
        return {str(k): bool(v) for k, v in flags.items()}

    def _names(self) -> list[str]:
        names = set(NON_CORE_CAPABILITIES)
        names.update(self._checks.keys())
        names.update(self._flags().keys())
        names.update(self._cli_overrides.keys())
        names.difference_update(CORE_CAPABILITIES)
        return sorted(names)

    def boot(self) -> CapabilityMap:
        states: dict[str, CapabilityState] = {}

        # Core capabilities are always enabled, regardless of flags or checks.
        for name in CORE_CAPABILITIES:
            states[name] = CapabilityState(name=name, status=ENABLED, reason="core capability", core=True)

        flags = self._flags()
        for name in self._names():
            # CLI flags override config; config overrides the default (enabled).
            if name in self._cli_overrides:
                wanted = self._cli_overrides[name]
                source = "cli flag"
            elif name in flags:
                wanted = flags[name]
                source = "config"
            else:
                wanted = True
                source = "default"

            if not wanted:
                states[name] = CapabilityState(
                    name=name, status=DISABLED, reason=f"disabled by {source}"
                )
                continue

            state = self._run_self_check(name)
            states[name] = state
            if state.status == DISABLED:
                self._emit_safe_mode(name, state.reason)

        return CapabilityMap(states=states)

    def _run_self_check(self, name: str) -> CapabilityState:
        check = self._checks.get(name)
        if check is None:
            return CapabilityState(name=name, status=ENABLED, reason="no self-check")
        try:
            outcome = check()
        except Exception as exc:  # noqa: BLE001 - failure auto-disables, never crashes boot
            return CapabilityState(name=name, status=DISABLED, reason=str(exc))
        # A check may return a DoctorCheck-shaped object to signal degraded health.
        status = getattr(outcome, "status", None)
        if status == "warn":
            return CapabilityState(
                name=name, status=DEGRADED, reason=getattr(outcome, "detail", "degraded")
            )
        if status == "fail":
            return CapabilityState(
                name=name, status=DISABLED, reason=getattr(outcome, "detail", "self-check failed")
            )
        return CapabilityState(name=name, status=ENABLED, reason="self-check ok")

    def _emit_safe_mode(self, name: str, reason: str) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.emit("capability.auto_disabled", {"capability": name, "reason": reason})
        except Exception:  # noqa: BLE001 - diagnostics must never crash safe-mode boot
            pass


__all__ = [
    "CORE_CAPABILITIES",
    "NON_CORE_CAPABILITIES",
    "CapabilityState",
    "CapabilityMap",
    "CapabilityRegistry",
    "ENABLED",
    "DEGRADED",
    "DISABLED",
]
