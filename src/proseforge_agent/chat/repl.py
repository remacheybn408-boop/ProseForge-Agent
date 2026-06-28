"""stdin/stdout chat REPL."""

from __future__ import annotations

import sys
from typing import TextIO

from ..agent import AgentKernel, AgentTurnRequest, IntentRouter
from .session import ChatSessionStore


class ChatRepl:
    """Small command-loop wrapper around the injected Agent Kernel."""

    def __init__(
        self,
        *,
        provider,
        session_store: ChatSessionStore,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        mode: str = "general_chat",
        project_slug: str | None = None,
        permission_level: str = "read_only",
        session_id: str = "cli",
    ) -> None:
        self.provider = provider
        self.session_store = session_store
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self.mode = mode
        self.project_slug = project_slug
        self.permission_level = permission_level
        self.session_id = session_id
        self.kernel = AgentKernel(
            provider=provider,
            session_store=session_store,
            intent_router=IntentRouter(),
        )

    def run(self) -> int:
        """Run until /exit or EOF."""
        self.session_store.ensure_session(self.session_id, self.mode, self.project_slug)
        self._write("Chat REPL")
        for raw_line in self.input_stream:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("/"):
                should_exit = self._handle_command(line)
                if should_exit:
                    return 0
                continue
            result = self.kernel.run_turn(
                AgentTurnRequest(
                    session_id=self.session_id,
                    text=line,
                    mode=self.mode,
                    project_slug=self.project_slug,
                    permission_level=self.permission_level,
                )
            )
            self._write(result.text)
        return 0

    def _handle_command(self, line: str) -> bool:
        command, _, argument = line.partition(" ")
        argument = argument.strip()
        if command == "/exit":
            return True
        if command == "/help":
            self._write("Commands: /exit /help /mode <name> /project <slug|none> /sessions")
            return False
        if command == "/mode":
            if argument:
                self.mode = argument
            self._write(f"mode: {self.mode}")
            return False
        if command == "/project":
            if argument:
                self.project_slug = None if argument == "none" else argument
            self._write(f"project: {self.project_slug or '(none)'}")
            return False
        if command == "/sessions":
            self._write("Sessions")
            for session in self.session_store.list(project_slug=self.project_slug):
                suffix = f" ({session.project_slug})" if session.project_slug else ""
                self._write(f"- {session.id} -> {session.mode}{suffix}")
            return False
        self._write(f"unknown command: {command}")
        return False

    def _write(self, text: str) -> None:
        print(text, file=self.output_stream)


__all__ = ["ChatRepl"]
