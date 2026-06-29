"""Guided setup reconfigure and repair tests."""

from __future__ import annotations

import yaml

from proseforge_agent.setup import SetupMode, SetupWizard
from proseforge_agent.setup.recovery import WORKSPACE_DIRS


def test_reconfigure_preserves_drafts_memory_and_agent_db(tmp_path):
    first = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    draft = first.workspace_path / "drafts" / "chapter.md"
    memory = first.workspace_path / "agent.db"
    draft.write_text("keep draft", encoding="utf-8")
    memory.write_text("keep db", encoding="utf-8")
    SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, reconfigure=True)
    assert draft.read_text(encoding="utf-8") == "keep draft"
    assert memory.read_text(encoding="utf-8") == "keep db"


def test_reconfigure_creates_config_backup(tmp_path):
    SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, reconfigure=True)
    assert result.backup_path is not None
    assert result.backup_path.exists()


def test_repair_recreates_missing_workspace_directories(tmp_path):
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    missing = result.workspace_path / "exports"
    missing.rmdir()
    repaired = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, repair=True)
    assert missing.exists()
    assert repaired.completed is True
    for name in WORKSPACE_DIRS:
        assert (repaired.workspace_path / name).exists()


def test_repair_fixes_setup_completed_flag_without_deleting_data(tmp_path):
    result = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL)
    payload = yaml.safe_load(result.config_path.read_text(encoding="utf-8"))
    payload["setup"]["completed"] = False
    result.config_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    sentinel = result.workspace_path / "projects" / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")
    repaired = SetupWizard(root=tmp_path).run(mode=SetupMode.MINIMAL, repair=True)
    updated = yaml.safe_load(repaired.config_path.read_text(encoding="utf-8"))
    assert updated["setup"]["completed"] is True
    assert sentinel.read_text(encoding="utf-8") == "keep"
