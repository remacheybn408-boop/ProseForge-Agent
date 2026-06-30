"""Literary style regression baselines and drift checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .writing_rules import WritingRulesStore


LITERARY_BASELINE_NAME = "literary_baseline.yaml"


class LiteraryRegressionSuite:
    """Compare current golden samples against stored style baselines."""

    def __init__(self, root: str | Path, *, slug: str, threshold: float = 0.25) -> None:
        self.root = Path(root)
        self.slug = slug
        self.threshold = threshold
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / LITERARY_BASELINE_NAME

    def baseline(self, samples: dict[str, str]) -> dict[str, Any]:
        data = {
            "slug": self.slug,
            "threshold": self.threshold,
            "samples": [
                {"id": sample_id, "metrics": self.metrics(text)}
                for sample_id, text in sorted(samples.items())
            ],
        }
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return data

    def test(self, samples: dict[str, str]) -> dict[str, Any]:
        baseline = self._load()
        baseline_by_id = {sample["id"]: sample["metrics"] for sample in baseline.get("samples", [])}
        drift: list[dict[str, Any]] = []
        current = []
        for sample_id, text in sorted(samples.items()):
            metrics = self.metrics(text)
            current.append({"id": sample_id, "metrics": metrics})
            expected = baseline_by_id.get(sample_id)
            if expected is None:
                drift.append({"sample": sample_id, "metric": "missing_baseline", "expected": None, "actual": "present"})
                continue
            drift.extend(_metric_drift(sample_id, expected, metrics, float(baseline.get("threshold", self.threshold))))
        return {
            "status": "ok" if not drift else "degraded",
            "threshold": baseline.get("threshold", self.threshold),
            "current": current,
            "drift": drift,
        }

    def metrics(self, text: str) -> dict[str, Any]:
        sentences = _sentences(text)
        rules = WritingRulesStore(self.root, slug=self.slug).list()
        return {
            "dialogue_density": _dialogue_density(text),
            "punctuation": {
                "quotes": text.count('"') + text.count("\u201c") + text.count("\u201d"),
                "em_dash": text.count("\u2014") + text.count("--"),
                "comma": text.count(","),
                "period": text.count(".") + text.count("\u3002"),
            },
            "narration_distance": len(re.findall(r"\b(realized|noticed|saw|felt)\b", text, flags=re.IGNORECASE)),
            "avg_sentence_length": sum(len(sentence.split()) for sentence in sentences) / max(1, len(sentences)),
            "keyword_style": _top_keywords(text),
            "custom_rule_hit_rate": _custom_rule_hit_rate(text, rules),
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"slug": self.slug, "threshold": self.threshold, "samples": []}
        return yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}


def read_golden_samples(path: str | Path) -> dict[str, str]:
    root = Path(path)
    samples: dict[str, str] = {}
    for item in sorted(root.glob("*.md")):
        samples[item.stem] = item.read_text(encoding="utf-8")
    for item in sorted(root.glob("*.txt")):
        samples[item.stem] = item.read_text(encoding="utf-8")
    return samples


def _metric_drift(sample_id: str, expected: dict[str, Any], actual: dict[str, Any], threshold: float) -> list[dict[str, Any]]:
    drift: list[dict[str, Any]] = []
    for metric in ("dialogue_density", "narration_distance", "avg_sentence_length", "custom_rule_hit_rate"):
        expected_value = float(expected.get(metric, 0))
        actual_value = float(actual.get(metric, 0))
        limit = max(threshold, abs(expected_value) * threshold)
        if abs(actual_value - expected_value) > limit:
            drift.append(
                {
                    "sample": sample_id,
                    "metric": metric,
                    "expected": expected_value,
                    "actual": actual_value,
                    "delta": actual_value - expected_value,
                }
            )
    for mark, expected_value in (expected.get("punctuation") or {}).items():
        actual_value = (actual.get("punctuation") or {}).get(mark, 0)
        if abs(float(actual_value) - float(expected_value)) > max(1, abs(float(expected_value)) * threshold):
            drift.append(
                {
                    "sample": sample_id,
                    "metric": f"punctuation.{mark}",
                    "expected": expected_value,
                    "actual": actual_value,
                    "delta": actual_value - expected_value,
                }
            )
    return drift


def _dialogue_density(text: str) -> float:
    quoted = len(re.findall(r'"([^"]*)"', text))
    return quoted / max(1, len(_sentences(text)))


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"[.!?\u3002\uff01\uff1f]+", text) if item.strip()]


def _top_keywords(text: str) -> list[str]:
    words = [word for word in re.findall(r"[A-Za-z]{4,}", text.lower()) if word not in {"that", "with", "from"}]
    counts = {word: words.count(word) for word in set(words)}
    return [word for word, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:8]]


def _custom_rule_hit_rate(text: str, rules) -> float:
    if not rules:
        return 1.0
    hits = 0
    for rule in rules:
        lowered = rule.text.lower()
        if "quotation" in lowered or "quote" in lowered:
            hits += 0 if '"' in text else 1
        elif "dash" in lowered:
            hits += 0 if "\u2014" in text or "--" in text else 1
        else:
            hits += 1
    return hits / len(rules)


__all__ = ["LITERARY_BASELINE_NAME", "LiteraryRegressionSuite", "read_golden_samples"]
