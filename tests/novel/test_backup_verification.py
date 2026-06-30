"""Backup verification tests (Task 108)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import BackupManager, NovelProjectStore


def _seed(tmp_path, slug="demo_novel"):
    NovelProjectStore(tmp_path).init_project(slug=slug)
    chapters = tmp_path / "projects" / slug / "chapters"
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "ch_001.md").write_text("内容", encoding="utf-8")
    return chapters


def test_backup_verification_contract(tmp_path):
    """A created backup is checksum-verified and supports a dry-run restore."""
    _seed(tmp_path)
    manager = BackupManager(tmp_path, slug="demo_novel")

    backup = manager.create()
    assert backup.status == "verified"
    assert backup.file_count >= 1

    verify = manager.verify(backup.id)
    assert verify.status == "verified"
    assert verify.mismatches == []

    restore = manager.restore(backup.id, dry_run=True)
    assert restore.status == "dry_run"
    assert restore.restored is False
    assert any("ch_001" in name for name in restore.files)


def test_verify_detects_corruption(tmp_path):
    _seed(tmp_path)
    manager = BackupManager(tmp_path, slug="demo_novel")
    backup = manager.create()
    (backup.path / "data" / "chapters" / "ch_001.md").write_text("篡改", encoding="utf-8")

    verify = manager.verify(backup.id)

    assert verify.status == "corrupted"
    assert verify.mismatches


def test_dry_run_restore_does_not_modify_project(tmp_path):
    chapters = _seed(tmp_path)
    manager = BackupManager(tmp_path, slug="demo_novel")
    backup = manager.create()
    (chapters / "ch_001.md").unlink()  # lose the file

    manager.restore(backup.id, dry_run=True)
    assert not (chapters / "ch_001.md").exists()  # dry-run did not restore

    manager.restore(backup.id, dry_run=False)
    assert (chapters / "ch_001.md").read_text(encoding="utf-8") == "内容"  # real restore recovers it


def test_unknown_backup_raises(tmp_path):
    _seed(tmp_path)
    manager = BackupManager(tmp_path, slug="demo_novel")

    try:
        manager.verify("backup_999")
    except ValueError as exc:
        assert "backup_999" in str(exc)
    else:
        raise AssertionError("unknown backup should fail")


def test_backup_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    chapters = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters"
    chapters.mkdir(parents=True)
    (chapters / "ch_001.md").write_text("内容", encoding="utf-8")

    assert main(["backup", "create", "--slug", "demo_novel"]) == 0
    out = capsys.readouterr().out
    assert "Backup" in out and "backup_001" in out

    assert main(["backup", "verify", "backup_001", "--slug", "demo_novel"]) == 0
    assert "verified" in capsys.readouterr().out

    assert main(["backup", "restore", "backup_001", "--slug", "demo_novel", "--dry-run"]) == 0
    assert "dry_run" in capsys.readouterr().out
