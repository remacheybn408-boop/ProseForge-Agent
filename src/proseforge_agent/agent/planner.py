"""Task planner and TODO tracking for the autonomous loop.

`TaskPlanner` decomposes a goal into an ordered :class:`TaskList` of tracked
sub-tasks with dependencies. The plan is *data, not execution*: the planner runs
no tools and calls no provider except through an injected ``planner_hook`` (so
tests stay deterministic with the fake). The autonomous loop (Task 68) selects
the next runnable task and writes status back. A blocked sub-task records a
reason and is never silently skipped, and the plan can be revised mid-run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from ..errors import ProseForgeAgentError

VALID_STATUSES: tuple[str, ...] = ("pending", "in_progress", "done", "blocked")


class PlanError(ProseForgeAgentError):
    """Raised on an invalid plan operation (unknown task, missing block reason)."""


@dataclass
class TaskItem:
    """One tracked sub-task."""

    id: str
    title: str
    status: str = "pending"
    depends_on: list[str] = field(default_factory=list)
    result_ref: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "depends_on": list(self.depends_on),
            "result_ref": self.result_ref,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskItem":
        return cls(
            id=payload["id"],
            title=payload["title"],
            status=payload.get("status", "pending"),
            depends_on=list(payload.get("depends_on", [])),
            result_ref=payload.get("result_ref", ""),
            reason=payload.get("reason", ""),
        )


class TaskList:
    """An ordered, dependency-aware list of tracked sub-tasks."""

    def __init__(self, items: list[TaskItem] | None = None) -> None:
        self.items: list[TaskItem] = list(items or [])

    def get(self, task_id: str) -> TaskItem:
        for item in self.items:
            if item.id == task_id:
                return item
        raise PlanError(f"unknown task {task_id!r}")

    def _done_ids(self) -> set[str]:
        return {item.id for item in self.items if item.status == "done"}

    def next(self) -> TaskItem | None:
        """Return the next runnable task: pending with all dependencies done."""
        done = self._done_ids()
        for item in self.items:
            if item.status == "pending" and all(dep in done for dep in item.depends_on):
                return item
        return None

    def update(
        self,
        task_id: str,
        status: str,
        *,
        reason: str = "",
        result_ref: str = "",
    ) -> TaskItem:
        if status not in VALID_STATUSES:
            raise PlanError(f"invalid task status {status!r}")
        item = self.get(task_id)
        if status == "blocked" and not reason:
            raise PlanError(f"task {task_id!r} cannot be blocked without a reason")
        item.status = status
        if reason:
            item.reason = reason
        if result_ref:
            item.result_ref = result_ref
        return item

    def add(self, item: TaskItem) -> TaskItem:
        """Add a sub-task mid-run without disturbing existing task status."""
        if any(existing.id == item.id for existing in self.items):
            raise PlanError(f"task {item.id!r} already exists")
        self.items.append(item)
        return item

    def is_complete(self) -> bool:
        return all(item.status in ("done", "blocked") for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"items": [item.to_dict() for item in self.items]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskList":
        return cls([TaskItem.from_dict(p) for p in payload.get("items", [])])

    def render_lines(self) -> list[str]:
        lines = []
        for item in self.items:
            suffix = f" — {item.reason}" if item.reason else ""
            deps = f" (after {', '.join(item.depends_on)})" if item.depends_on else ""
            lines.append(f"[{item.status}] {item.id}: {item.title}{deps}{suffix}")
        return lines


# Default decomposition stages for a writing goal. Each stage depends on the
# previous one, forming a deterministic linear plan.
_DEFAULT_STAGES: tuple[tuple[str, str], ...] = (
    ("gather", "检索与梳理上下文"),
    ("outline", "草拟结构大纲"),
    ("draft", "撰写初稿"),
    ("revise", "自检与修订"),
)


class TaskPlanner:
    """Decompose a goal into a tracked :class:`TaskList`."""

    def __init__(self, planner_hook: Callable[[str, dict | None], list[TaskItem]] | None = None) -> None:
        self._hook = planner_hook

    def decompose(self, goal: str, context: dict | None = None) -> TaskList:
        if self._hook is not None:
            items = list(self._hook(goal, context))
            return TaskList(items)
        return TaskList(self._default_decompose(goal))

    @staticmethod
    def _default_decompose(goal: str) -> list[TaskItem]:
        items: list[TaskItem] = []
        previous: str | None = None
        for index, (stage, label) in enumerate(_DEFAULT_STAGES, start=1):
            task_id = f"t{index}-{stage}"
            items.append(
                TaskItem(
                    id=task_id,
                    title=f"{label}：{goal}",
                    depends_on=[previous] if previous else [],
                )
            )
            previous = task_id
        return items


__all__ = ["TaskItem", "TaskList", "TaskPlanner", "PlanError", "VALID_STATUSES"]
