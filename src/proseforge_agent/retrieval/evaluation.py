"""RAG retrieval evaluation metrics."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class RagEvalCase:
    """One RAG evaluation query."""

    query: str
    expected_sources: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "RagEvalCase":
        return cls(query=str(payload["query"]), expected_sources=[str(source) for source in payload.get("expected_sources", [])])

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RagEvalResult:
    """Aggregate RAG evaluation result."""

    case_count: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    source_recall: float
    irrelevant_rate: float

    def to_dict(self) -> dict:
        return asdict(self)


class RagEvaluator:
    """Evaluate a searcher against expected source references."""

    def __init__(self, searcher) -> None:
        self.searcher = searcher

    def evaluate(self, cases: list[RagEvalCase], *, project_slug: str) -> RagEvalResult:
        if not cases:
            return RagEvalResult(0, 0.0, 0.0, 0.0, 0.0, 0.0)
        hit1 = hit3 = hit5 = 0
        expected_total = found_total = irrelevant_total = returned_total = 0
        for case in cases:
            results = self.searcher.search(case.query, project_slug=project_slug, top_k=5)
            sources = [_source_for(result) for result in results]
            expected = set(case.expected_sources)
            expected_total += len(expected)
            found_total += len(expected.intersection(sources))
            returned_total += len(sources)
            irrelevant_total += sum(1 for source in sources if source not in expected)
            hit1 += int(bool(expected.intersection(sources[:1])))
            hit3 += int(bool(expected.intersection(sources[:3])))
            hit5 += int(bool(expected.intersection(sources[:5])))
        count = len(cases)
        return RagEvalResult(
            case_count=count,
            hit_at_1=hit1 / count,
            hit_at_3=hit3 / count,
            hit_at_5=hit5 / count,
            source_recall=(found_total / expected_total) if expected_total else 0.0,
            irrelevant_rate=(irrelevant_total / returned_total) if returned_total else 0.0,
        )


def load_eval_cases(path: str | Path) -> list[RagEvalCase]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
    else:
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8-sig"))
    return [RagEvalCase.from_dict(item) for item in (payload or [])]


def default_eval_cases_from_documents(documents) -> list[RagEvalCase]:
    cases: list[RagEvalCase] = []
    for document in documents[:5]:
        source = document.metadata.get("source") or document.id
        cases.append(RagEvalCase(query=document.text[:120], expected_sources=[source]))
    return cases


def _source_for(result) -> str:
    return str(result.metadata.get("source") or result.id)


__all__ = ["RagEvalCase", "RagEvalResult", "RagEvaluator", "default_eval_cases_from_documents", "load_eval_cases"]
