"""Middleware chain wiring into the kernel (Task 196, finding 1.5)."""

from __future__ import annotations

from proseforge_agent.agent.kernel import AgentKernel
from proseforge_agent.agent.middleware import (
    MIDDLEWARE_KIND_LLM_REQUEST,
    MIDDLEWARE_KIND_TOOL_EXECUTION,
    MIDDLEWARE_KIND_TOOL_REQUEST,
    MiddlewareRegistry,
)
from proseforge_agent.agent.types import AgentTurnRequest
from proseforge_agent.llm import FakeProvider


class FakeTools:
    def __init__(self):
        self.called = []
        self.permissions = {"chapter.accept": "project_write", "draft.note": "draft_write"}

    def required_permission(self, name):
        return self.permissions[name]

    def execute(self, name, payload):
        self.called.append((name, payload))
        return {"ok": True, "name": name}


def _draft_note_request():
    return AgentTurnRequest(
        session_id="s1",
        text="draft note please",
        mode="workflow_chat",
        project_slug=None,
        permission_level="project_write",
    )


def test_tool_request_middleware_fires_on_dispatch():
    registry = MiddlewareRegistry()
    seen = []

    def tag(req):
        seen.append(req.tool_name)
        return req.with_arguments({**req.arguments, "tagged": True})

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "tag", tag, enabled=True)

    tools = FakeTools()
    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=tools, middleware=registry)
    result = kernel.run_turn(_draft_note_request())

    assert seen == ["draft.note"]  # middleware actually ran
    assert any(t.name == "tag" and t.rewritten for t in registry.traces())
    # rewritten arguments reached the tool
    assert tools.called and tools.called[0][1].get("tagged") is True
    assert result.tool_calls and result.tool_calls[0].status == "ok"


def test_rewritten_request_is_reauthorized_and_denied_when_ceiling_forbids():
    registry = MiddlewareRegistry()

    def escalate(req):
        # rewrite draft.note (draft_write) -> chapter.accept (project_write)
        return req.with_tool_name("chapter.accept")

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "escalate", escalate, enabled=True)

    tools = FakeTools()
    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=tools, middleware=registry)
    request = AgentTurnRequest(
        session_id="s1",
        text="draft note please",
        mode="workflow_chat",
        project_slug=None,
        permission_level="draft_write",  # allows draft.note, NOT chapter.accept
    )
    result = kernel.run_turn(request)

    assert tools.called == []  # denied before execution
    assert any(e["type"] == "permission_denied" for e in result.events)


def test_tool_execution_middleware_wraps_invoke_with_next_call():
    registry = MiddlewareRegistry()
    order = []

    def wrap(ctx, next_call):
        order.append("before")
        result = next_call(ctx)
        order.append("after")
        return result

    registry.register(MIDDLEWARE_KIND_TOOL_EXECUTION, "wrap", wrap, enabled=True)

    tools = FakeTools()
    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=tools, middleware=registry)
    kernel.run_turn(_draft_note_request())

    assert order == ["before", "after"]
    assert tools.called  # underlying tool still executed


def test_llm_request_middleware_fires_before_provider_call():
    registry = MiddlewareRegistry()
    fired = []

    def tag(req):
        fired.append(req.model)
        return req

    registry.register(MIDDLEWARE_KIND_LLM_REQUEST, "tag", tag, enabled=True)

    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=FakeTools(), middleware=registry)
    kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="hello",
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )
    )
    assert fired  # llm_request middleware ran before the provider generated


def test_middleware_none_leaves_tool_dispatch_unchanged():
    tools = FakeTools()
    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=tools)  # no middleware
    result = kernel.run_turn(_draft_note_request())
    assert tools.called == [("draft.note", {"text": "draft note please"})]
    assert result.tool_calls and result.tool_calls[0].status == "ok"


def test_failing_middleware_is_recorded_and_chain_continues():
    registry = MiddlewareRegistry()

    def boom(req):
        raise RuntimeError("bad middleware")

    registry.register(MIDDLEWARE_KIND_TOOL_REQUEST, "boom", boom, enabled=True)

    tools = FakeTools()
    kernel = AgentKernel(provider=FakeProvider(name="fake", model="fake-novelist"), tools=tools, middleware=registry)
    result = kernel.run_turn(_draft_note_request())

    assert registry.failures() and registry.failures()[0]["name"] == "boom"
    assert tools.called  # fail-open: tool still ran with original request
    assert result.tool_calls and result.tool_calls[0].status == "ok"
