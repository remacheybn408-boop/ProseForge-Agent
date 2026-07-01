"""Slash command registry tests (Task 152)."""

from __future__ import annotations

from proseforge_agent.chat.slash import SlashCommandContext, SlashCommandRegistry
from proseforge_agent.cli import main


def test_registry_resolves_builtin_command():
    registry = SlashCommandRegistry.default()

    action = registry.resolve("/mode creative_chat", SlashCommandContext(permission_ceiling="draft_write"))

    assert action is not None
    assert action.name == "mode"
    assert action.status == "ok"
    assert action.args["value"] == "creative_chat"
    assert action.action_type == "switch_mode"


def test_registry_returns_error_for_unknown_command():
    action = SlashCommandRegistry.default().resolve("/wat", SlashCommandContext())

    assert action is not None
    assert action.status == "error"
    assert "Unknown slash command" in action.message


def test_registry_denies_commands_above_permission_ceiling():
    action = SlashCommandRegistry.default().resolve("/undo", SlashCommandContext(permission_ceiling="read_only"))

    assert action is not None
    assert action.status == "denied"
    assert action.required_permission == "draft_write"


def test_registry_help_alias_is_deterministic():
    action = SlashCommandRegistry.default().resolve("/h", SlashCommandContext())

    assert action is not None
    assert action.name == "help"
    assert "/new" in action.message
    assert "/project" in action.message


def test_chat_cli_help_uses_slash_registry(capsys):
    assert main(["chat", "--message", "/help", "--provider", "fake", "--no-project"]) == 0

    out = capsys.readouterr().out
    assert "Slash Commands" in out
    assert "/retry" in out
