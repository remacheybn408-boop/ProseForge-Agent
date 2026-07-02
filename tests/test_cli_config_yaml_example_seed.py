"""CLI config YAML example seed tests (Task 195)."""

from __future__ import annotations

from pathlib import Path

import yaml

from proseforge_agent.cli import main
from proseforge_agent.setup.config_generator import (
    example_config_text,
    known_config_keys,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "configs" / "pf-agent.example.yaml"


def _dotted_keys(node, prefix=""):
    keys = set()
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.add(path)
            keys |= _dotted_keys(value, path)
    return keys


def test_known_config_keys_lists_core_sections():
    keys = set(known_config_keys())
    for expected in (
        "setup.mode",
        "agent.language",
        "llm.default_provider",
        "llm.fallback_provider",
        "llm.providers",
        "paths.workspace_root",
        "engine.enabled",
    ):
        assert expected in keys, f"missing known key: {expected}"


def test_example_yaml_file_parses_and_covers_known_keys():
    assert EXAMPLE.exists(), "configs/pf-agent.example.yaml must exist"
    loaded = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    present = _dotted_keys(loaded)
    for key in known_config_keys():
        assert key in present, f".example.yaml missing key: {key}"


def test_example_config_text_matches_committed_file():
    assert example_config_text() == EXAMPLE.read_text(encoding="utf-8")


def test_example_yaml_has_no_real_secrets():
    text = EXAMPLE.read_text(encoding="utf-8")
    assert "sk-" not in text
    loaded = yaml.safe_load(text)
    providers = loaded["llm"]["providers"]
    for payload in providers.values():
        assert "api_key" not in payload  # only api_key_ref indirection allowed


def test_cli_init_config_writes_seed(tmp_path):
    out = tmp_path / "config.yaml"
    code = main(["init", "--config", "--out", str(out)])
    assert code == 0
    assert out.exists()
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    present = _dotted_keys(loaded)
    for key in known_config_keys():
        assert key in present


def test_cli_init_config_does_not_run_first_run_wizard(tmp_path, monkeypatch):
    # --config must not create the full workspace tree, only the seed file.
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "seed.yaml"
    main(["init", "--config", "--out", str(out)])
    assert not (tmp_path / ".pf-agent").exists()
