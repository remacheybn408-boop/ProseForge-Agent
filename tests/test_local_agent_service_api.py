import json
from pathlib import Path

import pytest

from proseforge_agent.agent import AgentIntent, AgentTurnResult
from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.service import LocalAgentService


FIXTURE = Path(__file__).parent / "fixtures" / "local-agent-service-api" / "requests.json"


class KernelStub:
    def __init__(self):
        self.requests = []

    def run_turn(self, request):
        self.requests.append(request)
        return AgentTurnResult(
            text="hello",
            intent=AgentIntent(name="answer_directly"),
            evidence_refs=["ev-1"],
            events=[{"type": "provider_call", "api_key": "secret-value"}],
            trace_id="trace-service",
        )


class SessionStoreStub:
    def list(self, project_slug=None):
        return [
            type(
                "Session",
                (),
                {
                    "id": "chat-1",
                    "mode": "general_chat",
                    "project_slug": project_slug,
                    "updated_at": "2026-01-01T00:00:00Z",
                },
            )()
        ]


def test_health_reports_read_only_local_facade():
    service = LocalAgentService(kernel=KernelStub(), session_store=SessionStoreStub())
    assert service.health()["status"] == "ok"
    assert service.health()["bind"] == "127.0.0.1"
    assert service.health()["web_server"] is False


def test_chat_serializes_kernel_turn_without_secrets():
    kernel = KernelStub()
    service = LocalAgentService(kernel=kernel, session_store=SessionStoreStub())
    response = service.chat({"message": "hello", "provider": "fake"})
    assert response["text"] == "hello"
    assert response["intent"]["name"] == "answer_directly"
    assert response["events"][0]["api_key"] == "[redacted]"
    assert kernel.requests[0].text == "hello"


def test_remote_bind_requires_explicit_system_write_permission():
    with pytest.raises(ConfigurationError):
        LocalAgentService(
            kernel=KernelStub(),
            session_store=SessionStoreStub(),
            bind="0.0.0.0",
            allow_remote=True,
            permission_level="project_write",
        )


def test_sessions_provider_and_workflow_status_shapes():
    service = LocalAgentService(kernel=KernelStub(), session_store=SessionStoreStub())
    assert service.sessions(project_slug="demo")["sessions"][0]["project_slug"] == "demo"
    assert service.provider_status()["providers"][0]["name"] == "fake"
    assert service.workflow_status("run-1")["run_id"] == "run-1"


def test_service_start_check_cli(capsys):
    code = main(["service", "start", "--provider", "fake", "--check"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Local Agent Service" in out


def test_request_fixture_loads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["chat"]["message"] == "hello"
