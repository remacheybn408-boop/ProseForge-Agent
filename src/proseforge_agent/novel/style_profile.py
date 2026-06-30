"""Tone and style preference compiler."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .writing_rules import WritingRulesStore


STYLE_PROFILE_NAME = "style_profile.yaml"


@dataclass(frozen=True)
class StyleProfile:
    """Compiled style preferences as executable checks and prompt fragments."""

    preferences: list[str] = field(default_factory=list)
    lexical_checks: list[str] = field(default_factory=list)
    punctuation_checks: list[str] = field(default_factory=list)
    dialogue_ratio: dict[str, float] = field(default_factory=dict)
    narration_distance_checks: list[str] = field(default_factory=list)
    style_prompt_fragment: str = ""
    review_gate_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StyleProfile":
        return cls(
            preferences=[str(item) for item in payload.get("preferences", [])],
            lexical_checks=[str(item) for item in payload.get("lexical_checks", [])],
            punctuation_checks=[str(item) for item in payload.get("punctuation_checks", [])],
            dialogue_ratio=dict(payload.get("dialogue_ratio") or {}),
            narration_distance_checks=[str(item) for item in payload.get("narration_distance_checks", [])],
            style_prompt_fragment=str(payload.get("style_prompt_fragment") or ""),
            review_gate_rules=[str(item) for item in payload.get("review_gate_rules", [])],
        )


class StyleProfileCompiler:
    """Compile natural writing preferences into deterministic review checks."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.path = self.project_root / STYLE_PROFILE_NAME

    def compile(self, preferences: list[str]) -> StyleProfile:
        lexical_checks: list[str] = []
        punctuation_checks: list[str] = []
        narration_checks: list[str] = []
        dialogue_ratio: dict[str, float] = {}
        review_gate_rules: list[str] = []
        normalized = [item.strip() for item in preferences if item.strip()]
        for preference in normalized:
            lowered = preference.lower()
            if _mentions_quotes(lowered):
                _append_unique(punctuation_checks, "no_quotes")
                _append_unique(review_gate_rules, "no_quotes")
            if _mentions_dash(lowered):
                _append_unique(punctuation_checks, "no_em_dash")
                _append_unique(review_gate_rules, "no_em_dash")
            if _mentions_low_dialogue(lowered):
                dialogue_ratio["max"] = 0.35
                _append_unique(review_gate_rules, "dialogue_ratio")
            if "few adjectives" in lowered or "少形容词" in preference:
                _append_unique(lexical_checks, "adjective_density")
            if "show-don't-tell" in lowered or "show dont tell" in lowered or "show don't tell" in lowered:
                _append_unique(narration_checks, "show_dont_tell")
        profile = StyleProfile(
            preferences=normalized,
            lexical_checks=lexical_checks,
            punctuation_checks=punctuation_checks,
            dialogue_ratio=dialogue_ratio,
            narration_distance_checks=narration_checks,
            style_prompt_fragment="; ".join(normalized),
            review_gate_rules=review_gate_rules,
        )
        self._write(profile)
        return profile

    def compile_from_rules(self) -> StyleProfile:
        preferences = [rule.text for rule in WritingRulesStore(self.root, slug=self.slug).list()]
        return self.compile(preferences)

    def load(self) -> StyleProfile:
        if not self.path.exists():
            return StyleProfile()
        payload = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        return StyleProfile.from_dict(payload)

    def check_text(self, text: str, *, chapter: str = "") -> dict[str, Any]:
        profile = self.load()
        violations: list[dict[str, Any]] = []
        if "no_quotes" in profile.punctuation_checks and _has_quotes(text):
            violations.append({"code": "no_quotes", "chapter": chapter, "message": "quotation marks are disallowed"})
        if "no_em_dash" in profile.punctuation_checks and ("\u2014" in text or "--" in text):
            violations.append({"code": "no_em_dash", "chapter": chapter, "message": "em dashes are disallowed"})
        max_dialogue = profile.dialogue_ratio.get("max")
        ratio = _dialogue_ratio(text)
        if max_dialogue is not None and ratio > float(max_dialogue):
            violations.append(
                {
                    "code": "dialogue_ratio",
                    "chapter": chapter,
                    "message": "dialogue ratio exceeds profile maximum",
                    "ratio": ratio,
                    "max": max_dialogue,
                }
            )
        if "adjective_density" in profile.lexical_checks:
            density = _adjective_density(text)
            if density > 0.15:
                violations.append(
                    {
                        "code": "adjective_density",
                        "chapter": chapter,
                        "message": "adjective density exceeds profile preference",
                        "density": density,
                    }
                )
        return {"status": "ok" if not violations else "degraded", "chapter": chapter, "violations": violations}

    def check_chapter(self, chapter: str) -> dict[str, Any]:
        path = self.project_root / "chapters" / f"{chapter}.md"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        result = self.check_text(text, chapter=chapter)
        result["path"] = str(path)
        return result

    def _write(self, profile: StyleProfile) -> None:
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            yaml.safe_dump(profile.to_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


def _mentions_quotes(value: str) -> bool:
    return "quote" in value or "quotation" in value or "引号" in value


def _mentions_dash(value: str) -> bool:
    return "em dash" in value or "dash" in value or "破折号" in value


def _mentions_low_dialogue(value: str) -> bool:
    return "low dialogue" in value or "dialogue density" in value or "低对话" in value


def _has_quotes(text: str) -> bool:
    return any(mark in text for mark in ('"', "\u201c", "\u201d", "\u300c", "\u300d"))


def _dialogue_ratio(text: str) -> float:
    if not text:
        return 0.0
    quoted_matches = list(re.finditer(r'"([^"]*)"', text))
    quoted = sum(len(match.group(1)) for match in quoted_matches)
    char_ratio = quoted / len(text)
    sentence_count = max(1, len(re.findall(r"[.!?\u3002\uff01\uff1f]", text)))
    segment_ratio = len(quoted_matches) / sentence_count
    return max(char_ratio, segment_ratio)


def _adjective_density(text: str) -> float:
    words = re.findall(r"[A-Za-z]+", text.lower())
    if not words:
        return 0.0
    adjective_like = {"beautiful", "bright", "dark", "quiet", "very", "ornate", "soft", "cold"}
    return sum(1 for word in words if word in adjective_like) / len(words)


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


__all__ = ["STYLE_PROFILE_NAME", "StyleProfile", "StyleProfileCompiler"]
