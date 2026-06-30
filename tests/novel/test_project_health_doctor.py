"""Project health doctor tests (Task 103)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import NovelProjectStore, ProjectHealthDoctor


def _project(tmp_path, slug="demo_novel"):
    NovelProjectStore(tmp_path).init_project(slug=slug)
    return tmp_path / "projects" / slug


def test_project_health_doctor_contract(tmp_path):
    """Doctor finds missing dirs, orphan files, and numbering gaps; --fix repairs non-destructively."""
    proj = _project(tmp_path)
    (proj / "chapters").mkdir()
    (proj / "chapters" / "ch_001.md").write_text("a", encoding="utf-8")
    (proj / "chapters" / "ch_003.md").write_text("c", encoding="utf-8")  # gap: ch_002 missing
    (proj / "orphan.md").write_text("stray", encoding="utf-8")
    doctor = ProjectHealthDoctor(tmp_path, slug="demo_novel")

    report = doctor.diagnose()
    kinds = {issue.kind for issue in report.issues}
    assert {"missing_directory", "orphan_file", "chapter_numbering"} <= kinds
    assert report.status == "degraded"

    fixed = doctor.diagnose(fix=True)
    assert (proj / "revisions").exists()  # missing directory created
    assert (proj / "quarantine" / "orphan.md").exists()  # orphan moved, not deleted
    assert not (proj / "orphan.md").exists()
    assert (proj / "chapters" / "ch_001.md").read_text(encoding="utf-8") == "a"  # data preserved
    assert fixed.fixed
    assert fixed.to_dict()["fixed"]


def test_doctor_reports_missing_chapters_directory(tmp_path):
    _project(tmp_path)
    doctor = ProjectHealthDoctor(tmp_path, slug="demo_novel")

    report = doctor.diagnose()

    targets = {(issue.kind, issue.target) for issue in report.issues}
    assert ("missing_directory", "chapters") in targets


def test_doctor_clean_project_is_ok(tmp_path):
    proj = _project(tmp_path)
    (proj / "chapters").mkdir()
    (proj / "chapters" / "ch_001.md").write_text("a", encoding="utf-8")
    (proj / "chapters" / "ch_002.md").write_text("b", encoding="utf-8")
    (proj / "revisions").mkdir()
    doctor = ProjectHealthDoctor(tmp_path, slug="demo_novel")

    report = doctor.diagnose()

    assert report.status == "ok"
    assert report.issues == []


def test_doctor_fix_is_idempotent(tmp_path):
    proj = _project(tmp_path)
    (proj / "chapters").mkdir()
    (proj / "chapters" / "ch_001.md").write_text("a", encoding="utf-8")
    doctor = ProjectHealthDoctor(tmp_path, slug="demo_novel")

    doctor.diagnose(fix=True)
    second = doctor.diagnose(fix=True)

    assert second.fixed == []  # nothing left to repair


def test_project_doctor_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    proj = tmp_path / ".pf-agent" / "workspace" / "projects" / "demo_novel"
    (proj / "chapters").mkdir(parents=True)
    (proj / "chapters" / "ch_001.md").write_text("a", encoding="utf-8")
    (proj / "stray.md").write_text("x", encoding="utf-8")

    assert main(["project", "doctor", "--slug", "demo_novel"]) == 0
    assert "Project Health" in capsys.readouterr().out
    assert main(["project", "doctor", "--slug", "demo_novel", "--fix"]) == 0
    assert (proj / "quarantine" / "stray.md").exists()
