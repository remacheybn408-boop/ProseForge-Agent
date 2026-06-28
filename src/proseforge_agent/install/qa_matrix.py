"""Cross-platform native QA matrix."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class QACheck:
    """One required native QA check."""

    platform: str
    name: str
    command: str
    expected_artifact: str
    automated: bool
    backing_card: str = ""

    @property
    def key(self) -> str:
        return f"{self.platform}.{self.name}"


@dataclass(frozen=True)
class CoverageReport:
    """Coverage result for required native QA checks."""

    status: str
    covered: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class NativeQAMatrix:
    """Required native checks for installable local agent releases."""

    @staticmethod
    def required_checks() -> list[QACheck]:
        checks: list[QACheck] = []
        for platform in ("windows", "macos", "linux"):
            checks.extend(
                [
                    QACheck(
                        platform,
                        "install",
                        f"pf-agent init --portable --non-interactive ({platform})",
                        ".pf-agent/config.yaml",
                        True,
                        "Task 41",
                    ),
                    QACheck(
                        platform,
                        "chat",
                        f"pf-agent chat --message hello --provider fake ({platform})",
                        "agent turn report",
                        True,
                        "Task 35",
                    ),
                    QACheck(
                        platform,
                        "doctor",
                        f"pf-agent doctor --section {platform}",
                        "doctor report",
                        True,
                        f"Task {'49' if platform == 'windows' else '50' if platform == 'macos' else '51'}",
                    ),
                    QACheck(
                        platform,
                        "uninstall",
                        "pf-agent uninstall --plan",
                        "uninstall plan",
                        True,
                        "Task 54",
                    ),
                    QACheck(
                        platform,
                        "paths",
                        "pf-agent doctor --section paths",
                        "app directory report",
                        True,
                        "Task 43",
                    ),
                    QACheck(
                        platform,
                        "secrets",
                        "pf-agent doctor --section secrets",
                        "secret backend report",
                        True,
                        "Task 45",
                    ),
                ]
            )
        return checks

    @staticmethod
    def group_by_platform(checks: Iterable[QACheck]) -> dict[str, list[QACheck]]:
        grouped: dict[str, list[QACheck]] = {"windows": [], "macos": [], "linux": []}
        for check in checks:
            grouped.setdefault(check.platform, []).append(check)
        return grouped

    def validate_coverage(self, covered_checks: Iterable[str]) -> CoverageReport:
        covered = set(covered_checks)
        required = {check.key for check in self.required_checks()}
        missing = sorted(required - covered)
        return CoverageReport(
            status="ok" if not missing else "blocked",
            covered=sorted(covered & required),
            missing=missing,
        )

    def to_dict(self) -> dict[str, object]:
        grouped = self.group_by_platform(self.required_checks())
        return {
            "platforms": {
                platform: [asdict(check) for check in checks]
                for platform, checks in grouped.items()
            }
        }


__all__ = ["CoverageReport", "NativeQAMatrix", "QACheck"]
