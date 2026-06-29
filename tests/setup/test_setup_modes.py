"""Setup mode contract tests (Task 77)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.setup.modes import (
    SETUP_MODE_CONTRACTS,
    SetupMode,
    mode_menu_lines,
    resolve_mode_choice,
)


def test_setup_modes_contract():
    quick = SETUP_MODE_CONTRACTS[SetupMode.QUICK]
    full = SETUP_MODE_CONTRACTS[SetupMode.FULL]
    minimal = SETUP_MODE_CONTRACTS[SetupMode.MINIMAL]
    assert quick.provider_order[:4] == ("deepseek", "qwen", "glm", "doubao")
    assert "provider" in full.steps
    assert "shell_completion" in full.steps
    assert minimal.provider_order == ("fake",)
    assert minimal.requires_network is False


def test_setup_mode_choice_numbers_are_stable():
    assert resolve_mode_choice("1") == SetupMode.QUICK
    assert resolve_mode_choice("2") == SetupMode.FULL
    assert resolve_mode_choice("3") == SetupMode.MINIMAL


def test_setup_mode_menu_lists_quick_full_minimal():
    lines = mode_menu_lines()
    assert "[1] Quick" in lines
    assert "[2] Full" in lines
    assert "[3] Minimal" in lines


def test_bare_setup_prints_mode_selection_without_writing_config(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["setup"])
    out = capsys.readouterr().out
    assert code == 0
    assert "[1] Quick" in out
    assert "[2] Full" in out
    assert "[3] Minimal" in out
    assert not (tmp_path / ".pf-agent" / "config.yaml").exists()
