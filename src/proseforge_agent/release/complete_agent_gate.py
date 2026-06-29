"""Complete-agent release gate aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


REQUIRED_COMPLETE_AGENT_GATES: tuple[str, ...] = (
    "e2e_demo",
    "chat_drill",
    "provider_certification",
    "memory_audit",
    "install_doctor",
    "native_qa",
    "agent_eval",
    "docs_examples",
    "support_bundle",
)


@dataclass(frozen=True)
class ReleaseDecision:
    """Aggregate decision for the complete-agent release gate."""

    passed: bool
    status: str
    required_gates: list[str] = field(default_factory=list)
    passed_gates: list[str] = field(default_factory=list)
    failed_gates: list[str] = field(default_factory=list)
    missing_gates: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def render_lines(self) -> list[str]:
        lines = [f"status={self.status}"]
        for gate in self.required_gates:
            if gate in self.passed_gates:
                state = "ok"
            elif gate in self.failed_gates:
                state = "failed"
            else:
                state = "missing"
            lines.append(f"{gate} -> {state}")
        return lines


class CompleteAgentReleaseGate:
    """Combine existing release reports into the complete-agent gate."""

    required_gates = REQUIRED_COMPLETE_AGENT_GATES

    def evaluate(self, reports: Mapping[str, Any]) -> ReleaseDecision:
        passed: list[str] = []
        failed: list[str] = []
        missing: list[str] = []
        details: dict[str, Any] = {}
        for gate in self.required_gates:
            if gate not in reports:
                missing.append(gate)
                continue
            report = reports[gate]
            details[gate] = report
            if _report_passed(report):
                passed.append(gate)
            else:
                failed.append(gate)
        ok = not failed and not missing
        return ReleaseDecision(
            passed=ok,
            status="ok" if ok else "blocked",
            required_gates=list(self.required_gates),
            passed_gates=passed,
            failed_gates=failed,
            missing_gates=missing,
            details=details,
        )


def _report_passed(report: Any) -> bool:
    if isinstance(report, bool):
        return report
    if isinstance(report, str):
        return report.lower() in {"ok", "pass", "passed"}
    if isinstance(report, Mapping):
        if "passed" in report:
            return bool(report["passed"])
        return str(report.get("status", "")).lower() in {"ok", "pass", "passed"}
    return False


__all__ = [
    "CompleteAgentReleaseGate",
    "REQUIRED_COMPLETE_AGENT_GATES",
    "ReleaseDecision",
]
