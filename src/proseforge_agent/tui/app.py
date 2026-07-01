"""Minimal terminal UI shell."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TextIO


@dataclass(frozen=True)
class TerminalState:
    provider: str = "fake"
    project: str | None = None
    mode: str = "general_chat"
    running: bool = True
    chat_history: tuple[str, ...] = field(default_factory=tuple)

    def render_lines(self) -> list[str]:
        return [
            "ProseForge Agent TUI",
            f"Provider: {self.provider}",
            f"Project: {self.project or '(none)'}",
            f"Mode: {self.mode}",
            f"Status: {'running' if self.running else 'stopped'}",
            "History:",
            *([f"- {line}" for line in self.chat_history] or ["- (empty)"]),
        ]


class TerminalApp:
    """Deterministic stream-backed terminal shell."""

    def __init__(
        self,
        *,
        provider: str = "fake",
        project: str | None = None,
        mode: str = "general_chat",
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        history: tuple[str, ...] = (),
    ) -> None:
        self.state = TerminalState(
            provider=provider,
            project=project,
            mode=mode,
            chat_history=history,
        )
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout

    def start(self, *, check: bool = False) -> int:
        self.render()
        if check:
            return 0
        for raw_line in self.input_stream:
            line = raw_line.strip()
            if line in {"/exit", "/quit"}:
                break
            if line:
                self.output_stream.write(f"> {line}\n")
        return 0

    def render(self) -> None:
        self.output_stream.write("\n".join(self.state.render_lines()))
        self.output_stream.write("\n")
