"""Tests for the agent task-success eval harness (Task 75)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from proseforge_agent.agent.loop import LoopResult, StepRecord
from proseforge_agent.cli import main
from proseforge_agent.release.complete_agent_gate import CompleteAgentReleaseGate

from proseforge_agent.agent.eval import EvalHarness, EvalSuite, GoldenTask


SUITE_PATH = Path(__file__).parent / "suite" / "golden_tasks.json"


class ScriptedLoop:
    def __init__(self, text: str, status: str = "completed") -> None:
        self._text = text
        self._status = status

    def run(self, goal: str):
        return LoopResult(
            status=self._status,
            steps=[StepRecord(index=1, text=self._text, trace_id=f"trace-{goal}")],
            final_text=self._text,
        )


@pytest.fixture
def golden_suite() -> EvalSuite:
    return EvalSuite.load(SUITE_PATH)


@pytest.fixture
def fake_loop_factory():
    def factory(task: GoldenTask):
        return ScriptedLoop(f"completed {task.goal} [[done]]")

    return factory


def test_eval_reports_task_success_rate_over_golden_suite(fake_loop_factory, golden_suite):
    report = EvalHarness(loop_factory=fake_loop_factory, suite=golden_suite).run()
    assert 0.0 <= report.success_rate <= 1.0
    assert len(report.results) == len(golden_suite.tasks)
    assert isinstance(report.passed, bool)


def test_success_rate_below_threshold_marks_report_not_passed(golden_suite):
    def failing_factory(task: GoldenTask):
        return ScriptedLoop("missing required marker", status="stopped_budget")

    report = EvalHarness(loop_factory=failing_factory, suite=golden_suite, threshold=1.0).run()
    assert report.success_rate < 1.0
    assert report.passed is False


def test_each_golden_task_has_explicit_success_criteria(golden_suite):
    assert golden_suite.tasks
    assert all(task.success_criteria for task in golden_suite.tasks)


def test_eval_is_deterministic_across_repeated_runs(fake_loop_factory, golden_suite):
    first = EvalHarness(loop_factory=fake_loop_factory, suite=golden_suite).run()
    second = EvalHarness(loop_factory=fake_loop_factory, suite=golden_suite).run()
    assert first.to_dict() == second.to_dict()


def test_eval_report_renders_markdown_and_json(fake_loop_factory, golden_suite):
    report = EvalHarness(loop_factory=fake_loop_factory, suite=golden_suite).run()
    markdown = report.to_markdown()
    payload = json.loads(report.to_json())
    assert "Agent Eval Report" in markdown
    assert payload["success_rate"] == report.success_rate
    assert payload["results"][0]["task_id"]


def test_release_gate_consumes_eval_success_rate():
    reports = {
        gate: {"status": "ok"}
        for gate in CompleteAgentReleaseGate.required_gates
        if gate != "agent_eval"
    }
    reports["agent_eval"] = {"passed": True, "success_rate": 1.0, "threshold": 0.8}
    decision = CompleteAgentReleaseGate().evaluate(reports)
    assert decision.status == "ok"
    assert "agent_eval" in decision.passed_gates


def test_eval_cli_writes_report(capsys):
    code = main(["eval", "run", "--provider", "fake", "--write-report"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Agent Eval Report" in out
    assert "success_rate" in out
