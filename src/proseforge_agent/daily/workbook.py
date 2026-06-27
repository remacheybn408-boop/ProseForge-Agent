"""Date-based daily (and weekly) workbook generation.

The workbook is the writer's daily operating document: a precise date, a
state-based objective, reading/build/verification/integration blocks, a
closeout, and an acceptance checklist. It needs no model access; the next
action comes from the state recommender.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date as _date

from .recommend import ProjectState, Recommendation, StateRecommender


@dataclass
class DailyWorkbook:
    """One day's operating document."""

    date: str
    slug: str
    objective: str
    recommendation: Recommendation
    reading_context: list[str] = field(default_factory=list)
    build_block: list[str] = field(default_factory=list)
    verification_block: list[str] = field(default_factory=list)
    integration_block: list[str] = field(default_factory=list)
    closeout: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    human_review_questions: list[str] = field(default_factory=list)
    acceptance_checklist: list[str] = field(default_factory=list)
    memory_updates: list[str] = field(default_factory=list)
    next_day_risk: list[str] = field(default_factory=list)


@dataclass
class WeeklyRollup:
    """A summary of a week's workbooks."""

    week_start: str
    days: list[str]
    objectives: list[str]
    carried: list[str]


def _next_day(date: str) -> str:
    return _date.fromordinal(_date.fromisoformat(date).toordinal() + 1).isoformat()


class DailyWorkbookEngine:
    """Generate daily workbooks and weekly rollups from project state."""

    def __init__(self) -> None:
        self._recommender = StateRecommender()

    def generate(self, state: ProjectState, date: str) -> DailyWorkbook:
        recommendation = self._recommender.recommend(state)
        chapter = state.current_chapter
        tomorrow = _next_day(date)

        next_day_risk = list(recommendation.carry_over)
        next_day_risk.append(f"Carry unfinished work into {tomorrow}")

        return DailyWorkbook(
            date=date,
            slug=state.slug,
            objective=recommendation.next_action,
            recommendation=recommendation,
            reading_context=[
                f"Read the evidence pack for chapter {chapter}",
                "Review active canon and reader promises",
            ],
            build_block=[recommendation.next_action],
            verification_block=[
                "Run ProseForge post and review gates",
                "Run the project test suite",
            ],
            integration_block=[
                "Accept the approved draft",
                "Commit the chapter with its evidence",
            ],
            closeout=[
                f"Chapter {chapter} drafted and verified",
                "Memory updates recorded",
            ],
            files=[f"drafts/{state.slug}/chapter-{chapter:03d}.md"],
            commands=[f"pf-agent chapter --project {state.slug} --chapter {chapter}"],
            human_review_questions=[
                "Does the chapter honor established canon?",
                "Are reader promises advancing?",
            ],
            acceptance_checklist=[
                f"Date is {date}",
                f"Objective met: {recommendation.next_action}",
                "Acceptance gates green",
            ],
            memory_updates=["Record new canon facts and reader promises as candidates"],
            next_day_risk=next_day_risk,
        )

    def rollup_week(self, workbooks: list[DailyWorkbook], week_start: str) -> WeeklyRollup:
        carried: list[str] = []
        for wb in workbooks:
            carried.extend(wb.recommendation.carry_over)
        return WeeklyRollup(
            week_start=week_start,
            days=[wb.date for wb in workbooks],
            objectives=[wb.objective for wb in workbooks],
            carried=carried,
        )

    def apply_closeout(self, state: ProjectState, *, completed: bool) -> ProjectState:
        if not completed:
            return replace(state, overdue=True)
        return replace(
            state,
            completed_chapters=state.completed_chapters + 1,
            current_chapter=state.current_chapter + 1,
            overdue=False,
        )

    def render_markdown(self, workbook: DailyWorkbook) -> str:
        lines = [
            f"# Daily Workbook — {workbook.date} ({workbook.slug})",
            f"**Objective:** {workbook.objective}",
            "",
            "## Reading Context",
            *[f"- {x}" for x in workbook.reading_context],
            "## Build",
            *[f"- {x}" for x in workbook.build_block],
            "## Verification",
            *[f"- {x}" for x in workbook.verification_block],
            "## Integration",
            *[f"- {x}" for x in workbook.integration_block],
            "## Acceptance Checklist",
            *[f"- [ ] {x}" for x in workbook.acceptance_checklist],
            "## Next-Day Risk",
            *[f"- {x}" for x in workbook.next_day_risk],
        ]
        return "\n".join(lines)

    def render_json(self, workbook: DailyWorkbook) -> dict:
        return {
            "date": workbook.date,
            "slug": workbook.slug,
            "objective": workbook.objective,
            "recommendation": {
                "next_action": workbook.recommendation.next_action,
                "rationale": workbook.recommendation.rationale,
                "priority": workbook.recommendation.priority,
                "carry_over": workbook.recommendation.carry_over,
            },
            "reading_context": workbook.reading_context,
            "build_block": workbook.build_block,
            "verification_block": workbook.verification_block,
            "integration_block": workbook.integration_block,
            "closeout": workbook.closeout,
            "files": workbook.files,
            "commands": workbook.commands,
            "human_review_questions": workbook.human_review_questions,
            "acceptance_checklist": workbook.acceptance_checklist,
            "memory_updates": workbook.memory_updates,
            "next_day_risk": workbook.next_day_risk,
        }


__all__ = ["DailyWorkbook", "WeeklyRollup", "DailyWorkbookEngine"]
