"""First-run setup guidance tests."""

from __future__ import annotations

from proseforge_agent.setup.first_run import is_setup_complete, setup_guidance


def test_chat_without_setup_prints_setup_guidance():
    guidance = setup_guidance()
    assert "pf-agent setup --quick" in guidance
    assert "pf-agent setup --minimal" in guidance


def test_daily_workbook_without_setup_prints_setup_guidance():
    guidance = setup_guidance()
    assert "pf-agent doctor" in guidance


def test_non_interactive_bootstrap_returns_error_without_prompt():
    assert is_setup_complete({}) is False


def test_interactive_bootstrap_can_enter_setup():
    assert is_setup_complete({"setup": {"completed": True}}) is True
