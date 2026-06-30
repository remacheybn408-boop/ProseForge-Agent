"""Editorial pipeline tests (Task 105)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import DraftVersionStore, EditorialPipeline, NovelProjectStore


_NON_FINAL = ["outline", "rough_draft", "structure_edit", "style_edit", "continuity_check", "copy_edit"]


def _seed(tmp_path, slug="demo_novel", chapter="ch_001", text="初稿内容。"):
    NovelProjectStore(tmp_path).init_project(slug=slug)
    path = tmp_path / "projects" / slug / "chapters" / f"{chapter}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return tmp_path / "projects" / slug / "editorial" / chapter


def test_editorial_pipeline_contract(tmp_path):
    """A chapter advances through the stages to final, with every stage artifact preserved."""
    edir = _seed(tmp_path)
    pipe = EditorialPipeline(tmp_path, slug="demo_novel")

    state = pipe.run("ch_001")

    assert state.current_stage == "copy_edit"
    for stage in _NON_FINAL:
        assert (edir / f"{stage}.md").exists()

    pending = pipe.promote("ch_001", to="final")
    assert pending.status == "pending_approval"

    promoted = pipe.promote("ch_001", to="final", approve=True)
    assert promoted.status == "promoted"
    assert (edir / "final.md").exists()


def test_each_stage_artifact_records_dod(tmp_path):
    edir = _seed(tmp_path)
    EditorialPipeline(tmp_path, slug="demo_novel").run("ch_001")

    assert "DoD" in (edir / "rough_draft.md").read_text(encoding="utf-8")


def test_status_reports_current_stage(tmp_path):
    _seed(tmp_path)
    pipe = EditorialPipeline(tmp_path, slug="demo_novel")
    pipe.run("ch_001")

    status = pipe.status()

    by_chapter = {entry["chapter"]: entry for entry in status.to_dict()["chapters"]}
    assert by_chapter["ch_001"]["current_stage"] == "copy_edit"


def test_promote_to_final_commits_a_draft_version(tmp_path):
    _seed(tmp_path)
    pipe = EditorialPipeline(tmp_path, slug="demo_novel")
    pipe.run("ch_001")

    pipe.promote("ch_001", to="final", approve=True)

    versions = DraftVersionStore(tmp_path, slug="demo_novel").list_versions("ch_001")
    assert any(version.prompt == "final" for version in versions)


def test_unknown_stage_raises(tmp_path):
    _seed(tmp_path)
    pipe = EditorialPipeline(tmp_path, slug="demo_novel")

    try:
        pipe.promote("ch_001", to="galley", approve=True)
    except ValueError as exc:
        assert "galley" in str(exc)
    else:
        raise AssertionError("unknown stage should fail")


def test_editorial_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    chapter = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel" / "chapters" / "ch_001.md"
    chapter.parent.mkdir(parents=True)
    chapter.write_text("初稿。", encoding="utf-8")

    assert main(["editorial", "run", "--slug", "demo_novel", "--chapter", "ch_001"]) == 0
    assert "Editorial" in capsys.readouterr().out

    assert main(["editorial", "status", "--slug", "demo_novel"]) == 0
    assert "ch_001" in capsys.readouterr().out

    assert main(["editorial", "promote", "--slug", "demo_novel", "--chapter", "ch_001", "--to", "final", "--approve"]) == 0
    assert "promoted" in capsys.readouterr().out
