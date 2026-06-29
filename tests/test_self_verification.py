"""Tests for self-verification and reflection (Task 70)."""

from __future__ import annotations

import json
from pathlib import Path

from proseforge_agent.agent.reflection import Reflector, Verifier, VerifyResult

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "self-verification-and-reflection"
    / "criteria.json"
)


def test_failed_verification_triggers_one_reflection_retry():
    verifier = Verifier(verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]})
    verdict = verifier.check(output="短", criteria={"min_length": 50})
    assert verdict.passed is False
    revision = Reflector().revise(output="短", verdict=verdict)
    assert revision.retry is True
    assert revision.instruction


def test_passing_verification_triggers_no_retry():
    verifier = Verifier(verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]})
    verdict = verifier.check(output="x" * 60, criteria={"min_length": 50})
    assert verdict.passed is True
    revision = Reflector().revise(output="x" * 60, verdict=verdict)
    assert revision.retry is False


def test_reflection_is_bounded_by_max_reflections():
    verifier = Verifier(verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]})
    verdict = verifier.check(output="短", criteria={"min_length": 50})
    reflector = Reflector(max_reflections=1)
    first = reflector.revise(output="短", verdict=verdict)
    second = reflector.revise(output="短", verdict=verdict)
    assert first.retry is True
    assert second.retry is False  # budget exhausted, no infinite revise loop


def test_proseforge_review_can_register_as_a_domain_verifier():
    def proseforge_review(output, criteria):
        # Simulate the review gate: fail when the opening lacks a reader hook.
        has_hook = "钩子" in output
        return has_hook, "" if has_hook else "missing reader hook"

    verifier = Verifier()
    verifier.register("proseforge_review", proseforge_review)
    verdict = verifier.check(output="平淡的开头", criteria={})
    assert verdict.passed is False
    assert any(f["criterion"] == "proseforge_review" for f in verdict.failures)


def test_reflection_reason_is_emitted_as_event():
    events: list[dict] = []
    verifier = Verifier(verifiers={"min_length": lambda out, c: len(out) >= c["min_length"]})
    verdict = verifier.check(output="短", criteria={"min_length": 50})
    Reflector(events=events).revise(output="短", verdict=verdict)
    assert any(e["type"] == "reflection" for e in events)
    assert events[0]["reason"]


def test_verifier_failures_list_each_unmet_criterion():
    verifier = Verifier(
        verifiers={
            "min_length": lambda out, c: len(out) >= c["min_length"],
            "must_include": lambda out, c: c["must_include"] in out,
        }
    )
    verdict = verifier.check(output="短", criteria={"min_length": 50, "must_include": "钩子"})
    assert verdict.passed is False
    failed = {f["criterion"] for f in verdict.failures}
    assert failed == {"min_length", "must_include"}
    assert verdict.score == 0.0


def test_criteria_fixture_round_trips_utf8():
    criteria = json.loads(FIXTURE.read_text(encoding="utf-8"))
    verifier = Verifier(
        verifiers={"must_include": lambda out, c: c["must_include"] in out}
    )
    verdict = verifier.check(output="一个带钩子的开头", criteria=criteria)
    assert verdict.passed is True
    assert criteria["must_include"] == "钩子"
