import json
from pathlib import Path

from proseforge_agent.agent.control import ControlToken
from proseforge_agent.agent.loop import AgentLoop, Budget
from proseforge_agent.testing.fakes import FakeKernel


FIXTURE = Path(__file__).parent / "fixtures" / "interruptibility-and-steering" / "signals.json"


def test_interrupt_signal_stops_loop_at_next_safe_point():
    token = ControlToken()
    loop = AgentLoop(kernel=FakeKernel(), budget=Budget(max_iterations=100), control=token)
    token.interrupt()

    result = loop.run(goal="loop a while")

    assert result.status == "interrupted"
    assert result.resumable is True
    assert result.checkpoint["status"] == "interrupted"


def test_interrupt_saves_resumable_state_without_data_loss():
    token = ControlToken()
    kernel = FakeKernel()
    loop = AgentLoop(kernel=kernel, budget=Budget(max_iterations=5), control=token)
    token.interrupt()

    result = loop.run(goal="preserve progress")

    assert result.checkpoint["completed_steps"] == []
    assert result.checkpoint["goal"] == "preserve progress"


def test_steer_merges_new_instruction_into_plan():
    token = ControlToken()
    token.steer("focus on the antagonist")
    kernel = FakeKernel()
    loop = AgentLoop(kernel=kernel, budget=Budget(max_iterations=1), control=token)

    result = loop.run(goal="draft opening")

    assert result.events[0]["type"] == "control_steer"
    assert kernel.calls[0].text == "focus on the antagonist"


def test_interrupted_run_can_be_resumed():
    token = ControlToken()
    loop = AgentLoop(kernel=FakeKernel(), budget=Budget(max_iterations=3), control=token)
    token.interrupt()
    interrupted = loop.run(goal="resume me")

    resumed = AgentLoop(kernel=FakeKernel(scripted=["done [[done]]"]), budget=Budget(max_iterations=3)).run(
        goal=interrupted.checkpoint["goal"],
        context=interrupted.checkpoint,
    )

    assert interrupted.resumable is True
    assert resumed.status == "completed"


def test_control_signals_are_emitted_as_events():
    token = ControlToken()
    token.interrupt()

    result = AgentLoop(kernel=FakeKernel(), budget=Budget(max_iterations=3), control=token).run(goal="stop")

    assert result.events[0]["type"] == "control_interrupt"
    assert result.events[0]["trace_id"]


def test_interrupt_only_takes_effect_at_a_safe_point():
    class InterruptAfterFirstTurn:
        def __init__(self) -> None:
            self.seen = 0

        def poll(self):
            self.seen += 1
            if self.seen == 2:
                return ControlToken.interrupt_signal("after first turn")
            return None

    result = AgentLoop(
        kernel=FakeKernel(),
        budget=Budget(max_iterations=10),
        control=InterruptAfterFirstTurn(),
    ).run(goal="stop after one safe point")

    assert result.status == "interrupted"
    assert len(result.steps) == 1


def test_fixture_documents_control_signals():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["interrupt"]["kind"] == "interrupt"
    assert data["steer"]["instruction"] == "focus on the antagonist"
