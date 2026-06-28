import yaml
from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.provider_setup import ProviderSetupResult, ProviderSetupWizard
from proseforge_agent.install.secrets import SecretStore


FIXTURE = Path(__file__).parent / "fixtures" / "provider-setup-wizard" / "expected_profile.yaml"


def test_openai_compatible_provider_uses_compatible_profile_shape(tmp_path):
    result = ProviderSetupWizard(tmp_path, SecretStore.for_platform("linux", False)).configure(
        provider="deepseek",
        api_key="sk-secret",
        model="deepseek-chat",
    )
    payload = yaml.safe_load(result.profile_path.read_text(encoding="utf-8"))
    assert result.secret_ref == "secret://deepseek/api_key"
    assert payload["protocol"] == "openai_compatible"
    assert "sk-secret" not in result.profile_path.read_text(encoding="utf-8")


def test_native_provider_uses_native_profile_shape(tmp_path):
    result = ProviderSetupWizard(tmp_path, SecretStore.for_platform("macos", True)).configure(
        provider="anthropic",
        api_key="sk-ant",
        model="claude-sonnet",
    )
    payload = yaml.safe_load(result.profile_path.read_text(encoding="utf-8"))
    assert payload["protocol"] == "native"
    assert result.provider == "anthropic"


def test_verify_flag_routes_through_normalized_contract(tmp_path):
    result = ProviderSetupWizard(tmp_path, SecretStore.for_platform("linux", False)).configure(
        provider="deepseek",
        api_key="sk-secret",
        model="deepseek-chat",
        verify=True,
    )
    assert isinstance(result, ProviderSetupResult)
    assert result.verified is True


def test_unknown_provider_raises_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError):
        ProviderSetupWizard(tmp_path, SecretStore.for_platform("linux", False)).configure(
            provider="unknown",
            api_key="x",
            model="m",
        )


def test_profile_supports_utf8_provider_display_names(tmp_path):
    result = ProviderSetupWizard(tmp_path, SecretStore.for_platform("linux", False)).configure(
        provider="qwen",
        api_key="sk-secret",
        model="通义千问",
    )
    assert "通义千问" in result.profile_path.read_text(encoding="utf-8")


def test_provider_setup_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["provider", "setup", "--provider", "deepseek", "--model", "deepseek-chat"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Provider Setup" in out
    assert (tmp_path / ".pf-agent" / "providers" / "deepseek.yaml").exists()


def test_expected_profile_fixture_shape():
    payload = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert payload["secret_ref"] == "secret://deepseek/api_key"
