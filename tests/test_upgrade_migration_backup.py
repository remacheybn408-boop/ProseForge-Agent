from pathlib import Path

import pytest

from proseforge_agent.cli import main
from proseforge_agent.errors import ConfigurationError
from proseforge_agent.install.migrations import MigrationRunner


def _seed_workspace(root: Path) -> None:
    (root / "chats").mkdir(parents=True)
    (root / "memory").mkdir()
    (root / "runs").mkdir()
    (root / "chats" / "session.json").write_text('{"text":"今天写什么？"}', encoding="utf-8")
    (root / "memory" / "items.jsonl").write_text('{"text":"记忆"}\n', encoding="utf-8")
    (root / "runs" / "run.json").write_text('{"state":"created"}', encoding="utf-8")


def test_failed_migration_restores_from_backup_and_reports_rollback(tmp_path):
    _seed_workspace(tmp_path)
    result = MigrationRunner(tmp_path, fail_after_backup=True).run("1", "2")
    assert result.status == "rolled_back"
    assert result.backup_path.exists()
    assert result.rollback_steps
    assert (tmp_path / "chats" / "session.json").exists()


def test_upgrade_preserves_chats_memory_and_workflow_runs(tmp_path):
    _seed_workspace(tmp_path)
    result = MigrationRunner(tmp_path).run("1", "2")
    assert result.status == "migrated"
    assert (tmp_path / "chats" / "session.json").exists()
    assert (tmp_path / "memory" / "items.jsonl").exists()
    assert (tmp_path / "runs" / "run.json").exists()


def test_no_op_when_versions_match(tmp_path):
    _seed_workspace(tmp_path)
    result = MigrationRunner(tmp_path).run("2", "2")
    assert result.status == "noop"
    assert result.migrated_files == []


def test_unknown_target_version_raises_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError):
        MigrationRunner(tmp_path).run("1", "99")


def test_chinese_content_survives_migration_round_trip(tmp_path):
    _seed_workspace(tmp_path)
    MigrationRunner(tmp_path).run("1", "2")
    assert "今天写什么？" in (tmp_path / "chats" / "session.json").read_text(encoding="utf-8")


def test_fixture_workspace_exists():
    fixture = Path(__file__).parent / "fixtures" / "upgrade-migration-and-backup" / "workspace_v1"
    assert (fixture / "chats" / "session.json").exists()


def test_upgrade_check_cli(capsys):
    code = main(["upgrade", "--check"])
    out = capsys.readouterr().out
    assert code == 0
    assert "Upgrade" in out
