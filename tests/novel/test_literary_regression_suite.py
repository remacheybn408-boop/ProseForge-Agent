"""Literary regression suite tests (Task 99)."""

from __future__ import annotations

from proseforge_agent.cli import main
from proseforge_agent.novel import LiteraryRegressionSuite, NovelProjectStore


def test_literary_regression_suite_contract(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    suite = LiteraryRegressionSuite(tmp_path, slug="demo_novel")
    baseline = suite.baseline({"sample_001": "Quiet rain fell. Lin walked home."})

    assert baseline["samples"][0]["id"] == "sample_001"
    assert baseline["samples"][0]["metrics"]["dialogue_density"] == 0

    result = suite.test({"sample_001": '"Hello." "No." "Yes."'})

    assert result["status"] == "degraded"
    assert result["drift"][0]["sample"] == "sample_001"
    assert result["drift"][0]["metric"] == "dialogue_density"


def test_literary_regression_passes_stable_samples(tmp_path):
    NovelProjectStore(tmp_path).init_project(slug="demo_novel")
    suite = LiteraryRegressionSuite(tmp_path, slug="demo_novel")
    suite.baseline({"sample_001": "Quiet rain fell. Lin walked home."})

    result = suite.test({"sample_001": "Soft rain fell. Lin walked home."})

    assert result["status"] == "ok"
    assert result["drift"] == []


def test_literary_cli_baseline_and_test(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["project", "init", "--slug", "demo_novel"]) == 0
    golden = tmp_path / "tests" / "literary" / "golden"
    golden.mkdir(parents=True)
    sample = golden / "sample_001.md"
    sample.write_text("Quiet rain fell. Lin walked home.", encoding="utf-8")

    assert main(["literary", "baseline", "--slug", "demo_novel", "--golden-dir", str(golden)]) == 0
    sample.write_text('"Hello." "No." "Yes."', encoding="utf-8")
    assert main(["literary", "test", "--slug", "demo_novel", "--golden-dir", str(golden)]) == 0
    out = capsys.readouterr().out
    assert "Literary Regression" in out
    assert "dialogue_density" in out
