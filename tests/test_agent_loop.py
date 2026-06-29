"""Tests for the autonomous agent loop (Task 68)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proseforge_agent.agent.loop import AgentLoop, Budget, LoopResult
from proseforge_agent.agent.types import AgentIntent, AgentTurnResult
from proseforge_agent.testing.fakes import FakeKernel

FIXTURE = (
    Path(__file__).parent / "fixtures" / "autonomous-agent-loop" / "run_trace.json"
)


class ConstantKernel:
    """Returns the same text every turn (no progress)."""

    def __init__(self, text: str = "no progress") -> None:
        self.calls = []
        self._text = text

    def run_turn(self, request):
        index = len(self.calls)
        self.calls.append(request)
        return AgentTurnResult(
            text=self._text,
            intent=AgentIntent(name="answer_directly"),
            trace_id=f"trace-{index + 1}",
        )


class _Control:
    def __init__(self, interrupt_after: int) -> None:
        self._after = interrupt_after
        self._seen = 0

    def is_interrupted(self) -> bool:
        interrupted = self._seen >= self._after
        self._seen += 1
        return interrupted


class _RecordingBus:
    def __init__(self) -> None:
        self.events = []

    def emit(self, event_type, payload=None, *, trace_id=None):
        self.events.append((event_type, trace_id))


@pytest.fixture
def fake_kernel_done_on_second_turn() -> FakeKernel:
    return FakeKernel(scripted=["还在起草开头……", "完成开头 [[done]]"])


def test_loop_stops_when_goal_satisfied_within_budget(fake_kernel_done_on_second_turn):
    loop = AgentLoop(kernel=fake_kernel_done_on_second_turn, budget=Budget(max_iterations=10))
    result = loop.run(goal="say hello then stop")
    assert result.status == "completed"
    assert len(result.steps) == 2


def test_loop_halts_at_iteration_budget_without_infinite_loop():
    # Default FakeKernel produces a new text each turn, so it never "completes";
    # it must stop exactly at the iteration budget.
    loop = AgentLoop(kernel=FakeKernel(), budget=Budget(max_iterations=5))
    result = loop.run(goal="keep going forever")
    assert result.status == "stopped_budget"
    assert len(result.steps) == 5


def test_no_progress_is_detected_and_stops_the_run():
    loop = AgentLoop(
        kernel=ConstantKernel(),
        budget=Budget(max_iterations=50),
        no_progress_limit=3,
    )
    result = loop.run(goal="stuck")
    assert result.status == "stopped_no_progress"
    assert len(result.steps) == 3  # stopped well before the budget


def test_working_context_is_compacted_when_over_threshold():
    loop = AgentLoop(
        kernel=FakeKernel(),
        budget=Budget(max_iterations=8),
        context_threshold=2,
    )
    result = loop.run(goal="long run")
    assert result.compactions > 0


def test_each_iteration_emits_an_event_with_trace_id():
    bus = _RecordingBus()
    loop = AgentLoop(kernel=FakeKernel(), budget=Budget(max_iterations=3), event_bus=bus)
    result = loop.run(goal="emit events")
    step_events = [e for e in bus.events if e[0] == "loop_step"]
    assert len(step_events) == len(result.steps) == 3
    assert all(trace_id for _, trace_id in step_events)


def test_interrupt_signal_stops_with_interrupted_status():
    loop = AgentLoop(
        kernel=FakeKernel(),
        budget=Budget(max_iterations=10),
        control=_Control(interrupt_after=2),
    )
    result = loop.run(goal="will be interrupted")
    assert result.status == "interrupted"
    assert len(result.steps) == 2  # two turns ran, then interrupt was seen


def test_loop_does_not_mutate_the_kernel():
    kernel = FakeKernel()
    attrs_before = set(vars(kernel))
    loop = AgentLoop(kernel=kernel, budget=Budget(max_iterations=3))
    loop.run(goal="hands off the kernel")
    assert loop._kernel is kernel
    assert set(vars(kernel)) == attrs_before  # no attributes added to the kernel


def test_loop_result_is_serializable_and_fixture_matches():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    loop = AgentLoop(
        kernel=FakeKernel(scripted=expected["scripted_turns"]),
        budget=Budget(max_iterations=10),
    )
    result = loop.run(goal=expected["goal"])
    assert isinstance(result, LoopResult)
    assert result.status == expected["expected_status"]
    assert len(result.steps) == expected["expected_steps"]
    assert "status" in result.to_dict()
