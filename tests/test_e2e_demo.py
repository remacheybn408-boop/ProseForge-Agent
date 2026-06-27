import os
from pathlib import Path

from proseforge_agent.demo import DemoRunner
from proseforge_agent.planning.intake import load_intake

_FIXTURE_INTAKE = (
    Path(__file__).parent / "fixtures" / "demo_project" / "intake.yaml"
)


def test_fake_provider_demo_writes_required_artifacts(tmp_path):
    result = DemoRunner(tmp_path).run(provider="fake")
    assert result.status == "ok"
    assert result.daily_workbook.exists()
    assert result.chapter_draft.exists()
    assert result.report_pack.exists()


def test_demo_status_ok_and_all_artifacts_exist(tmp_path):
    result = DemoRunner(tmp_path).run(provider="fake")
    for path in (
        result.intake,
        result.phase_plan,
        result.daily_workbook,
        result.chapter_context,
        result.chapter_draft,
        result.review_report,
        result.export_report,
        result.memory_candidates,
        result.closeout,
        result.report_pack,
    ):
        assert path.exists(), path


def test_demo_uses_no_api_keys(tmp_path, monkeypatch):
    for key in [k for k in os.environ if k.endswith("_API_KEY")]:
        monkeypatch.delenv(key, raising=False)
    result = DemoRunner(tmp_path).run(provider="fake")
    assert result.status == "ok"
    assert result.provider == "fake"
    assert result.provider_certified is True


def test_demo_is_deterministic(tmp_path):
    a = DemoRunner(tmp_path / "a").run(provider="fake")
    b = DemoRunner(tmp_path / "b").run(provider="fake")
    assert a.chapter_draft.read_text(encoding="utf-8") == b.chapter_draft.read_text(
        encoding="utf-8"
    )


def test_demo_report_pack_lists_artifacts(tmp_path):
    result = DemoRunner(tmp_path).run(provider="fake")
    text = result.report_pack.read_text(encoding="utf-8")
    assert "daily-workbook" in text
    assert "draft" in text


def test_demo_report_pack_has_no_machine_path(tmp_path):
    result = DemoRunner(tmp_path).run(provider="fake")
    text = result.report_pack.read_text(encoding="utf-8")
    assert str(tmp_path) not in text


def test_demo_fixture_intake_is_valid():
    intake = load_intake(_FIXTURE_INTAKE)
    assert intake.slug == "demo_novel"
    assert intake.target_chapters == 12
