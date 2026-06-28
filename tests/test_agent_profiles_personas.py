from pathlib import Path

from proseforge_agent.agent.profiles import AgentProfileRegistry
from proseforge_agent.cli import main


FIXTURE = Path(__file__).parent / "fixtures" / "agent-profiles-and-personas" / "profiles.yaml"


def test_builtin_profiles_cover_agent_personas():
    registry = AgentProfileRegistry.builtins()
    assert set(registry.names()) >= {"writer", "editor", "operator", "general"}
    assert registry.get("operator").mode == "operator_chat"


def test_profile_permission_can_only_lower_session_ceiling():
    registry = AgentProfileRegistry.builtins()
    resolved = registry.resolve("operator", session_permission_max="draft_write")
    assert resolved.permission_ceiling == "draft_write"
    assert resolved.source_permission_ceiling == "engine_write"


def test_writer_profile_prompt_pack_metadata_is_stable():
    profile = AgentProfileRegistry.builtins().resolve("writer", session_permission_max="project_write")
    assert profile.mode == "creative_chat"
    assert profile.prompt_pack["persona"] == "writer"
    assert "draft" in profile.provider_roles


def test_profiles_load_from_yaml_fixture():
    registry = AgentProfileRegistry.from_yaml(FIXTURE)
    profile = registry.resolve("copychief", session_permission_max="project_write")
    assert profile.name == "copychief"
    assert profile.mode == "creative_chat"
    assert profile.memory_scope == "project"


def test_chat_cli_accepts_profile(capsys):
    code = main(["chat", "--message", "hello", "--provider", "fake", "--profile", "operator"])
    out = capsys.readouterr().out
    assert code == 0
    assert "profile: operator" in out


def test_profile_fixture_exists():
    assert "copychief" in FIXTURE.read_text(encoding="utf-8")
