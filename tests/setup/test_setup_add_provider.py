"""Guided setup provider-addition tests."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup import SetupMode, SetupWizard


def test_add_provider_appends_deepseek_without_resetting_fake(tmp_path):
    SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    result = SetupWizard(root=tmp_path).run(
        mode=SetupMode.QUICK,
        add_provider="deepseek",
        skip_provider_test=True,
    )
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert "deepseek" in payload["providers"]
    assert payload["providers"]["fake"]["enabled"] is True
    assert any(provider.name == "deepseek" for provider in result.providers)


def test_provider_ping_failure_is_warning_not_setup_failure(tmp_path):
    def ping(_name):
        raise RuntimeError("network unavailable")

    result = SetupWizard(
        root=tmp_path,
        env={"DEEPSEEK_API_KEY": "sk-test"},
        provider_ping=ping,
    ).run(mode=SetupMode.QUICK)
    assert result.completed is True
    assert any("network unavailable" in warning for warning in result.warnings)
    assert any(provider.status == "warn" for provider in result.providers)


def test_skip_provider_test_marks_provider_unverified(tmp_path):
    result = SetupWizard(root=tmp_path).run(
        mode=SetupMode.QUICK,
        add_provider="deepseek",
        skip_provider_test=True,
    )
    deepseek = next(provider for provider in result.providers if provider.name == "deepseek")
    assert deepseek.status == "skip"
    assert deepseek.reason == "provider test skipped"


def test_quick_mode_prefers_deepseek_env_key_then_openai_then_fake(tmp_path):
    deepseek = SetupWizard(root=tmp_path / "deepseek", env={"DEEPSEEK_API_KEY": "sk-test"}).run(mode=SetupMode.QUICK)
    openai = SetupWizard(root=tmp_path / "openai", env={"OPENAI_API_KEY": "sk-test"}).run(mode=SetupMode.QUICK)
    fake = SetupWizard(root=tmp_path / "fake", env={}).run(mode=SetupMode.QUICK)
    assert deepseek.providers[0].name == "deepseek"
    assert openai.providers[0].name == "openai"
    assert fake.providers[0].name == "fake"


def test_setup_add_provider_cli_keeps_fake_fallback(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["setup", "--add-provider", "deepseek", "--skip-provider-test"])
    out = capsys.readouterr().out
    payload = yaml.safe_load((tmp_path / ".pf-agent" / "config.yaml").read_text(encoding="utf-8"))
    assert code == 0
    assert "provider deepseek: skip" in out
    assert "fake" in payload["providers"]
