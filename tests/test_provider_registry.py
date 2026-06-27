from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.llm import (
    STANDARD_ROLES,
    Message,
    ProviderRequest,
    ProviderRegistry,
)

EXAMPLE_CONFIG = (
    Path(__file__).parents[1] / "configs" / "providers.example.yaml"
)


def _base_data():
    return {
        "default_provider": "fake_main",
        "providers": [
            {"name": "fake_main", "kind": "fake", "model": "fake-novelist", "options": {}}
        ],
        "roles": {role: "fake_main" for role in STANDARD_ROLES},
    }


def test_registry_resolves_all_standard_roles():
    registry = ProviderRegistry.from_dict(_base_data())
    for role in STANDARD_ROLES:
        provider = registry.provider_for_role(role)
        assert provider.name == "fake_main"


def test_unknown_provider_name_raises_configuration_error():
    data = _base_data()
    data["roles"]["drafter"] = "ghost"
    with pytest.raises(ConfigurationError) as exc:
        ProviderRegistry.from_dict(data)
    assert "ghost" in str(exc.value)


def test_role_without_mapping_falls_back_to_default():
    data = _base_data()
    del data["roles"]["critic"]
    registry = ProviderRegistry.from_dict(data)
    provider = registry.provider_for_role("critic")
    assert provider.name == "fake_main"


def test_registry_loads_example_yaml_offline():
    registry = ProviderRegistry.from_yaml(EXAMPLE_CONFIG)
    provider = registry.provider_for_role("drafter")
    result = provider.generate(
        ProviderRequest(role="drafter", messages=[Message(role="user", content="hi")])
    )
    assert result.provider == provider.name
    assert result.text != ""


def test_unknown_kind_raises_configuration_error():
    data = _base_data()
    data["providers"][0]["kind"] = "mystery"
    registry = ProviderRegistry.from_dict(data)
    with pytest.raises(ConfigurationError):
        registry.provider_for_role("drafter")
