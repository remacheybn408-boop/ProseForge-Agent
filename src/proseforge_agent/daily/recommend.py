"""State-based next-action recommendation for the daily workbook.

The recommendation is driven by project state, not a static date: a provider
failure, a memory-audit risk, a block, or overdue work each change what the
writer should do next, and incomplete work carries forward.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectState:
    """A snapshot of project progress used to recommend the next action."""

    slug: str
    target_chapters: int
    completed_chapters: int
    current_chapter: int
    status: str = "active"
    blocked_reason: str = ""
    overdue: bool = False
    memory_risk: list[str] = field(default_factory=list)
    provider_failed: bool = False
    last_action: str = ""


@dataclass(frozen=True)
class Recommendation:
    """A prioritized, explained next action."""

    next_action: str
    rationale: str
    priority: str
    carry_over: list[str] = field(default_factory=list)


class StateRecommender:
    """Recommend the next action from project state, in priority order."""

    def recommend(self, state: ProjectState) -> Recommendation:
        if state.provider_failed:
            return Recommendation(
                next_action="Resolve the provider failure and re-run the failed model step",
                rationale="A model step failed; output cannot proceed until it is fixed",
                priority="critical",
            )
        if state.memory_risk:
            risks = ", ".join(state.memory_risk)
            return Recommendation(
                next_action=f"Audit memory risks before drafting: {risks}",
                rationale="Unresolved memory risks could introduce continuity errors",
                priority="high",
                carry_over=list(state.memory_risk),
            )
        if state.blocked_reason:
            return Recommendation(
                next_action=f"Unblock: {state.blocked_reason}",
                rationale="Work is blocked and must be cleared before drafting",
                priority="high",
                carry_over=[state.blocked_reason],
            )
        if state.overdue:
            return Recommendation(
                next_action=f"Catch up on overdue chapter {state.current_chapter}",
                rationale="Previous chapter is overdue and carries forward",
                priority="high",
                carry_over=[f"chapter {state.current_chapter}"],
            )
        if state.completed_chapters < state.target_chapters:
            return Recommendation(
                next_action=f"Draft chapter {state.current_chapter}",
                rationale="On track; continue with the next chapter",
                priority="normal",
            )
        return Recommendation(
            next_action="Begin review and closeout; all target chapters are drafted",
            rationale="All target chapters complete",
            priority="normal",
        )


__all__ = ["ProjectState", "Recommendation", "StateRecommender"]
