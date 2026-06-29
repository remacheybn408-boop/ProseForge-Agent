import json
import time
from pathlib import Path

from proseforge_agent.agent.loop import LoopResult, StepRecord
from proseforge_agent.agent.subagent import Scope, SubAgentRunner


FIXTURE = Path(__file__).parent / "fixtures" / "sub-agent-delegation" / "delegation.json"


class FakeLoop:
    def __init__(self, *, fail: bool = False, delay: float = 0) -> None:
        self.fail = fail
        self.delay = delay
        self.calls = []

    def run(self, goal: str, context=None):
        if self.delay:
            time.sleep(self.delay)
        self.calls.append((goal, context))
        if self.fail:
            raise RuntimeError("subagent failed")
        return LoopResult(
            status="completed",
            steps=[StepRecord(index=1, text=f"done: {goal}", trace_id="trace-sub")],
            final_text=f"done: {goal}",
            events=[{"type": "loop_step", "trace_id": "trace-sub"}],
        )


def test_delegated_subagent_runs_with_scoped_permissions_and_returns_result():
    loops = []

    def fake_loop_factory(scope):
        loop = FakeLoop()
        loops.append((scope, loop))
        return loop

    runner = SubAgentRunner(loop_factory=fake_loop_factory, parent_ceiling="draft_write")
    result = runner.delegate(task="research the setting", scope=Scope(permission_ceiling="system_write"))

    assert result.status == "completed"
    assert result.effective_ceiling == "draft_write"
    assert result.output == "done: research the setting"
    assert loops[0][1].calls[0][1]["permission_ceiling"] == "draft_write"


def test_subagent_ceiling_is_clamped_to_parent_grant():
    runner = SubAgentRunner(loop_factory=lambda scope: FakeLoop(), parent_ceiling="read_only")

    result = runner.delegate("draft a scene", Scope(permission_ceiling="system_write"))

    assert result.effective_ceiling == "read_only"


def test_subagent_failure_does_not_corrupt_parent_context():
    parent_context = {"notes": []}
    runner = SubAgentRunner(loop_factory=lambda scope: FakeLoop(fail=True), parent_ceiling="project_write")

    result = runner.delegate("fail safely", Scope(permission_ceiling="draft_write"), parent_context=parent_context)

    assert result.status == "failed"
    assert "subagent failed" in result.error
    assert parent_context == {"notes": []}


def test_independent_subagents_can_run_in_parallel():
    runner = SubAgentRunner(loop_factory=lambda scope: FakeLoop(delay=0.2), parent_ceiling="draft_write")
    started = time.perf_counter()

    results = runner.delegate_many(
        [
            ("research", Scope(permission_ceiling="read_only")),
            ("draft", Scope(permission_ceiling="draft_write")),
        ]
    )

    elapsed = time.perf_counter() - started
    assert [result.status for result in results] == ["completed", "completed"]
    assert elapsed < 0.35


def test_subagent_results_are_aggregated_for_the_parent():
    runner = SubAgentRunner(loop_factory=lambda scope: FakeLoop(), parent_ceiling="draft_write")

    results = runner.delegate_many([("research", Scope()), ("draft", Scope())])
    summary = runner.aggregate(results)

    assert "research: completed" in summary
    assert "draft: completed" in summary


def test_subagent_output_round_trips_utf8():
    runner = SubAgentRunner(loop_factory=lambda scope: FakeLoop(), parent_ceiling="draft_write")

    result = runner.delegate("写一段雨夜开场", Scope(permission_ceiling="draft_write"))

    assert "雨夜" in result.output


def test_fixture_documents_delegation_contract():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["task"] == "research the setting"
    assert data["scope"]["permission_ceiling"] == "draft_write"
