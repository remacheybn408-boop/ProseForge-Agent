import json
from pathlib import Path

from proseforge_agent.cli import main
from proseforge_agent.release import ReleaseChecker
from proseforge_agent.release.complete_agent_gate import CompleteAgentReleaseGate


FIXTURE = Path(__file__).parent / "fixtures" / "complete-agent-release-gate" / "reports" / "passing.json"


def test_release_checker_import_stays_compatible():
    assert ReleaseChecker(Path(__file__).parents[1]).run().checks


def test_complete_agent_gate_passes_all_required_reports():
    reports = json.loads(FIXTURE.read_text(encoding="utf-8"))
    decision = CompleteAgentReleaseGate().evaluate(reports)
    assert decision.passed is True
    assert decision.status == "ok"


def test_complete_agent_gate_blocks_missing_reports():
    decision = CompleteAgentReleaseGate().evaluate({"e2e_demo": {"status": "ok"}})
    assert decision.status == "blocked"
    assert "native_qa" in decision.missing_gates


def test_complete_agent_gate_lists_failed_reports():
    reports = json.loads(FIXTURE.read_text(encoding="utf-8"))
    reports["support_bundle"] = {"status": "fail"}
    decision = CompleteAgentReleaseGate().evaluate(reports)
    assert decision.status == "blocked"
    assert "support_bundle" in decision.failed_gates


def test_complete_agent_release_cli(capsys):
    code = main(["release", "check", "--complete-agent", "--write-report"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Complete Agent Release Gate" in out


def test_release_gate_fixture_loads():
    reports = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert reports["chat_drill"]["status"] == "ok"
