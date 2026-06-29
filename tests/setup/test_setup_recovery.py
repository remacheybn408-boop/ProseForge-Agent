"""Setup recovery contract tests (Task 79)."""

from __future__ import annotations

import yaml

from proseforge_agent.setup import SetupMode, SetupWizard
from proseforge_agent.setup.recovery import backup_config


def test_setup_recovery_contract(tmp_path):
    first = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    original = first.config_path.read_text(encoding="utf-8")
    result = SetupWizard(root=tmp_path).run(
        mode=SetupMode.QUICK,
        add_provider="deepseek",
        skip_provider_test=True,
    )
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.backup_path.read_text(encoding="utf-8") == original
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert "deepseek" in payload["llm"]["providers"]
    assert "fake" in payload["llm"]["providers"]


def test_repair_creates_config_backup_before_fixing_fields(tmp_path):
    first = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    payload = yaml.safe_load(first.config_path.read_text(encoding="utf-8"))
    payload["setup"]["completed"] = False
    first.config_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, repair=True)
    updated = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert updated["setup"]["completed"] is True


def test_config_backups_never_overwrite_each_other(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("version: 1\n", encoding="utf-8")
    first = backup_config(config)
    second = backup_config(config)
    assert first is not None and second is not None
    assert first != second
    assert first.exists()
    assert second.exists()


def test_invalid_provider_key_is_warning_not_setup_blocker(tmp_path):
    def ping(_name):
        raise RuntimeError("invalid provider key")

    result = SetupWizard(
        root=tmp_path,
        env={"DEEPSEEK_API_KEY": "sk-test"},
        provider_ping=ping,
    ).run(mode=SetupMode.QUICK)
    assert result.completed is True
    assert any("invalid provider key" in warning for warning in result.warnings)
    assert any(provider.name == "fake" for provider in result.providers)
