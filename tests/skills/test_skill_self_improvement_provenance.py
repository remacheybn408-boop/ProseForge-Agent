"""Skill self-improvement and provenance tests (Task 177)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.skills.improvement import SkillRevisionStore


def test_revision_candidate_preserves_base_version(tmp_path):
    store = SkillRevisionStore(tmp_path)

    candidate = store.propose(
        skill_id="demo-skill",
        base_version="1.0.0",
        proposed_instructions="Add a clearer checklist.",
        evidence_refs=["usage-1"],
    )

    assert candidate.base_version == "1.0.0"
    assert candidate.proposed_version == "1.0.1"
    assert candidate.approval_state == "pending"
    assert candidate.evidence_refs == ["usage-1"]
    assert "Add a clearer checklist" in candidate.diff


def test_revision_blocks_permission_escalation(tmp_path):
    store = SkillRevisionStore(tmp_path)

    candidate = store.propose(
        skill_id="demo-skill",
        base_version="1.0.0",
        proposed_instructions="Need write access.",
        evidence_refs=["usage-1"],
        requested_permissions=["project_write"],
    )

    assert "permission_escalation" in candidate.risk_flags
    assert candidate.approval_state == "blocked"


def test_revision_approval_keeps_previous_version_recoverable(tmp_path):
    store = SkillRevisionStore(tmp_path)
    candidate = store.propose("demo-skill", "1.0.0", "New instructions.", ["usage-1"])

    approved = store.approve(candidate.id)

    assert approved.approval_state == "approved"
    assert store.history("demo-skill")[0].base_version == "1.0.0"


def test_revision_rejection_records_decision(tmp_path):
    store = SkillRevisionStore(tmp_path)
    candidate = store.propose("demo-skill", "1.0.0", "New instructions.", ["usage-1"])

    rejected = store.reject(candidate.id)

    assert rejected.approval_state == "rejected"


def test_skills_improve_cli_dry_run(capsys):
    assert main(["skills", "improve", "demo-skill", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Skill Improvement" in out
    assert "demo-skill" in out
