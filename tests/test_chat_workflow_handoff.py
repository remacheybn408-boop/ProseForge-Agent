import json
from pathlib import Path

from proseforge_agent.chat.handoff import ChatWorkflowHandoff, HandoffPackage
from proseforge_agent.cli import main


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "chat-to-workflow-handoff"
    / "handoff_example.json"
)


def test_handoff_package_for_write_workflow_requires_confirmation():
    package = ChatWorkflowHandoff().create(
        "继续第3章的改稿",
        project_slug="demo",
        mode="workflow_chat",
    )
    assert isinstance(package, HandoffPackage)
    assert package.workflow_name == "workflow.continue"
    assert package.required_permission == "project_write"
    assert package.confirmation_required is True
    assert package.is_runnable() is False
    assert package.with_confirmation(True).is_runnable() is True


def test_read_only_handoff_is_runnable_without_confirmation():
    package = ChatWorkflowHandoff().create(
        "解释这个报告",
        project_slug="demo",
        mode="project_chat",
    )
    assert package.workflow_name == "report.render"
    assert package.required_permission == "read_only"
    assert package.is_runnable() is True


def test_handoff_creation_does_not_start_workflow(tmp_path):
    package = ChatWorkflowHandoff().create("继续第3章的改稿", project_slug="demo")
    assert package.to_dict()["status"] == "proposed"
    assert not list(tmp_path.glob("run-*.json"))


def test_handoff_fixture_round_trips():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    package = HandoffPackage.from_dict(payload)
    assert package.workflow_name == "workflow.continue"
    assert package.is_runnable() is False


def test_propose_handoff_cli_prints_non_runnable_package(capsys):
    code = main(
        [
            "chat",
            "--message",
            "继续第3章的改稿",
            "--project",
            "demo",
            "--provider",
            "fake",
            "--propose-handoff",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "Handoff Package" in out
    assert "workflow.continue" in out
    assert "runnable=false" in out
    assert "Agent Chat" not in out
