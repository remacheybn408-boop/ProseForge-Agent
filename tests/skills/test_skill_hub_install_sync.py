"""Skill hub install and sync tests (Task 175)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.skills.hub import FakeSkillHubClient
from proseforge_agent.skills.install import SkillInstaller


def test_install_dry_run_reports_permissions_and_checksum(tmp_path):
    installer = SkillInstaller(root=tmp_path, hub=FakeSkillHubClient())

    plan = installer.install("demo-skill", dry_run=True)

    assert plan.status == "planned"
    assert plan.skill_id == "demo-skill"
    assert plan.checksum.startswith("sha256:")
    assert plan.requested_permissions == ["read_only"]
    assert plan.rollback_plan["action"] == "remove"
    assert not (tmp_path / "demo-skill").exists()


def test_skill_hub_search_returns_deterministic_matches():
    results = FakeSkillHubClient().search("demo")

    assert results[0].skill_id == "demo-skill"
    assert results[0].version == "1.0.0"


def test_install_denies_permission_above_ceiling(tmp_path):
    installer = SkillInstaller(root=tmp_path, hub=FakeSkillHubClient())

    plan = installer.install("writer-skill", dry_run=True, permission_ceiling="read_only")

    assert plan.status == "blocked"
    assert "requires draft_write" in plan.reason


def test_update_all_dry_run_uses_offline_cache(tmp_path):
    installer = SkillInstaller(root=tmp_path, hub=FakeSkillHubClient())

    plans = installer.update_all(dry_run=True, use_offline_cache=True)

    assert plans
    assert all(plan.status in {"planned", "blocked"} for plan in plans)
    assert plans[0].source == "offline-cache"


def test_skills_install_cli_dry_run(capsys):
    assert main(["skills", "install", "demo-skill", "--dry-run", "--provider", "fake"]) == 0

    out = capsys.readouterr().out
    assert "Skill Install" in out
    assert "sha256:" in out
