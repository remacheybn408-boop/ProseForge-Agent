"""Product-grade setup config generator tests (Task 78)."""

from __future__ import annotations

import yaml

from proseforge_agent.setup import SetupMode, SetupWizard
from proseforge_agent.setup.config_generator import SetupConfigGenerator


def test_setup_config_generator_contract():
    config = SetupConfigGenerator().build_product_config(
        mode=SetupMode.QUICK,
        workspace_path="~/.proseforge-agent/workspace",
        providers={
            "fake": {
                "enabled": True,
                "configured": True,
                "model": "fake-local",
            },
            "deepseek": {
                "enabled": True,
                "configured": True,
                "api_key_ref": "keychain://proseforge-agent/deepseek",
                "model": "deepseek-chat",
            },
        },
    )
    assert config["agent"]["profile"] == "default"
    assert config["agent"]["language"] == "zh-CN"
    assert config["llm"]["default_provider"] == "deepseek"
    assert config["llm"]["fallback_provider"] == "fake"
    assert config["llm"]["providers"]["deepseek"]["api_key_ref"] == "keychain://proseforge-agent/deepseek"
    assert "api_key" not in config["llm"]["providers"]["deepseek"]
    assert config["paths"]["workspace_root"] == "~/.proseforge-agent/workspace"
    assert config["setup"]["completed"] is True


def test_setup_wizard_writes_product_schema_and_env_template(tmp_path):
    result = SetupWizard(root=tmp_path, env={"DEEPSEEK_API_KEY": "sk-test"}).run(mode=SetupMode.QUICK)
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert payload["llm"]["default_provider"] == "deepseek"
    assert payload["llm"]["fallback_provider"] == "fake"
    assert payload["paths"]["workspace_root"] == str(result.workspace_path)
    assert "sk-test" not in result.config_path.read_text(encoding="utf-8")
    assert "sk-test" not in env_text
    assert "DEEPSEEK_API_KEY=" in env_text
