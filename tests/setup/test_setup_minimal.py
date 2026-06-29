"""Minimal guided setup tests (Task 76)."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup import SetupMode, SetupWizard


def test_minimal_setup_creates_fake_provider_workspace_and_config(tmp_path):
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    config_text = result.config_path.read_text(encoding="utf-8")
    assert result.completed is True
    assert result.workspace_path.exists()
    assert "fake" in config_text
    assert "completed: true" in config_text
    assert result.errors == []


def test_minimal_setup_keeps_fake_as_default_provider(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "providers:\n  deepseek:\n    enabled: true\n    configured: true\n",
        encoding="utf-8",
    )
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert payload["default_provider"] == "fake"


def test_minimal_setup_cli_exits_zero_and_prints_summary(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["setup", "--minimal"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Guided Setup" in out
    assert "fake" in out
    assert (tmp_path / ".pf-agent" / "config.yaml").exists()
