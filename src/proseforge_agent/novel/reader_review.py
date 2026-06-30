"""Reader experience review: editorial-grade reader analysis for chapters and volumes."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


READER_REPORT_DIR = "reader_reports"

READER_SIGNAL_NAMES = (
    "pacing",
    "info_density",
    "suspense",
    "payoff",
    "oppression",
    "fatigue",
    "confusion",
    "emotion_curve",
    "chapter_hook",
)

_SUSPENSE_CUES = ("但是", "然而", "突然", "忽然", "可是", "难道", "为什么", "?", "？", "but", "suddenly", "however", "why")
_PAYOFF_CUES = ("胜利", "终于", "成功", "反击", "逆袭", "痛快", "畅快", "triumph", "finally", "victory", "won")
_OPPRESSION_CUES = ("压抑", "绝望", "黑暗", "痛苦", "窒息", "沉重", "死寂", "despair", "dark", "heavy", "suffocat")
_EMOTION_CUES = _PAYOFF_CUES + _OPPRESSION_CUES + ("笑", "哭", "怒", "恐惧", "喜悦", "愤怒", "悲伤", "fear", "joy", "anger", "grief", "smile", "cry")
_HOOK_CUES = _SUSPENSE_CUES + ("……", "—", "未完", "到底", "竟然", "cliff")
_PRONOUNS = ("他们", "她们", "他", "她", "它", "我", "你", "they", "him", "her", "she", "he")

_SUGGESTIONS = {
    "pacing": "调整句长节奏：拆开冗长段落或合并过碎短句，让推进更稳。",
    "info_density": "平衡信息密度：稀释处补充细节，过载处把设定分散到后续章节。",
    "suspense": "强化悬念：在场景中埋入未解的问题或迫近的威胁。",
    "payoff": "补一个爽点：让主角在本章取得一次可感知的进展或反击。",
    "oppression": "降低压抑感：在沉重段落之间留出喘息的明亮或希望节拍。",
    "fatigue": "消除疲劳点：替换重复的词句与雷同句式。",
    "confusion": "减少读者困惑：在代词密集处补上明确的人名锚点。",
    "emotion_curve": "拉开情绪曲线：让本章前后的情绪强度形成起伏而非平直。",
    "chapter_hook": "加强章节钩子：用悬念、反转或未尽之言收尾，牵引读者翻页。",
}


@dataclass(frozen=True)
class ReaderSignal:
    """One reader-experience signal with a normalized health score."""

    name: str
    score: float
    level: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReaderSuggestion:
    """One actionable revision suggestion tied to a signal."""

    signal: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReaderReport:
    """Structured reader-experience report for a chapter or volume."""

    target: str
    scope: str
    status: str
    signals: list[ReaderSignal] = field(default_factory=list)
    suggestions: list[ReaderSuggestion] = field(default_factory=list)
    path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "scope": self.scope,
            "status": self.status,
            "signals": [signal.to_dict() for signal in self.signals],
            "suggestions": [suggestion.to_dict() for suggestion in self.suggestions],
            "path": str(self.path) if self.path is not None else "",
        }


class ReaderExperienceReviewer:
    """Produce deterministic, editorial-grade reader reports for chapters and volumes."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.chapters_root = self.project_root / "chapters"
        self.report_root = self.project_root / READER_REPORT_DIR

    def review(self, *, chapter: str | None = None, volume: str | None = None) -> ReaderReport:
        if bool(chapter) == bool(volume):
            raise ValueError("pass exactly one of chapter or volume")
        if chapter:
            text = self._read_chapter(chapter)
            return self._review_text(text, target=chapter, scope="chapter")
        text = self._read_volume(volume or "")
        return self._review_text(text, target=volume or "", scope="volume")

    def _read_chapter(self, chapter: str) -> str:
        path = self.chapters_root / f"{chapter}.md"
        if not path.exists():
            raise ValueError(f"chapter {chapter!r} not found at {path}")
        return path.read_text(encoding="utf-8")

    def _read_volume(self, volume: str) -> str:
        chapters = sorted(self.chapters_root.glob("*.md")) if self.chapters_root.exists() else []
        if not chapters:
            raise ValueError(f"volume {volume!r} has no chapters under {self.chapters_root}")
        return "\n".join(path.read_text(encoding="utf-8") for path in chapters)

    def _review_text(self, text: str, *, target: str, scope: str) -> ReaderReport:
        signals = _analyze(text)
        suggestions = [
            ReaderSuggestion(signal=signal.name, message=_SUGGESTIONS[signal.name])
            for signal in signals
            if signal.level != "ok"
        ]
        status = "ok" if all(signal.level == "ok" for signal in signals) else "degraded"
        report = ReaderReport(
            target=target,
            scope=scope,
            status=status,
            signals=signals,
            suggestions=suggestions,
            path=self.report_root / f"{target}.md",
        )
        self._write_report(report)
        return report

    def _write_report(self, report: ReaderReport) -> None:
        self.report_root.mkdir(parents=True, exist_ok=True)
        lines = [f"# Reader Experience Review — {report.target} ({report.scope})", "", "## Signals", ""]
        for signal in report.signals:
            lines.append(f"- {signal.name}: {signal.level} ({signal.score:.2f}) — {signal.detail}")
        lines += ["", "## Suggestions", ""]
        if report.suggestions:
            lines += [f"- [{item.signal}] {item.message}" for item in report.suggestions]
        else:
            lines.append("- 无需改动：各项读者体验信号均健康。")
        assert report.path is not None
        report.path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _level(score: float) -> str:
    if score >= 0.7:
        return "ok"
    if score >= 0.4:
        return "watch"
    return "risk"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s*", text.strip())
    return [part for part in parts if part.strip()]


