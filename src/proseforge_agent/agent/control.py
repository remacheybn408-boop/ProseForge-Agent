"""Cooperative control signals for long-running agent loops."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ControlSignal:
    """One cooperative control signal consumed at a safe point."""

    kind: str
    instruction: str = ""
    reason: str = ""
    trace_id: str = ""


class ControlToken:
    """Thread-safe enough single-process token for interrupt and steer requests."""

    def __init__(self) -> None:
        self._signal: ControlSignal | None = None

    @staticmethod
    def interrupt_signal(reason: str = "") -> ControlSignal:
        return ControlSignal(kind="interrupt", reason=reason, trace_id=f"control-{uuid.uuid4().hex[:12]}")

    @staticmethod
    def steer_signal(instruction: str) -> ControlSignal:
        return ControlSignal(kind="steer", instruction=instruction, trace_id=f"control-{uuid.uuid4().hex[:12]}")

    def interrupt(self, reason: str = "user requested stop") -> None:
        self._signal = self.interrupt_signal(reason)

    def steer(self, instruction: str) -> None:
        self._signal = self.steer_signal(instruction)

    def poll(self) -> ControlSignal | None:
        signal = self._signal
        self._signal = None
        return signal


__all__ = ["ControlSignal", "ControlToken"]
