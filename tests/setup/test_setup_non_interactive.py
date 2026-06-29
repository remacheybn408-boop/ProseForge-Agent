"""Non-interactive guided setup tests."""

from __future__ import annotations

import json

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup import SetupMode, SetupWizard


def test_non_interactive_uses_env_and_defaults_without_prompt(tmp_path):
    result = SetupWizard(root=tmp_path, env={"DEEPSEEK_API_KEY": "sk-test"}).run(mode=SetupMode.NON_INTERACTIVE)
    assert result.completed is True
    assert result.providers[0].name == "deepseek"


def test_non_interactive_without_keys_enables_fake_provider(tmp_path):
    result = SetupWizard(root=tmp_path, env={}).run(mode=SetupMode.NON_INTERACTIVE)
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert result.providers[0].name == "fake"
    assert payload["providers"]["fake"]["configured"] is True


def test_non_interactive_json_summary_is_machine_readable(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["setup", "--non-interactive", "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["title"] == "Guided Setup"
    assert payload["data"]["completed"] is True


def test_non_interactive_missing_engine_is_warning_not_failure(tmp_path):
    result = SetupWizard(root=tmp_path, env={}).run(mode=SetupMode.NON_INTERACTIVE)
    assert result.completed is True
    assert any("engine.enabled=false" in warning for warning in result.warnings)
