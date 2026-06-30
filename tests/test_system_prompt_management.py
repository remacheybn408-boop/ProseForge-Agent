"""System prompt management tests (Task 112)."""

from __future__ import annotations

from proseforge_agent.chat import ChatPromptBuilder
from proseforge_agent.chat.system_prompts import (
    SystemPromptComposer,
    SystemPromptRegistry,
    SystemPromptStore,
)
from proseforge_agent.cli import main


def test_system_prompt_registry_and_session_override_round_trip(tmp_path):
    registry = SystemPromptRegistry.builtins()
    store = SystemPromptStore(tmp_path)

    template = registry.get("professional_novel_editor")
    record = store.set_session_template("session_001", "cold_editor", registry=registry)

    assert template.version == "1"
    assert record.template_id == "cold_editor"
    assert record.version == registry.get("cold_editor").version
    assert store.get_session_prompt("session_001", registry).template_id == "cold_editor"


def test_system_prompt_composition_order_is_stable(tmp_path):
    registry = SystemPromptRegistry.builtins()
    store = SystemPromptStore(tmp_path)
    store.set_session_override("session_001", "Session override.")

    composed = SystemPromptComposer(registry=registry, store=store).compose(
        session_id="session_001",
        base_template="professional_novel_editor",
        agent_profile="Profile text.",
        project_context="Project context.",
        writing_rules=["No quotes."],
        provider_constraints=["fake provider."],
    )

    assert composed.sections == [
        "base system prompt",
        "agent profile",
        "project context",
        "writing rules",
        "provider constraints",
        "session override",
    ]
    assert composed.text.index("Profile text.") < composed.text.index("Project context.")
    assert composed.version.startswith("professional_novel_editor@1+session_override@")


def test_chat_prompt_builder_accepts_session_system_override():
    pack = ChatPromptBuilder().build(
        text="hello",
        mode="general_chat",
        system_override="You are a cold editor.",
    )

    assert pack.system == "You are a cold editor."


def test_prompt_cli_and_chat_system_override(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert main(["prompt", "list"]) == 0
    assert main(["prompt", "show", "professional_novel_editor"]) == 0
    assert main(["prompt", "set", "--session", "session_001", "--template", "cold_editor"]) == 0
    assert main(["chat", "--message", "hello", "--provider", "fake", "--system", "You are cold.", "--show-prompt"]) == 0

    out = capsys.readouterr().out
    assert "professional_novel_editor" in out
    assert "cold_editor" in out
    assert "You are cold." in out
