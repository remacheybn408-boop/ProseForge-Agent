"""Scoped sub-agent delegation over independent AgentLoop instances."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from typing import Any

from .loop import Budget
from .permissions import PERMISSION_LEVELS

_ORDER = {name: index for index, name in enumerate(PERMISSION_LEVELS)}


def _clamp_permission(requested: str, parent: str) -> str:
    requested_index = _ORDER.get(requested, 0)
    parent_index = _ORDER.get(parent, 0)
    return requested if requested_index <= parent_index else parent


@dataclass(frozen=True)
class Scope:
    """Scope granted to one delegated sub-agent."""

    permission_ceiling: str = "read_only"
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    budget: Budget = field(default_factory=lambda: Budget(max_iterations=3))

    def clamped(self, parent_ceiling: str) -> "Scope":
        return replace(
            self,
            permission_ceiling=_clamp_permission(self.permission_ceiling, parent_ceiling),
        )

    def to_context(self) -> dict[str, Any]:
        return {
            "permission_ceiling": self.permission_ceiling,
            "allowed_tools": list(self.allowed_tools),
            "budget": {
                "max_iterations": self.budget.max_iterations,
                "cost_cap": self.budget.cost_cap,
            },
            "isolated": True,
        }


@dataclass(frozen=True)
class SubAgentResult:
    """Contained result from one delegated sub-agent."""

    task: str
    status: str
    output: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    used_budget: int = 0
    effective_ceiling: str = "read_only"
    error: str = ""


class SubAgentRunner:
    """Run delegated tasks in isolated loops with clamped permissions."""

    def __init__(self, loop_factory, parent_ceiling: str = "read_only") -> None:
        self._loop_factory = loop_factory
        self._parent_ceiling = parent_ceiling

    def delegate(
        self,
        task: str,
        scope: Scope,
        *,
        parent_context: dict[str, Any] | None = None,
    ) -> SubAgentResult:
        effective_scope = scope.clamped(self._parent_ceiling)
        sub_context = dict(effective_scope.to_context())
        if parent_context:
            sub_context["parent_context_keys"] = sorted(parent_context)

        try:
            loop = self._loop_factory(effective_scope)
            result = loop.run(goal=task, context=sub_context)
        except Exception as exc:  # noqa: BLE001 - sub-agent failures are contained
            return SubAgentResult(
                task=task,
                status="failed",
                effective_ceiling=effective_scope.permission_ceiling,
                error=str(exc),
            )

        return SubAgentResult(
            task=task,
            status=result.status,
            output=result.final_text,
            events=list(result.events),
            used_budget=len(result.steps),
            effective_ceiling=effective_scope.permission_ceiling,
        )

    def delegate_many(self, tasks: list[tuple[str, Scope]]) -> list[SubAgentResult]:
        with ThreadPoolExecutor(max_workers=max(1, len(tasks))) as executor:
            futures = [executor.submit(self.delegate, task, scope) for task, scope in tasks]
            return [future.result() for future in futures]

    def aggregate(self, results: list[SubAgentResult]) -> str:
        return "\n".join(
            f"{result.task}: {result.status} ({result.effective_ceiling})"
            for result in results
        )


__all__ = ["Scope", "SubAgentResult", "SubAgentRunner"]
