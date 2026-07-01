"""Remote file sync and checkpoint tests (Task 167)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.environments import EnvironmentCheckpoint, FileSyncPlanner


def test_sync_plan_excludes_secrets_and_outside_paths(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "chapter.md").write_text("hello", encoding="utf-8")
    (root / ".env").write_text("TOKEN=secret", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("nope", encoding="utf-8")

    plan = FileSyncPlanner(root=root).plan(
        includes=["chapter.md", ".env", "../outside.txt"],
        destination="remote:/workspace",
        dry_run=True,
    )

    assert plan.operations == [{"action": "upload", "source": "chapter.md", "destination": "remote:/workspace/chapter.md"}]
    assert ".env" in plan.excludes
    assert "../outside.txt" in plan.redactions


def test_checkpoint_records_restore_plan_and_artifact_refs(tmp_path):
    checkpoint = EnvironmentCheckpoint.create(
        backend_id="ssh",
        project_refs=["demo"],
        artifact_refs=["artifact-1"],
        root=tmp_path,
    )

    assert checkpoint.backend_id == "ssh"
    assert checkpoint.artifact_refs == ["artifact-1"]
    assert checkpoint.restore_plan == ["restore checkpoint metadata", "sync artifact refs", "resume backend ssh"]


def test_environment_sync_cli_dry_run(capsys):
    assert main(["environments", "sync", "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert "Environment Sync" in out
    assert "dry_run=true" in out
