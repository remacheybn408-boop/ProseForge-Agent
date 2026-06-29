"""Guided setup config generation tests."""

from __future__ import annotations

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup import SetupMode, SetupWizard


def test_config_generator_never_writes_plaintext_api_key(tmp_path):
    result = SetupWizard(root=tmp_path, env={"DEEPSEEK_API_KEY": "sk-test"}).run(mode=SetupMode.QUICK)
    config_text = result.config_path.read_text(encoding="utf-8")
    assert "sk-test" not in config_text
    assert "env://DEEPSEEK_API_KEY" in config_text


def test_existing_config_is_backed_up_before_reconfigure(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("user_owned: true\n", encoding="utf-8")
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, reconfigure=True)
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert "user_owned: true" in result.backup_path.read_text(encoding="utf-8")


def test_print_config_outputs_key_ref_only(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / ".pf-agent"
    root.mkdir()
    (root / "config.yaml").write_text("api_key: sk-test\nkey_ref: env://DEEPSEEK_API_KEY\n", encoding="utf-8")
    code = main(["setup", "--print-config"])
    out = capsys.readouterr().out
    assert code == 0
    assert "sk-test" not in out
    assert "api_key: [redacted]" in out
    assert "env://DEEPSEEK_API_KEY" in out


def test_config_merge_preserves_unknown_user_fields(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("custom:\n  owner: user\n", encoding="utf-8")
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    assert payload["custom"]["owner"] == "user"
    assert payload["setup"]["completed"] is True
