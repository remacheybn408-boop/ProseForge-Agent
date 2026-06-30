"""Novel-project health doctor: diagnose and non-destructively repair project structure."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .manifest import MANIFEST_NAME


# Directories a healthy novel project is expected to carry.
PROJECT_HEALTH_DIRS = ("chapters", "revisions")
QUARANTINE_DIR = "quarantine"

_CHAPTER_RE = re.compile(r"^ch_(\d+)$")


@dataclass(frozen=True)
class HealthIssue:
    """One detected project-health problem."""

    kind: str
    target: str
    severity: str
    fixable: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HealthReport:
    """Project-health diagnosis with any repairs that were applied."""

    slug: str
    status: str
    issues: list[HealthIssue] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "status": self.status,
            "issues": [issue.to_dict() for issue in self.issues],
            "fixed": list(self.fixed),
        }


class ProjectHealthDoctor:
    """Diagnose novel-project structure problems and optionally repair the safe ones."""

    def __init__(self, root: str | Path, *, slug: str) -> None:
        self.root = Path(root)
        self.slug = slug
        self.project_root = self.root / "projects" / slug

    def diagnose(self, *, fix: bool = False) -> HealthReport:
        issues: list[HealthIssue] = []
        fixed: list[str] = []

        self._check_directories(issues, fixed, fix=fix)
        self._check_orphans(issues, fixed, fix=fix)
        self._check_numbering(issues)

        status = "ok" if not issues else "degraded"
        return HealthReport(slug=self.slug, status=status, issues=issues, fixed=fixed)

    def _check_directories(self, issues: list[HealthIssue], fixed: list[str], *, fix: bool) -> None:
        for name in PROJECT_HEALTH_DIRS:
            path = self.project_root / name
            if path.exists():
                continue
            if fix:
                path.mkdir(parents=True, exist_ok=True)
                fixed.append(f"created directory {name}")
            else:
                issues.append(
                    HealthIssue(
                        kind="missing_directory",
                        target=name,
                        severity="warning",
                        fixable=True,
                        detail=f"expected project directory {name!r} is missing",
                    )
                )

    def _check_orphans(self, issues: list[HealthIssue], fixed: list[str], *, fix: bool) -> None:
        if not self.project_root.exists():
            return
        quarantine = self.project_root / QUARANTINE_DIR
        for entry in sorted(self.project_root.iterdir()):
            if not entry.is_file() or entry.name == MANIFEST_NAME:
                continue
            if fix:
                quarantine.mkdir(parents=True, exist_ok=True)
                entry.rename(quarantine / entry.name)
                fixed.append(f"quarantined orphan {entry.name}")
            else:
                issues.append(
                    HealthIssue(
                        kind="orphan_file",
                        target=entry.name,
                        severity="warning",
                        fixable=True,
                        detail="stray file is not under a recognized project directory",
                    )
                )

    def _check_numbering(self, issues: list[HealthIssue]) -> None:
        chapters_root = self.project_root / "chapters"
        if not chapters_root.exists():
            return
        numbers: list[int] = []
        for path in sorted(chapters_root.glob("*.md")):
            match = _CHAPTER_RE.match(path.stem)
            if match:
                numbers.append(int(match.group(1)))
        if len(numbers) < 2:
            return
        present = set(numbers)
        for number in range(min(numbers), max(numbers) + 1):
            if number not in present:
                issues.append(
                    HealthIssue(
                        kind="chapter_numbering",
                        target=f"ch_{number:03d}",
                        severity="error",
                        fixable=False,
                        detail="chapter number is missing from the sequence",
                    )
                )
        for number in sorted({n for n in numbers if numbers.count(n) > 1}):
            issues.append(
                HealthIssue(
                    kind="chapter_numbering",
                    target=f"ch_{number:03d}",
                    severity="error",
                    fixable=False,
                    detail="chapter number is duplicated",
                )
            )


__all__ = [
    "PROJECT_HEALTH_DIRS",
    "QUARANTINE_DIR",
    "HealthIssue",
    "HealthReport",
    "ProjectHealthDoctor",
]
