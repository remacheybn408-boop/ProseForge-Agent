"""Writing quality gates and chapter reports."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .style_profile import StyleProfileCompiler


QUALITY_REPORT_DIR = "quality_reports"


@dataclass(frozen=True)
class QualityViolation:
    """One actionable writing quality violation."""

    code: str
    message: str
    line: int
    column: int
    suggestion: str
    severity: str = "warning"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QualityCheckResult:
    """Quality check result for one chapter."""

    chapter: str
    status: str
    violations: list[QualityViolation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "status": self.status,
            "violations": [violation.to_dict() for violation in self.violations],
        }


class WritingQualityGateRunner:
    """Run deterministic writing quality gates for chapters."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug
        self.report_root = self.project_root / QUALITY_REPORT_DIR

    def check_text(self, text: str, *, chapter: str) -> dict[str, Any]:
        violations: list[QualityViolation] = []
        violations.extend(self._style_violations(text, chapter))
        violations.extend(_pov_violations(text))
        violations.extend(_narration_violations(text))
        result = QualityCheckResult(
            chapter=chapter,
            status="ok" if not violations else "degraded",
            violations=violations,
        )
        self._write_result(result)
        return result.to_dict()

    def check_chapter(self, chapter: str) -> dict[str, Any]:
        path = self.project_root / "chapters" / f"{chapter}.md"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        result = self.check_text(text, chapter=chapter)
        result["path"] = str(path)
        return result

    def report(self) -> dict[str, Any]:
        chapters = []
        for path in sorted(self.report_root.glob("*.yaml")):
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            chapters.append(payload)
        total = sum(len(chapter.get("violations", [])) for chapter in chapters)
        return {
            "status": "ok" if total == 0 else "degraded",
            "summary": {"chapters": len(chapters), "total_violations": total},
            "chapters": chapters,
        }

    def _style_violations(self, text: str, chapter: str) -> list[QualityViolation]:
        style_result = StyleProfileCompiler(self.root, slug=self.slug).check_text(text, chapter=chapter)
        violations: list[QualityViolation] = []
        for violation in style_result["violations"]:
            line, column = _location_for_code(text, violation["code"])
            violations.append(
                QualityViolation(
                    code=violation["code"],
                    message=violation["message"],
                    line=line,
                    column=column,
                    suggestion=_suggestion_for_code(violation["code"]),
                )
            )
        return violations

    def _write_result(self, result: QualityCheckResult) -> None:
        self.report_root.mkdir(parents=True, exist_ok=True)
        path = self.report_root / f"{result.chapter}.yaml"
        path.write_text(
            yaml.safe_dump(result.to_dict(), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )


def _pov_violations(text: str) -> list[QualityViolation]:
    first = re.search(r"\bI\b|\bme\b|\bmy\b", text)
    third = re.search(r"\bShe\b|\bHe\b|\bThey\b|\bHer\b|\bHis\b", text)
    if not first or not third:
        return []
    line, column = _offset_to_line_column(text, third.start())
    return [
        QualityViolation(
            code="pov_consistency",
            message="first-person and third-person POV markers appear in the same passage",
            line=line,
            column=column,
            suggestion="Keep the scene in one POV or mark a deliberate POV break.",
        )
    ]


def _narration_violations(text: str) -> list[QualityViolation]:
    violations: list[QualityViolation] = []
    show = re.search(r"\bfelt\s+\w+|\bwas\s+(sad|angry|afraid|happy)\b", text, flags=re.IGNORECASE)
    if show:
        line, column = _offset_to_line_column(text, show.start())
        violations.append(
            QualityViolation(
                code="show_dont_tell",
                message="emotion is told directly instead of dramatized",
                line=line,
                column=column,
                suggestion="Replace the label with physical action, dialogue, or concrete sensory detail.",
            )
        )
    passive = re.search(r"\b(was|were|is|are|been|being)\s+\w+ed\b", text, flags=re.IGNORECASE)
    if passive:
        line, column = _offset_to_line_column(text, passive.start())
        violations.append(
            QualityViolation(
                code="passive_narration",
                message="passive narration weakens the action",
                line=line,
                column=column,
                suggestion="Name the actor and use an active verb where possible.",
            )
        )
    distance = re.search(r"\b(realized|noticed|saw)\b", text, flags=re.IGNORECASE)
    if distance:
        line, column = _offset_to_line_column(text, distance.start())
        violations.append(
            QualityViolation(
                code="narration_distance",
                message="filter verb increases narrative distance",
                line=line,
                column=column,
                suggestion="Show the perception directly unless the filter is intentional.",
            )
        )
    tense = re.search(r"\b(yesterday|tomorrow)\b.*\b(now|today)\b|\b(now|today)\b.*\b(yesterday|tomorrow)\b", text, flags=re.IGNORECASE | re.DOTALL)
    if tense:
        line, column = _offset_to_line_column(text, tense.start())
        violations.append(
            QualityViolation(
                code="time_distance",
                message="relative time markers may conflict",
                line=line,
                column=column,
                suggestion="Anchor the time reference to story day or chapter chronology.",
            )
        )
    return violations


def _location_for_code(text: str, code: str) -> tuple[int, int]:
    needles = {
        "no_quotes": ['"', "\u201c", "\u201d", "\u300c", "\u300d"],
        "no_em_dash": ["\u2014", "--"],
    }
    for needle in needles.get(code, []):
        index = text.find(needle)
        if index >= 0:
            return _offset_to_line_column(text, index)
    return (1, 1)


def _suggestion_for_code(code: str) -> str:
    return {
        "no_quotes": "Rewrite dialogue without quotation marks or update the style profile.",
        "no_em_dash": "Replace the em dash with a comma, period, or sentence break.",
        "dialogue_ratio": "Convert some dialogue into action beats or narration.",
        "adjective_density": "Cut stacked modifiers and keep only concrete details.",
    }.get(code, "Revise the passage or adjust the gate rule.")


def _offset_to_line_column(text: str, offset: int) -> tuple[int, int]:
    prefix = text[:offset]
    line = prefix.count("\n") + 1
    last_newline = prefix.rfind("\n")
    column = offset + 1 if last_newline < 0 else offset - last_newline
    return line, column


__all__ = ["QUALITY_REPORT_DIR", "QualityCheckResult", "QualityViolation", "WritingQualityGateRunner"]
