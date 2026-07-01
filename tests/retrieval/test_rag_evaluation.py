"""RAG evaluation tests (Task 138)."""

from __future__ import annotations

import json

from proseforge_agent.retrieval.evaluation import RagEvalCase, RagEvaluator
from proseforge_agent.retrieval.hybrid import HybridSearchResult
from proseforge_agent.cli import main


class _FakeSearcher:
    def search(self, query: str, *, project_slug: str, top_k: int = 5):
        return [
            HybridSearchResult("hit-1", "hero", project_slug, {"source": "ch_001"}, 1.0, 1.0, 0.0, ["keyword"]),
            HybridSearchResult("hit-2", "timeline", project_slug, {"source": "timeline_event_003"}, 0.8, 0.3, 0.5, ["vector"]),
        ][:top_k]


def test_rag_evaluation_reports_hit_rates_and_recall():
    evaluator = RagEvaluator(_FakeSearcher())

    result = evaluator.evaluate(
        [RagEvalCase(query="where did it happen?", expected_sources=["ch_001", "timeline_event_003"])],
        project_slug="demo",
    )

    assert result.hit_at_1 == 1.0
    assert result.hit_at_3 == 1.0
    assert result.hit_at_5 == 1.0
    assert result.source_recall == 1.0
    assert result.irrelevant_rate == 0.0


def test_rag_evaluation_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    chunks_dir = tmp_path / ".pf-agent" / "workspace" / "demo_novel" / "rag"
    chunks_dir.mkdir(parents=True)
    (chunks_dir / "chunks.jsonl").write_text(
        json.dumps(
            {
                "id": "chunk-1",
                "text": "hero memory",
                "project_slug": "demo_novel",
                "metadata": {"source": "ch_001"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    suite = tmp_path / "suite.yaml"
    suite.write_text("- query: hero memory\n  expected_sources:\n    - ch_001\n", encoding="utf-8")

    assert main(["rag", "eval", "--slug", "demo_novel", "--suite", str(suite)]) == 0

    out = capsys.readouterr().out
    assert "RAG Evaluation" in out
    assert "hit@1=1.000" in out
