"""Autonomous, bounded agent loop over the single-turn kernel.

`AgentLoop` orchestrates many kernel turns toward a goal: it plans, acts (one
``kernel.run_turn`` per iteration), observes, optionally verifies, compacts the
working context when it grows past a threshold, and repeats until a stop
condition holds — goal satisfied, iteration/cost budget spent, progress stalls,
or the user interrupts. It never modifies the kernel (which stays single-turn and
independently testable) and never exceeds ``max_iterations`` (no runaway).

This implements the control flow in ``architecture/11-autonomous-agent-runtime.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import AgentTurnRequest

# Default marker a turn can emit to signal the goal is satisfied.
DEFAULT_DONE_MARKER = "[[done]]"


@dataclass(frozen=True)
class Budget:
    """Bounds for a run. ``cost_cap`` is delegated to Task 61's metering."""

    max_iterations: int = 10
    cost_cap: float | None = None


@dataclass
class StepRecord:
    """One loop iteration's record."""

    index: int
    text: str
    trace_id: str
    status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "text": self.text, "trace_id": self.trace_id, "status": self.status}


@dataclass
class LoopResult:
    """Outcome of an autonomous run."""

    status: str  # completed | stopped_budget | stopped_no_progress | stopped_unverified | interrupted
    steps: list[StepRecord] = field(default_factory=list)
    final_text: str = ""
    transcript_ref: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    compactions: int = 0
    resumable: bool = False
    checkpoint: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "final_text": self.final_text,
            "transcript_ref": self.transcript_ref,
            "compactions": self.compactions,
            "resumable": self.resumable,
            "checkpoint": self.checkpoint,
        }


