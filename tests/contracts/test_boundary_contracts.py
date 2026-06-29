"""Cross-module boundary contract tests (Task 67).

Each test exercises one interface between subsystems using only the canonical
fakes, and asserts the *shape* of the data crossing that boundary. A failure
names the specific broken boundary so a regression points at the exact seam.
"""

from __future__ import annotations

import proseforge_agent.llm.fake as llm_fake
import pytest
from proseforge_agent.agent.kernel import AgentKernel
from proseforge_agent.agent.types import AgentTurnRequest
from proseforge_agent.testing.fakes import (
    FakeKernel,
    FakeProvider,
    FakeRetrieval,
    FakeSessionStore,
    FakeTools,
)


def assert_contract(boundary: str, condition: bool, detail: str = "") -> None:
    """Assert a boundary contract, naming the boundary on failure."""
    if not condition:
        raise AssertionError(f"contract broken at boundary {boundary!r}: {detail}")


def _turn(text: str, *, permission_level: str = "read_only") -> AgentTurnRequest:
    return AgentTurnRequest(
        session_id="new",
        text=text,
        mode="general_chat",
        project_slug=None,
        permission_level=permission_level,
    )


def test_kernel_provider_contract_holds_with_canonical_fakes():
    kernel = AgentKernel(
        provider=FakeProvider(), tools=FakeTools(), session_store=FakeSessionStore()
    )
    result = kernel.run_turn(_turn("hi"))
    for field in ("text", "intent", "tool_calls", "evidence_refs", "events"):
        assert_contract("kernel<->provider", hasattr(result, field), f"missing {field}")


def test_kernel_tools_boundary_contract():
    kernel = AgentKernel(
        provider=FakeProvider(), tools=FakeTools(), session_store=FakeSessionStore()
    )
    result = kernel.run_turn(_turn("accept chapter 3", permission_level="project_write"))
    assert_contract("kernel<->tools", len(result.tool_calls) == 1, "expected one tool call")
    call = result.tool_calls[0]
    for field in ("name", "status"):
        assert_contract("kernel<->tools", hasattr(call, field), f"ToolCallResult missing {field}")
    assert_contract("kernel<->tools", call.status == "ok", f"unexpected status {call.status}")


def test_retrieval_memory_boundary_contract():
    retrieval = FakeRetrieval()
    items = retrieval.retrieve("demo", "今天写什么")
    assert_contract("retrieval<->memory", isinstance(items, list) and items, "no evidence")
    for item in items:
        assert_contract("retrieval<->memory", "id" in item and "text" in item, "evidence shape")


def test_workflow_engine_adapter_boundary_contract(tmp_path):
    from proseforge_agent.workflow.state import StepResult, WorkflowStateStore

    store = WorkflowStateStore(tmp_path / "runs")
    run = store.create("demo", 1)
    run = store.append_step(
        run.id,
        StepResult(name="context", status="ok", started_at="t0", summary="context ready"),
    )
    assert_contract("workflow<->engine", run.step_history, "no step recorded")
    step = run.step_history[-1]
    for field in ("name", "status", "started_at", "artifacts"):
        assert_contract("workflow<->engine", hasattr(step, field), f"StepResult missing {field}")


def test_chat_kernel_boundary_contract():
    import io

    from proseforge_agent.chat.repl import ChatRepl

    output = io.StringIO()
    repl = ChatRepl(
        provider=FakeProvider(),
        session_store=FakeSessionStore(),
        input_stream=io.StringIO("hello\n/exit\n"),
        output_stream=output,
    )
    repl.run()
    assert_contract("chat<->kernel", "hello" in output.getvalue() or output.getvalue(), "no output")


def test_fake_kernel_satisfies_run_turn_contract():
    kernel = FakeKernel(scripted=["one", "two"])
    result = kernel.run_turn(_turn("go"))
    for field in ("text", "intent", "tool_calls", "evidence_refs", "events", "trace_id"):
        assert_contract("loop<->kernel", hasattr(result, field), f"missing {field}")
    assert result.text == "one"


def test_contract_failure_message_names_the_broken_boundary():
    with pytest.raises(AssertionError) as excinfo:
        assert_contract("kernel<->provider", False, "deliberate")
    assert "kernel<->provider" in str(excinfo.value)


def test_canonical_fakes_are_reused_not_redefined_per_card():
    # The canonical FakeProvider must be the real llm fake (reused, not a copy),
    # so the contract it satisfies can never silently drift.
    assert issubclass(FakeProvider, llm_fake.FakeProvider)
    from proseforge_agent.testing import fakes

    for name in ("FakeProvider", "FakeTools", "FakeSessionStore", "FakeRetrieval", "FakeKernel", "FakeHTTP"):
        assert hasattr(fakes, name)