def _tokens(text: str) -> list[str]:
    latin = re.findall(r"[A-Za-z0-9']+", text.lower())
    cjk = re.findall(r"[一-鿿]", text)
    return latin + cjk


def _count_cues(text: str, cues: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(lowered.count(cue.lower()) for cue in cues)


def _analyze(text: str) -> list[ReaderSignal]:
    sentences = _sentences(text)
    tokens = _tokens(text)
    sentence_count = max(1, len(sentences))
    token_count = max(1, len(tokens))
    return [
        _pacing(sentences),
        _info_density(tokens, token_count),
        _density_signal("suspense", text, _SUSPENSE_CUES, sentence_count, want=True),
        _density_signal("payoff", text, _PAYOFF_CUES, sentence_count, want=True),
        _oppression(text, sentence_count),
        _fatigue(tokens, token_count),
        _confusion(text, sentence_count),
        _emotion_curve(text),
        _chapter_hook(sentences),
    ]


def _pacing(sentences: list[str]) -> ReaderSignal:
    if not sentences:
        return ReaderSignal("pacing", 0.0, "risk", "章节为空，无法评估节奏。")
    avg = sum(len(sentence) for sentence in sentences) / len(sentences)
    score = _clamp(1.0 - abs(avg - 22.0) / 40.0)
    return ReaderSignal("pacing", round(score, 2), _level(score), f"平均句长 {avg:.1f} 字。")


def _info_density(tokens: list[str], token_count: int) -> ReaderSignal:
    diversity = len(set(tokens)) / token_count
    score = _clamp(1.0 - abs(diversity - 0.6) / 0.5)
    return ReaderSignal("info_density", round(score, 2), _level(score), f"词汇多样度 {diversity:.2f}。")


def _density_signal(name: str, text: str, cues: tuple[str, ...], sentence_count: int, *, want: bool) -> ReaderSignal:
    density = _count_cues(text, cues) / sentence_count
    score = _clamp(density * 3.0) if want else _clamp(1.0 - density * 4.0)
    detail = f"{name} 线索密度 {density:.2f}/句。"
    return ReaderSignal(name, round(score, 2), _level(score), detail)


def _oppression(text: str, sentence_count: int) -> ReaderSignal:
    density = _count_cues(text, _OPPRESSION_CUES) / sentence_count
    score = _clamp(1.0 - density * 4.0)
    return ReaderSignal("oppression", round(score, 2), _level(score), f"压抑线索密度 {density:.2f}/句。")


def _fatigue(tokens: list[str], token_count: int) -> ReaderSignal:
    if not tokens:
        return ReaderSignal("fatigue", 0.0, "risk", "无正文内容。")
    most_common = Counter(tokens).most_common(1)[0][1]
    ratio = most_common / token_count
    score = _clamp(1.0 - (ratio - 0.12) / 0.3)
    return ReaderSignal("fatigue", round(score, 2), _level(score), f"最高词频占比 {ratio:.2f}。")


def _confusion(text: str, sentence_count: int) -> ReaderSignal:
    pronouns = _count_cues(text, _PRONOUNS)
    per_sentence = pronouns / sentence_count
    score = _clamp(1.0 - (per_sentence - 0.5) / 1.5)
    return ReaderSignal("confusion", round(score, 2), _level(score), f"代词密度 {per_sentence:.2f}/句。")


def _emotion_curve(text: str) -> ReaderSignal:
    half = max(1, len(text) // 2)
    first = _count_cues(text[:half], _EMOTION_CUES) / half * 100
    second = _count_cues(text[half:], _EMOTION_CUES) / max(1, len(text) - half) * 100
    diff = abs(first - second)
    score = _clamp(diff * 0.8)
    return ReaderSignal("emotion_curve", round(score, 2), _level(score), f"前后情绪强度差 {diff:.2f}。")


def _chapter_hook(sentences: list[str]) -> ReaderSignal:
    if not sentences:
        return ReaderSignal("chapter_hook", 0.0, "risk", "无结尾句。")
    ending = sentences[-1]
    has_hook = any(cue.lower() in ending.lower() for cue in _HOOK_CUES)
    score = 0.9 if has_hook else 0.2
    detail = "结尾留有钩子。" if has_hook else "结尾收束、缺少牵引。"
    return ReaderSignal("chapter_hook", score, _level(score), detail)


__all__ = [
    "READER_REPORT_DIR",
    "READER_SIGNAL_NAMES",
    "ReaderExperienceReviewer",
    "ReaderReport",
    "ReaderSignal",
    "ReaderSuggestion",
]