class AgentLoop:
    """Drive many kernel turns toward a goal, bounded and reflective."""

    def __init__(
        self,
        kernel,
        budget: Budget,
        planner=None,
        verifier=None,
        control=None,
        *,
        criteria: dict | None = None,
        reflector=None,
        max_reflections: int = 1,
        event_bus=None,
        done_marker: str = DEFAULT_DONE_MARKER,
        no_progress_limit: int = 3,
        context_threshold: int = 12,
    ) -> None:
        self._kernel = kernel
        self._budget = budget
        self._planner = planner
        # verifier is a Task-70 Verifier (has .check); criteria are its acceptance
        # standards. reflector proposes bounded revisions on failure.
        self._verifier = verifier
        self._criteria = criteria
        self._max_reflections = max(0, max_reflections)
        self._reflector = reflector
        self._control = control
        self._event_bus = event_bus
        self._done_marker = done_marker
        self._no_progress_limit = max(1, no_progress_limit)
        self._context_threshold = max(1, context_threshold)
        self._pending_instruction: str | None = None

    def run(self, goal: str, context: dict | None = None) -> LoopResult:
        plan = self._planner.decompose(goal, context) if self._planner is not None else None
        steps: list[StepRecord] = []
        events: list[dict[str, Any]] = []
        working_context: list[str] = []
        compactions = 0
        last_text: str | None = None
        repeat_count = 0
        final_text = ""
        status = "stopped_budget"  # default if the budget is exhausted
        checkpoint: dict[str, Any] = {}
        resumable = False

        # A fresh reflector per run so its bounded budget resets.
        reflector = self._reflector
        if reflector is None and self._verifier is not None and self._criteria is not None:
            from .reflection import Reflector

            reflector = Reflector(max_reflections=self._max_reflections)
        self._pending_instruction = None

        for index in range(self._budget.max_iterations):
            control_signal = self._poll_control()
            if control_signal is not None and control_signal.kind == "interrupt":
                status = "interrupted"
                resumable = True
                checkpoint = self._checkpoint(goal, steps, status)
                event = {
                    "type": "control_interrupt",
                    "trace_id": control_signal.trace_id or f"control-{index + 1}",
                    "reason": control_signal.reason,
                    "safe_point": index,
                }
                events.append(event)
                self._emit(event)
                break
            if control_signal is not None and control_signal.kind == "steer":
                self._pending_instruction = control_signal.instruction
                event = {
                    "type": "control_steer",
                    "trace_id": control_signal.trace_id or f"control-{index + 1}",
                    "instruction": control_signal.instruction,
                    "safe_point": index,
                }
                events.append(event)
                self._emit(event)

            request = self._build_request(goal, plan, index)
            result = self._kernel.run_turn(request)
            trace_id = getattr(result, "trace_id", "") or f"trace-{index + 1}"
            step = StepRecord(index=index + 1, text=result.text, trace_id=trace_id)
            steps.append(step)
            event = {"type": "loop_step", "trace_id": trace_id, "index": index + 1}
            events.append(event)
            self._emit(event)
            final_text = result.text

            # Self-verification + bounded reflection (only when configured).
            if self._verifier is not None and self._criteria is not None:
                verdict = self._verifier.check(result.text, self._criteria)
                verify_event = {
                    "type": "verify",
                    "trace_id": trace_id,
                    "passed": verdict.passed,
                    "failures": verdict.failures,
                }
                events.append(verify_event)
                self._emit(verify_event)
                if not verdict.passed:
                    revision = reflector.revise(result.text, verdict)
                    if revision.retry:
                        refl_event = {
                            "type": "reflection",
                            "trace_id": trace_id,
                            "reason": revision.reason,
                        }
                        events.append(refl_event)
                        self._emit(refl_event)
                        # Retry the same work with the revision instruction; do not
                        # advance the plan or mark done on an unverified output.
                        self._pending_instruction = revision.instruction
                        continue
                    # Reflection budget exhausted and still failing: stop cleanly.
                    status = "stopped_unverified"
                    break

            # Mark plan progress so dependents unblock as work completes.
            if plan is not None:
                nxt = plan.next()
                if nxt is not None:
                    plan.update(nxt.id, "done", result_ref=trace_id)

            if self._is_done(result, plan):
                status = "completed"
                break

            # No-progress detection: identical outputs N times in a row.
            if result.text == last_text:
                repeat_count += 1
            else:
                repeat_count = 1
            last_text = result.text
            if repeat_count >= self._no_progress_limit:
                status = "stopped_no_progress"
                break

            # Compact the working context when it grows past the threshold.
            working_context.append(result.text)
            if len(working_context) > self._context_threshold:
                working_context = self._compact(working_context)
                compactions += 1
                events.append({"type": "context_compacted", "trace_id": trace_id})

        return LoopResult(
            status=status,
            steps=steps,
            final_text=final_text,
            transcript_ref="",
            events=events,
            compactions=compactions,
            resumable=resumable,
            checkpoint=checkpoint,
        )

    # -- helpers --------------------------------------------------------

    def _build_request(self, goal: str, plan, index: int) -> AgentTurnRequest:
        # A pending reflection instruction takes precedence: retry the same work.
        if self._pending_instruction:
            text = self._pending_instruction
            self._pending_instruction = None
            return AgentTurnRequest(
                session_id="autonomous",
                text=text,
                mode="general_chat",
                project_slug=None,
                permission_level="read_only",
            )
        text = goal
        if plan is not None:
            nxt = plan.next()
            if nxt is not None:
                text = nxt.title
        return AgentTurnRequest(
            session_id="autonomous",
            text=text,
            mode="general_chat",
            project_slug=None,
            permission_level="read_only",
        )

    def _is_done(self, result, plan) -> bool:
        if self._done_marker and self._done_marker in getattr(result, "text", ""):
            return True
        if plan is not None and plan.items and plan.is_complete():
            return True
        return False

    def _compact(self, working_context: list[str]) -> list[str]:
        """Summarize older context, keeping recent turns verbatim (never blind truncation)."""
        keep = max(1, self._context_threshold // 2)
        older = working_context[:-keep]
        recent = working_context[-keep:]
        summary = f"[compacted {len(older)} earlier steps]"
        return [summary, *recent]

    def _poll_control(self):
        if self._control is None:
            return None
        poll = getattr(self._control, "poll", None)
        if callable(poll):
            return poll()
        if getattr(self._control, "is_interrupted", lambda: False)():
            from .control import ControlToken

            return ControlToken.interrupt_signal("legacy interrupt signal")
        return None

    @staticmethod
    def _checkpoint(goal: str, steps: list[StepRecord], status: str) -> dict[str, Any]:
        return {
            "goal": goal,
            "status": status,
            "completed_steps": [step.to_dict() for step in steps],
            "next_step_index": len(steps) + 1,
        }

    def _emit(self, event: dict[str, Any]) -> None:
        if self._event_bus is None:
            return
        try:
            self._event_bus.emit(event["type"], event, trace_id=event.get("trace_id"))
        except Exception:  # noqa: BLE001 - diagnostics must not break the run
            pass


__all__ = ["AgentLoop", "Budget", "LoopResult", "StepRecord", "DEFAULT_DONE_MARKER"]
