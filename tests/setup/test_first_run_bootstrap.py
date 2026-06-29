"""First-run bootstrap tests (Task 80)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup.first_run import FirstRunBootstrap


def test_first_run_bootstrap_contract(tmp_path):
    verdict = FirstRunBootstrap(root=tmp_path).check()
    assert verdict.ready is False
    assert "config missing" in verdict.reasons
    assert "pf-agent setup --quick" in verdict.guidance
    assert "pf-agent setup --minimal" in verdict.guidance


def test_incomplete_setup_is_not_ready(tmp_path):
    root = tmp_path / ".pf-agent"
    root.mkdir()
    (root / "config.yaml").write_text("setup:\n  completed: false\n", encoding="utf-8")
    verdict = FirstRunBootstrap(root=root).check()
    assert verdict.ready is False
    assert "setup.completed is not true" in verdict.reasons


def test_missing_workspace_is_not_ready(tmp_path):
    root = tmp_path / ".pf-agent"
    root.mkdir()
    (root / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "setup": {"completed": True},
                "paths": {"workspace_root": str(root / "workspace")},
                "llm": {"default_provider": "fake", "providers": {"fake": {"enabled": True}}},
            }
        ),
        encoding="utf-8",
    )
    verdict = FirstRunBootstrap(root=root).check()
    assert verdict.ready is False
    assert "workspace missing" in verdict.reasons


def test_default_provider_unavailable_is_not_ready(tmp_path):
    root = tmp_path / ".pf-agent"
    workspace = root / "workspace"
    workspace.mkdir(parents=True)
    (root / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "setup": {"completed": True},
                "paths": {"workspace_root": str(workspace)},
                "llm": {"default_provider": "deepseek", "providers": {"fake": {"enabled": True}}},
            }
        ),
        encoding="utf-8",
    )
    verdict = FirstRunBootstrap(root=root).check()
    assert verdict.ready is False
    assert "default provider unavailable" in verdict.reasons


def test_chat_without_setup_prints_guidance_not_traceback(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["chat", "--message", "hello"])
    out = capsys.readouterr().out
    assert code == 2
    assert "pf-agent setup --quick" in out
    assert "pf-agent setup --minimal" in out
    assert "Traceback" not in out


def test_explicit_fake_chat_remains_zero_config_escape_hatch(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["chat", "--provider", "fake", "--message", "hello"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Agent Chat" in out
