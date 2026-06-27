from pathlib import Path

import pytest

from proseforge_agent.errors import ConfigurationError
from proseforge_agent.llm.profiles import CAPABILITY_KEYS, load_provider_profiles

FIXTURE = Path(__file__).parent / "fixtures" / "providers" / "local_profiles.yaml"


def _write(tmp_path, body):
    path = tmp_path / "providers.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_local_openai_compatible_profile_loads_without_key(tmp_path):
    path = tmp_path / "providers.yaml"
    path.write_text(
        """providers:
  ollama_main:
    family: ollama
    protocol: local_openai_compatible
    base_url: http://localhost:11434/v1
    model: llama-local
""",
        encoding="utf-8",
    )
    profiles = load_provider_profiles(path)
    assert profiles["ollama_main"].privacy_class == "local"


def test_capabilities_default_to_unknown(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    protocol: local_openai_compatible
    model: m
""",
    )
    caps = load_provider_profiles(path)["p"].capabilities
    assert set(caps) == set(CAPABILITY_KEYS)
    assert all(value == "unknown" for value in caps.values())


def test_explicit_capabilities_override_defaults(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    protocol: local_openai_compatible
    model: m
    capabilities:
      text: "yes"
""",
    )
    caps = load_provider_profiles(path)["p"].capabilities
    assert caps["text"] == "yes"
    assert caps["streaming"] == "unknown"


def test_missing_family_rejected(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    protocol: local_openai_compatible
    model: m
""",
    )
    with pytest.raises(ConfigurationError) as exc:
        load_provider_profiles(path)
    assert "family" in str(exc.value)
    assert "p" in str(exc.value)


def test_missing_protocol_rejected(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    model: m
""",
    )
    with pytest.raises(ConfigurationError) as exc:
        load_provider_profiles(path)
    assert "protocol" in str(exc.value)


def test_missing_model_rejected(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    protocol: local_openai_compatible
""",
    )
    with pytest.raises(ConfigurationError) as exc:
        load_provider_profiles(path)
    assert "model" in str(exc.value)


def test_explicit_privacy_class_is_respected(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: openrouter
    protocol: openai_compatible
    model: m
    privacy_class: foreign
""",
    )
    assert load_provider_profiles(path)["p"].privacy_class == "foreign"


def test_local_family_without_protocol_prefix_is_local(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    protocol: openai_compatible
    model: m
""",
    )
    assert load_provider_profiles(path)["p"].privacy_class == "local"


def test_api_key_env_recorded_for_cloud_profile(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  gateway:
    family: openrouter
    protocol: openai_compatible
    base_url: https://openrouter.ai/api/v1
    model: m
    api_key_env: OPENROUTER_API_KEY
""",
    )
    assert load_provider_profiles(path)["gateway"].api_key_env == "OPENROUTER_API_KEY"


def test_certification_level_defaults_to_uncertified(tmp_path):
    path = _write(
        tmp_path,
        """providers:
  p:
    family: ollama
    protocol: local_openai_compatible
    model: m
""",
    )
    assert load_provider_profiles(path)["p"].certification_level == "uncertified"


def test_load_local_profiles_fixture_offline():
    profiles = load_provider_profiles(FIXTURE)
    assert len(profiles) >= 3
    assert all(profile.model for profile in profiles.values())
