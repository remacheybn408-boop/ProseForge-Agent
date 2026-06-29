"""Task-success eval harness for the autonomous agent runtime."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable


DEFAULT_THRESHOLD = 0.8


@dataclass(frozen=True)
class GoldenTask:
    """One deterministic task in the agent eval suite."""

    id: str
    goal: str
    success_criteria: dict[str, Any]
    max_iterations: int = 5

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoldenTask":
        criteria = dict(data.get("success_criteria") or {})
        if not criteria:
            raise ValueError(f"golden task {data.get('id', '<missing>')} has no success_criteria")
        return cls(
            id=str(data["id"]),
            goal=str(data["goal"]),
            success_criteria=criteria,
            max_iterations=int(data.get("max_iterations", 5)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvalSuite:
    """A golden suite plus its passing threshold."""

    tasks: list[GoldenTask] = field(default_factory=list)
    threshold: float = DEFAULT_THRESHOLD

    @classmethod
    def load(cls, path: str | Path) -> "EvalSuite":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalSuite":
        tasks = [GoldenTask.from_dict(item) for item in data.get("tasks", [])]
        if not tasks:
            raise ValueError("eval suite must contain at least one task")
        return cls(tasks=tasks, threshold=float(data.get("threshold", DEFAULT_THRESHOLD)))

    @classmethod
    def default(cls) -> "EvalSuite":
        return cls.from_dict(
            {
                "threshold": DEFAULT_THRESHOLD,
                "tasks": [
                    {
                        "id": "hello-chat",
                        "goal": "answer a friendly hello",
                        "success_criteria": {
                            "status": "completed",
                            "contains": "answer a friendly hello",
                            "min_steps": 1,
                        },
                        "max_iterations": 2,
                    },
                    {
                        "id": "summarize-plan",
                        "goal": "summarize the next writing step",
                        "success_criteria": {
                            "status": "completed",
                            "contains": "summarize the next writing step",
                            "min_steps": 1,
                        },
                        "max_iterations": 2,
                    },
                ],
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "threshold": self.threshold,
            "tasks": [task.to_dict() for task in self.tasks],
        }


@dataclass(frozen=True)
class EvalTaskResult:
    """Per-task eval result."""

    task_id: str
    passed: bool
    status: str
    steps: int
    used_budget: int
    failures: list[str] = field(default_factory=list)
    final_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvalReport:
    """Aggregate eval report."""

    success_rate: float
    results: list[EvalTaskResult]
    threshold: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "success_rate": self.success_rate,
            "threshold": self.threshold,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def to_markdown(self) -> str:
        lines = [
            "# Agent Eval Report",
            "",
            f"- success_rate: {self.success_rate:.3f}",
            f"- threshold: {self.threshold:.3f}",
            f"- passed: {str(self.passed).lower()}",
            "",
            "## Results",
        ]
        for result in self.results:
            state = "pass" if result.passed else "fail"
            failures = "; ".join(result.failures) if result.failures else "none"
            lines.append(
                f"- {result.task_id}: {state} "
                f"(status={result.status}, steps={result.steps}, used_budget={result.used_budget}, failures={failures})"
            )
        return "\n".join(lines) + "\n"


LoopFactory = Callable[[GoldenTask], Any]


class EvalHarness:
    """Run a golden suite through fresh autonomous loops and score the results."""

    def __init__(
        self,
        *,
        loop_factory: LoopFactory,
        suite: EvalSuite,
        threshold: float | None = None,
    ) -> None:
        self._loop_factory = loop_factory
        self._suite = suite
        self._threshold = suite.threshold if threshold is None else float(threshold)

    def run(self) -> EvalReport:
        results = [self._run_task(task) for task in self._suite.tasks]
        passed_count = sum(1 for result in results if result.passed)
        success_rate = passed_count / len(results) if results else 0.0
        return EvalReport(
            success_rate=success_rate,
            results=results,
            threshold=self._threshold,
            passed=success_rate >= self._threshold,
        )

    def _run_task(self, task: GoldenTask) -> EvalTaskResult:
        loop = self._loop_factory(task)
        result = loop.run(task.goal)
        steps = list(getattr(result, "steps", []))
        final_text = str(getattr(result, "final_text", ""))
        status = str(getattr(result, "status", "unknown"))
        failures = _score(status=status, steps=steps, final_text=final_text, criteria=task.success_criteria)
        return EvalTaskResult(
            task_id=task.id,
            passed=not failures,
            status=status,
            steps=len(steps),
            used_budget=len(steps),
            failures=failures,
            final_text=final_text,
        )


def _score(
    *,
    status: str,
    steps: Iterable[Any],
    final_text: str,
    criteria: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    step_count = len(list(steps))

    expected_status = criteria.get("status")
    if expected_status is not None and status != expected_status:
        failures.append(f"status expected {expected_status!r}, got {status!r}")

    contains = criteria.get("contains")
    if contains is not None and str(contains) not in final_text:
        failures.append(f"missing required text {contains!r}")

    not_contains = criteria.get("not_contains")
    if not_contains is not None and str(not_contains) in final_text:
        failures.append(f"forbidden text present {not_contains!r}")

    min_steps = criteria.get("min_steps")
    if min_steps is not None and step_count < int(min_steps):
        failures.append(f"steps expected >= {int(min_steps)}, got {step_count}")

    max_steps = criteria.get("max_steps")
    if max_steps is not None and step_count > int(max_steps):
        failures.append(f"steps expected <= {int(max_steps)}, got {step_count}")

    return failures


__all__ = [
    "DEFAULT_THRESHOLD",
    "EvalHarness",
    "EvalReport",
    "EvalSuite",
    "EvalTaskResult",
    "GoldenTask",
]
