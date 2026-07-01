"""Autonomous skill creation tests (Task 176)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.skills.creation import SkillCandidateStore


def test_skill_candidate_is_not_enabled_by_default(tmp_path):
    store = SkillCandidateStore(tmp_path)

    candidate = store.propose_from_trace(
        trigger="repeat demo task",
        purpose="Handle repeated demo steps",
        instructions="Run the same checklist with token=secret.",
        source_trace_ids=["trace-1"],
    )

    assert candidate.enabled is False
    assert candidate.approval_state == "pending"
    assert "token=secret" not in candidate.instructions
    assert candidate.redaction_status == "redacted"


def test_skill_candidate_deduplicates_by_trigger_and_purpose(tmp_path):
    store = SkillCandidateStore(tmp_path)

    first = store.propose_from_trace("repeat", "purpose", "instructions", ["trace-1"])
    second = store.propose_from_trace("repeat", "purpose", "instructions again", ["trace-2"])

    assert first.id == second.id
    assert second.source_trace_ids == ["trace-1", "trace-2"]


def test_skill_candidate_approval_returns_dry_run_install_plan(tmp_path):
    store = SkillCandidateStore(tmp_path)
    candidate = store.propose_from_trace("repeat", "purpose", "instructions", ["trace-1"])

    plan = store.approve(candidate.id, dry_run=True)

    assert plan.status == "planned"
    assert plan.skill_id == candidate.id
    assert plan.dry_run is True
    assert store.get(candidate.id).approval_state == "pending"


def test_skill_candidate_rejection_marks_record(tmp_path):
    store = SkillCandidateStore(tmp_path)
    candidate = store.propose_from_trace("repeat", "purpose", "instructions", ["trace-1"])

    rejected = store.reject(candidate.id)

    assert rejected.approval_state == "rejected"
    assert rejected.enabled is False


def test_skills_candidates_cli_list(capsys):
    assert main(["skills", "candidates", "list"]) == 0

    out = capsys.readouterr().out
    assert "Skill Candidates" in out
