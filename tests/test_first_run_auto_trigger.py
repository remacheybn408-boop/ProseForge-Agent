"""First-run bootstrap auto-trigger tests (Task 188)."""

from __future__ import annotations

import json

from proseforge_agent.cli import main
from proseforge_agent.install.auto_trigger import (
    AutoBootstrap,
    BootstrapDecision,
    complete_first_run,
)


def test_decide_returns_skip_when_marker_present(tmp_path):
    complete_first_run(tmp_path)
    decision = AutoBootstrap(root=tmp_path).decide()
    assert isinstance(decision, BootstrapDecision)
    assert decision.verdict == "SKIP"


def test_decide_returns_onboard_full_on_fresh_home(tmp_path):
    decision = AutoBootstrap(root=tmp_path / "fresh").decide()
    assert decision.verdict == "ONBOARD_FULL"
    assert decision.missing  # at least "config missing"


def test_decide_returns_onboard_minimal_when_workspace_ok_provider_missing(tmp_path):
    (tmp_path / "config.yaml").write_text("mode: portable\n", encoding="utf-8")
    (tmp_path / "workspace").mkdir()
    decision = AutoBootstrap(root=tmp_path).decide()
    assert decision.verdict == "ONBOARD_MINIMAL"


def test_decide_skips_via_env_override(tmp_path):
    decision = AutoBootstrap(root=tmp_path / "fresh", env={"PF_AGENT_SKIP_FIRST_RUN": "1"}).decide()
    assert decision.verdict == "SKIP"
    assert "env" in decision.reason.lower()


def test_decide_corrupt_marker_triggers_onboard(tmp_path):
    marker = tmp_path / ".first-run-completed.json"
    marker.write_text("{ this is not json", encoding="utf-8")
    decision = AutoBootstrap(root=tmp_path).decide()
    assert decision.verdict in {"ONBOARD_FULL", "ONBOARD_MINIMAL"}


def test_complete_first_run_writes_versioned_marker(tmp_path):
    path = complete_first_run(tmp_path)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] >= 1


def test_router_skips_to_repl_when_marker_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    complete_first_run(tmp_path / ".pf-agent")
    called = {}

    def fake_run_repl(argv=None, *, provider="fake", **kwargs):
        called["ran"] = True
        return 0

    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", fake_run_repl)
    exit_code = main([])
    assert exit_code == 0
    assert called.get("ran") is True


def test_router_runs_bootstrap_then_repl_on_fresh(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    called = {}

    def fake_run_repl(argv=None, *, provider="fake", **kwargs):
        called["ran"] = True
        return 0

    monkeypatch.setattr("proseforge_agent.chat.repl.run_repl", fake_run_repl)
    exit_code = main([])
    assert exit_code == 0
    assert called.get("ran") is True
    # after auto-bootstrap, the consent marker exists so the next run skips
    assert (tmp_path / ".pf-agent" / ".first-run-completed.json").exists()
