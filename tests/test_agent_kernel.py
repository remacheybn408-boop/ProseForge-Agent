import json
from pathlib import Path

import pytest

from proseforge_agent.agent.kernel import AgentKernel
from proseforge_agent.agent.types import AgentTurnRequest
from proseforge_agent.chat.session import ChatSessionStore
from proseforge_agent.llm import FakeProvider, ProviderResult


FIXTURE = Path(__file__).parent / "fixtures" / "agent" / "kernel_turn.json"


class FakeSessionStore:
    def __init__(self):
        self.messages = []
        self.events = []
        self.memory_candidates = []

    def ensure_session(self, session_id, mode, project_slug):
        return {"session_id": session_id, "mode": mode, "project_slug": project_slug}

    def append_message(self, session_id, role, content):
        self.messages.append({"session_id": session_id, "role": role, "content": content})

    def record_event(self, event):
        self.events.append(event)

    def save_memory_candidate(self, session_id, text):
        memory_id = f"mem-{len(self.memory_candidates) + 1}"
        self.memory_candidates.append({"id": memory_id, "session_id": session_id, "text": text})
        return memory_id


class FakeRetrieval:
    def __init__(self):
        self.calls = []

    def retrieve(self, project_slug, text):
        self.calls.append({"project_slug": project_slug, "text": text})
        return [{"id": "ev-1", "text": "昨天写到第二章。"}]


class FakeTools:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.called = []
        self.permissions = {
            "chapter.accept": "project_write",
            "draft.note": "draft_write",
        }

    def required_permission(self, name):
        return self.permissions[name]

    def execute(self, name, payload):
        self.called.append((name, payload))
        if self.fail:
            raise RuntimeError("tool failed")
        return {"ok": True, "name": name}


class BrokenProvider:
    name = "broken"
    model = "broken-model"

    def generate(self, request):
        raise RuntimeError("provider failed")

    def generate_stream(self, request):
        raise RuntimeError("provider failed")


class CapturingProvider:
    name = "capture"
    model = "capture-model"

    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return ProviderResult(provider=self.name, model=self.model, text="captured")

    def generate_stream(self, request):
        raise NotImplementedError


@pytest.fixture
def fake_provider():
    return FakeProvider(name="fake", model="fake-novelist")


@pytest.fixture
def fake_tools():
    return FakeTools()


@pytest.fixture
def fake_session_store():
    return FakeSessionStore()


def test_kernel_runs_read_only_chat_turn_without_project(fake_provider, fake_tools, fake_session_store):
    kernel = AgentKernel(
        provider=fake_provider,
        tools=fake_tools,
        session_store=fake_session_store,
    )
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="new",
            text="hello",
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )
    )
    assert result.intent.name == "answer_directly"
    assert result.tool_calls == []
    assert result.text
    assert result.events


def test_kernel_retrieves_evidence_for_project_question(fake_provider, fake_tools, fake_session_store):
    retrieval = FakeRetrieval()
    kernel = AgentKernel(
        provider=fake_provider,
        tools=fake_tools,
        session_store=fake_session_store,
        retrieval=retrieval,
    )
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="今天该写什么？",
            mode="project_chat",
            project_slug="demo",
            permission_level="read_only",
        )
    )
    assert retrieval.calls
    assert result.intent.name == "retrieve_context"
    assert result.evidence_refs == ["ev-1"]


def test_kernel_blocks_write_tool_when_permission_is_read_only(fake_provider, fake_session_store):
    tools = FakeTools()
    kernel = AgentKernel(provider=fake_provider, tools=tools, session_store=fake_session_store)
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="accept chapter",
            mode="workflow_chat",
            project_slug="demo",
            permission_level="read_only",
        )
    )
    assert tools.called == []
    assert result.intent.name == "accept_chapter"
    assert "permission" in result.text.lower()
    assert any(event["type"] == "permission_denied" for event in result.events)


def test_kernel_records_provider_failure_as_event(fake_tools, fake_session_store):
    kernel = AgentKernel(provider=BrokenProvider(), tools=fake_tools, session_store=fake_session_store)
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="hello",
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )
    )
    assert "trace" in result.text.lower()
    assert any(event["type"] == "provider_error" for event in result.events)


def test_kernel_returns_recovery_message_when_tool_fails(fake_provider, fake_session_store):
    tools = FakeTools(fail=True)
    kernel = AgentKernel(provider=fake_provider, tools=tools, session_store=fake_session_store)
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="draft note",
            mode="workflow_chat",
            project_slug="demo",
            permission_level="draft_write",
        )
    )
    assert "failed" in result.text.lower()
    assert any(event["type"] == "tool_error" for event in result.events)


def test_kernel_saves_memory_candidate_for_durable_user_preference(fake_provider, fake_tools, fake_session_store):
    kernel = AgentKernel(provider=fake_provider, tools=fake_tools, session_store=fake_session_store)
    result = kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="remember I prefer concise reports",
            mode="creative_chat",
            project_slug=None,
            permission_level="draft_write",
        )
    )
    assert result.memory_candidate_ids == ["mem-1"]
    assert fake_session_store.memory_candidates[0]["text"] == "remember I prefer concise reports"


def test_kernel_sends_effective_session_context_to_provider(tmp_path, fake_tools):
    provider = CapturingProvider()
    store = ChatSessionStore(tmp_path / ".pf-agent")
    kernel = AgentKernel(provider=provider, tools=fake_tools, session_store=store)
    request = AgentTurnRequest(
        session_id="s1",
        text="first",
        mode="general_chat",
        project_slug=None,
        permission_level="read_only",
    )
    kernel.run_turn(request)

    kernel.run_turn(
        AgentTurnRequest(
            session_id="s1",
            text="second",
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )
    )

    contents = [message.content for message in provider.requests[-1].messages]
    assert contents[0] == "first"
    assert contents[1].startswith("captured\nTrace: trace-")
    assert contents[-1] == "second"


def test_kernel_fixture_is_portable_utf8():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["mode"] == "general_chat"
    assert "路径" in payload["text"]
