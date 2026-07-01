"""User model and memory nudge tests (Task 179)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.memory.nudges import MemoryNudgeGenerator
from proseforge_agent.memory.user_model import UserModelStore


def test_nudge_does_not_accept_memory_automatically(tmp_path):
    store = UserModelStore(tmp_path)
    candidate = store.add_candidate(
        text="User prefers concise Chinese answers.",
        scope="global",
        source_refs=["chat-1"],
    )

    nudges = MemoryNudgeGenerator(store).generate()

    assert nudges[0].candidate_id == candidate.id
    assert nudges[0].action_choices == ["accept", "reject", "keep_pending"]
    assert store.get_candidate(candidate.id).status == "candidate"
    assert store.facts(scope="global") == []


def test_user_model_separates_global_and_project_facts(tmp_path):
    store = UserModelStore(tmp_path)

    global_fact = store.add_fact("Answer in Chinese.", scope="global", source_refs=["chat-1"])
    project_fact = store.add_fact("Use noir tone.", scope="project:demo", source_refs=["chat-2"])

    assert store.facts(scope="global") == [global_fact]
    assert store.facts(scope="project:demo") == [project_fact]


def test_memory_nudges_surface_contradictions(tmp_path):
    store = UserModelStore(tmp_path)
    store.add_fact("Answer in Chinese.", scope="global", source_refs=["chat-1"])
    candidate = store.add_candidate("Answer in English.", scope="global", source_refs=["chat-2"])

    nudge = MemoryNudgeGenerator(store).generate()[0]

    assert nudge.candidate_id == candidate.id
    assert "contradiction" in nudge.reason


def test_user_model_redacts_secret_candidates(tmp_path):
    store = UserModelStore(tmp_path)

    candidate = store.add_candidate("My token=secret-value", scope="global", source_refs=["chat-1"])

    assert "secret-value" not in candidate.text
    assert candidate.redaction_applied is True


def test_memory_nudges_cli(capsys):
    assert main(["memory", "nudges", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Memory Nudges" in out
