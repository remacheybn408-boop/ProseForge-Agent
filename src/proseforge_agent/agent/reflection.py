"""Self-verification and reflection.

`Verifier` checks a step output against acceptance criteria and returns a
structured :class:`VerifyResult`. On failure, `Reflector` produces a
:class:`Revision` with a concrete next-attempt instruction so the autonomous
loop (Task 68) can retry within a bounded reflection budget. Domain verifiers
are pluggable via :meth:`Verifier.register` — e.g. the ProseForge ``post`` /
``review`` gates register as verifiers so a failed writing guard triggers a
rewrite instead of a silent accept.

Verification performs no mutating action; it only judges and proposes. This
realises the verify step in ``architecture/11-autonomous-agent-runtime.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# A verifier function judges an output against criteria. It may return a bool,
# or a ``(bool, detail)`` pair when it wants to explain a failure.
VerifierFn = Callable[[str, dict], Any]


@dataclass(frozen=True)
class VerifyResult:
    """Aggregated verdict over all applicable verifiers."""

    passed: bool
    failures: list[dict] = field(default_factory=list)
    score: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "failures": list(self.failures), "score": self.score}


@dataclass(frozen=True)
class Revision:
    """A reflection outcome: whether to retry and the next-attempt instruction."""

    retry: bool
    instruction: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"retry": self.retry, "instruction": self.instruction, "reason": self.reason}


def _normalize(outcome: Any) -> tuple[bool, str]:
    """Normalize a verifier return value into ``(passed, detail)``."""
    if isinstance(outcome, tuple):
        ok = bool(outcome[0])
        detail = str(outcome[1]) if len(outcome) > 1 and outcome[1] else ""
        return ok, detail
    return bool(outcome), ""


class Verifier:
    """Run generic and registered domain verifiers over an output."""

    def __init__(self, verifiers: dict[str, VerifierFn] | None = None) -> None:
        self._verifiers: dict[str, VerifierFn] = dict(verifiers or {})

    def register(self, name: str, verifier_fn: VerifierFn) -> None:
        """Add a domain verifier (e.g. ``proseforge_post``, ``proseforge_review``)."""
        self._verifiers[name] = verifier_fn

    def check(self, output: str, criteria: dict | None = None) -> VerifyResult:
        criteria = criteria or {}
        failures: list[dict] = []
        total = 0
        passed_count = 0
        for name, fn in self._verifiers.items():
            total += 1
            try:
                outcome = fn(output, criteria)
            except Exception as exc:  # noqa: BLE001 - a broken verifier fails its criterion, never crashes
                failures.append({"criterion": name, "detail": f"verifier error: {exc}"})
                continue
            ok, detail = _normalize(outcome)
            if ok:
                passed_count += 1
            else:
                failures.append({"criterion": name, "detail": detail or f"failed {name}"})
        score = (passed_count / total) if total else 1.0
        return VerifyResult(passed=not failures, failures=failures, score=score)


class Reflector:
    """Propose bounded revisions when verification fails."""

    def __init__(self, max_reflections: int = 2, events: list[dict] | None = None) -> None:
        self.max_reflections = max(0, max_reflections)
        self._used = 0
        self._events = events

    @property
    def used(self) -> int:
        return self._used

    def revise(self, output: str, verdict: VerifyResult) -> Revision:
        if verdict.passed:
            return Revision(retry=False, reason="verification passed")
        if self._used >= self.max_reflections:
            return Revision(retry=False, reason="reflection budget exhausted")

        details = "; ".join(
            f"{f['criterion']}: {f['detail']}" for f in verdict.failures
        ) or "未满足验收标准"
        instruction = f"上一次输出未通过校验（{details}）。请针对这些问题修订后重试。"
        self._used += 1
        if self._events is not None:
            self._events.append(
                {"type": "reflection", "reason": details, "instruction": instruction}
            )
        return Revision(retry=True, instruction=instruction, reason=details)


def register_proseforge_gates(verifier: Verifier, gates: dict[str, VerifierFn]) -> None:
    """Helper to register ProseForge domain gates (e.g. post/review) as verifiers.

    The gate functions are supplied by the caller (through the engine adapter);
    this module does not import or change the adapter.
    """
    for name, fn in gates.items():
        verifier.register(name, fn)


__all__ = [
    "VerifyResult",
    "Revision",
    "Verifier",
    "Reflector",
    "VerifierFn",
    "register_proseforge_gates",
]
